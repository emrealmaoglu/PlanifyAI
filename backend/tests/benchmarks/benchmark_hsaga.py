"""
H-SAGA Performance Benchmarks
==============================

Measures execution time, memory usage, and identifies bottlenecks.

Created: 2026-01-02 (Week 4 Day 3)
"""

import time

import pytest
from shapely.geometry import Polygon

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA


@pytest.fixture
def small_problem():
    """5 buildings - small problem."""
    buildings = [Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 4) for i in range(5)]
    bounds = (0, 0, 150, 150)
    return buildings, bounds


@pytest.fixture
def medium_problem():
    """10 buildings - medium problem."""
    buildings = [Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 4) for i in range(10)]
    bounds = (0, 0, 250, 250)
    return buildings, bounds


@pytest.fixture
def large_problem():
    """15 buildings - large problem."""
    buildings = [Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 4) for i in range(15)]
    bounds = (0, 0, 400, 400)
    return buildings, bounds


@pytest.fixture
def sa_config_fast():
    """Fast SA config for benchmarking."""
    return {
        "initial_temp": 100.0,
        "final_temp": 0.1,
        "cooling_rate": 0.95,
        "num_chains": 2,
        "chain_iterations": 50,
    }


@pytest.fixture
def ga_config_fast():
    """Fast GA config for benchmarking."""
    return {
        "population_size": 20,
        "generations": 20,
        "crossover_rate": 0.8,
        "mutation_rate": 0.15,
        "elite_size": 3,
        "tournament_size": 3,
    }


class TestHSAGAPerformance:
    """Performance benchmarks for H-SAGA optimizer."""

    def test_small_problem_baseline(self, small_problem, sa_config_fast, ga_config_fast):
        """Baseline: 5 buildings, 20 generations."""
        buildings, bounds = small_problem

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_fast,
            ga_config=ga_config_fast,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        assert result["fitness"] > 0
        print(f"\n5 buildings, 20 gen: {elapsed:.3f}s")
        print(f"Fitness: {result['fitness']:.4f}")

    def test_medium_problem_baseline(self, medium_problem, sa_config_fast, ga_config_fast):
        """Baseline: 10 buildings, 20 generations."""
        buildings, bounds = medium_problem

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_fast,
            ga_config=ga_config_fast,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        assert result["fitness"] > 0
        print(f"\n10 buildings, 20 gen: {elapsed:.3f}s")
        print(f"Fitness: {result['fitness']:.4f}")

    def test_large_problem_baseline(self, large_problem, sa_config_fast):
        """Baseline: 15 buildings, 15 generations."""
        buildings, bounds = large_problem

        ga_config = {
            "population_size": 20,
            "generations": 15,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 3,
            "tournament_size": 3,
        }

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_fast,
            ga_config=ga_config,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        assert result["fitness"] > 0
        print(f"\n15 buildings, 15 gen: {elapsed:.3f}s")
        print(f"Fitness: {result['fitness']:.4f}")

    def test_phase_timing_analysis(self, small_problem, sa_config_fast, ga_config_fast):
        """Analyze SA vs GA phase timing using result statistics."""
        buildings, bounds = small_problem

        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_fast,
            ga_config=ga_config_fast,
        )

        result = optimizer.optimize()
        stats = result["statistics"]

        total_time = stats["runtime"]
        sa_time = stats["sa_time"]
        ga_time = stats["ga_time"]

        sa_percent = (sa_time / total_time) * 100
        ga_percent = (ga_time / total_time) * 100

        print(f"\nTotal runtime: {total_time:.3f}s")
        print(f"SA phase: {sa_time:.3f}s ({sa_percent:.1f}%)")
        print(f"GA phase: {ga_time:.3f}s ({ga_percent:.1f}%)")
        print(f"SA chains: {stats['sa_chains']}")
        print(f"GA generations: {stats['ga_generations']}")
        print(f"Total evaluations: {stats['evaluations']}")

    def test_large_population_parallel(self, sa_config_fast):
        """Test parallel evaluation with large population (100+)."""
        # Use larger area for large population
        buildings = [Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 4) for i in range(10)]
        bounds = (0, 0, 400, 400)  # Larger area for population=100

        ga_config = {
            "population_size": 100,  # Large population for parallel
            "generations": 10,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 10,
            "tournament_size": 3,
        }

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_fast,
            ga_config=ga_config,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        stats = result["statistics"]
        print(f"\n10 buildings, pop=100, 10 gen: {elapsed:.3f}s")
        print(f"Fitness: {result['fitness']:.4f}")
        print(f"Total evaluations: {stats['evaluations']}")

        assert result["fitness"] > 0

    def test_scalability_analysis(self, sa_config_fast):
        """Analyze how execution time scales with problem size."""
        results = []

        ga_config = {
            "population_size": 15,
            "generations": 10,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 2,
            "tournament_size": 3,
        }

        for n_buildings in [3, 5, 10]:
            buildings = [
                Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 4) for i in range(n_buildings)
            ]
            bounds = (0, 0, n_buildings * 30, n_buildings * 30)

            start_time = time.perf_counter()
            optimizer = HybridSAGA(
                buildings=buildings,
                bounds=bounds,
                sa_config=sa_config_fast,
                ga_config=ga_config,
            )
            optimizer.optimize()
            elapsed = time.perf_counter() - start_time

            results.append((n_buildings, elapsed))

        print("\nScalability Analysis:")
        print("Buildings | Time (s) | Time/Building (ms)")
        print("-" * 45)
        for n, t in results:
            print(f"{n:9d} | {t:8.3f} | {t/n*1000:18.2f}")

        # Check that we're not exponential
        time_3 = results[0][1]
        time_10 = results[2][1]
        ratio = time_10 / time_3

        # 3.3x buildings should not take more than 15x time
        assert ratio < 15, f"Scaling worse than quadratic: {ratio:.1f}x"


class TestRobustnessPerformance:
    """Performance benchmarks for robustness analysis."""

    def test_robustness_analysis_timing(self, small_problem):
        """Measure robustness analysis overhead."""
        from backend.core.quality.robustness_analyzer import RobustnessAnalyzer
        from src.algorithms.solution import Solution

        buildings, bounds = small_problem

        # Create a mock solution
        solution = Solution(buildings)
        for i, building in enumerate(buildings):
            solution.positions[building.id] = (i * 30 + 20, 20)
            solution.rotations[building.id] = 0

        def simple_fitness(sol):
            return 0.75

        # Test with different sample sizes
        for n_samples in [10, 50, 100]:
            analyzer = RobustnessAnalyzer(
                evaluate_fitness=simple_fitness,
                n_samples=n_samples,
                random_seed=42,
            )

            start_time = time.perf_counter()
            analyzer.analyze_solution(solution, perturbation_strength=0.05)
            elapsed = time.perf_counter() - start_time

            print(f"\nRobustness ({n_samples} samples): {elapsed:.3f}s")
            print(f"Time per sample: {elapsed/n_samples*1000:.2f}ms")


class TestCompliancePerformance:
    """Performance benchmarks for compliance checking."""

    def test_compliance_check_timing(self, small_problem):
        """Measure compliance checking overhead."""
        from backend.core.regulatory.compliance_checker import ComplianceChecker

        buildings, bounds = small_problem

        site_params = {
            "area": bounds.area,
            "max_far": 1.5,
            "max_height": 21.0,
            "required_green_ratio": 0.30,
            "provided_parking_spaces": 50,
            "provided_green_area": bounds.area * 0.35,
            "boundary": bounds,
        }

        building_polygons = {
            f"B{i}": Polygon([(i * 30, 0), (i * 30 + 20, 0), (i * 30 + 20, 20), (i * 30, 20)])
            for i in range(len(buildings))
        }

        checker = ComplianceChecker(language="en")

        start_time = time.perf_counter()
        checker.check_all(buildings, site_params, building_polygons)
        checker.generate_report()
        elapsed = time.perf_counter() - start_time

        print(f"\nCompliance check (5 buildings): {elapsed*1000:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
