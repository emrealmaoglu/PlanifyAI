"""
Tests for Gateway Clearance Constraint
"""

import pytest
from shapely.geometry import Point, Polygon

from backend.core.domain.models.campus import Gateway
from backend.core.optimization.constraints.gateway_clearance import GatewayClearanceConstraint


def test_circular_clearance_zone():
    """Test basic circular clearance (no directional)."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0,
        use_directional_clearance=False
    )

    # Clearance zone should be circular with radius 50
    zone = constraint.clearance_zones[0]

    # Check boundary points are ~50m from center
    bounds = zone.bounds
    assert abs(bounds[0] - (-50)) < 1  # minx
    assert abs(bounds[1] - (-50)) < 1  # miny
    assert abs(bounds[2] - 50) < 1     # maxx
    assert abs(bounds[3] - 50) < 1     # maxy

    print(f"Circular zone test: radius=50m ✓")


def test_bearing_conversion_formula():
    """
    Test that bearing conversion formula is correct.

    Bearing convention: Clockwise from North
    Shapely convention: Counter-clockwise from East

    Conversion: shapely_angle = 90 - bearing
    """

    test_cases = [
        # (bearing, expected_shapely_angle, direction_name)
        (0, 90, "North"),
        (90, 0, "East"),
        (180, -90, "South"),
        (270, -180, "West"),
        (45, 45, "Northeast"),
        (135, -45, "Southeast"),
    ]

    for bearing, expected_angle, direction in test_cases:
        shapely_angle = 90 - bearing
        assert shapely_angle == expected_angle, \
            f"{direction}: bearing={bearing}° should convert to shapely_angle={expected_angle}°"

    print(f"Bearing conversion test: All 6 directions verified ✓")


def test_directional_zone_north_facing():
    """
    Test that North-facing gateway (bearing=0°) has clearance extending North.

    Bearing=0° → shapely_angle=90° → ellipse extends in +Y direction (North)
    """

    gateway = Gateway(id="north", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0,
        use_directional_clearance=True
    )

    zone = constraint.clearance_zones[0]
    bounds = zone.bounds
    minx, miny, maxx, maxy = bounds

    # Ellipse should extend 2x in Y direction (North)
    # x-direction: ~50m
    # y-direction: ~100m (2x)

    print(f"North-facing gateway clearance zone:")
    print(f"  X range: [{minx:.1f}, {maxx:.1f}] (should be ~±50m)")
    print(f"  Y range: [{miny:.1f}, {maxy:.1f}] (should be ~±100m)")

    # Y should extend more than X (directional elongation)
    y_extent = maxy - miny
    x_extent = maxx - minx

    assert y_extent > x_extent, "North-facing gateway should have Y > X"
    assert y_extent >= 140, f"Y extent should be >=140m, got {y_extent:.1f}m"
    assert x_extent <= 105, f"X extent should be <=105m, got {x_extent:.1f}m"

    # North direction should extend further than South
    assert maxy > abs(miny), "North (+Y) should extend more than South (-Y)"

    print(f"  Y extent ({y_extent:.1f}m) > X extent ({x_extent:.1f}m) ✓")
    print(f"  North extension ({maxy:.1f}m) > South ({abs(miny):.1f}m) ✓")


def test_directional_zone_east_facing():
    """
    Test that East-facing gateway (bearing=90°) has clearance extending East.

    Bearing=90° → shapely_angle=0° → ellipse extends in +X direction (East)
    """

    gateway = Gateway(id="east", location=Point(0, 0), bearing=90, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0,
        use_directional_clearance=True
    )

    zone = constraint.clearance_zones[0]
    bounds = zone.bounds
    minx, miny, maxx, maxy = bounds

    print(f"East-facing gateway clearance zone:")
    print(f"  X range: [{minx:.1f}, {maxx:.1f}] (should be ~±100m)")
    print(f"  Y range: [{miny:.1f}, {maxy:.1f}] (should be ~±50m)")

    # X should extend more than Y (directional elongation)
    x_extent = maxx - minx
    y_extent = maxy - miny

    assert x_extent > y_extent, "East-facing gateway should have X > Y"
    assert x_extent >= 140, f"X extent should be >=140m, got {x_extent:.1f}m"
    assert y_extent <= 105, f"Y extent should be <=105m, got {y_extent:.1f}m"

    # East direction should extend further than West
    assert maxx > abs(minx), "East (+X) should extend more than West (-X)"

    print(f"  X extent ({x_extent:.1f}m) > Y extent ({y_extent:.1f}m) ✓")
    print(f"  East extension ({maxx:.1f}m) > West ({abs(minx):.1f}m) ✓")


def test_directional_zone_south_facing():
    """
    Test that South-facing gateway (bearing=180°) has clearance extending South.

    Bearing=180° → shapely_angle=-90° → ellipse extends in -Y direction (South)
    """

    gateway = Gateway(id="south", location=Point(0, 0), bearing=180, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0,
        use_directional_clearance=True
    )

    zone = constraint.clearance_zones[0]
    bounds = zone.bounds
    minx, miny, maxx, maxy = bounds

    print(f"South-facing gateway clearance zone:")
    print(f"  X range: [{minx:.1f}, {maxx:.1f}]")
    print(f"  Y range: [{miny:.1f}, {maxy:.1f}]")

    # Y should extend more than X
    y_extent = maxy - miny
    x_extent = maxx - minx

    assert y_extent > x_extent, "South-facing gateway should have Y > X"

    # South direction should extend further than North
    assert abs(miny) > maxy, "South (-Y) should extend more than North (+Y)"

    print(f"  Y extent ({y_extent:.1f}m) > X extent ({x_extent:.1f}m) ✓")
    print(f"  South extension ({abs(miny):.1f}m) > North ({maxy:.1f}m) ✓")


def test_is_valid_no_violations():
    """Test that buildings outside clearance zone are valid."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0
    )

    # Building far from gateway (at x=200)
    buildings = [
        Polygon([(200, 0), (220, 0), (220, 20), (200, 20)])
    ]

    assert constraint.is_valid(buildings) is True
    print(f"No violation test: Building at x=200 is valid ✓")


def test_is_valid_with_violations():
    """Test that buildings inside clearance zone are invalid."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0
    )

    # Building overlapping gateway (centered at origin)
    buildings = [
        Polygon([(-10, -10), (10, -10), (10, 10), (-10, 10)])
    ]

    assert constraint.is_valid(buildings) is False
    print(f"Violation test: Building at origin is invalid ✓")


def test_get_violation_distance():
    """Test violation area calculation."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0,
        use_directional_clearance=False  # Circular for easy calculation
    )

    # Small building at center (20x20 = 400m²)
    buildings = [
        Polygon([(-10, -10), (10, -10), (10, 10), (-10, 10)])
    ]

    violation_area = constraint.get_violation_distance(buildings)

    # Building is completely inside clearance zone
    # Violation area should be ~400m²
    assert 380 < violation_area < 420, f"Expected ~400m², got {violation_area:.1f}m²"

    print(f"Violation area test: {violation_area:.1f}m² ≈ 400m² ✓")


def test_get_violations_details():
    """Test detailed violation information."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(200, 0), bearing=90, type="secondary")
    ]

    constraint = GatewayClearanceConstraint(
        gateways=gateways,
        clearance_radius=50.0
    )

    # Building violating g1 only
    buildings = [
        Polygon([(-10, -10), (10, -10), (10, 10), (-10, 10)])
    ]

    violations = constraint.get_violations(buildings)

    # Should have 1 violation (building 0, gateway 0)
    assert len(violations) == 1
    building_idx, gateway_idx, area = violations[0]

    assert building_idx == 0
    assert gateway_idx == 0
    assert area > 0

    print(f"Violation details test: 1 violation detected ✓")
    print(f"  Building {building_idx}, Gateway {gateway_idx}, Area {area:.1f}m²")


def test_get_minimum_clearance():
    """Test minimum clearance distance calculation."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0,
        use_directional_clearance=False
    )

    # Building at x=100 (edge at x=80, clearance edge at x=50)
    # Distance should be ~30m
    building = Polygon([(80, -10), (100, -10), (100, 10), (80, 10)])

    min_clearance = constraint.get_minimum_clearance_for_building(building)

    assert min_clearance is not None
    assert 25 < min_clearance < 35, f"Expected ~30m clearance, got {min_clearance:.1f}m"

    print(f"Minimum clearance test: {min_clearance:.1f}m ≈ 30m ✓")


def test_get_minimum_clearance_violation():
    """Test that buildings inside zone return None."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0
    )

    # Building at origin (violating)
    building = Polygon([(-10, -10), (10, -10), (10, 10), (-10, 10)])

    min_clearance = constraint.get_minimum_clearance_for_building(building)

    assert min_clearance is None, "Violating building should return None"

    print(f"Violation clearance test: None returned for violating building ✓")


def test_empty_buildings():
    """Test that empty building list is valid."""

    gateway = Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")
    constraint = GatewayClearanceConstraint(
        gateways=[gateway],
        clearance_radius=50.0
    )

    assert constraint.is_valid([]) is True
    assert constraint.get_violation_distance([]) == 0.0

    print(f"Empty buildings test: Valid with 0 violation ✓")


def test_multiple_gateways():
    """Test constraint with multiple gateways."""

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=0, type="main"),
        Gateway(id="g2", location=Point(200, 0), bearing=90, type="secondary"),
        Gateway(id="g3", location=Point(0, 200), bearing=180, type="pedestrian")
    ]

    constraint = GatewayClearanceConstraint(
        gateways=gateways,
        clearance_radius=50.0
    )

    # Should have 3 clearance zones
    assert len(constraint.clearance_zones) == 3

    # Building far from all gateways
    buildings = [
        Polygon([(100, 100), (120, 100), (120, 120), (100, 120)])
    ]

    assert constraint.is_valid(buildings) is True

    print(f"Multiple gateways test: 3 zones created, valid layout ✓")


def test_real_kastamonu_bearings():
    """
    Test with real Kastamonu University gateway bearings.

    From /detect response:
    - bearing: -1.91° (near North)
    - bearing: -0.69° (near North)
    - bearing: 2.52° (near North)
    """

    gateways = [
        Gateway(id="g1", location=Point(0, 0), bearing=-1.91, type="main"),
        Gateway(id="g2", location=Point(200, 0), bearing=-0.69, type="main"),
        Gateway(id="g3", location=Point(0, 200), bearing=2.52, type="main")
    ]

    constraint = GatewayClearanceConstraint(
        gateways=gateways,
        clearance_radius=30.0,
        use_directional_clearance=True
    )

    # All should create valid elliptical zones without errors
    assert len(constraint.clearance_zones) == 3

    # All zones should extend more in Y (North) direction
    for i, zone in enumerate(constraint.clearance_zones):
        bounds = zone.bounds
        x_extent = bounds[2] - bounds[0]
        y_extent = bounds[3] - bounds[1]

        # Y should be larger (North-facing)
        assert y_extent > x_extent, \
            f"Gateway {i} (bearing={gateways[i].bearing}°) should extend North"

    print(f"Real Kastamonu bearings test:")
    print(f"  3 gateways with bearings: -1.91°, -0.69°, 2.52°")
    print(f"  All zones extend North (Y > X) ✓")


if __name__ == "__main__":
    # Run tests manually
    test_circular_clearance_zone()
    test_bearing_conversion_formula()
    test_directional_zone_north_facing()
    test_directional_zone_east_facing()
    test_directional_zone_south_facing()
    test_is_valid_no_violations()
    test_is_valid_with_violations()
    test_get_violation_distance()
    test_get_violations_details()
    test_get_minimum_clearance()
    test_get_minimum_clearance_violation()
    test_empty_buildings()
    test_multiple_gateways()
    test_real_kastamonu_bearings()

    print("\n✅ All tests passed!")
