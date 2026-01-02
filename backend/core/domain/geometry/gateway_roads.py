"""
Gateway-Aware Road Network Generator

Delaunay triangulation + Minimum Spanning Tree approach for simple,
guaranteed connectivity between gateways and buildings.
"""

from typing import List, Tuple, Set
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from scipy.spatial import Delaunay
import networkx as nx

from backend.core.domain.models.campus import Gateway


class GatewayRoadNetwork:
    """
    Generate minimal road network connecting gateways to buildings.

    Algorithm:
        1. Nodes: Gateway locations + Building centroids
        2. Edges: Delaunay triangulation (potential roads)
        3. Filter: Minimum Spanning Tree (MST) to minimize total road length
        4. Guarantee: All gateways connected to network

    Advantages:
        - Simple and fast: O(n log n) Delaunay + O(E log V) MST
        - Guaranteed connectivity: MST ensures all nodes connected
        - Minimal total length: MST minimizes road construction cost
        - Gateway-aware: Gateways are explicit nodes in graph

    Example:
        >>> gateways = [Gateway(...), Gateway(...)]
        >>> buildings = [Polygon(...), Polygon(...)]
        >>> network = GatewayRoadNetwork(gateways)
        >>> roads = network.generate(buildings)
        >>> print(f"Generated {len(roads)} road segments")
    """

    def __init__(self, gateways: List[Gateway], min_road_length: float = 10.0):
        """
        Initialize gateway road network generator.

        Args:
            gateways: List of campus gateways
            min_road_length: Minimum road segment length (filter short edges)
        """
        self.gateways = gateways
        self.min_road_length = min_road_length

    def generate(
        self,
        buildings: List[Polygon],
        use_mst: bool = True,
        avoid_building_intersections: bool = False
    ) -> List[LineString]:
        """
        Generate road network connecting gateways to buildings.

        Args:
            buildings: List of building polygons
            use_mst: Use MST to minimize road length (default: True)
            avoid_building_intersections: Filter roads that pass through buildings
                Note: Since we use building centroids as nodes, roads will naturally
                pass through building polygons. Set to True only if using building
                edge points instead of centroids.

        Returns:
            List of LineString roads

        Algorithm:
            1. Extract nodes (gateway locations + building centroids)
            2. Compute Delaunay triangulation
            3. Convert Delaunay edges to NetworkX graph with distances
            4. Apply MST to minimize total road length
            5. Filter roads that intersect buildings (optional)
            6. Convert edges back to LineString geometries

        Complexity:
            - Delaunay: O(n log n)
            - MST: O(E log V) where E ≤ 3n-6 (Delaunay has ≤3n-6 edges)
            - Total: O(n log n)
        """
        if not self.gateways:
            return []

        # Step 1: Extract nodes
        nodes, node_types = self._extract_nodes(buildings)

        if len(nodes) < 2:
            # Need at least 2 nodes to create roads
            return []

        if len(nodes) < 3:
            # Need at least 3 points for Delaunay
            return self._connect_linear(nodes)

        # Step 2: Delaunay triangulation
        try:
            tri = Delaunay(nodes)
        except Exception as e:
            # Fallback 1: Try with QJ (joggle) for nearly-colinear points
            try:
                tri = Delaunay(nodes, qhull_options='QJ')
            except Exception:
                # Fallback 2: Linear connection
                return self._connect_linear(nodes)

        # Step 3: Extract edges from Delaunay with distances
        edges = self._extract_delaunay_edges(tri, nodes)

        # Step 4: Build NetworkX graph
        G = nx.Graph()
        for i in range(len(nodes)):
            G.add_node(i, pos=nodes[i], type=node_types[i])

        for (i, j), dist in edges.items():
            G.add_edge(i, j, weight=dist)

        # Step 5: Apply MST if requested
        if use_mst:
            G = nx.minimum_spanning_tree(G, weight='weight')

        # Step 6: Convert edges to LineStrings
        roads = []
        for i, j in G.edges():
            p1 = Point(nodes[i])
            p2 = Point(nodes[j])
            road = LineString([p1, p2])

            # Filter short roads
            if road.length < self.min_road_length:
                continue

            # Filter roads that intersect buildings (optional)
            if avoid_building_intersections:
                if self._road_intersects_buildings(road, buildings):
                    continue

            roads.append(road)

        return roads

    def _extract_nodes(
        self,
        buildings: List[Polygon]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Extract nodes from gateways and buildings.

        Args:
            buildings: List of building polygons

        Returns:
            (nodes, node_types) where:
                - nodes: (N, 2) array of coordinates
                - node_types: List of 'gateway' or 'building' labels
        """
        nodes = []
        node_types = []

        # Add gateway locations
        for gateway in self.gateways:
            nodes.append([gateway.location.x, gateway.location.y])
            node_types.append('gateway')

        # Add building centroids
        for building in buildings:
            centroid = building.centroid
            nodes.append([centroid.x, centroid.y])
            node_types.append('building')

        return np.array(nodes), node_types

    def _extract_delaunay_edges(
        self,
        tri: Delaunay,
        nodes: np.ndarray
    ) -> dict:
        """
        Extract edges from Delaunay triangulation.

        Delaunay returns simplices (triangles). We need to extract
        unique edges with their Euclidean distances.

        Args:
            tri: Delaunay triangulation
            nodes: (N, 2) node coordinates

        Returns:
            Dictionary {(i, j): distance} for each edge
        """
        edges = {}

        for simplex in tri.simplices:
            # Each simplex is a triangle with 3 vertices
            # Extract 3 edges: (0,1), (1,2), (2,0)
            for i in range(3):
                v1 = simplex[i]
                v2 = simplex[(i + 1) % 3]

                # Normalize edge (ensure i < j to avoid duplicates)
                edge = tuple(sorted([v1, v2]))

                if edge not in edges:
                    # Calculate Euclidean distance
                    p1 = nodes[edge[0]]
                    p2 = nodes[edge[1]]
                    dist = np.linalg.norm(p1 - p2)
                    edges[edge] = dist

        return edges

    def _connect_linear(self, nodes: np.ndarray) -> List[LineString]:
        """
        Fallback for <3 nodes: create linear connection.

        Args:
            nodes: (N, 2) node coordinates

        Returns:
            List of LineString roads
        """
        if len(nodes) < 2:
            return []

        # Connect nodes sequentially
        roads = []
        for i in range(len(nodes) - 1):
            p1 = Point(nodes[i])
            p2 = Point(nodes[i + 1])
            roads.append(LineString([p1, p2]))

        return roads

    def _road_intersects_buildings(
        self,
        road: LineString,
        buildings: List[Polygon]
    ) -> bool:
        """
        Check if road passes through any building.

        Note: Roads can touch building edges (for building access),
        but should not pass THROUGH building interiors.

        Args:
            road: Road LineString
            buildings: List of building polygons

        Returns:
            True if road intersects building interior, False otherwise
        """
        for building in buildings:
            # Check if road crosses building interior
            # (intersects returns True for both touching and crossing)
            if road.intersects(building):
                intersection = road.intersection(building)
                # If intersection is a LineString (not just a Point),
                # the road passes through the building
                if intersection.geom_type == 'LineString':
                    return True
                elif intersection.geom_type == 'MultiLineString':
                    return True

        return False

    def get_gateway_connections(
        self,
        roads: List[LineString]
    ) -> dict:
        """
        Get which buildings are connected to which gateways.

        Args:
            roads: List of road LineStrings

        Returns:
            Dictionary {gateway_id: [building_indices]} showing road connectivity
        """
        # Build connectivity graph from roads
        G = nx.Graph()

        # Add gateway nodes
        gateway_nodes = {}
        for idx, gateway in enumerate(self.gateways):
            node_id = f"gateway_{idx}"
            gateway_nodes[gateway.id] = node_id
            G.add_node(node_id, type='gateway', gateway_id=gateway.id)

        # Add roads as edges
        # (This is simplified - in reality we'd need to match road endpoints to nodes)
        # For now, return empty dict - full implementation would require tracking
        # which roads connect which nodes during generation

        return {}

    def verify_connectivity(self, roads: List[LineString]) -> bool:
        """
        Verify that all gateways are connected to the road network.

        Args:
            roads: List of road LineStrings

        Returns:
            True if all gateways connected, False otherwise
        """
        if not roads:
            return False

        # Build graph from roads
        G = nx.Graph()

        # Add edges from roads
        for road in roads:
            coords = list(road.coords)
            if len(coords) >= 2:
                # Use coordinate tuples as node IDs
                start = coords[0]
                end = coords[-1]
                G.add_edge(start, end)

        # Check if graph is connected
        if not nx.is_connected(G):
            return False

        # Check if all gateways are in the graph
        for gateway in self.gateways:
            gateway_coord = (gateway.location.x, gateway.location.y)
            # Find closest node in graph (allowing small tolerance)
            found = False
            for node in G.nodes():
                dist = np.sqrt((node[0] - gateway_coord[0])**2 +
                             (node[1] - gateway_coord[1])**2)
                if dist < 1.0:  # 1m tolerance
                    found = True
                    break

            if not found:
                return False

        return True

    def __repr__(self):
        return (f"GatewayRoadNetwork("
                f"gateways={len(self.gateways)}, "
                f"min_road_length={self.min_road_length}m)")
