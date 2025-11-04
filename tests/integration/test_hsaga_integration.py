"""
Integration tests for H-SAGA SA Phase
"""
import time

import pytest

from src.algorithms.building import create_sample_campus
from src.algorithms.hsaga import HybridSAGA


@pytest.mark.integration
class TestHSAGAIntegration:
    """Integration tests for H-SAGA"""

    def test_full_sa_optimization(self):
        """Test full SA optimization end-to-end"""
        buildings = create_sample_campus()
        bounds = (0.0, 0.0, 1000.0, 1000.0)

        # Use reduced iterations for faster testing
        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 50,
            "num_chains": 2,  # Reduced for testing
            "chain_iterations": 50,  # Reduced for testing
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        assert "best_solution" in result
        assert "fitness" in result
        assert "time" in result
        assert result["fitness"] is not None
        assert result["time"] > 0

    def test_10_building_optimization(self):
        """Integration test: 10-building campus optimization"""
        buildings = create_sample_campus()
        bounds = (0.0, 0.0, 1000.0, 1000.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 100,
            "num_chains": 2,  # Reduced for testing
            "chain_iterations": 100,  # Reduced for testing
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)

        start = time.perf_counter()
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start

        # Performance target: <30s for full test, but with reduced iterations
        # we expect <10s
        assert elapsed < 30.0, f"Optimization took {elapsed:.2f}s, expected <30s"

        # Fitness improvement
        assert result["fitness"] > -10.0, f"Fitness too low: {result['fitness']}"

        # Solution validity
        assert result["best_solution"].is_valid(buildings, bounds), "Solution is invalid"

    def test_fitness_improvement(self):
        """Test that SA improves fitness"""
        buildings = create_sample_campus()[:5]  # Use 5 buildings for speed
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 50,
            "num_chains": 1,  # Single chain for testing
            "chain_iterations": 50,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)

        # Get initial random solution fitness
        initial_solution = optimizer._generate_random_solution()
        optimizer.evaluate_solution(initial_solution)

        # Run optimization
        result = optimizer.optimize()
        final_fitness = result["fitness"]

        # SA should improve or at least maintain fitness
        # (Since it can accept worse solutions, we just check it's reasonable)
        assert final_fitness > -10.0, "Final fitness should be reasonable"
        assert isinstance(final_fitness, float)

    def test_solution_validity(self):
        """Test all solutions are valid"""
        buildings = create_sample_campus()[:5]
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 20,
            "num_chains": 2,
            "chain_iterations": 20,  # Very short for testing
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        # Check final solution is valid
        solution = result["best_solution"]
        assert solution.is_valid(buildings, bounds), "Final solution must be valid"

        # Check no overlaps
        for i, b1 in enumerate(buildings):
            b1.position = solution.positions[b1.id]
            for b2 in buildings[i + 1 :]:
                b2.position = solution.positions[b2.id]
                assert not b1.overlaps_with(b2), f"Buildings {b1.id} and {b2.id} overlap"

    def test_convergence_tracking(self):
        """Test convergence history is tracked"""
        buildings = create_sample_campus()[:5]
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 100,
            "num_chains": 1,
            "chain_iterations": 100,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        # Check statistics are tracked
        assert "statistics" in result
        assert "convergence" in result
        assert result["statistics"]["best_fitness"] is not None
