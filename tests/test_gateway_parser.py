"""
Tests for Gateway Parser Utility
"""

from backend.core.domain.geometry.gateway_parser import (
    parse_gateways_from_geojson,
    parse_boundary_from_geojson
)


def test_parse_single_gateway():
    """Test parsing a single gateway from GeoJSON."""

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.78, 41.38]},
                "properties": {
                    "layer": "gateway",
                    "id": "gateway_1",
                    "bearing": -1.91,
                    "type": "main",
                    "name": "Main Entrance"
                }
            }
        ]
    }

    gateways = parse_gateways_from_geojson(geojson)

    assert len(gateways) == 1
    assert gateways[0].id == "gateway_1"
    assert gateways[0].bearing == -1.91
    assert gateways[0].type == "main"
    assert gateways[0].name == "Main Entrance"
    assert gateways[0].location.x == 33.78
    assert gateways[0].location.y == 41.38

    print("✓ Single gateway parsed correctly")


def test_parse_multiple_gateways():
    """Test parsing multiple gateways from GeoJSON."""

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.78, 41.38]},
                "properties": {
                    "layer": "gateway",
                    "id": "g1",
                    "bearing": 0.0,
                    "type": "main"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.79, 41.39]},
                "properties": {
                    "layer": "gateway",
                    "id": "g2",
                    "bearing": 90.0,
                    "type": "secondary"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.80, 41.40]},
                "properties": {
                    "layer": "gateway",
                    "id": "g3",
                    "bearing": 180.0,
                    "type": "service"
                }
            }
        ]
    }

    gateways = parse_gateways_from_geojson(geojson)

    assert len(gateways) == 3
    assert gateways[0].id == "g1"
    assert gateways[1].id == "g2"
    assert gateways[2].id == "g3"
    assert gateways[0].bearing == 0.0
    assert gateways[1].bearing == 90.0
    assert gateways[2].bearing == 180.0

    print("✓ Multiple gateways parsed correctly")


def test_parse_mixed_features():
    """Test parsing gateways from GeoJSON with mixed feature types."""

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                "properties": {"layer": "boundary"}
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.78, 41.38]},
                "properties": {
                    "layer": "gateway",
                    "id": "g1",
                    "bearing": 0.0,
                    "type": "main"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]},
                "properties": {"layer": "existing_building"}
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.79, 41.39]},
                "properties": {
                    "layer": "gateway",
                    "id": "g2",
                    "bearing": 90.0,
                    "type": "secondary"
                }
            }
        ]
    }

    gateways = parse_gateways_from_geojson(geojson)

    # Should only extract gateway features
    assert len(gateways) == 2
    assert gateways[0].id == "g1"
    assert gateways[1].id == "g2"

    print("✓ Gateways extracted from mixed features")


def test_parse_empty_geojson():
    """Test parsing from empty GeoJSON."""

    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    gateways = parse_gateways_from_geojson(geojson)
    assert len(gateways) == 0

    print("✓ Empty GeoJSON handled correctly")


def test_parse_none_geojson():
    """Test parsing from None."""

    gateways = parse_gateways_from_geojson(None)
    assert len(gateways) == 0

    print("✓ None input handled correctly")


def test_parse_missing_properties():
    """Test parsing gateway with missing optional properties."""

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.78, 41.38]},
                "properties": {
                    "layer": "gateway",
                    "id": "g1"
                    # Missing: bearing, type, name
                }
            }
        ]
    }

    gateways = parse_gateways_from_geojson(geojson)

    assert len(gateways) == 1
    assert gateways[0].id == "g1"
    assert gateways[0].bearing == 0.0  # Default
    assert gateways[0].type == "main"  # Default
    assert gateways[0].name is None  # None is acceptable

    print("✓ Missing properties handled with defaults")


def test_parse_malformed_gateway():
    """Test that malformed gateways are skipped."""

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.78, 41.38]},
                "properties": {
                    "layer": "gateway",
                    "id": "g1",
                    "bearing": 0.0
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                "properties": {
                    "layer": "gateway",  # Wrong geometry type
                    "id": "g2",
                    "bearing": 90.0
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [33.79, 41.39]},
                "properties": {
                    "layer": "gateway",
                    "id": "g3",
                    "bearing": "invalid"  # Invalid bearing (will be caught)
                }
            }
        ]
    }

    gateways = parse_gateways_from_geojson(geojson)

    # Only g1 should be parsed successfully
    assert len(gateways) == 1
    assert gateways[0].id == "g1"

    print("✓ Malformed gateways skipped gracefully")


def test_parse_boundary():
    """Test parsing boundary from GeoJSON."""

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]]
                },
                "properties": {"layer": "boundary"}
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [50, 50]},
                "properties": {"layer": "gateway", "id": "g1"}
            }
        ]
    }

    boundary = parse_boundary_from_geojson(geojson)

    assert boundary is not None
    assert boundary.geom_type == "Polygon"
    assert boundary.area == 10000  # 100x100

    print("✓ Boundary parsed correctly")


def test_parse_boundary_none():
    """Test parsing boundary from None."""

    boundary = parse_boundary_from_geojson(None)
    assert boundary is None

    print("✓ None boundary input handled correctly")


def test_parse_real_kastamonu_format():
    """Test parsing with real Kastamonu University gateway format."""

    # Simulated output from /api/campus/relocate
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                "properties": {
                    "layer": "gateway",
                    "id": "gateway_0",
                    "bearing": -1.91,
                    "type": "main",
                    "name": None
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [500.0, 0.0]},
                "properties": {
                    "layer": "gateway",
                    "id": "gateway_1",
                    "bearing": -0.69,
                    "type": "main",
                    "name": None
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [250.0, 433.0]},
                "properties": {
                    "layer": "gateway",
                    "id": "gateway_2",
                    "bearing": 2.52,
                    "type": "main",
                    "name": None
                }
            }
        ]
    }

    gateways = parse_gateways_from_geojson(geojson)

    assert len(gateways) == 3
    assert all(gw.type == "main" for gw in gateways)
    assert gateways[0].bearing == -1.91
    assert gateways[1].bearing == -0.69
    assert gateways[2].bearing == 2.52

    print("✓ Real Kastamonu format parsed correctly")


if __name__ == "__main__":
    test_parse_single_gateway()
    test_parse_multiple_gateways()
    test_parse_mixed_features()
    test_parse_empty_geojson()
    test_parse_none_geojson()
    test_parse_missing_properties()
    test_parse_malformed_gateway()
    test_parse_boundary()
    test_parse_boundary_none()
    test_parse_real_kastamonu_format()

    print("\n✅ All gateway parser tests passed!")
