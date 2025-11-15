"""
Unit tests for result export utilities.

Created: 2025-11-09
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import Polygon

from src.algorithms.solution import Solution
from src.data.campus_data import CampusData
from src.data.export import ResultExporter


@pytest.fixture
def sample_campus():
    """Create a sample campus."""
    boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    return CampusData(
        name="Test Campus",
        location="Istanbul, Turkey",
        boundary=boundary,
        buildings=[],
        constraints={},
        metadata={},
    )


@pytest.fixture
def sample_solution():
    """Create a sample solution."""
    positions = {
        "B1": (200, 200),
        "B2": (500, 500),
        "B3": (800, 800),
    }
    return Solution(positions, fitness=0.85)


@pytest.fixture
def sample_result():
    """Create a sample result dictionary."""
    return {
        "best_solution": Solution({"B1": (200, 200), "B2": (500, 500)}, fitness=0.85),
        "fitness": 0.85,
        "objectives": {"cost": 0.9, "walking": 0.8, "adjacency": 0.85},
        "statistics": {"runtime": 1.5, "evaluations": 1000},
    }


class TestResultExporter:
    """Test ResultExporter class."""

    def test_to_geojson(self, sample_solution, sample_campus):
        """Test GeoJSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.geojson"
            ResultExporter.to_geojson(sample_solution, sample_campus, str(filepath))

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)
                assert "type" in data
                assert "features" in data

    def test_to_csv(self, sample_solution):
        """Test CSV export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.csv"
            ResultExporter.to_csv(sample_solution, str(filepath))

            assert filepath.exists()
            df = pd.read_csv(filepath)
            assert "building_id" in df.columns
            assert "x" in df.columns
            assert "y" in df.columns
            assert len(df) == len(sample_solution.positions)

    def test_to_json(self, sample_result):
        """Test JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            ResultExporter.to_json(sample_result, str(filepath))

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)
                assert "fitness" in data
                assert "objectives" in data
                assert "statistics" in data

    def test_generate_report(self, sample_result):
        """Test Markdown report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.md"
            ResultExporter.generate_report(sample_result, str(filepath))

            assert filepath.exists()
            content = filepath.read_text()
            assert "Fitness" in content
            assert "Objectives" in content
            assert "Statistics" in content

    def test_to_geojson_dict(self, sample_solution, sample_campus):
        """Test GeoJSON dictionary export."""
        from src.algorithms.building import Building, BuildingType

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
            Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
        ]

        geojson = ResultExporter.to_geojson_dict(sample_solution, sample_campus, buildings)

        assert isinstance(geojson, dict)
        assert "type" in geojson
        assert geojson["type"] == "FeatureCollection"
        assert "features" in geojson
        assert len(geojson["features"]) > 0

        # Check boundary feature
        boundary_features = [
            f for f in geojson["features"] if f["properties"]["type"] == "campus_boundary"
        ]
        assert len(boundary_features) == 1

        # Check building features
        building_features = [
            f for f in geojson["features"] if f["properties"]["type"] != "campus_boundary"
        ]
        assert len(building_features) == len(sample_solution.positions)

    def test_to_geojson_dict_no_buildings(self, sample_solution, sample_campus):
        """Test GeoJSON dictionary export without building metadata."""
        geojson = ResultExporter.to_geojson_dict(sample_solution, sample_campus, buildings=None)

        assert isinstance(geojson, dict)
        assert "features" in geojson
        # Should still have building features, but with default metadata
        building_features = [
            f for f in geojson["features"] if f["properties"]["type"] != "campus_boundary"
        ]
        assert len(building_features) == len(sample_solution.positions)
        # Check default values
        for feature in building_features:
            assert feature["properties"]["type"] == "unknown"
            assert feature["properties"]["area"] == 0.0

    def test_to_csv_string(self, sample_solution):
        """Test CSV string export."""
        from src.algorithms.building import Building, BuildingType

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
            Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
        ]

        csv_string = ResultExporter.to_csv_string(sample_solution, buildings)

        assert isinstance(csv_string, str)
        assert "building_id" in csv_string
        assert "x" in csv_string
        assert "y" in csv_string
        assert "type" in csv_string
        assert "area" in csv_string
        assert "floors" in csv_string

        # Parse and verify
        import io

        df = pd.read_csv(io.StringIO(csv_string))
        assert len(df) == len(sample_solution.positions)
        assert "building_id" in df.columns

    def test_to_csv_string_no_buildings(self, sample_solution):
        """Test CSV string export without building metadata."""
        csv_string = ResultExporter.to_csv_string(sample_solution, buildings=None)

        assert isinstance(csv_string, str)
        assert "building_id" in csv_string

        # Parse and verify default values
        import io

        df = pd.read_csv(io.StringIO(csv_string))
        assert len(df) == len(sample_solution.positions)
        # Check that unknown type is used
        assert all(df["type"] == "unknown")

    def test_generate_report_string(self, sample_result):
        """Test Markdown report string generation."""
        report_string = ResultExporter.generate_report_string(sample_result)

        assert isinstance(report_string, str)
        assert "Fitness" in report_string
        assert "Objectives" in report_string
        assert "Statistics" in report_string
        assert "0.85" in report_string  # Fitness value

    def test_generate_report_string_with_constraints(self, sample_result):
        """Test report generation with constraint violations."""
        sample_result["constraints"] = {
            "satisfied": False,
            "penalty": 0.15,
            "violations": {"setback": 0.1, "coverage": 0.05},
        }

        report_string = ResultExporter.generate_report_string(sample_result)

        assert isinstance(report_string, str)
        assert "Constraints" in report_string
        assert "violations" in report_string.lower() or "penalty" in report_string.lower()

    def test_to_csv_with_buildings(self, sample_solution):
        """Test CSV export with building metadata."""
        from src.algorithms.building import Building, BuildingType

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
            Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.csv"
            ResultExporter.to_csv(sample_solution, str(filepath), buildings=buildings)

            assert filepath.exists()
            df = pd.read_csv(filepath)
            assert "building_id" in df.columns
            assert "type" in df.columns
            assert "area" in df.columns
            assert "floors" in df.columns
            assert len(df) == len(sample_solution.positions)
