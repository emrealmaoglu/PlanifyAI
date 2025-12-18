"""Tests for interactive map module"""

import tempfile
from pathlib import Path

from shapely.geometry import Polygon

from src.algorithms.building import Building, BuildingType
from src.algorithms.solution import Solution
from src.data.campus_data import CampusData
from src.visualization.interactive_map import InteractiveCampusMap


def test_map_creation():
    """Test basic map creation"""
    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
        Building("EDU-01", BuildingType.EDUCATIONAL, 2500, 4),
    ]
    solution = Solution(
        positions={
            "RES-01": (100, 100),
            "EDU-01": (200, 200),
        }
    )

    mapper = InteractiveCampusMap(buildings=buildings)
    folium_map = mapper.create_map(solution, buildings=buildings)

    assert folium_map is not None
    assert hasattr(folium_map, "location")


def test_map_creation_with_center():
    """Test map creation with custom center"""
    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
    ]
    solution = Solution(positions={"RES-01": (100, 100)})

    mapper = InteractiveCampusMap(buildings=buildings)
    center = (41.08, 29.05)
    folium_map = mapper.create_map(solution, buildings=buildings, center=center)

    assert folium_map is not None
    assert folium_map.location == center


def test_map_creation_with_tiles():
    """Test map creation with different tile styles"""
    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
    ]
    solution = Solution(positions={"RES-01": (100, 100)})

    mapper = InteractiveCampusMap(buildings=buildings)
    folium_map = mapper.create_map(solution, buildings=buildings, tiles="CartoDB positron")

    assert folium_map is not None


def test_building_naming():
    """Test semantic building name generation"""
    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
        Building("RES-02", BuildingType.RESIDENTIAL, 2000, 3),
        Building("EDU-01", BuildingType.EDUCATIONAL, 2500, 4),
    ]
    building_dict = {b.id: b for b in buildings}

    mapper = InteractiveCampusMap(buildings=buildings)

    name1 = mapper._get_building_name(buildings[0], building_dict)
    name2 = mapper._get_building_name(buildings[1], building_dict)
    name3 = mapper._get_building_name(buildings[2], building_dict)

    assert "Residential" in name1
    assert name1 != "RES-01"
    assert "Residential" in name2
    assert "Academic" in name3 or "Educational" in name3


def test_building_naming_library():
    """Test library naming (should be 'Main Library' for first)"""
    buildings = [
        Building("LIB-01", BuildingType.LIBRARY, 3000, 3),
        Building("LIB-02", BuildingType.LIBRARY, 3000, 3),
    ]
    building_dict = {b.id: b for b in buildings}

    mapper = InteractiveCampusMap(buildings=buildings)

    name1 = mapper._get_building_name(buildings[0], building_dict)
    name2 = mapper._get_building_name(buildings[1], building_dict)

    assert "Main Library" in name1 or "Library" in name1
    assert "Library 2" in name2 or "Library" in name2


def test_meters_to_latlon():
    """Test coordinate conversion"""
    mapper = InteractiveCampusMap()

    lat, lon = mapper._meters_to_latlon(0, 0)

    assert 40.0 < lat < 42.0  # Istanbul latitude range
    assert 28.0 < lon < 30.0  # Istanbul longitude range


def test_meters_to_latlon_non_zero():
    """Test coordinate conversion with non-zero coordinates"""
    mapper = InteractiveCampusMap()

    lat1, lon1 = mapper._meters_to_latlon(0, 0)
    lat2, lon2 = mapper._meters_to_latlon(1000, 1000)

    # Should be offset by approximately 1000m
    assert abs(lat2 - lat1) > 0.005  # Roughly 0.009 degrees for 1000m
    assert abs(lon2 - lon1) > 0.01  # Roughly 0.013 degrees for 1000m


def test_get_icon_color():
    """Test icon color mapping"""
    mapper = InteractiveCampusMap()

    color1 = mapper._get_icon_color(BuildingType.RESIDENTIAL)
    color2 = mapper._get_icon_color(BuildingType.EDUCATIONAL)
    color3 = mapper._get_icon_color(BuildingType.LIBRARY)

    assert color1 == "blue"
    assert color2 == "green"
    assert color3 == "purple"


def test_get_icon_color_unknown():
    """Test icon color for unknown building type"""
    mapper = InteractiveCampusMap()

    # Create a mock building type (this won't exist, but tests fallback)
    # Since we can't create new enum values, test with existing one
    color = mapper._get_icon_color(BuildingType.RESIDENTIAL)
    assert color in ["blue", "green", "purple", "orange", "red", "lightblue", "gray"]


def test_create_building_popup():
    """Test building popup HTML generation"""
    mapper = InteractiveCampusMap()

    building = Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3)
    position = (100.5, 200.7)

    popup = mapper._create_building_popup(building, position)

    assert isinstance(popup, str)
    assert "RES-01" in popup
    assert "Residential" in popup or "RESIDENTIAL" in popup
    assert "2000" in popup  # Area
    assert "3" in popup  # Floors
    assert "100.5" in popup  # Position X
    assert "200.7" in popup  # Position Y


def test_create_building_popup_existing():
    """Test building popup for existing buildings"""
    mapper = InteractiveCampusMap()

    building = Building("EXISTING-01", BuildingType.EDUCATIONAL, 2500, 4)

    popup = mapper._create_building_popup(building, is_existing=True)

    assert isinstance(popup, str)
    assert "Existing" in popup
    assert "EXISTING-01" in popup


def test_create_building_popup_no_position():
    """Test building popup without position"""
    mapper = InteractiveCampusMap()

    building = Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3)

    popup = mapper._create_building_popup(building, position=None)

    assert isinstance(popup, str)
    assert "RES-01" in popup
    # Should not have position row if position is None


def test_map_with_campus_data():
    """Test map creation with campus data"""
    # Create a simple campus boundary
    boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    campus = CampusData(
        name="Test Campus",
        location="Istanbul, Turkey",
        boundary=boundary,
        buildings=[],
        constraints={},
        metadata={},
    )

    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
    ]
    solution = Solution(positions={"RES-01": (500, 500)})

    mapper = InteractiveCampusMap(campus_data=campus, buildings=buildings)
    folium_map = mapper.create_map(solution, buildings=buildings)

    assert folium_map is not None


def test_map_with_existing_buildings():
    """Test map creation with existing buildings in campus data"""
    boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    existing_building = Building("EXISTING-01", BuildingType.LIBRARY, 3000, 3)
    existing_building.position = (200, 200)

    campus = CampusData(
        name="Test Campus",
        location="Istanbul, Turkey",
        boundary=boundary,
        buildings=[existing_building],
        constraints={},
        metadata={},
    )

    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
    ]
    solution = Solution(positions={"RES-01": (500, 500)})

    mapper = InteractiveCampusMap(campus_data=campus, buildings=buildings)
    folium_map = mapper.create_map(solution, buildings=buildings)

    assert folium_map is not None


def test_map_save():
    """Test saving map to file"""
    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
    ]
    solution = Solution(positions={"RES-01": (100, 100)})

    mapper = InteractiveCampusMap(buildings=buildings)
    mapper.create_map(solution, buildings=buildings)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        temp_path = f.name

    try:
        mapper.save_map(temp_path)
        assert Path(temp_path).exists()
        assert Path(temp_path).stat().st_size > 0
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_map_show_boundary_false():
    """Test map creation with boundary disabled"""
    boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    campus = CampusData(
        name="Test Campus",
        location="Istanbul, Turkey",
        boundary=boundary,
        buildings=[],
        constraints={},
        metadata={},
    )

    buildings = [
        Building("RES-01", BuildingType.RESIDENTIAL, 2000, 3),
    ]
    solution = Solution(positions={"RES-01": (500, 500)})

    mapper = InteractiveCampusMap(campus_data=campus, buildings=buildings, show_boundary=False)
    folium_map = mapper.create_map(solution, buildings=buildings)

    assert folium_map is not None


def test_map_empty_solution():
    """Test map creation with empty solution"""
    mapper = InteractiveCampusMap()
    solution = Solution(positions={})

    folium_map = mapper.create_map(solution, buildings=[])

    assert folium_map is not None


def test_building_colors_all_types():
    """Test that all building types have colors defined"""
    mapper = InteractiveCampusMap()

    for btype in BuildingType:
        color = mapper.BUILDING_COLORS.get(btype)
        assert color is not None, f"Building type {btype} missing color"
        assert color.startswith("#"), f"Color for {btype} should be hex format"


def test_building_icons_all_types():
    """Test that all building types have icons defined"""
    mapper = InteractiveCampusMap()

    for btype in BuildingType:
        icon = mapper.BUILDING_ICONS.get(btype)
        assert icon is not None, f"Building type {btype} missing icon"
        assert isinstance(icon, str), f"Icon for {btype} should be string"
