"""
Integration Tests for Adaptive Cooling with H-SAGA
===================================================

Tests adaptive cooling integration with AdaptiveHSAGA optimizer.

Created: 2026-01-03
"""

import numpy as np
import pytest

from src.algorithms import Building, BuildingType
from src.algorithms.hsaga_adaptive import AdaptiveHSAGA


class TestAdaptiveCoolingIntegration:
    """Test adaptive cooling schedules integrated with H-SAGA."""

    @pytest.fixture
    def simple_buildings(self):
        """Create simple building set for testing."""
        return [
            Building("Library", BuildingType.EDUCATIONAL, 2000, 3),
            Building("Dorm", BuildingType.RESIDENTIAL, 3000, 5),
            Building("Cafe", BuildingType.COMMERCIAL, 1500, 2),
        ]

    @pytest.fixture
    def bounds(self):
        """Simple bounds for testing."""
        return (0, 0, 500, 500)

    def test_adaptive_specific_heat_cooling(self, simple_buildings, bounds):
        """Test H-SAGA with adaptive specific heat cooling."""
        np.random.seed(42)

        # Configure with adaptive cooling
        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "num_chains": 1,
            "chain_iterations": 50,
            "cooling_schedule": "adaptive_specific_heat",
            "adaptive_alpha": 0.95,
            "markov_base_length": 5,
            "use_adaptive_markov": True,
        }

        ga_config = {
            "population_size": 10,
            "generations": 5,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 2,
            "tournament_size": 3,
        }

        optimizer = AdaptiveHSAGA(
            buildings=simple_buildings,
            bounds=bounds,
            sa_config=sa_config,
            ga_config=ga_config,
            enable_adaptive=True,
        )

        result = optimizer.optimize()

        # Verify results
        assert result is not None
        assert "best_solution" in result
        assert "fitness" in result
        assert result["fitness"] > 0

        # Verify solution is valid
        best_solution = result["best_solution"]
        assert len(best_solution.positions) == len(simple_buildings)
        assert best_solution.fitness is not None

    def test_hybrid_cooling_schedule(self, simple_buildings, bounds):
        """Test H-SAGA with hybrid cooling schedule."""
        np.random.seed(42)

        # Configure with hybrid cooling
        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "num_chains": 1,
            "chain_iterations": 50,
            "cooling_schedule": "hybrid",
            "markov_base_length": 5,
            "use_adaptive_markov": False,  # Disable for hybrid
        }

        ga_config = {
            "population_size": 10,
            "generations": 5,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 2,
            "tournament_size": 3,
        }

        optimizer = AdaptiveHSAGA(
            buildings=simple_buildings,
            bounds=bounds,
            sa_config=sa_config,
            ga_config=ga_config,
            enable_adaptive=True,
        )

        result = optimizer.optimize()

        # Verify results
        assert result is not None
        assert result["fitness"] > 0
        assert len(result["best_solution"].positions) == len(simple_buildings)

    def test_exponential_cooling_baseline(self, simple_buildings, bounds):
        """Test H-SAGA with standard exponential cooling (baseline)."""
        np.random.seed(42)

        # Configure with standard exponential cooling
        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "num_chains": 1,
            "chain_iterations": 50,
            "cooling_schedule": "exponential",  # Default
            "markov_base_length": 5,
            "use_adaptive_markov": False,
        }

        ga_config = {
            "population_size": 10,
            "generations": 5,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 2,
            "tournament_size": 3,
        }

        optimizer = AdaptiveHSAGA(
            buildings=simple_buildings,
            bounds=bounds,
            sa_config=sa_config,
            ga_config=ga_config,
            enable_adaptive=True,
        )

        result = optimizer.optimize()

        # Verify results
        assert result is not None
        assert result["fitness"] > 0

    def test_adaptive_markov_chain_length(self, simple_buildings, bounds):
        """Test adaptive Markov chain length feature."""
        np.random.seed(42)

        # Configure with adaptive Markov chain
        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "num_chains": 1,
            "chain_iterations": 50,
            "cooling_schedule": "adaptive_specific_heat",
            "markov_base_length": 10,
            "use_adaptive_markov": True,  # Enable adaptive
        }

        ga_config = {
            "population_size": 10,
            "generations": 5,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 2,
            "tournament_size": 3,
        }

        optimizer = AdaptiveHSAGA(
            buildings=simple_buildings,
            bounds=bounds,
            sa_config=sa_config,
            ga_config=ga_config,
            enable_adaptive=True,
        )

        result = optimizer.optimize()

        # Should complete successfully with adaptive Markov chains
        assert result is not None
        assert result["fitness"] > 0

    def test_cooling_schedules_comparison(self, simple_buildings, bounds):
        """Compare different cooling schedules."""
        np.random.seed(42)

        schedules = ["exponential", "adaptive_specific_heat", "hybrid"]
        results = {}

        for schedule in schedules:
            sa_config = {
                "initial_temp": 100.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "num_chains": 1,
                "chain_iterations": 30,
                "cooling_schedule": schedule,
                "adaptive_alpha": 0.95,
                "markov_base_length": 5,
                "use_adaptive_markov": (schedule == "adaptive_specific_heat"),
            }

            ga_config = {
                "population_size": 8,
                "generations": 3,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            }

            optimizer = AdaptiveHSAGA(
                buildings=simple_buildings,
                bounds=bounds,
                sa_config=sa_config,
                ga_config=ga_config,
                enable_adaptive=False,  # Disable for clean comparison
            )

            result = optimizer.optimize()
            results[schedule] = result["fitness"]

        # All schedules should produce valid results
        for schedule, fitness in results.items():
            assert fitness > 0, f"{schedule} should produce positive fitness"

        # Results should be comparable (not testing superiority, just functionality)
        print("\nCooling schedule comparison:")
        for schedule, fitness in results.items():
            print(f"  {schedule}: {fitness:.4f}")


class TestAdaptiveCoolingWithMultipleChains:
    """Test adaptive cooling with multiple SA chains."""

    @pytest.fixture
    def buildings(self):
        """Create building set."""
        return [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
            Building("B3", BuildingType.COMMERCIAL, 1000, 2),
            Building("B4", BuildingType.SOCIAL, 1500, 2),
        ]

    @pytest.fixture
    def bounds(self):
        return (0, 0, 600, 600)

    def test_multiple_chains_adaptive_cooling(self, buildings, bounds):
        """Test adaptive cooling with multiple SA chains."""
        np.random.seed(42)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "num_chains": 2,  # Multiple chains
            "chain_iterations": 30,
            "cooling_schedule": "adaptive_specific_heat",
            "adaptive_alpha": 0.95,
            "markov_base_length": 5,
            "use_adaptive_markov": True,
        }

        ga_config = {
            "population_size": 10,
            "generations": 5,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 2,
            "tournament_size": 3,
        }

        optimizer = AdaptiveHSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config,
            ga_config=ga_config,
            enable_adaptive=True,
        )

        result = optimizer.optimize()

        # Should complete successfully
        assert result is not None
        assert result["fitness"] > 0
        assert len(result["best_solution"].positions) == len(buildings)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
