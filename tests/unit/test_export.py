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
