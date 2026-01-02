"""
Adaptive H-SAGA Realistic Benchmarks
=====================================

Tests Adaptive H-SAGA performance with production-scale problems.

Demonstrates that adaptive operator selection scales to large problems:
- 50-150 buildings
- Different selection strategies
- Performance comparison with original H-SAGA

Created: 2026-01-02 (Week 4 Day 3)
"""

import time

import numpy as np
import pytest

from src.algorithms import AdaptiveHSAGA
from src.algorithms.adaptive import SelectionStrategy

from .benchmark_realistic import (
    generate_flat_terrain,
    generate_mixed_campus,
    generate_sloped_terrain,
)

# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture
def sa_config_realistic():
    """SA config for realistic large-scale problems."""
    return {
        "initial_temp": 1000.0,
        "final_temp": 0.1,
        "cooling_rate": 0.95,
        "num_chains": 4,
        "chain_iterations": 100,
    }


@pytest.fixture
def ga_config_realistic():
    """GA config for realistic large-scale problems."""
    return {
        "population_size": 50,
        "generations": 30,
        "crossover_rate": 0.8,
        "mutation_rate": 0.15,
        "elite_size": 5,
        "tournament_size": 3,
    }


# =============================================================================
# BENCHMARK TESTS
# =============================================================================


class TestAdaptiveRealisticScale:
    """Test Adaptive H-SAGA with realistic large-scale problems."""

    @pytest.mark.slow
    def test_50_buildings_adaptive_pursuit(self, sa_config_realistic, ga_config_realistic):
        """50 buildings with Adaptive Pursuit strategy."""
        terrain = generate_flat_terrain(width=600, height=600)
        buildings, bounds = generate_mixed_campus(n_buildings=50, terrain=terrain)

        start_time = time.perf_counter()
        optimizer = AdaptiveHSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_realistic,
            ga_config=ga_config_realistic,
            selection_strategy=SelectionStrategy.ADAPTIVE_PURSUIT,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        stats = result["statistics"]

        print("\n" + "=" * 70)
        print("ADAPTIVE H-SAGA - 50 Buildings (Adaptive Pursuit)")
        print("=" * 70)
        print(f"Runtime: {elapsed:.2f}s")
        print(f"Fitness: {result['fitness']:.4f}")
        print(f"Evaluations: {stats['evaluations']}")
        print(f"SA time: {stats['sa_time']:.2f}s ({stats['sa_time']/elapsed*100:.1f}%)")
        print(f"GA time: {stats['ga_time']:.2f}s ({stats['ga_time']/elapsed*100:.1f}%)")

        # Print operator statistics
        print("\nTop Operators by Success Rate:")
        for op_type in ["perturbation", "mutation", "crossover"]:
            op_stats = result["operator_stats"][op_type]
            # Sort by success rate
            sorted_ops = sorted(
                [(name, data) for name, data in op_stats.items() if data["uses"] > 0],
                key=lambda x: x[1]["success_rate"],
                reverse=True,
            )
            if sorted_ops:
                print(f"\n  {op_type.upper()}:")
                for name, data in sorted_ops[:3]:  # Top 3
                    print(
                        f"    {name:>12}: {data['uses']:>4} uses, "
                        f"{data['success_rate']:>5.1%} success, "
                        f"Δ={data['avg_improvement']:>+.4f}"
                    )

        assert result["fitness"] > 0
        assert elapsed < 300  # Should complete in < 5 minutes

    @pytest.mark.slow
    def test_100_buildings_ucb(self, sa_config_realistic, ga_config_realistic):
        """100 buildings with UCB strategy on sloped terrain."""
        terrain = generate_sloped_terrain(width=800, height=800, max_slope=10.0)
        buildings, bounds = generate_mixed_campus(n_buildings=100, terrain=terrain)

        start_time = time.perf_counter()
        optimizer = AdaptiveHSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_realistic,
            ga_config=ga_config_realistic,
            selection_strategy=SelectionStrategy.UCB,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        stats = result["statistics"]

        print("\n" + "=" * 70)
        print("ADAPTIVE H-SAGA - 100 Buildings (UCB Strategy)")
        print("=" * 70)
        print(f"Runtime: {elapsed:.2f}s")
        print(f"Fitness: {result['fitness']:.4f}")
        print(f"Evaluations: {stats['evaluations']}")

        assert result["fitness"] > 0
        assert elapsed < 600  # < 10 minutes


class TestAdaptiveStrategyComparison:
    """Compare different adaptive strategies at scale."""

    def test_strategy_comparison_medium_scale(self, sa_config_realistic):
        """Compare all 5 strategies on medium-scale problem (30 buildings)."""
        # Medium scale for faster comparison
        # Calculate terrain size: 30 buildings * avg 3000m² * 20x spacing = 1.8M m²
        terrain_size = int(np.sqrt(30 * 3000 * 20))  # ~1342m
        terrain = generate_flat_terrain(width=terrain_size, height=terrain_size)
        buildings, bounds = generate_mixed_campus(n_buildings=30, terrain=terrain, seed=42)

        # Faster GA config
        ga_config = {
            "population_size": 40,
            "generations": 25,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 4,
            "tournament_size": 3,
        }

        strategies = [
            SelectionStrategy.UNIFORM,
            SelectionStrategy.GREEDY,
            SelectionStrategy.ADAPTIVE_PURSUIT,
            SelectionStrategy.UCB,
            SelectionStrategy.SOFTMAX,
        ]

        results = {}

        for strategy in strategies:
            np.random.seed(42)  # Same seed for fair comparison

            start_time = time.perf_counter()
            optimizer = AdaptiveHSAGA(
                buildings=buildings,
                bounds=bounds,
                sa_config=sa_config_realistic,
                ga_config=ga_config,
                selection_strategy=strategy,
            )
            result = optimizer.optimize()
            elapsed = time.perf_counter() - start_time

            results[strategy.value] = {
                "time": elapsed,
                "fitness": result["fitness"],
                "evaluations": result["statistics"]["evaluations"],
            }

        print("\n" + "=" * 70)
        print("ADAPTIVE STRATEGY COMPARISON (30 buildings)")
        print("=" * 70)
        print(f"{'Strategy':<20} | {'Time (s)':<10} | {'Fitness':<10} | Evals")
        print("-" * 70)

        for strategy_name, data in results.items():
            time_val = data["time"]
            fit_val = data["fitness"]
            evals = data["evaluations"]
            print(f"{strategy_name:<20} | {time_val:>8.2f}s | {fit_val:>8.4f} | {evals}")

        # Find best strategy by fitness
        best_strategy = max(results.items(), key=lambda x: x[1]["fitness"])
        print(f"\nBest strategy: {best_strategy[0]} (fitness={best_strategy[1]['fitness']:.4f})")

        # All should produce valid solutions
        for data in results.values():
            assert data["fitness"] > 0


class TestAdaptiveVsOriginalScale:
    """Compare Adaptive vs Original H-SAGA at different scales."""

    def test_comparison_scaling(self, sa_config_realistic):
        """Test both algorithms at 20, 40 buildings to show scaling."""
        from src.algorithms import HybridSAGA

        # Faster configs for comparison
        ga_config = {
            "population_size": 30,
            "generations": 20,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 3,
            "tournament_size": 3,
        }

        scales = [20, 40]
        results_original = {}
        results_adaptive = {}

        for n_buildings in scales:
            # Generate problem
            terrain_size = int(np.sqrt(n_buildings * 5000 * 20))  # 20x footprint
            terrain = generate_flat_terrain(width=terrain_size, height=terrain_size)
            buildings, bounds = generate_mixed_campus(
                n_buildings=n_buildings, terrain=terrain, seed=42
            )

            # Original H-SAGA
            np.random.seed(42)
            start_time = time.perf_counter()
            optimizer_original = HybridSAGA(
                buildings=buildings,
                bounds=bounds,
                sa_config=sa_config_realistic,
                ga_config=ga_config,
            )
            result_original = optimizer_original.optimize()
            time_original = time.perf_counter() - start_time

            results_original[n_buildings] = {
                "time": time_original,
                "fitness": result_original["fitness"],
            }

            # Adaptive H-SAGA
            np.random.seed(42)
            start_time = time.perf_counter()
            optimizer_adaptive = AdaptiveHSAGA(
                buildings=buildings,
                bounds=bounds,
                sa_config=sa_config_realistic,
                ga_config=ga_config,
                selection_strategy=SelectionStrategy.ADAPTIVE_PURSUIT,
            )
            result_adaptive = optimizer_adaptive.optimize()
            time_adaptive = time.perf_counter() - start_time

            results_adaptive[n_buildings] = {
                "time": time_adaptive,
                "fitness": result_adaptive["fitness"],
            }

        print("\n" + "=" * 80)
        print("ORIGINAL vs ADAPTIVE H-SAGA - SCALING COMPARISON")
        print("=" * 80)
        print(
            f"{'Buildings':<12} | {'Original Time':<14} | {'Adaptive Time':<14} | "
            f"{'Speedup':<10} | Δ Fitness"
        )
        print("-" * 80)

        for n in scales:
            orig = results_original[n]
            adap = results_adaptive[n]
            speedup = orig["time"] / adap["time"]
            fitness_delta = ((adap["fitness"] - orig["fitness"]) / orig["fitness"]) * 100

            print(
                f"{n:<12} | {orig['time']:>12.2f}s | {adap['time']:>12.2f}s | "
                f"{speedup:>8.2f}x | {fitness_delta:>+6.1f}%"
            )

        print("\nNote: Speedup shows Adaptive/Original ratio")


class TestAdaptiveOperatorInsights:
    """Extract insights about which operators work best."""

    def test_operator_effectiveness_medium_problem(self, sa_config_realistic, ga_config_realistic):
        """Run on medium problem and analyze operator effectiveness."""
        # Calculate terrain size: 25 buildings * avg 3000m² * 20x spacing
        terrain_size = int(np.sqrt(25 * 3000 * 20))  # ~1225m
        terrain = generate_flat_terrain(width=terrain_size, height=terrain_size)
        buildings, bounds = generate_mixed_campus(n_buildings=25, terrain=terrain)

        optimizer = AdaptiveHSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_realistic,
            ga_config=ga_config_realistic,
            selection_strategy=SelectionStrategy.ADAPTIVE_PURSUIT,
        )

        result = optimizer.optimize()

        print("\n" + "=" * 70)
        print("OPERATOR EFFECTIVENESS ANALYSIS (25 buildings)")
        print("=" * 70)

        # Analyze each operator type
        for op_type in ["perturbation", "mutation", "crossover", "selection"]:
            op_stats = result["operator_stats"][op_type]

            if not op_stats:
                continue

            print(f"\n{op_type.upper()} OPERATORS:")
            print(f"  {'Operator':<15} | {'Uses':<6} | {'Success':<8} | {'Avg Δ':<10}")
            print("  " + "-" * 50)

            # Sort by average improvement
            sorted_ops = sorted(
                [(name, data) for name, data in op_stats.items()],
                key=lambda x: x[1]["avg_improvement"],
                reverse=True,
            )

            for name, data in sorted_ops:
                if data["uses"] > 0:
                    print(
                        f"  {name:<15} | {data['uses']:<6} | "
                        f"{data['success_rate']:>6.1%} | {data['avg_improvement']:>+9.5f}"
                    )

        assert result["fitness"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
