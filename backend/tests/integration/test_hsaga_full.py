"""
Integration tests for complete H-SAGA optimization pipeline.

Tests the full two-stage optimization process.

Created: 2025-11-07
"""
import time

import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA


@pytest.fixture
def test_campus():
    """Create test campus with 10 buildings"""
    types = [
        BuildingType.RESIDENTIAL,
        BuildingType.RESIDENTIAL,
        BuildingType.EDUCATIONAL,
        BuildingType.EDUCATIONAL,
        BuildingType.ADMINISTRATIVE,
        BuildingType.HEALTH,
        BuildingType.SOCIAL,
        BuildingType.COMMERCIAL,
        BuildingType.LIBRARY,
        BuildingType.DINING,
    ]

    buildings = []
    for i, btype in enumerate(types):
        area = np.random.uniform(1500, 3500)
        floors = np.random.randint(2, 5)
        buildings.append(Building(f"B{i:02d}", btype, area, floors))

    return buildings


class TestHSAGAFullPipeline:
    """Integration tests for complete H-SAGA"""

    def test_complete_pipeline_executes(self, test_campus):
        """Test that complete pipeline executes without errors"""
        optimizer = HybridSAGA(test_campus, (0, 0, 1000, 1000))

        # Reduce for fast test
        optimizer.sa_config["chain_iterations"] = 5
        optimizer.sa_config["num_chains"] = 2
        optimizer.ga_config["generations"] = 10
        optimizer.ga_config["population_size"] = 10

        result = optimizer.optimize()

        # Check result structure
        assert "best_solution" in result
        assert "fitness" in result
        assert "objectives" in result
        assert "statistics" in result
        assert "convergence" in result

    def test_result_validity(self, test_campus):
        """Test that result contains valid data"""
        optimizer = HybridSAGA(test_campus, (0, 0, 1000, 1000))

        optimizer.sa_config["chain_iterations"] = 5
        optimizer.sa_config["num_chains"] = 2
        optimizer.ga_config["generations"] = 10
        optimizer.ga_config["population_size"] = 10

        result = optimizer.optimize()

        # Check fitness is valid
        assert 0.0 <= result["fitness"] <= 1.0
        assert not np.isnan(result["fitness"])

        # Check objectives
        for obj_name, score in result["objectives"].items():
            assert 0.0 <= score <= 1.0, f"{obj_name} = {score}"

        # Check solution
        solution = result["best_solution"]
        assert len(solution.positions) == len(test_campus)

    def test_10_buildings_under_30s(self, test_campus):
        """Test 10 building optimization completes under 30 seconds"""
        optimizer = HybridSAGA(test_campus, (0, 0, 1000, 1000))

        start = time.time()
        result = optimizer.optimize()
        elapsed = time.time() - start

        # Should complete under 30s
        assert elapsed < 30.0, f"Took {elapsed:.1f}s, expected <30s"

        # Should find valid solution
        assert result["fitness"] > 0.0

        print(f"\n✅ 10 buildings optimized in {elapsed:.2f}s")
        print(f"   Fitness: {result['fitness']:.4f}")

    def test_ga_improves_sa(self, test_campus):
        """Test that GA phase improves or maintains SA results"""
        optimizer = HybridSAGA(test_campus, (0, 0, 1000, 1000))

        optimizer.sa_config["chain_iterations"] = 10
        optimizer.sa_config["num_chains"] = 2
        optimizer.ga_config["generations"] = 20
        optimizer.ga_config["population_size"] = 20

        result = optimizer.optimize()

        # Get convergence data
        ga_best = result["convergence"]["ga_best_history"]

        # Final should be >= initial (or very close)
        initial = ga_best[0]
        final = ga_best[-1]

        assert (
            final >= initial * 0.95
        ), f"GA final ({final:.4f}) should be >= SA initial ({initial:.4f})"

    def test_convergence_tracking(self, test_campus):
        """Test that convergence is tracked correctly"""
        optimizer = HybridSAGA(test_campus, (0, 0, 1000, 1000))

        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Check convergence data
        assert len(result["convergence"]["ga_best_history"]) == 15
        assert len(result["convergence"]["ga_avg_history"]) == 15

        # Best should be monotonically non-decreasing (due to elitism)
        ga_best = result["convergence"]["ga_best_history"]
        for i in range(1, len(ga_best)):
            assert (
                ga_best[i] >= ga_best[i - 1] * 0.999
            ), f"Gen {i}: {ga_best[i]:.4f} < {ga_best[i-1]:.4f}"
