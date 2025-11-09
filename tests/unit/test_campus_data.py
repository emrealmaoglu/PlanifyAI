"""
Tests for CampusData class.

Created: 2025-11-08
"""

import pytest
from shapely.geometry import Point, Polygon

from src.algorithms.building import Building, BuildingType
from src.data.campus_data import CampusData


@pytest.fixture
def sample_boundary():
    """Create a sample campus boundary."""
    return Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])


@pytest.fixture
def sample_buildings():
    """Create sample existing buildings."""
    return [
        Building("existing_lib", BuildingType.LIBRARY, 3000, 3, position=(500, 500)),
        Building("existing_admin", BuildingType.ADMINISTRATIVE, 2000, 2, position=(200, 200)),
    ]


class TestCampusDataInitialization:
    """Test CampusData initialization."""

    def test_initialization_with_valid_data(self, sample_boundary, sample_buildings):
        """Test initialization with valid data."""
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=sample_boundary,
            buildings=sample_buildings,
            constraints={"setback": 10.0},
            metadata={"area": 1000000},
        )

        assert campus.name == "Test Campus"
        assert campus.location == "Istanbul, Turkey"
        assert len(campus.buildings) == 2
        assert campus.constraints["setback"] == 10.0

    def test_initialization_with_invalid_boundary(self):
        """Test initialization with invalid boundary."""
        # Invalid polygon (self-intersecting)
        invalid_polygon = Polygon([(0, 0), (1000, 1000), (1000, 0), (0, 1000)])

        with pytest.raises(ValueError, match="boundary polygon is not valid"):
            CampusData(
                name="Test",
                location="Test",
                boundary=invalid_polygon,
            )

    def test_initialization_with_building_without_position(self, sample_boundary):
        """Test initialization with building without position."""
        building = Building("test", BuildingType.RESIDENTIAL, 1000, 2)

        with pytest.raises(ValueError, match="must have a position set"):
            CampusData(
                name="Test",
                location="Test",
                boundary=sample_boundary,
                buildings=[building],
            )


class TestCampusDataMethods:
    """Test CampusData methods."""

    def test_get_bounds(self, sample_boundary):
        """Test get_bounds method."""
        campus = CampusData(
            name="Test",
            location="Test",
            boundary=sample_boundary,
        )

        bounds = campus.get_bounds()
        assert bounds == (0.0, 0.0, 1000.0, 1000.0)

    def test_is_valid_position(self, sample_boundary):
        """Test is_valid_position method."""
        campus = CampusData(
            name="Test",
            location="Test",
            boundary=sample_boundary,
        )

        # Point inside boundary
        assert campus.is_valid_position(Point(500, 500)) is True
        assert campus.is_valid_position((500, 500)) is True

        # Point outside boundary
        assert campus.is_valid_position(Point(1500, 1500)) is False

        # Point on boundary
        assert campus.is_valid_position(Point(0, 500)) is True

    def test_get_total_area(self, sample_boundary):
        """Test get_total_area method."""
        campus = CampusData(
            name="Test",
            location="Test",
            boundary=sample_boundary,
        )

        area = campus.get_total_area()
        assert area == 1000000.0  # 1000 x 1000

    def test_to_dict(self, sample_boundary, sample_buildings):
        """Test to_dict serialization."""
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=sample_boundary,
            buildings=sample_buildings,
            constraints={"setback": 10.0},
            metadata={"area": 1000000},
        )

        data = campus.to_dict()

        assert data["name"] == "Test Campus"
        assert data["location"] == "Istanbul, Turkey"
        assert len(data["existing_buildings"]) == 2
        assert data["constraints"]["setback"] == 10.0
        assert "boundary" in data
        assert data["boundary"]["type"] == "Polygon"

    def test_from_dict(self, sample_boundary, sample_buildings):
        """Test from_dict deserialization."""
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=sample_boundary,
            buildings=sample_buildings,
            constraints={"setback": 10.0},
            metadata={"area": 1000000},
        )

        data = campus.to_dict()
        campus2 = CampusData.from_dict(data)

        assert campus2.name == campus.name
        assert campus2.location == campus.location
        assert len(campus2.buildings) == len(campus.buildings)
        assert campus2.constraints == campus.constraints
        assert campus2.metadata == campus.metadata

        # Verify buildings
        assert campus2.buildings[0].id == "existing_lib"
        assert campus2.buildings[0].type == BuildingType.LIBRARY
        assert campus2.buildings[0].position == (500, 500)


class TestCampusDataEdgeCases:
    """Test edge cases."""

    def test_empty_buildings_list(self, sample_boundary):
        """Test with empty buildings list."""
        campus = CampusData(
            name="Test",
            location="Test",
            boundary=sample_boundary,
            buildings=[],
        )

        assert len(campus.buildings) == 0
        assert campus.get_bounds() == (0.0, 0.0, 1000.0, 1000.0)

    def test_irregular_boundary(self):
        """Test with irregular boundary shape."""
        # L-shaped boundary
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (1000, 500), (1000, 1000), (0, 1000)])

        campus = CampusData(
            name="Test",
            location="Test",
            boundary=boundary,
        )

        assert campus.is_valid_position(Point(250, 250)) is True
        assert campus.is_valid_position(Point(750, 750)) is True
        assert campus.is_valid_position(Point(750, 250)) is False
