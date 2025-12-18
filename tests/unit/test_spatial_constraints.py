"""
Unit tests for spatial constraints.

Created: 2025-11-09
"""

import pytest
from shapely.geometry import Polygon

from src.algorithms.building import Building, BuildingType
from src.algorithms.solution import Solution
from src.constraints.spatial_constraints import (
    ConstraintManager,
    CoverageRatioConstraint,
    FloorAreaRatioConstraint,
    GreenSpaceConstraint,
    SetbackConstraint,
)
from src.data.campus_data import CampusData


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
def sample_buildings():
    """Create sample buildings."""
    return [
        Building("B1", BuildingType.RESIDENTIAL, 2000, 2),  # footprint: 1000
        Building("B2", BuildingType.EDUCATIONAL, 3000, 3),  # footprint: 1000
        Building("B3", BuildingType.LIBRARY, 4000, 4),  # footprint: 1000
    ]


@pytest.fixture
def sample_solution(sample_buildings):
    """Create a sample solution."""
    positions = {
        "B1": (200, 200),
        "B2": (500, 500),
        "B3": (800, 800),
    }
    return Solution(positions)


class TestSetbackConstraint:
    """Test SetbackConstraint class."""

    def test_setback_constraint_satisfied(self, sample_campus, sample_buildings, sample_solution):
        """Test setback constraint when satisfied."""
        constraint = SetbackConstraint(setback_distance=10.0)
        # Buildings are well within boundary with 10m setback
        assert constraint.check(sample_solution, sample_campus, sample_buildings) is True
        assert constraint.penalty(sample_solution, sample_campus, sample_buildings) == 0.0

    def test_setback_constraint_violated(self, sample_campus, sample_buildings):
        """Test setback constraint when violated."""
        constraint = SetbackConstraint(setback_distance=50.0)
        # Place buildings too close to boundary
        positions = {
            "B1": (5, 5),  # Very close to boundary
            "B2": (10, 10),
            "B3": (15, 15),
        }
        solution = Solution(positions)
        assert constraint.check(solution, sample_campus, sample_buildings) is False
        penalty = constraint.penalty(solution, sample_campus, sample_buildings)
        assert penalty > 0.0
        assert penalty <= 1.0

    def test_setback_constraint_zero_setback(
        self, sample_campus, sample_buildings, sample_solution
    ):
        """Test setback constraint with zero setback."""
        constraint = SetbackConstraint(setback_distance=0.0)
        assert constraint.check(sample_solution, sample_campus, sample_buildings) is True
        assert constraint.penalty(sample_solution, sample_campus, sample_buildings) == 0.0

    def test_setback_constraint_invalid_setback(self):
        """Test setback constraint with invalid setback."""
        with pytest.raises(ValueError, match="setback_distance must be >= 0"):
            SetbackConstraint(setback_distance=-5.0)


class TestCoverageRatioConstraint:
    """Test CoverageRatioConstraint class."""

    def test_coverage_constraint_satisfied(self, sample_campus, sample_buildings, sample_solution):
        """Test coverage constraint when satisfied."""
        constraint = CoverageRatioConstraint(max_coverage_ratio=0.5)
        # Total footprint: 3000, Site area: 1000000, Coverage: 0.003 (well below 0.5)
        assert constraint.check(sample_solution, sample_campus, sample_buildings) is True
        assert constraint.penalty(sample_solution, sample_campus, sample_buildings) == 0.0

    def test_coverage_constraint_violated(self, sample_campus):
        """Test coverage constraint when violated."""
        constraint = CoverageRatioConstraint(max_coverage_ratio=0.001)
        # Create buildings with large footprint
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 1),  # footprint: 2000
        ]
        positions = {"B1": (500, 500)}
        solution = Solution(positions)
        # Coverage: 2000/1000000 = 0.002 > 0.001
        assert constraint.check(solution, sample_campus, buildings) is False
        penalty = constraint.penalty(solution, sample_campus, buildings)
        assert penalty > 0.0
        assert penalty <= 1.0

    def test_coverage_constraint_invalid_ratio(self):
        """Test coverage constraint with invalid ratio."""
        with pytest.raises(ValueError, match="max_coverage_ratio must be between 0 and 1"):
            CoverageRatioConstraint(max_coverage_ratio=1.5)


class TestFloorAreaRatioConstraint:
    """Test FloorAreaRatioConstraint class."""

    def test_far_constraint_satisfied(self, sample_campus, sample_buildings, sample_solution):
        """Test FAR constraint when satisfied."""
        constraint = FloorAreaRatioConstraint(max_far=1.0)
        # Total area: 9000, Site area: 1000000, FAR: 0.009 (well below 1.0)
        assert constraint.check(sample_solution, sample_campus, sample_buildings) is True
        assert constraint.penalty(sample_solution, sample_campus, sample_buildings) == 0.0

    def test_far_constraint_violated(self, sample_campus):
        """Test FAR constraint when violated."""
        constraint = FloorAreaRatioConstraint(max_far=0.001)
        # Create buildings with large area
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 1),  # area: 2000
        ]
        positions = {"B1": (500, 500)}
        solution = Solution(positions)
        # FAR: 2000/1000000 = 0.002 > 0.001
        assert constraint.check(solution, sample_campus, buildings) is False
        penalty = constraint.penalty(solution, sample_campus, buildings)
        assert penalty > 0.0
        assert penalty <= 1.0

    def test_far_constraint_invalid_far(self):
        """Test FAR constraint with invalid FAR."""
        with pytest.raises(ValueError, match="max_far must be > 0"):
            FloorAreaRatioConstraint(max_far=-1.0)


class TestGreenSpaceConstraint:
    """Test GreenSpaceConstraint class."""

    def test_green_space_constraint_satisfied(
        self, sample_campus, sample_buildings, sample_solution
    ):
        """Test green space constraint when satisfied."""
        constraint = GreenSpaceConstraint(min_green_ratio=0.1)
        # Coverage is very low, so green space is high
        assert constraint.check(sample_solution, sample_campus, sample_buildings) is True
        assert constraint.penalty(sample_solution, sample_campus, sample_buildings) == 0.0

    def test_green_space_constraint_violated(self, sample_campus):
        """Test green space constraint when violated."""
        # Create many buildings to reduce green space
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 50000, 1),  # Large footprint
            Building("B2", BuildingType.EDUCATIONAL, 50000, 1),
        ]
        positions = {"B1": (300, 300), "B2": (700, 700)}
        solution = Solution(positions)
        # Coverage: 100000/1000000 = 0.1, Green: 0.9, but we need >0.95
        # Create a case where green space is violated
        constraint = GreenSpaceConstraint(min_green_ratio=0.95)
        assert constraint.check(solution, sample_campus, buildings) is False
        penalty = constraint.penalty(solution, sample_campus, buildings)
        assert penalty > 0.0

    def test_green_space_constraint_invalid_ratio(self):
        """Test green space constraint with invalid ratio."""
        with pytest.raises(ValueError, match="min_green_ratio must be between 0 and 1"):
            GreenSpaceConstraint(min_green_ratio=1.5)


class TestConstraintManager:
    """Test ConstraintManager class."""

    def test_constraint_manager_add_constraint(self):
        """Test adding constraints to manager."""
        manager = ConstraintManager()
        manager.add_constraint(SetbackConstraint(10.0))
        manager.add_constraint(CoverageRatioConstraint(0.3))
        assert len(manager) == 2

    def test_constraint_manager_check_all(self, sample_campus, sample_buildings, sample_solution):
        """Test checking all constraints."""
        manager = ConstraintManager()
        manager.add_constraint(SetbackConstraint(10.0))
        manager.add_constraint(CoverageRatioConstraint(0.5))
        assert manager.check_all(sample_solution, sample_campus, sample_buildings) is True

    def test_constraint_manager_total_penalty(
        self, sample_campus, sample_buildings, sample_solution
    ):
        """Test calculating total penalty."""
        manager = ConstraintManager()
        manager.add_constraint(SetbackConstraint(10.0))
        manager.add_constraint(CoverageRatioConstraint(0.5))
        penalty = manager.total_penalty(sample_solution, sample_campus, sample_buildings)
        assert penalty >= 0.0
        assert penalty <= 2.0  # Max 2 constraints, each max 1.0

    def test_constraint_manager_violations(self, sample_campus):
        """Test getting violations."""
        manager = ConstraintManager()
        manager.add_constraint(SetbackConstraint(50.0))  # Large setback, likely violated
        manager.add_constraint(CoverageRatioConstraint(0.001))  # Very strict coverage

        buildings = [Building("B1", BuildingType.RESIDENTIAL, 5000, 1)]
        positions = {"B1": (5, 5)}  # Very close to boundary
        solution = Solution(positions)

        violations = manager.violations(solution, sample_campus, buildings)
        assert len(violations) > 0  # Should have violations
        assert all(0 < penalty <= 1.0 for penalty in violations.values())

    def test_constraint_manager_invalid_constraint(self):
        """Test adding invalid constraint."""
        manager = ConstraintManager()
        with pytest.raises(TypeError, match="constraint must be SpatialConstraint"):
            manager.add_constraint("not a constraint")

    def test_constraint_manager_repr(self):
        """Test constraint manager representation."""
        manager = ConstraintManager()
        manager.add_constraint(SetbackConstraint(10.0))
        repr_str = repr(manager)
        assert "ConstraintManager" in repr_str
        assert "1 constraints" in repr_str
