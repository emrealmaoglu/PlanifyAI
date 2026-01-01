"""
Kansky Network Connectivity Indices
====================================

Implements Kansky (1963) graph-theoretic indices for evaluating road network topology.
These metrics quantify network connectivity and complexity.

Indices:
    - Alpha (α): Network connectivity (0 = tree, 1 = complete graph)
    - Beta (β): Average edges per node (complexity)
    - Gamma (γ): Actual vs maximum possible connections
    - Eta (η): Average edge length (efficiency)

References:
    - Kansky, K. J. (1963): Structure of transportation networks
    - Rodrigue et al. (2020): The Geography of Transport Systems
    - Research: "Campus Planning Standards" document

Created: 2026-01-01
"""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class KanskyIndices:
    """
    Container for Kansky network connectivity indices.

    Attributes:
        alpha: Cyclomatic complexity (0-1, higher = more loops)
        beta: Average edges per node (>1 = connected, >3 = well-connected)
        gamma: Connectivity ratio (0-1, actual/maximum connections)
        eta: Average edge length in meters (lower = more efficient)
        n_nodes: Number of nodes (intersections)
        n_edges: Number of edges (road segments)
        n_circuits: Number of independent circuits (loops)
    """

    alpha: float
    beta: float
    gamma: float
    eta: float
    n_nodes: int
    n_edges: int
    n_circuits: int


def calculate_kansky_indices(
    nodes: List[Tuple[float, float]],
    edges: List[Tuple[int, int]],
    edge_lengths: List[float] = None,
) -> KanskyIndices:
    """
    Calculate Kansky indices for a road network.

    Args:
        nodes: List of (x, y) coordinates for intersections
        edges: List of (node_i, node_j) index pairs defining road segments
        edge_lengths: Optional list of edge lengths (meters). If None, computed from nodes.

    Returns:
        KanskyIndices dataclass with all metrics

    Example:
        >>> nodes = [(0, 0), (100, 0), (100, 100), (0, 100)]
        >>> edges = [(0, 1), (1, 2), (2, 3), (3, 0)]  # Square
        >>> indices = calculate_kansky_indices(nodes, edges)
        >>> print(f"Alpha: {indices.alpha:.2f}")
        >>> print(f"Beta: {indices.beta:.2f}")

    Notes:
        - Alpha = 0: Tree network (no loops)
        - Alpha = 1: Complete graph (all possible connections)
        - Beta < 1: Disconnected network
        - Beta = 1: Minimally connected tree
        - Beta > 1: Network has circuits
        - Gamma = 1: Maximum connectivity (all nodes connected to all others)
    """
    n_nodes = len(nodes)
    n_edges = len(edges)

    if n_nodes == 0 or n_edges == 0:
        # Degenerate network
        return KanskyIndices(
            alpha=0.0,
            beta=0.0,
            gamma=0.0,
            eta=0.0,
            n_nodes=n_nodes,
            n_edges=n_edges,
            n_circuits=0,
        )

    # Calculate number of independent circuits (loops)
    # For planar graph: μ = e - v + 1
    n_circuits = max(0, n_edges - n_nodes + 1)

    # Alpha Index: Network connectivity
    # α = μ / (2v - 5)  for planar graphs
    # Range: [0, 1] where 0 = tree, 1 = complete graph
    max_circuits = max(1, 2 * n_nodes - 5)  # Avoid division by zero
    alpha = n_circuits / max_circuits if max_circuits > 0 else 0.0
    alpha = min(1.0, max(0.0, alpha))  # Clamp to [0, 1]

    # Beta Index: Average edges per node (complexity)
    # β = e / v
    # β < 1: disconnected
    # β = 1: tree (minimally connected)
    # β > 1: has circuits
    beta = n_edges / n_nodes if n_nodes > 0 else 0.0

    # Gamma Index: Connectivity ratio
    # γ = e / (3(v - 2))  for planar graphs
    # Range: [0, 1] where 1 = maximum connectivity
    max_edges_planar = max(1, 3 * (n_nodes - 2))  # Avoid division by zero
    gamma = n_edges / max_edges_planar if max_edges_planar > 0 else 0.0
    gamma = min(1.0, max(0.0, gamma))  # Clamp to [0, 1]

    # Eta Index: Average edge length (efficiency)
    # η = sum(L_i) / e
    # Lower is better (shorter average road length)
    if edge_lengths is None:
        # Compute from node coordinates
        edge_lengths = []
        for i, j in edges:
            if i < len(nodes) and j < len(nodes):
                x1, y1 = nodes[i]
                x2, y2 = nodes[j]
                length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                edge_lengths.append(length)

    if edge_lengths:
        eta = float(np.mean(edge_lengths))
    else:
        eta = 0.0

    return KanskyIndices(
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        eta=eta,
        n_nodes=n_nodes,
        n_edges=n_edges,
        n_circuits=n_circuits,
    )


def road_network_to_graph(
    major_roads: List[np.ndarray],
    minor_roads: List[np.ndarray],
    intersection_threshold: float = 10.0,
) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int]], List[float]]:
    """
    Convert road network (list of polylines) to graph representation.

    Identifies intersections and creates node-edge graph structure.

    Args:
        major_roads: List of (N, 2) arrays (road polylines)
        minor_roads: List of (M, 2) arrays
        intersection_threshold: Max distance to consider points as same node (meters)

    Returns:
        (nodes, edges, edge_lengths) where:
        - nodes: List of (x, y) intersection coordinates
        - edges: List of (i, j) node index pairs
        - edge_lengths: List of edge lengths (meters)

    Example:
        >>> major = [np.array([[0, 0], [100, 0]]), np.array([[50, -50], [50, 50]])]
        >>> minor = []
        >>> nodes, edges, lengths = road_network_to_graph(major, minor)
        >>> # Detects intersection at (50, 0)
    """
    # Collect all road segments
    all_roads = major_roads + minor_roads

    if not all_roads:
        return [], [], []

    # Extract all road endpoints and segment points
    potential_nodes = []

    for road in all_roads:
        if len(road) < 2:
            continue

        # Add start and end points
        potential_nodes.append(tuple(road[0]))
        potential_nodes.append(tuple(road[-1]))

        # Also add intermediate points that might be intersections
        # (simplified: just use all points)
        for point in road:
            potential_nodes.append(tuple(point))

    # Cluster nearby points into single nodes
    nodes = []
    node_mapping = {}  # Maps original point index to clustered node index

    for i, point in enumerate(potential_nodes):
        # Check if point is close to existing node
        found_existing = False

        for j, existing_node in enumerate(nodes):
            distance = np.sqrt(
                (point[0] - existing_node[0]) ** 2 + (point[1] - existing_node[1]) ** 2
            )

            if distance < intersection_threshold:
                # Merge with existing node
                node_mapping[i] = j
                found_existing = True
                break

        if not found_existing:
            # Create new node
            node_mapping[i] = len(nodes)
            nodes.append(point)

    # Build edges from road segments
    edges = []
    edge_lengths = []
    edge_set = set()  # Avoid duplicates

    point_index = 0

    for road in all_roads:
        if len(road) < 2:
            continue

        # For each consecutive pair of points in road
        for k in range(len(road) - 1):
            # Map to clustered nodes
            node_i = node_mapping.get(point_index + k)
            node_j = node_mapping.get(point_index + k + 1)

            if node_i is not None and node_j is not None and node_i != node_j:
                # Add edge (undirected - store in sorted order)
                edge_tuple = tuple(sorted([node_i, node_j]))

                if edge_tuple not in edge_set:
                    edge_set.add(edge_tuple)
                    edges.append(edge_tuple)

                    # Compute edge length
                    p1 = road[k]
                    p2 = road[k + 1]
                    length = float(np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2))
                    edge_lengths.append(length)

        point_index += len(road)

    return nodes, edges, edge_lengths


def calculate_network_connectivity(
    major_roads: List[np.ndarray],
    minor_roads: List[np.ndarray],
) -> KanskyIndices:
    """
    High-level function to calculate Kansky indices for road network.

    Args:
        major_roads: List of (N, 2) road polylines
        minor_roads: List of (M, 2) road polylines

    Returns:
        KanskyIndices with all connectivity metrics

    Example:
        >>> from backend.core.geospatial.road_network_generator import RoadNetworkGenerator
        >>> gen = RoadNetworkGenerator(bounds=(0, 0, 1000, 1000))
        >>> major, minor, stats = gen.generate(buildings)
        >>> indices = calculate_network_connectivity(major, minor)
        >>> print(f"Network connectivity (gamma): {indices.gamma:.2f}")
    """
    # Convert road network to graph
    nodes, edges, edge_lengths = road_network_to_graph(major_roads, minor_roads)

    # Calculate Kansky indices
    indices = calculate_kansky_indices(nodes, edges, edge_lengths)

    return indices


def connectivity_quality_score(indices: KanskyIndices) -> float:
    """
    Aggregate connectivity indices into single quality score.

    Combines alpha, beta, gamma into normalized score [0, 1].

    Args:
        indices: KanskyIndices from calculate_kansky_indices()

    Returns:
        Quality score where 1.0 = excellent connectivity, 0.0 = poor

    Formula:
        score = 0.4 * gamma + 0.3 * alpha + 0.3 * min(beta/3, 1.0)

        Rationale:
        - Gamma: Most important (actual vs max connections)
        - Alpha: Presence of circuits (redundancy)
        - Beta: Network complexity (normalized to [0, 1])
    """
    # Normalize beta to [0, 1] (beta=3 considered ideal)
    beta_normalized = min(indices.beta / 3.0, 1.0)

    # Weighted combination
    score = 0.4 * indices.gamma + 0.3 * indices.alpha + 0.3 * beta_normalized

    return float(np.clip(score, 0.0, 1.0))
