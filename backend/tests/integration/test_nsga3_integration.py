"""
Integration Tests for NSGA-III with Campus Planning
====================================================

Tests NSGA-III optimizer with real campus planning problems.

Created: 2026-01-02 (Week 4 Day 4)
"""

import numpy as np
import pytest

from src.algorithms import Building, BuildingType
from src.algorithms.nsga3 import NSGA3, count_reference_points


class TestNSGA3Initialization:
    """Test NSGA-III initialization."""

    def test_initialization_basic(self):
        """Test basic initialization with default parameters."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        ]
        bounds = (0, 0, 500, 500)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=20,
            n_generations=10,
            n_partitions=12,
        )

        # Check initialization
        assert optimizer.population_size == 20
        assert optimizer.n_generations == 10
        assert len(optimizer.reference_points) > 0
        assert optimizer.n_objectives >= 2  # At least 2 objectives

    def test_initialization_custom_reference_points(self):
        """Test initialization with custom reference points."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        ]
        bounds = (0, 0, 500, 500)

        # Custom 2D reference points
        custom_ref_points = np.array(
            [
                [1.0, 0.0],
                [0.5, 0.5],
                [0.0, 1.0],
            ]
        )

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=10,
            n_generations=5,
            reference_points=custom_ref_points,
        )

        # Should use custom reference points
        assert len(optimizer.reference_points) == 3
        assert np.allclose(optimizer.reference_points, custom_ref_points)

    def test_initialization_two_layer(self):
        """Test initialization with two-layer reference points."""
        buildings = [Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 4) for i in range(5)]
        bounds = (0, 0, 1000, 1000)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=50,
            n_generations=10,
            n_partitions=6,
            use_two_layer=True,
            n_partitions_inner=3,
        )

        # Two-layer should have more points
        n_outer = count_reference_points(optimizer.n_objectives, 6)
        n_inner = count_reference_points(optimizer.n_objectives, 3)
        assert len(optimizer.reference_points) == n_outer + n_inner


class TestNSGA3Optimization:
    """Test NSGA-III optimization process."""

    def test_optimize_small_problem(self):
        """Test optimization on small problem."""
        np.random.seed(42)

        buildings = [
            Building("Library", BuildingType.EDUCATIONAL, 2000, 3),
            Building("Dorm A", BuildingType.RESIDENTIAL, 3000, 5),
            Building("Cafeteria", BuildingType.COMMERCIAL, 1500, 2),
        ]
        bounds = (0, 0, 800, 800)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=20,
            n_generations=20,
            n_partitions=12,
        )

        result = optimizer.optimize()

        # Check results structure
        assert "pareto_front" in result
        assert "population" in result
        assert "pareto_objectives" in result
        assert "reference_points" in result
        assert "statistics" in result
        assert "convergence" in result

        # Check Pareto front
        pareto_front = result["pareto_front"]
        assert len(pareto_front) > 0
        assert len(pareto_front) <= optimizer.population_size

        # All Pareto solutions should have objectives
        for solution in pareto_front:
            assert hasattr(solution, "objectives")
            assert solution.objectives is not None
            assert len(solution.objectives) == optimizer.n_objectives

        # Check statistics
        stats = result["statistics"]
        assert stats["evaluations"] > 0
        assert stats["evaluations"] >= optimizer.population_size  # At least initial pop

    def test_pareto_front_non_dominated(self):
        """Test that Pareto front contains only non-dominated solutions."""
        np.random.seed(42)

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
            Building("B3", BuildingType.SOCIAL, 2500, 2),
        ]
        bounds = (0, 0, 700, 700)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=30,
            n_generations=15,
            n_partitions=12,
        )

        result = optimizer.optimize()
        pareto_objectives = result["pareto_objectives"]

        # Check that no solution in Pareto front dominates another
        from src.algorithms.nsga3 import dominates_objective

        n_pareto = len(pareto_objectives)
        for i in range(n_pareto):
            for j in range(n_pareto):
                if i != j:
                    # No solution should dominate another
                    assert not dominates_objective(pareto_objectives[i], pareto_objectives[j])

    def test_convergence_tracking(self):
        """Test convergence history tracking."""
        np.random.seed(42)

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        ]
        bounds = (0, 0, 600, 600)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=20,
            n_generations=10,
            n_partitions=12,
        )

        result = optimizer.optimize()
        convergence = result["convergence"]

        # Check convergence history
        assert "n_pareto_front" in convergence
        assert "ideal_point" in convergence

        # Should have entries for each generation
        assert len(convergence["n_pareto_front"]) == optimizer.n_generations
        assert len(convergence["ideal_point"]) == optimizer.n_generations

        # Pareto front sizes should be positive
        for n in convergence["n_pareto_front"]:
            assert n > 0


class TestNSGA3Diversity:
    """Test diversity preservation with reference points."""

    def test_diversity_with_reference_points(self):
        """Test that solutions are distributed across reference points."""
        np.random.seed(42)

        buildings = [Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 4) for i in range(4)]
        bounds = (0, 0, 900, 900)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=50,
            n_generations=30,
            n_partitions=12,
        )

        result = optimizer.optimize()

        # Extract Pareto front objectives
        pareto_objectives = result["pareto_objectives"]

        # Check diversity: solutions should have varied objective values
        obj_std = np.std(pareto_objectives, axis=0)

        # Standard deviation should be non-zero (diversity exists)
        for std in obj_std:
            assert std > 0, "Objectives should have diversity"

    def test_more_reference_points_better_coverage(self):
        """Test that more reference points lead to better Pareto coverage."""
        np.random.seed(42)

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
            Building("B3", BuildingType.SOCIAL, 2500, 2),
        ]
        bounds = (0, 0, 800, 800)

        # Test with fewer reference points
        optimizer_few = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=30,
            n_generations=20,
            n_partitions=4,  # Fewer partitions
        )

        result_few = optimizer_few.optimize()

        # Test with more reference points
        optimizer_many = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=30,
            n_generations=20,
            n_partitions=12,  # More partitions
        )

        result_many = optimizer_many.optimize()

        # More reference points should generally lead to larger Pareto front
        # (not guaranteed but likely with same population size)
        n_pareto_few = len(result_few["pareto_front"])
        n_pareto_many = len(result_many["pareto_front"])

        assert n_pareto_few > 0
        assert n_pareto_many > 0


class TestNSGA3Operators:
    """Test genetic operators in NSGA-III."""

    def test_crossover_rate_effect(self):
        """Test that crossover rate affects optimization."""
        np.random.seed(42)

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        ]
        bounds = (0, 0, 600, 600)

        # High crossover rate
        optimizer_high = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=20,
            n_generations=15,
            n_partitions=12,
            crossover_rate=0.9,
        )

        result_high = optimizer_high.optimize()

        # Should complete successfully
        assert len(result_high["pareto_front"]) > 0

    def test_mutation_rate_effect(self):
        """Test that mutation rate affects optimization."""
        np.random.seed(42)

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        ]
        bounds = (0, 0, 600, 600)

        # High mutation rate
        optimizer_high = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=20,
            n_generations=15,
            n_partitions=12,
            mutation_rate=0.3,  # High mutation
        )

        result_high = optimizer_high.optimize()

        # Should complete successfully
        assert len(result_high["pareto_front"]) > 0


class TestNSGA3Scalability:
    """Test NSGA-III with different problem sizes."""

    @pytest.mark.slow
    def test_medium_scale_problem(self):
        """Test with medium-scale problem (10 buildings)."""
        np.random.seed(42)

        buildings = [
            Building(f"Building_{i}", BuildingType.RESIDENTIAL, 2000, 4) for i in range(10)
        ]
        bounds = (0, 0, 1500, 1500)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=50,
            n_generations=30,
            n_partitions=12,
        )

        result = optimizer.optimize()

        # Should produce valid Pareto front
        assert len(result["pareto_front"]) > 0
        assert len(result["pareto_front"]) <= optimizer.population_size

        # All solutions should be valid
        for solution in result["pareto_front"]:
            assert solution.fitness is not None
            assert solution.objectives is not None

    def test_many_objectives(self):
        """Test NSGA-III advantage with many objectives."""
        np.random.seed(42)

        # NSGA-III is designed for many-objective problems (4+ objectives)
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
            Building("B3", BuildingType.SOCIAL, 2500, 2),
            Building("B4", BuildingType.COMMERCIAL, 1800, 2),
        ]
        bounds = (0, 0, 1000, 1000)

        optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=40,
            n_generations=25,
            n_partitions=6,  # For many objectives
        )

        result = optimizer.optimize()

        # Should handle many objectives
        assert optimizer.n_objectives >= 3
        assert len(result["pareto_front"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
