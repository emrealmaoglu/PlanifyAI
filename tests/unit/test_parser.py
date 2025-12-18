"""
Unit tests for CampusDataParser.

Created: 2025-11-09
"""

import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from src.algorithms.building import Building, BuildingType
from src.data.campus_data import CampusData
from src.data.parser import CampusDataParser


@pytest.fixture
def sample_campus_dict():
    """Create a sample campus dictionary."""
    return {
        "name": "Test Campus",
        "location": "Istanbul, Turkey",
        "boundary": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]],
        },
        "existing_buildings": [
            {
                "id": "B1",
                "type": "residential",
                "area": 2000,
                "floors": 3,
                "position": [100, 100],
            }
        ],
        "constraints": {
            "setback_from_boundary": 10.0,
            "coverage_ratio_max": 0.3,
            "far_max": 2.0,
            "min_green_space_ratio": 0.4,
        },
        "metadata": {
            "total_area_m2": 1000000,
            "student_count": 5000,
            "established": 1970,
        },
    }


class TestCampusDataParser:
    """Test CampusDataParser class."""

    def test_from_dict(self, sample_campus_dict):
        """Test from_dict method."""
        campus = CampusDataParser.from_dict(sample_campus_dict)
        assert campus.name == "Test Campus"
        assert campus.location == "Istanbul, Turkey"
        assert len(campus.buildings) == 1
        assert campus.buildings[0].id == "B1"

    def test_from_dict_missing_name(self):
        """Test from_dict with missing name."""
        data = {
            "location": "Istanbul, Turkey",
            "boundary": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]],
            },
        }
        with pytest.raises(ValueError, match="Missing required field: 'name'"):
            CampusDataParser.from_dict(data)

    def test_from_dict_missing_location(self):
        """Test from_dict with missing location."""
        data = {
            "name": "Test Campus",
            "boundary": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]],
            },
        }
        with pytest.raises(ValueError, match="Missing required field: 'location'"):
            CampusDataParser.from_dict(data)

    def test_from_dict_missing_boundary(self):
        """Test from_dict with missing boundary."""
        data = {
            "name": "Test Campus",
            "location": "Istanbul, Turkey",
        }
        with pytest.raises(ValueError, match="Missing required field: 'boundary'"):
            CampusDataParser.from_dict(data)

    def test_from_geojson(self, sample_campus_dict):
        """Test from_geojson method."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_campus_dict, f)
            temp_path = f.name

        try:
            campus = CampusDataParser.from_geojson(temp_path)
            assert campus.name == "Test Campus"
            assert campus.location == "Istanbul, Turkey"
            assert len(campus.buildings) == 1
        finally:
            Path(temp_path).unlink()

    def test_from_geojson_file_not_found(self):
        """Test from_geojson with non-existent file."""
        with pytest.raises(FileNotFoundError):
            CampusDataParser.from_geojson("nonexistent_file.json")

    def test_validate_data(self, sample_campus_dict):
        """Test validate_data method."""
        campus = CampusDataParser.from_dict(sample_campus_dict)
        assert CampusDataParser.validate_data(campus) is True

    def test_validate_data_building_outside_boundary(self):
        """Test validate_data with building outside boundary."""
        boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        buildings = [Building("B1", BuildingType.RESIDENTIAL, 2000, 3, position=(1500, 1500))]
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=boundary,
            buildings=buildings,
        )
        with pytest.raises(ValueError, match="Building.*is outside campus boundary"):
            CampusDataParser.validate_data(campus)

    def test_validate_data_invalid_setback(self):
        """Test validate_data with invalid setback."""
        boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=boundary,
            constraints={"setback_from_boundary": -5.0},
        )
        with pytest.raises(ValueError, match="setback_from_boundary must be >= 0"):
            CampusDataParser.validate_data(campus)

    def test_validate_data_invalid_coverage_ratio(self):
        """Test validate_data with invalid coverage ratio."""
        boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=boundary,
            constraints={"coverage_ratio_max": 1.5},
        )
        with pytest.raises(ValueError, match="coverage_ratio_max must be between 0 and 1"):
            CampusDataParser.validate_data(campus)

    def test_validate_data_invalid_far(self):
        """Test validate_data with invalid FAR."""
        boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=boundary,
            constraints={"far_max": -1.0},
        )
        with pytest.raises(ValueError, match="far_max must be > 0"):
            CampusDataParser.validate_data(campus)

    def test_validate_data_invalid_green_space_ratio(self):
        """Test validate_data with invalid green space ratio."""
        boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=boundary,
            constraints={"min_green_space_ratio": 1.5},
        )
        with pytest.raises(ValueError, match="min_green_space_ratio must be between 0 and 1"):
            CampusDataParser.validate_data(campus)

    def test_from_dict_empty_buildings(self):
        """Test from_dict with empty buildings list."""
        data = {
            "name": "Test Campus",
            "location": "Istanbul, Turkey",
            "boundary": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]],
            },
            "existing_buildings": [],
            "constraints": {},
            "metadata": {},
        }
        campus = CampusDataParser.from_dict(data)
        assert campus.name == "Test Campus"
        assert len(campus.buildings) == 0

    def test_from_dict_no_constraints(self):
        """Test from_dict without constraints."""
        data = {
            "name": "Test Campus",
            "location": "Istanbul, Turkey",
            "boundary": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]],
            },
        }
        campus = CampusDataParser.from_dict(data)
        assert campus.name == "Test Campus"
        assert campus.constraints == {}

    def test_from_dict_no_metadata(self):
        """Test from_dict without metadata."""
        data = {
            "name": "Test Campus",
            "location": "Istanbul, Turkey",
            "boundary": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]],
            },
        }
        campus = CampusDataParser.from_dict(data)
        assert campus.name == "Test Campus"
        assert campus.metadata == {}

    def test_from_dict_invalid_boundary_coordinates(self):
        """Test from_dict with invalid boundary coordinates."""
        data = {
            "name": "Test Campus",
            "location": "Istanbul, Turkey",
            "boundary": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1000, 0]]],  # Invalid: not closed
            },
        }
        # Should raise an error when trying to create Polygon
        with pytest.raises((ValueError, TypeError)):
            CampusDataParser.from_dict(data)

    def test_validate_data_no_buildings(self):
        """Test validate_data with no buildings."""
        boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        campus = CampusData(
            name="Test Campus",
            location="Istanbul, Turkey",
            boundary=boundary,
            buildings=[],
        )
        assert CampusDataParser.validate_data(campus) is True
