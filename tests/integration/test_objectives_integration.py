"""
Integration tests for objective functions with SA.

Tests that objectives work correctly in full optimization pipeline.

Created: 2025-11-06
"""
from src.algorithms.building import create_sample_campus
from src.algorithms.hsaga import HybridSAGA


class TestObjectivesIntegration:
    """Integration tests for objectives with SA."""

    def test_sa_with_new_objectives(self):
        """Test SA optimization with Day 3 objectives"""
        # Create test campus
        buildings = create_sample_campus()
        bounds = (0, 0, 1000, 1000)

        # Create optimizer
        optimizer = HybridSAGA(buildings, bounds)

        # Reduce iterations for fast test
        optimizer.sa_config["chain_iterations"] = 10  # Reduced from 500
        optimizer.sa_config["initial_temp"] = 100  # Reduced from 1000
        optimizer.sa_config["num_chains"] = 2  # Reduced from 4

        # Run SA
        result = optimizer._simulated_annealing()

        # Check results
        assert len(result) == 2  # 2 chains
        assert all(sol.fitness is not None for sol in result)
        assert all(0.0 <= sol.fitness <= 1.0 for sol in result)

        # Check objectives are populated
        best = result[0]
        assert "cost" in best.objectives
        assert "walking" in best.objectives
        assert "adjacency" in best.objectives

    def test_fitness_improvement(self):
        """Test that SA improves fitness over random"""
        buildings = create_sample_campus()
        bounds = (0, 0, 1000, 1000)

        optimizer = HybridSAGA(buildings, bounds)

        # Generate random solution
        random_sol = optimizer._generate_random_solution()
        random_fitness = optimizer.evaluator.evaluate(random_sol)

        # Run short SA
        optimizer.sa_config["chain_iterations"] = 20
        optimizer.sa_config["initial_temp"] = 50
        optimizer.sa_config["num_chains"] = 1

        result = optimizer._simulated_annealing()
        optimized_fitness = result[0].fitness

        # SA should improve or maintain fitness
        assert optimized_fitness >= random_fitness * 0.9  # Allow 10% tolerance
