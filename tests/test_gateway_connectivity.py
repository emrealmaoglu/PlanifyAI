"""
Tests for Gateway Connectivity Objective
"""

import pytest
from shapely.geometry import Point, Polygon

from backend.core.domain.models.campus import Gateway
from backend.core.optimization.objectives.gateway_connectivity import GatewayConnectivityObjective


def test_gateway_connectivity_perfect_score():
    """Test that buildings right next to gateways get high scores."""

    # Campus boundary: 1000m x 1000m
    boundary = Polygon([
        (0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)
    ])

    # Two gateways
    gateways = [
        Gateway(id="g1", location=Point(500, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(500, 1000), bearing=180, type="main")
    ]

    objective = GatewayConnectivityObjective(gateways, boundary, weight=1.0)

    # Buildings very close to gateways
    buildings = [
        Polygon([(490, 10), (510, 10), (510, 30), (490, 30)]),  # Near g1
        Polygon([(490, 970), (510, 970), (510, 990), (490, 990)])  # Near g2
    ]

    score = objective.calculate(buildings)

    # Score should be very high (close to 1.0)
    assert score > 0.95
    print(f"Perfect score test: {score:.4f} > 0.95 ✓")


def test_gateway_connectivity_poor_score():
    """Test that buildings far from gateways get low scores."""

    # Campus boundary: 1000m x 1000m
    boundary = Polygon([
        (0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)
    ])

    # Two gateways at edges
    gateways = [
        Gateway(id="g1", location=Point(0, 500), bearing=0, type="main"),
        Gateway(id="g2", location=Point(1000, 500), bearing=180, type="main")
    ]

    objective = GatewayConnectivityObjective(gateways, boundary, weight=1.0)

    # Buildings in center, far from both gateways
    buildings = [
        Polygon([(450, 450), (550, 450), (550, 550), (450, 550)])
    ]

    score = objective.calculate(buildings)

    # Score should be moderate (buildings are ~500m from gateways)
    # avg_distance = 500, max_dimension = 1000
    # normalized = 0.5, score = 1/(1+0.5) = 0.667
    assert 0.6 < score < 0.7
    print(f"Poor score test: 0.6 < {score:.4f} < 0.7 ✓")


def test_gateway_connectivity_empty_buildings():
    """Test that empty building list returns 0."""

    boundary = Polygon([
        (0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)
    ])

    gateways = [
        Gateway(id="g1", location=Point(500, 500), bearing=0, type="main")
    ]

    objective = GatewayConnectivityObjective(gateways, boundary)

    score = objective.calculate([])

    assert score == 0.0
    print(f"Empty buildings test: {score:.4f} == 0.0 ✓")


def test_gateway_connectivity_no_gateways():
    """Test that no gateways returns 0."""

    boundary = Polygon([
        (0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)
    ])

    objective = GatewayConnectivityObjective([], boundary)

    buildings = [
        Polygon([(450, 450), (550, 450), (550, 550), (450, 550)])
    ]

    score = objective.calculate(buildings)

    assert score == 0.0
    print(f"No gateways test: {score:.4f} == 0.0 ✓")


def test_gateway_connectivity_boundary_normalization():
    """
    Test that boundary-based normalization prevents early generation bias.

    This is the key improvement from SPRINT_3_IMPROVEMENTS.md
    """

    # Large campus: 2000m x 2000m
    boundary = Polygon([
        (0, 0), (2000, 0), (2000, 2000), (0, 2000), (0, 0)
    ])

    gateways = [
        Gateway(id="g1", location=Point(1000, 0), bearing=0, type="main")
    ]

    objective = GatewayConnectivityObjective(gateways, boundary, weight=1.0)

    # Scenario 1: Buildings clustered in small area (100m x 100m)
    # This simulates early generation where buildings might cluster
    clustered_buildings = [
        Polygon([(950, 50), (1000, 50), (1000, 100), (950, 100)]),
        Polygon([(1000, 50), (1050, 50), (1050, 100), (1000, 100)])
    ]

    score_clustered = objective.calculate(clustered_buildings)

    # Scenario 2: Same buildings, same distance from gateway, but spread out
    spread_buildings = [
        Polygon([(950, 50), (1000, 50), (1000, 100), (950, 100)]),
        Polygon([(950, 1900), (1000, 1900), (1000, 1950), (950, 1950)])
    ]

    score_spread = objective.calculate(spread_buildings)

    # Both should use the SAME max_dimension (2000m from boundary)
    # So scores should be comparable
    assert objective.max_dimension == 2000

    # Clustered buildings are both close to gateway
    # Spread buildings have one close, one far
    # So clustered should score higher
    assert score_clustered > score_spread

    print(f"Boundary normalization test:")
    print(f"  max_dimension = {objective.max_dimension} ✓")
    print(f"  clustered score = {score_clustered:.4f}")
    print(f"  spread score = {score_spread:.4f}")
    print(f"  clustered > spread: {score_clustered > score_spread} ✓")


def test_get_closest_gateway():
    """Test finding closest gateway for a building."""

    boundary = Polygon([
        (0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)
    ])

    gateways = [
        Gateway(id="north", location=Point(500, 0), bearing=0, type="main"),
        Gateway(id="south", location=Point(500, 1000), bearing=180, type="main")
    ]

    objective = GatewayConnectivityObjective(gateways, boundary)

    # Building near north gateway
    building_north = Polygon([(450, 50), (550, 50), (550, 150), (450, 150)])
    closest = objective.get_closest_gateway_for_building(building_north)

    assert closest.id == "north"
    print(f"Closest gateway test: {closest.id} == 'north' ✓")


def test_gateway_distribution():
    """Test gateway distribution calculation."""

    boundary = Polygon([
        (0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)
    ])

    gateways = [
        Gateway(id="g1", location=Point(250, 500), bearing=0, type="main"),
        Gateway(id="g2", location=Point(750, 500), bearing=180, type="main")
    ]

    objective = GatewayConnectivityObjective(gateways, boundary)

    # 3 buildings near g1, 2 buildings near g2
    buildings = [
        # Near g1 (x < 500)
        Polygon([(100, 100), (200, 100), (200, 200), (100, 200)]),
        Polygon([(100, 300), (200, 300), (200, 400), (100, 400)]),
        Polygon([(100, 700), (200, 700), (200, 800), (100, 800)]),

        # Near g2 (x > 500)
        Polygon([(800, 100), (900, 100), (900, 200), (800, 200)]),
        Polygon([(800, 700), (900, 700), (900, 800), (800, 800)])
    ]

    distribution = objective.get_gateway_distribution(buildings)

    assert distribution["g1"] == 3
    assert distribution["g2"] == 2
    print(f"Gateway distribution test: g1={distribution['g1']}, g2={distribution['g2']} ✓")


def test_zero_dimension_boundary_error():
    """Test that zero-dimension boundary raises error."""

    # Invalid boundary (zero area)
    boundary = Polygon([(0, 0), (0, 0), (0, 0), (0, 0)])

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    ]

    with pytest.raises(ValueError, match="zero dimension"):
        GatewayConnectivityObjective(gateways, boundary)

    print("Zero dimension boundary test: ValueError raised ✓")


if __name__ == "__main__":
    # Run tests manually
    test_gateway_connectivity_perfect_score()
    test_gateway_connectivity_poor_score()
    test_gateway_connectivity_empty_buildings()
    test_gateway_connectivity_no_gateways()
    test_gateway_connectivity_boundary_normalization()
    test_get_closest_gateway()
    test_gateway_distribution()
    test_zero_dimension_boundary_error()

    print("\n✅ All tests passed!")
