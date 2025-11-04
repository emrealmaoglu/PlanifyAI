"""
Unit tests for Solution class
"""
import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.solution import Solution


class TestSolutionCreation:
    """Test Solution object creation"""

    def test_solution_creation(self):
        """Test creating a solution with positions"""
        positions = {"b1": (100.0, 200.0), "b2": (300.0, 400.0)}
        solution = Solution(positions)
        assert len(solution.positions) == 2
        assert solution.positions["b1"] == (100.0, 200.0)
        assert solution.positions["b2"] == (300.0, 400.0)
        assert solution.fitness is None
        assert solution.objectives == {}
        assert solution.metadata == {}

    def test_solution_creation_with_fitness(self):
        """Test creating a solution with fitness score"""
        positions = {"b1": (100.0, 200.0)}
        solution = Solution(positions, fitness=0.85)
        assert solution.fitness == 0.85

    def test_solution_creation_with_objectives(self):
        """Test creating a solution with objectives"""
        positions = {"b1": (100.0, 200.0)}
        objectives = {"compactness": 0.7, "accessibility": 0.8}
        solution = Solution(positions, objectives=objectives)
        assert solution.objectives == objectives


class TestSolutionCopy:
    """Test Solution copying"""

    def test_solution_copy(self):
        """Test deep copy of solution"""
        positions = {"b1": (100.0, 200.0), "b2": (300.0, 400.0)}
        solution = Solution(positions, fitness=0.85)
        solution.metadata["test"] = "value"

        copy_solution = solution.copy()

        # Should be equal
        assert copy_solution.positions == solution.positions
        assert copy_solution.fitness == solution.fitness
        assert copy_solution.metadata == solution.metadata

        # But should be independent
        copy_solution.set_position("b1", (999.0, 999.0))
        assert solution.positions["b1"] == (100.0, 200.0)  # Original unchanged

        copy_solution.metadata["new_key"] = "new_value"
        assert "new_key" not in solution.metadata  # Original unchanged


class TestSolutionPositionManagement:
    """Test Solution position get/set methods"""

    def test_solution_get_position(self):
        """Test getting position of a building"""
        positions = {"b1": (100.0, 200.0), "b2": (300.0, 400.0)}
        solution = Solution(positions)
        assert solution.get_position("b1") == (100.0, 200.0)
        assert solution.get_position("b2") == (300.0, 400.0)

    def test_solution_set_position(self):
        """Test setting position of a building"""
        positions = {"b1": (100.0, 200.0)}
        solution = Solution(positions, fitness=0.85)
        solution.set_position("b1", (500.0, 600.0))
        assert solution.positions["b1"] == (500.0, 600.0)
        # Fitness should be invalidated
        assert solution.fitness is None

    def test_solution_get_all_coordinates(self):
        """Test getting all coordinates as NumPy array"""
        positions = {"b1": (100.0, 200.0), "b2": (300.0, 400.0)}
        solution = Solution(positions)
        coords = solution.get_all_coordinates()
        assert isinstance(coords, np.ndarray)
        assert coords.shape == (2, 2)
        assert np.allclose(coords, [[100.0, 200.0], [300.0, 400.0]])


class TestSolutionGeometry:
    """Test Solution geometric calculations"""

    def test_solution_centroid_calculation(self):
        """Test centroid calculation"""
        positions = {
            "b1": (0.0, 0.0),
            "b2": (100.0, 0.0),
            "b3": (0.0, 100.0),
            "b4": (100.0, 100.0),
        }
        solution = Solution(positions)
        centroid = solution.compute_centroid()
        expected_centroid = (50.0, 50.0)
        assert centroid == pytest.approx(expected_centroid)

    def test_solution_centroid_single_building(self):
        """Test centroid with single building"""
        positions = {"b1": (100.0, 200.0)}
        solution = Solution(positions)
        centroid = solution.compute_centroid()
        assert centroid == (100.0, 200.0)

    def test_solution_bounding_box(self):
        """Test bounding box calculation"""
        positions = {
            "b1": (10.0, 20.0),
            "b2": (50.0, 30.0),
            "b3": (30.0, 60.0),
        }
        solution = Solution(positions)
        bbox = solution.compute_bounding_box()
        assert bbox == (10.0, 20.0, 50.0, 60.0)  # x_min, y_min, x_max, y_max

    def test_solution_bounding_box_single_point(self):
        """Test bounding box with single building"""
        positions = {"b1": (100.0, 200.0)}
        solution = Solution(positions)
        bbox = solution.compute_bounding_box()
        assert bbox == (100.0, 200.0, 100.0, 200.0)


class TestSolutionValidity:
    """Test Solution validity checking"""

    def test_solution_valid_all_within_bounds(self):
        """Test validity when all buildings are within bounds"""
        buildings = [
            Building("b1", BuildingType.LIBRARY, 5000.0, 3),
            Building("b2", BuildingType.EDUCATIONAL, 6000.0, 4),
        ]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        positions = {
            "b1": (100.0, 100.0),  # Well within bounds
            "b2": (200.0, 200.0),  # Well within bounds
        }
        solution = Solution(positions)

        # Set positions on buildings for overlap check
        buildings[0].position = positions["b1"]
        buildings[1].position = positions["b2"]

        assert solution.is_valid(buildings, bounds)

    def test_solution_invalid_missing_building(self):
        """Test validity when building ID is missing"""
        buildings = [
            Building("b1", BuildingType.LIBRARY, 5000.0, 3),
            Building("b2", BuildingType.EDUCATIONAL, 6000.0, 4),
        ]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        positions = {"b1": (100.0, 100.0)}  # Missing b2
        solution = Solution(positions)
        assert not solution.is_valid(buildings, bounds)

    def test_solution_invalid_out_of_bounds(self):
        """Test validity when building is out of bounds"""
        building = Building("b1", BuildingType.LIBRARY, 5000.0, 3)
        bounds = (0.0, 0.0, 100.0, 100.0)
        # Building radius is ~23m, so position near edge should be invalid
        positions = {"b1": (10.0, 10.0)}  # Too close to edge (radius ~23m)
        solution = Solution(positions)
        building.position = positions["b1"]
        assert not solution.is_valid([building], bounds)

    def test_solution_invalid_overlapping_buildings(self):
        """Test validity when buildings overlap"""
        buildings = [
            Building("b1", BuildingType.LIBRARY, 5000.0, 3),
            Building("b2", BuildingType.EDUCATIONAL, 6000.0, 4),
        ]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        # Place buildings very close (will overlap)
        positions = {"b1": (100.0, 100.0), "b2": (100.0, 100.0)}
        solution = Solution(positions)
        assert not solution.is_valid(buildings, bounds)

    def test_solution_valid_no_overlaps(self):
        """Test validity when buildings don't overlap"""
        buildings = [
            Building("b1", BuildingType.LIBRARY, 5000.0, 3),
            Building("b2", BuildingType.EDUCATIONAL, 6000.0, 4),
        ]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        # Place buildings far apart
        positions = {"b1": (100.0, 100.0), "b2": (500.0, 500.0)}
        solution = Solution(positions)
        assert solution.is_valid(buildings, bounds)


class TestSolutionRepresentation:
    """Test Solution string representation"""

    def test_solution_repr_without_fitness(self):
        """Test solution representation without fitness"""
        positions = {"b1": (100.0, 200.0), "b2": (300.0, 400.0)}
        solution = Solution(positions)
        repr_str = repr(solution)
        assert "2 buildings" in repr_str
        assert "unscored" in repr_str.lower()

    def test_solution_repr_with_fitness(self):
        """Test solution representation with fitness"""
        positions = {"b1": (100.0, 200.0)}
        solution = Solution(positions, fitness=0.85)
        repr_str = repr(solution)
        assert "1 buildings" in repr_str
        assert "0.8500" in repr_str or "0.85" in repr_str
