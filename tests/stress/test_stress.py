"""
Stress tests for H-SAGA optimizer.

Tests system behavior under extreme conditions.

Run: pytest tests/stress/ -v -s

Note: These tests may take longer to run.
"""
import time

import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA


@pytest.mark.slow
class TestScalabilityStress:
    """Test performance at different scales"""

    def test_20_buildings_performance(self):
        """Stress test with 20 buildings"""
        np.random.seed(42)
        types = list(BuildingType)

        buildings = []
        for i in range(20):
            btype = np.random.choice(types)
            area = np.random.uniform(1500, 4000)
            floors = np.random.randint(2, 6)
            buildings.append(Building(f"B{i:02d}", btype, area, floors))

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        start = time.time()
        result = optimizer.optimize()
        elapsed = time.time() - start

        # Should complete in <60s
        assert elapsed < 60.0, f"Took {elapsed:.1f}s, expected <60s"
        assert result["fitness"] > 0.0

        print(f"\n✅ 20 buildings: {elapsed:.2f}s, fitness: {result['fitness']:.4f}")

    @pytest.mark.timeout(180)  # 3 minute timeout
    def test_50_buildings_performance(self):
        """Stress test with 50 buildings"""
        np.random.seed(42)
        types = list(BuildingType)

        buildings = []
        for i in range(50):
            btype = np.random.choice(types)
            area = np.random.uniform(1500, 4000)
            floors = np.random.randint(2, 6)
            buildings.append(Building(f"B{i:02d}", btype, area, floors))

        optimizer = HybridSAGA(buildings, (0, 0, 1500, 1500))

        # Increase GA config for larger problem
        optimizer.ga_config["generations"] = 100
        optimizer.ga_config["population_size"] = 100

        start = time.time()
        result = optimizer.optimize()
        elapsed = time.time() - start

        # Should complete in <120s
        assert elapsed < 120.0, f"Took {elapsed:.1f}s, expected <120s"
        assert result["fitness"] > 0.0

        print(f"\n✅ 50 buildings: {elapsed:.2f}s, fitness: {result['fitness']:.4f}")

    def test_memory_stability_long_run(self):
        """Test memory doesn't grow unbounded during long optimization"""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not available")

        process = psutil.Process()

        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(10)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))
        optimizer.ga_config["generations"] = 100  # Long run

        mem_before = process.memory_info().rss / 1024 / 1024

        optimizer.optimize()

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        # Memory increase should be reasonable (<300MB)
        assert mem_increase < 300, f"Memory increased {mem_increase:.1f}MB"

        print(f"\n✅ Memory stable: {mem_increase:.1f}MB increase")


@pytest.mark.slow
class TestConvergenceStress:
    """Test convergence under extreme conditions"""

    def test_convergence_with_many_generations(self):
        """Test convergence with 200 generations"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        optimizer.sa_config["iterations_per_temp"] = 5  # Quick SA
        optimizer.ga_config["generations"] = 200  # Many generations
        optimizer.ga_config["population_size"] = 30

        result = optimizer.optimize()

        # Check convergence is tracked
        assert len(result["convergence"]["ga_best_history"]) == 200

        # Best fitness should be monotonically non-decreasing (elitism)
        ga_best = result["convergence"]["ga_best_history"]
        for i in range(1, len(ga_best)):
            assert (
                ga_best[i] >= ga_best[i - 1] * 0.999
            ), f"Gen {i}: fitness decreased from {ga_best[i-1]:.4f} to {ga_best[i]:.4f}"

        print("\n✅ Converged over 200 generations")

    def test_convergence_with_large_population(self):
        """Test with very large population (200 individuals)"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        optimizer.sa_config["iterations_per_temp"] = 5
        optimizer.ga_config["generations"] = 20
        optimizer.ga_config["population_size"] = 200  # Huge population

        result = optimizer.optimize()

        # Should handle large population
        assert result["fitness"] > 0.0
        # With 200 pop and 20 generations, expect many evaluations
        # Actual may vary based on SA phase, so use a lower threshold
        assert result["statistics"]["evaluations"] > 1500  # Many evals

        print("\n✅ Large population (200) handled successfully")
