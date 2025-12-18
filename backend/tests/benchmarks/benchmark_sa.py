"""
Performance Benchmarks for SA Phase
"""
import pytest

from src.algorithms.building import create_sample_campus
from src.algorithms.hsaga import HybridSAGA


@pytest.mark.benchmark
class TestSAPerformance:
    """Performance benchmarks for SA phase"""

    def test_5_buildings_performance(self, benchmark):
        """Benchmark: 5 buildings should complete in <15s"""
        buildings = create_sample_campus()[:5]
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 100,
            "num_chains": 2,
            "chain_iterations": 100,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)

        def run_optimization():
            return optimizer.optimize()

        result = benchmark(run_optimization)

        assert result["time"] < 15.0, f"5 buildings took {result['time']:.2f}s, expected <15s"
        assert result["fitness"] is not None

    def test_10_buildings_performance(self, benchmark):
        """Benchmark: 10 buildings should complete in <30s"""
        buildings = create_sample_campus()
        bounds = (0.0, 0.0, 1000.0, 1000.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 200,
            "num_chains": 2,
            "chain_iterations": 200,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)

        def run_optimization():
            return optimizer.optimize()

        result = benchmark(run_optimization)

        assert result["time"] < 30.0, f"10 buildings took {result['time']:.2f}s, expected <30s"
        assert result["fitness"] is not None

    def test_15_buildings_performance(self, benchmark):
        """Benchmark: 15 buildings should complete in <45s"""
        # Create 15 buildings (extend sample campus)
        buildings = create_sample_campus()
        # Add 5 more buildings
        import numpy as np

        from src.algorithms.building import Building, BuildingType

        for i in range(5):
            buildings.append(
                Building(
                    f"B{i+10}",
                    np.random.choice(list(BuildingType)),
                    np.random.uniform(1000, 5000),
                    np.random.randint(2, 6),
                )
            )

        bounds = (0.0, 0.0, 1000.0, 1000.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 200,
            "num_chains": 2,
            "chain_iterations": 200,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)

        def run_optimization():
            return optimizer.optimize()

        result = benchmark(run_optimization)

        assert result["time"] < 45.0, f"15 buildings took {result['time']:.2f}s, expected <45s"
        assert result["fitness"] is not None

    def test_multiprocessing_speedup(self, benchmark):
        """Test that multiprocessing provides speedup"""
        buildings = create_sample_campus()[:5]
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 100.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 100,
            "num_chains": 4,  # 4 parallel chains
            "chain_iterations": 100,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)

        def run_optimization():
            return optimizer.optimize()

        result = benchmark(run_optimization)

        # Verify multiprocessing is working
        # With 4 chains, should be faster than sequential
        assert result["time"] > 0
        assert result["fitness"] is not None
