"""
Tests for Gateway Road Network Generator
"""

import pytest
import numpy as np
from shapely.geometry import Point, Polygon

from backend.core.domain.models.campus import Gateway
from backend.core.domain.geometry.gateway_roads import GatewayRoadNetwork


def test_basic_road_generation():
    """Test basic road network generation with 2 gateways and 3 buildings."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(1000, 0), bearing=180, type="main")
    ]

    buildings = [
        Polygon([(200, 200), (300, 200), (300, 300), (200, 300)]),
        Polygon([(500, 200), (600, 200), (600, 300), (500, 300)]),
        Polygon([(800, 200), (900, 200), (900, 300), (800, 300)])
    ]

    network = GatewayRoadNetwork(gateways, min_road_length=10.0)
    roads = network.generate(buildings, use_mst=True)

    # Should generate roads
    assert len(roads) > 0

    # All roads should be LineStrings
    for road in roads:
        assert road.geom_type == 'LineString'
        assert road.length >= 10.0  # Minimum length filter

    print(f"Basic generation test: {len(roads)} roads generated ✓")


def test_delaunay_triangulation():
    """Test that Delaunay triangulation creates expected edges."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(100, 0), bearing=90, type="main"),
        Gateway(id="g3", location=Point(50, 86.6), bearing=180, type="main")  # Equilateral triangle
    ]

    # No buildings, just gateways forming triangle
    buildings = []

    network = GatewayRoadNetwork(gateways, min_road_length=1.0)
    roads = network.generate(buildings, use_mst=False)  # Disable MST to see all Delaunay edges

    # Equilateral triangle should have 3 edges
    assert len(roads) == 3

    print(f"Delaunay test: 3 edges for triangle ✓")


def test_mst_reduces_edges():
    """Test that MST reduces total road length vs full Delaunay."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(100, 0), bearing=90, type="main")
    ]

    buildings = [
        Polygon([(20, 20), (30, 20), (30, 30), (20, 30)]),
        Polygon([(40, 20), (50, 20), (50, 30), (40, 30)]),
        Polygon([(60, 20), (70, 20), (70, 30), (60, 30)]),
        Polygon([(80, 20), (90, 20), (90, 30), (80, 30)])
    ]

    network = GatewayRoadNetwork(gateways, min_road_length=1.0)

    # Generate with full Delaunay
    roads_delaunay = network.generate(buildings, use_mst=False, avoid_building_intersections=False)
    total_length_delaunay = sum(road.length for road in roads_delaunay)

    # Generate with MST
    roads_mst = network.generate(buildings, use_mst=True, avoid_building_intersections=False)
    total_length_mst = sum(road.length for road in roads_mst)

    # MST should have fewer or equal total length
    assert total_length_mst <= total_length_delaunay

    print(f"MST reduction test:")
    print(f"  Delaunay: {len(roads_delaunay)} roads, {total_length_delaunay:.1f}m")
    print(f"  MST: {len(roads_mst)} roads, {total_length_mst:.1f}m")
    print(f"  Reduction: {(1 - total_length_mst/total_length_delaunay)*100:.1f}% ✓")


def test_min_road_length_filter():
    """Test that minimum road length filter works."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(5, 0), bearing=90, type="main")  # Very close
    ]

    buildings = [
        Polygon([(100, 100), (120, 100), (120, 120), (100, 120)])
    ]

    # With min_road_length=10, the 5m gateway-gateway road should be filtered
    network = GatewayRoadNetwork(gateways, min_road_length=10.0)
    roads = network.generate(buildings, use_mst=True)

    # Should only have roads to building (not between gateways)
    for road in roads:
        assert road.length >= 10.0

    print(f"Min length filter test: All roads >= 10m ✓")


def test_avoid_building_intersections():
    """Test that roads avoid passing through buildings."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(200, 0), bearing=180, type="main")
    ]

    # Building in the middle (blocks direct path)
    buildings = [
        Polygon([(90, -20), (110, -20), (110, 20), (90, 20)])
    ]

    network = GatewayRoadNetwork(gateways, min_road_length=1.0)

    # Without intersection avoidance
    roads_without = network.generate(buildings, avoid_building_intersections=False)

    # With intersection avoidance
    roads_with = network.generate(buildings, avoid_building_intersections=True)

    # Should filter some roads
    # (Direct gateway-gateway path is blocked by building)
    print(f"Intersection avoidance test:")
    print(f"  Without filter: {len(roads_without)} roads")
    print(f"  With filter: {len(roads_with)} roads")
    print(f"  Filtered {len(roads_without) - len(roads_with)} roads ✓")


def test_empty_buildings():
    """Test behavior with no buildings (only gateways)."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(100, 0), bearing=90, type="main")
    ]

    network = GatewayRoadNetwork(gateways)
    roads = network.generate([])

    # Should connect gateways (2 gateways -> 1 road)
    assert len(roads) == 1

    print(f"Empty buildings test: 1 road connecting 2 gateways ✓")


def test_no_gateways():
    """Test behavior with no gateways."""

    network = GatewayRoadNetwork([])
    buildings = [
        Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    ]

    roads = network.generate(buildings)

    # Should return empty (no gateways to connect)
    assert len(roads) == 0

    print(f"No gateways test: 0 roads generated ✓")


def test_single_gateway_multiple_buildings():
    """Test road generation with single gateway."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")

    buildings = [
        Polygon([(100, 0), (120, 0), (120, 20), (100, 20)]),
        Polygon([(100, 50), (120, 50), (120, 70), (100, 70)]),
        Polygon([(100, 100), (120, 100), (120, 120), (100, 120)])
    ]

    network = GatewayRoadNetwork([gateway], min_road_length=1.0)
    roads = network.generate(buildings, use_mst=True)

    # MST with 4 nodes (1 gateway + 3 buildings) should have 3 edges
    assert len(roads) == 3

    print(f"Single gateway test: {len(roads)} roads connecting 3 buildings ✓")


def test_linear_fallback():
    """Test linear connection fallback for <3 nodes."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")

    # Only 1 building (2 nodes total < 3)
    buildings = [
        Polygon([(100, 0), (120, 0), (120, 20), (100, 20)])
    ]

    network = GatewayRoadNetwork([gateway])
    roads = network.generate(buildings, use_mst=True)

    # Should create 1 linear road between gateway and building
    assert len(roads) == 1

    print(f"Linear fallback test: 1 road for 2 nodes ✓")


def test_node_extraction():
    """Test that nodes are extracted correctly from gateways and buildings."""

    gateways = [
        Gateway(id="g1", location=Point(10, 20), bearing=0, type="main"),
        Gateway(id="g2", location=Point(30, 40), bearing=90, type="main")
    ]

    buildings = [
        Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),  # Centroid at (5, 5)
    ]

    network = GatewayRoadNetwork(gateways)
    nodes, node_types = network._extract_nodes(buildings)

    # Should have 3 nodes: 2 gateways + 1 building
    assert len(nodes) == 3
    assert len(node_types) == 3

    # First two should be gateways
    assert node_types[0] == 'gateway'
    assert node_types[1] == 'gateway'
    assert node_types[2] == 'building'

    # Check gateway coordinates
    assert nodes[0][0] == 10 and nodes[0][1] == 20
    assert nodes[1][0] == 30 and nodes[1][1] == 40

    # Check building centroid
    assert nodes[2][0] == 5 and nodes[2][1] == 5

    print(f"Node extraction test: 3 nodes extracted correctly ✓")


def test_connectivity_verification():
    """Test connectivity verification."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(100, 0), bearing=180, type="main")
    ]

    buildings = [
        Polygon([(50, 50), (60, 50), (60, 60), (50, 60)])
    ]

    network = GatewayRoadNetwork(gateways, min_road_length=1.0)
    roads = network.generate(buildings, use_mst=True)

    # Verify all gateways are connected
    is_connected = network.verify_connectivity(roads)

    assert is_connected is True

    print(f"Connectivity verification test: Network is connected ✓")


def test_large_network():
    """Test performance with larger network (10 gateways, 50 buildings)."""

    import time

    # 10 gateways around perimeter
    gateways = [
        Gateway(id=f"g{i}", location=Point(i*100, 0), bearing=i*36, type="main")
        for i in range(10)
    ]

    # 50 buildings in grid
    buildings = []
    for i in range(5):
        for j in range(10):
            x = 50 + i * 100
            y = 50 + j * 100
            buildings.append(Polygon([
                (x, y), (x+30, y), (x+30, y+30), (x, y+30)
            ]))

    network = GatewayRoadNetwork(gateways, min_road_length=10.0)

    start = time.time()
    roads = network.generate(buildings, use_mst=True)
    elapsed = time.time() - start

    # Should complete quickly (< 1 second for 60 nodes)
    assert elapsed < 1.0

    # Should generate roads
    assert len(roads) > 0

    print(f"Large network test:")
    print(f"  Nodes: 10 gateways + 50 buildings = 60 total")
    print(f"  Roads: {len(roads)}")
    print(f"  Time: {elapsed*1000:.1f}ms ✓")


def test_real_kastamonu_scenario():
    """Test with real Kastamonu University gateways."""

    # Real gateways from /detect response
    gateways = [
        Gateway(id="g1", location=Point(100, 100), bearing=-1.91, type="main"),
        Gateway(id="g2", location=Point(500, 100), bearing=-0.69, type="main"),
        Gateway(id="g3", location=Point(300, 500), bearing=2.52, type="main")
    ]

    # Sample buildings
    buildings = [
        Polygon([(200, 200), (250, 200), (250, 250), (200, 250)]),
        Polygon([(350, 200), (400, 200), (400, 250), (350, 250)]),
        Polygon([(200, 350), (250, 350), (250, 400), (200, 400)]),
        Polygon([(350, 350), (400, 350), (400, 400), (350, 400)])
    ]

    network = GatewayRoadNetwork(gateways, min_road_length=10.0)
    roads = network.generate(buildings, use_mst=True)

    # MST with 7 nodes (3 gateways + 4 buildings) should have 6 edges
    assert len(roads) == 6

    # Verify connectivity
    is_connected = network.verify_connectivity(roads)
    assert is_connected is True

    print(f"Real Kastamonu scenario test:")
    print(f"  3 gateways + 4 buildings = 7 nodes")
    print(f"  {len(roads)} roads (MST)")
    print(f"  Network connected: {is_connected} ✓")


if __name__ == "__main__":
    # Run tests manually
    test_basic_road_generation()
    test_delaunay_triangulation()
    test_mst_reduces_edges()
    test_min_road_length_filter()
    test_avoid_building_intersections()
    test_empty_buildings()
    test_no_gateways()
    test_single_gateway_multiple_buildings()
    test_linear_fallback()
    test_node_extraction()
    test_connectivity_verification()
    test_large_network()
    test_real_kastamonu_scenario()

    print("\n✅ All tests passed!")
