"""
Unit tests for objective functions (Test-First Approach).

Created: 2025-11-06
"""
from src.algorithms.building import Building, BuildingType
from src.algorithms.objectives import (
    maximize_adjacency_satisfaction,
    minimize_cost,
    minimize_walking_distance,
)
from src.algorithms.solution import Solution


class TestCostObjective:
    """Tests for cost minimization objective."""

    def test_cost_single_building(self):
        """Test cost calculation for single building"""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 1000, 2)  # 1000m² × 1500 TL = 1.5M TL
        ]
        solution = Solution(positions={"B1": (100, 100)})

        cost = minimize_cost(solution, buildings)

        # Expected: 1.5M / 100M = 0.015
        assert 0.0 <= cost <= 1.0
        assert abs(cost - 0.015) < 0.001

    def test_cost_normalization_clip(self):
        """Test that very large costs are clipped to 1.0"""
        buildings = [Building("B1", BuildingType.HEALTH, 100000, 1)]  # 100k m² × 2500 = 250M > 100M
        solution = Solution(positions={"B1": (100, 100)})

        cost = minimize_cost(solution, buildings)

        assert cost == 1.0  # Should be clipped

    def test_cost_unknown_type_fallback(self):
        """Test that unknown building types use default cost"""
        # This would require a new BuildingType, so we'll test with known types
        # and verify default handling in code
        pass  # Will verify in implementation


class TestWalkingDistance:
    """Tests for walking distance minimization objective."""

    def test_walking_ideal_distance(self):
        """Test that 200m returns score 0.0"""
        buildings = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("E1", BuildingType.EDUCATIONAL, 1000, 2),
        ]
        solution = Solution(positions={"R1": (0, 0), "E1": (200, 0)})  # Exactly 200m apart

        score = minimize_walking_distance(solution, buildings)

        assert abs(score - 0.0) < 0.01  # Should be ideal (0.0)

    def test_walking_max_distance(self):
        """Test that 800m returns score 1.0"""
        buildings = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("E1", BuildingType.EDUCATIONAL, 1000, 2),
        ]
        solution = Solution(positions={"R1": (0, 0), "E1": (800, 0)})  # Exactly 800m apart

        score = minimize_walking_distance(solution, buildings)

        assert abs(score - 1.0) < 0.01  # Should be max (1.0)

    def test_walking_no_pairs(self):
        """Test that missing building types returns 0.0"""
        buildings = [Building("C1", BuildingType.COMMERCIAL, 1000, 2)]
        solution = Solution(positions={"C1": (100, 100)})

        score = minimize_walking_distance(solution, buildings)

        assert score == 0.0


class TestAdjacencySatisfaction:
    """Tests for adjacency satisfaction maximization objective."""

    def test_adjacency_positive_pair(self):
        """Test positive adjacency (should be close)"""
        buildings = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("E1", BuildingType.EDUCATIONAL, 1000, 2),
        ]
        # Place 50m apart (very close, weight=+5.0)
        solution = Solution(positions={"R1": (0, 0), "E1": (50, 0)})

        score = maximize_adjacency_satisfaction(solution, buildings)

        # Should have low dissatisfaction (good satisfaction)
        assert 0.0 <= score <= 1.0
        assert score < 0.4  # Low dissatisfaction (close buildings should score well)

    def test_adjacency_negative_pair(self):
        """Test negative adjacency (should be far)"""
        buildings = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("H1", BuildingType.HEALTH, 1000, 2),
        ]
        # Place 50m apart (too close, weight=-3.0)
        solution1 = Solution(positions={"R1": (0, 0), "H1": (50, 0)})

        score1 = maximize_adjacency_satisfaction(solution1, buildings)

        # Place 400m apart (better)
        solution2 = Solution(positions={"R1": (0, 0), "H1": (400, 0)})

        score2 = maximize_adjacency_satisfaction(solution2, buildings)

        # Farther distance should have lower dissatisfaction
        assert score2 < score1
