"""
Unit tests for visualization utilities.

Created: 2025-11-09
"""

import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from src.algorithms.solution import Solution
from src.data.campus_data import CampusData
from src.visualization.plot_utils import CampusPlotter


@pytest.fixture
def sample_campus():
    """Create a sample campus."""
    boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    return CampusData(
        name="Test Campus",
        location="Istanbul, Turkey",
        boundary=boundary,
        constraints={"setback_from_boundary": 10.0},
    )


@pytest.fixture
def sample_solution():
    """Create a sample solution."""
    positions = {
        "B1": (200, 200),
        "B2": (500, 500),
        "B3": (800, 800),
    }
    return Solution(positions)


class TestCampusPlotter:
    """Test CampusPlotter class."""

    def test_plotter_initialization(self, sample_campus):
        """Test plotter initialization."""
        plotter = CampusPlotter(sample_campus)
        assert plotter.campus_data == sample_campus

    def test_plot_solution(self, sample_campus, sample_solution):
        """Test plotting solution."""
        plotter = CampusPlotter(sample_campus)

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            plotter.plot_solution(sample_solution, save_path=temp_path)
            # Check file was created
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink()

    def test_plot_convergence(self, sample_campus):
        """Test plotting convergence."""
        plotter = CampusPlotter(sample_campus)

        result = {
            "convergence": {
                "ga_best_history": [0.5, 0.6, 0.7, 0.75, 0.8],
                "ga_avg_history": [0.4, 0.5, 0.6, 0.65, 0.7],
            }
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            plotter.plot_convergence(result, save_path=temp_path)
            # Check file was created
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink()

    def test_plot_objectives(self, sample_campus):
        """Test plotting objectives."""
        plotter = CampusPlotter(sample_campus)

        result = {
            "objectives": {
                "cost": 0.3,
                "walking": 0.4,
                "adjacency": 0.5,
            },
            "constraints": {
                "violations": {
                    "Setback from boundary: 10m": 0.1,
                }
            },
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            plotter.plot_objectives(result, save_path=temp_path)
            # Check file was created
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink()
