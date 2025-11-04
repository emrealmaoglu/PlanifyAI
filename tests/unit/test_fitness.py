"""
Unit tests for Fitness Evaluator
"""
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.fitness import FitnessEvaluator
from src.algorithms.solution import Solution


class TestFitnessEvaluator:
    """Test FitnessEvaluator class"""

    def test_initialization_valid(self, sample_buildings, bounds):
        """Test valid initialization"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)
        assert evaluator.buildings == sample_buildings
        assert evaluator.bounds == bounds
        assert evaluator.safety_margin == 5.0

    def test_initialization_empty_buildings(self, bounds):
        """Test initialization with empty buildings list"""
        with pytest.raises(ValueError, match="buildings list cannot be empty"):
            FitnessEvaluator([], bounds)

    def test_initialization_invalid_bounds(self, sample_buildings):
        """Test initialization with invalid bounds"""
        # Invalid: x_min >= x_max
        with pytest.raises(ValueError, match="Invalid bounds"):
            FitnessEvaluator(sample_buildings, (100, 0, 50, 500))

        # Invalid: wrong number of values
        with pytest.raises(ValueError, match="bounds must be"):
            FitnessEvaluator(sample_buildings, (0, 0, 500))

    def test_initialization_invalid_weights(self, sample_buildings, bounds):
        """Test initialization with invalid weights"""
        weights = {"compactness": 0.5, "accessibility": 0.6}  # Sums to 1.1
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            FitnessEvaluator(sample_buildings, bounds, weights=weights)

    def test_compactness_score_ideal_distance(self, sample_buildings, bounds):
        """Test compactness with ideal inter-building distance"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)

        # Create solution with ~100m distances
        positions = {
            "B1": (100.0, 100.0),
            "B2": (200.0, 100.0),  # 100m away
            "B3": (100.0, 200.0),  # 100m away
        }
        solution = Solution(positions)

        score = evaluator._compactness_score(solution)
        assert 0.8 <= score <= 1.0, f"Expected high score for ideal distance, got {score}"

    def test_compactness_score_too_close(self, sample_buildings, bounds):
        """Test compactness with buildings too close"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)

        # Create solution with very close buildings
        positions = {
            "B1": (100.0, 100.0),
            "B2": (105.0, 100.0),  # 5m away (too close)
            "B3": (110.0, 100.0),  # 10m away
        }
        solution = Solution(positions)

        score = evaluator._compactness_score(solution)
        assert 0.0 <= score < 0.5, f"Expected low score for close buildings, got {score}"

    def test_compactness_score_single_building(self, bounds):
        """Test compactness with single building"""
        building = Building("B1", BuildingType.RESIDENTIAL, 2000, 5)
        evaluator = FitnessEvaluator([building], bounds)

        positions = {"B1": (250.0, 250.0)}
        solution = Solution(positions)

        score = evaluator._compactness_score(solution)
        assert score == 1.0, "Single building should have perfect compactness"

    def test_accessibility_score(self, sample_buildings, bounds):
        """Test accessibility score calculation"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)

        # Place buildings near centroid
        positions = {
            "B1": (250.0, 250.0),  # Near centroid
            "B2": (260.0, 250.0),
            "B3": (250.0, 260.0),
        }
        solution = Solution(positions)

        score = evaluator._accessibility_score(solution)
        assert 0.0 <= score <= 1.0
        assert score > 0.5, "Buildings near centroid should have high accessibility"

    def test_constraint_penalties_bounds_violation(self, sample_buildings, bounds):
        """Test penalty for out-of-bounds buildings"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)

        # Place building outside bounds
        positions = {
            "B1": (600.0, 250.0),  # Outside bounds (x_max = 500)
            "B2": (250.0, 250.0),
            "B3": (250.0, 250.0),
        }
        solution = Solution(positions)

        penalty = evaluator._calculate_penalties(solution)
        assert penalty >= 1000.0, "Out-of-bounds should have penalty >= 1000"

    def test_constraint_penalties_overlap(self, sample_buildings, bounds):
        """Test penalty for overlapping buildings"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)

        # Place buildings on top of each other
        positions = {
            "B1": (250.0, 250.0),
            "B2": (250.0, 250.0),  # Same position
            "B3": (250.0, 250.0),  # Same position
        }
        solution = Solution(positions)

        penalty = evaluator._calculate_penalties(solution)
        assert penalty >= 500.0, "Overlaps should have penalty >= 500"

    def test_evaluate_integration(self, sample_buildings, bounds):
        """Test full evaluation with valid solution"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)

        # Create valid solution
        positions = {
            "B1": (100.0, 100.0),
            "B2": (200.0, 100.0),
            "B3": (150.0, 200.0),
        }
        solution = Solution(positions)

        fitness = evaluator.evaluate(solution)
        assert isinstance(fitness, float)
        assert fitness > -10.0, "Fitness should be reasonable"

    def test_evaluate_missing_position(self, sample_buildings, bounds):
        """Test evaluation with missing position"""
        evaluator = FitnessEvaluator(sample_buildings, bounds)

        # Missing position for B2
        positions = {
            "B1": (100.0, 100.0),
            "B3": (150.0, 200.0),
        }
        solution = Solution(positions)

        with pytest.raises(ValueError, match="missing position"):
            evaluator.evaluate(solution)
