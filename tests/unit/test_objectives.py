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
    """Tests for walking distance satisfaction objective."""

    def test_walking_distance_not_zero(self):
        """Test that walking distance returns non-zero for typical solutions"""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
            Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
        ]
        solution = Solution(
            positions={
                "B1": (100, 100),
                "B2": (200, 200),
            }
        )

        score = minimize_walking_distance(solution, buildings)

        assert score > 0.5, f"Walking distance score should be >0.5, got {score}"
        assert score < 1.0, f"Walking distance score should be <1.0, got {score}"

    def test_walking_close_buildings(self):
        """Test that closer buildings get higher scores"""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("B2", BuildingType.EDUCATIONAL, 1000, 2),
        ]
        # Close buildings (centroid distance ~50m)
        solution1 = Solution(positions={"B1": (0, 0), "B2": (100, 0)})
        # Far buildings (centroid distance ~500m)
        solution2 = Solution(positions={"B1": (0, 0), "B2": (1000, 0)})

        score1 = minimize_walking_distance(solution1, buildings)
        score2 = minimize_walking_distance(solution2, buildings)

        # Closer buildings should have higher score
        assert (
            score1 > score2
        ), f"Close buildings ({score1}) should score higher than far ({score2})"

    def test_walking_empty_solution(self):
        """Test that empty solution returns 0.0"""
        buildings = [Building("B1", BuildingType.COMMERCIAL, 1000, 2)]
        solution = Solution(positions={})

        score = minimize_walking_distance(solution, buildings)

        assert score == 0.0


class TestAdjacencySatisfaction:
    """Tests for adjacency satisfaction maximization objective."""

    def test_adjacency_not_zero(self):
        """Test that adjacency returns non-zero for typical solutions"""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
            Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
            Building("B3", BuildingType.LIBRARY, 3000, 2),
        ]
        solution = Solution(
            positions={
                "B1": (100, 100),
                "B2": (150, 100),  # Close to B1 (compatible)
                "B3": (140, 100),  # Close to B2 (very compatible)
            }
        )

        score = maximize_adjacency_satisfaction(solution, buildings)

        assert score > 0.3, f"Adjacency score should be >0.3, got {score}"
        assert score < 1.0, f"Adjacency score should be <1.0, got {score}"

    def test_adjacency_compatible_pair_close(self):
        """Test that compatible buildings close together get high scores"""
        buildings = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("E1", BuildingType.EDUCATIONAL, 1000, 2),
        ]
        # Place 100m apart (ideal distance for compatible pair)
        solution = Solution(positions={"R1": (0, 0), "E1": (100, 0)})

        score = maximize_adjacency_satisfaction(solution, buildings)

        # Should have good satisfaction (compatible and close)
        assert 0.0 <= score <= 1.0
        assert score > 0.4, f"Compatible close buildings should score >0.4, got {score}"

    def test_adjacency_compatible_vs_incompatible(self):
        """Test that compatible pairs score higher than incompatible pairs"""
        # Compatible pair: RESIDENTIAL-EDUCATIONAL
        buildings1 = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("E1", BuildingType.EDUCATIONAL, 1000, 2),
        ]
        solution1 = Solution(positions={"R1": (0, 0), "E1": (100, 0)})

        # Less compatible pair: RESIDENTIAL-COMMERCIAL (neutral compatibility)
        buildings2 = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
            Building("C1", BuildingType.COMMERCIAL, 1000, 2),
        ]
        solution2 = Solution(positions={"R1": (0, 0), "C1": (100, 0)})

        score1 = maximize_adjacency_satisfaction(solution1, buildings1)
        score2 = maximize_adjacency_satisfaction(solution2, buildings2)

        # Compatible pair should score higher
        assert (
            score1 > score2
        ), f"Compatible pair ({score1}) should score higher than neutral ({score2})"
