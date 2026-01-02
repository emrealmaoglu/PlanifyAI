"""
Adaptive H-SAGA vs Original H-SAGA Comparison
==============================================

Performance comparison between adaptive and non-adaptive H-SAGA.

Metrics:
- Convergence speed
- Final fitness quality
- Operator selection statistics
- Runtime overhead

Created: 2026-01-02 (Week 4 Day 3)
"""

import time

import numpy as np
import pytest

from src.algorithms import AdaptiveHSAGA, Building, BuildingType, HybridSAGA
from src.algorithms.adaptive import SelectionStrategy


@pytest.fixture
def small_campus():
    """5 buildings for quick comparison."""
    return [
        Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
        Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        Building("B3", BuildingType.ADMINISTRATIVE, 1200, 2),
        Building("B4", BuildingType.SOCIAL, 1800, 2),
        Building("B5", BuildingType.COMMERCIAL, 1000, 1),
    ]


@pytest.fixture
def medium_campus():
    """10 buildings for realistic comparison."""
    buildings = []
    types = [
        BuildingType.RESIDENTIAL,
        BuildingType.EDUCATIONAL,
        BuildingType.ADMINISTRATIVE,
        BuildingType.SOCIAL,
        BuildingType.COMMERCIAL,
    ]

    for i in range(10):
        btype = types[i % len(types)]
        area = np.random.randint(1000, 3000)
        floors = np.random.randint(1, 5)
        buildings.append(Building(f"B{i+1}", btype, area, floors))

    return buildings


@pytest.fixture
def bounds_small():
    """Bounds for small campus."""
    return (0, 0, 300, 300)


@pytest.fixture
def bounds_medium():
    """Bounds for medium campus."""
    return (0, 0, 500, 500)


@pytest.fixture
def comparison_sa_config():
    """SA config for fair comparison."""
    return {
        "initial_temp": 100.0,
        "final_temp": 0.1,
        "cooling_rate": 0.95,
        "num_chains": 2,
        "chain_iterations": 100,
    }


@pytest.fixture
def comparison_ga_config():
    """GA config for fair comparison."""
    return {
        "population_size": 30,
        "generations": 30,
        "crossover_rate": 0.8,
        "mutation_rate": 0.15,
        "elite_size": 5,
        "tournament_size": 3,
    }


class TestAdaptiveVsOriginal:
    """Compare adaptive vs original H-SAGA."""

    def test_small_problem_comparison(
        self, small_campus, bounds_small, comparison_sa_config, comparison_ga_config
    ):
        """Compare on small problem (5 buildings)."""
        print("\n" + "=" * 70)
        print("📊 SMALL PROBLEM COMPARISON (5 buildings)")
        print("=" * 70)

        # Original H-SAGA
        print("\n🔹 Running Original H-SAGA...")
        np.random.seed(42)
        start = time.perf_counter()

        optimizer_original = HybridSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=comparison_sa_config,
            ga_config=comparison_ga_config,
        )
        result_original = optimizer_original.optimize()

        time_original = time.perf_counter() - start

        print(f"✅ Original: {result_original['fitness']:.4f} in {time_original:.2f}s")

        # Adaptive H-SAGA
        print("\n🔸 Running Adaptive H-SAGA...")
        np.random.seed(42)
        start = time.perf_counter()

        optimizer_adaptive = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=comparison_sa_config,
            ga_config=comparison_ga_config,
            selection_strategy=SelectionStrategy.ADAPTIVE_PURSUIT,
            enable_adaptive=True,
        )
        result_adaptive = optimizer_adaptive.optimize()

        time_adaptive = time.perf_counter() - start

        print(f"✅ Adaptive: {result_adaptive['fitness']:.4f} in {time_adaptive:.2f}s")

        # Comparison
        print("\n" + "=" * 70)
        print("📈 COMPARISON RESULTS")
        print("=" * 70)
        print(f"Original Fitness:  {result_original['fitness']:.4f}")
        print(f"Adaptive Fitness:  {result_adaptive['fitness']:.4f}")
        print(
            f"Improvement:       {result_adaptive['fitness'] - result_original['fitness']:+.4f} "
            f"({((result_adaptive['fitness'] / result_original['fitness']) - 1) * 100:+.1f}%)"
        )
        print()
        print(f"Original Time:     {time_original:.2f}s")
        print(f"Adaptive Time:     {time_adaptive:.2f}s")
        print(
            f"Overhead:          {time_adaptive - time_original:+.2f}s "
            f"({((time_adaptive / time_original) - 1) * 100:+.1f}%)"
        )

        # Operator stats
        if "operator_stats" in result_adaptive:
            print("\n" + "=" * 70)
            print("🎯 OPERATOR SELECTION STATISTICS")
            print("=" * 70)

            stats = result_adaptive["operator_stats"]

            for op_type, op_stats in stats.items():
                if not op_stats:
                    continue

                print(f"\n{op_type.upper()}:")
                for name, data in op_stats.items():
                    if data["uses"] > 0:
                        print(
                            f"  {name:<12}: "
                            f"Uses={data['uses']:>4}, "
                            f"Success={data['success_rate']:>5.1%}, "
                            f"Avg Δ={data['avg_improvement']:>+7.4f}"
                        )

        print("\n" + "=" * 70)

        # Both should produce valid results
        assert result_original["fitness"] > 0
        assert result_adaptive["fitness"] > 0

    def test_medium_problem_comparison(
        self, medium_campus, bounds_medium, comparison_sa_config, comparison_ga_config
    ):
        """Compare on medium problem (10 buildings)."""
        print("\n" + "=" * 70)
        print("📊 MEDIUM PROBLEM COMPARISON (10 buildings)")
        print("=" * 70)

        # Original H-SAGA
        print("\n🔹 Running Original H-SAGA...")
        np.random.seed(42)
        start = time.perf_counter()

        optimizer_original = HybridSAGA(
            buildings=medium_campus,
            bounds=bounds_medium,
            sa_config=comparison_sa_config,
            ga_config=comparison_ga_config,
        )
        result_original = optimizer_original.optimize()

        time_original = time.perf_counter() - start

        print(f"✅ Original: {result_original['fitness']:.4f} in {time_original:.2f}s")

        # Adaptive H-SAGA
        print("\n🔸 Running Adaptive H-SAGA...")
        np.random.seed(42)
        start = time.perf_counter()

        optimizer_adaptive = AdaptiveHSAGA(
            buildings=medium_campus,
            bounds=bounds_medium,
            sa_config=comparison_sa_config,
            ga_config=comparison_ga_config,
            selection_strategy=SelectionStrategy.ADAPTIVE_PURSUIT,
            enable_adaptive=True,
        )
        result_adaptive = optimizer_adaptive.optimize()

        time_adaptive = time.perf_counter() - start

        print(f"✅ Adaptive: {result_adaptive['fitness']:.4f} in {time_adaptive:.2f}s")

        # Comparison
        print("\n" + "=" * 70)
        print("📈 COMPARISON RESULTS")
        print("=" * 70)
        print(f"Original Fitness:  {result_original['fitness']:.4f}")
        print(f"Adaptive Fitness:  {result_adaptive['fitness']:.4f}")
        print(
            f"Improvement:       {result_adaptive['fitness'] - result_original['fitness']:+.4f} "
            f"({((result_adaptive['fitness'] / result_original['fitness']) - 1) * 100:+.1f}%)"
        )
        print()
        print(f"Original Time:     {time_original:.2f}s")
        print(f"Adaptive Time:     {time_adaptive:.2f}s")
        print(
            f"Overhead:          {time_adaptive - time_original:+.2f}s "
            f"({((time_adaptive / time_original) - 1) * 100:+.1f}%)"
        )
        print("\n" + "=" * 70)

        # Both should produce valid results
        assert result_original["fitness"] > 0
        assert result_adaptive["fitness"] > 0

    def test_convergence_comparison(
        self, small_campus, bounds_small, comparison_sa_config, comparison_ga_config
    ):
        """Compare convergence behavior."""
        print("\n" + "=" * 70)
        print("📊 CONVERGENCE COMPARISON")
        print("=" * 70)

        # Run both optimizers
        np.random.seed(42)
        optimizer_original = HybridSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=comparison_sa_config,
            ga_config=comparison_ga_config,
        )
        result_original = optimizer_original.optimize()

        np.random.seed(42)
        optimizer_adaptive = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=comparison_sa_config,
            ga_config=comparison_ga_config,
            enable_adaptive=True,
        )
        result_adaptive = optimizer_adaptive.optimize()

        # Compare convergence
        orig_history = result_original["convergence"]["ga_best_history"]
        adap_history = result_adaptive["convergence"]["ga_best_history"]

        print("\nGA Convergence (Best Fitness by Generation):")
        print("Gen | Original | Adaptive | Δ")
        print("-" * 50)

        for gen in [0, 10, 20, 29]:
            if gen < len(orig_history):
                orig_fit = orig_history[gen]
                adap_fit = adap_history[gen]
                delta = adap_fit - orig_fit
                print(f"{gen:>3} | {orig_fit:>8.4f} | {adap_fit:>8.4f} | {delta:>+7.4f}")

        print("\n" + "=" * 70)

        # Check that both converged
        assert len(orig_history) > 0
        assert len(adap_history) > 0


class TestSelectionStrategyComparison:
    """Compare different selection strategies."""

    @pytest.mark.parametrize(
        "strategy",
        [
            SelectionStrategy.UNIFORM,
            SelectionStrategy.GREEDY,
            SelectionStrategy.ADAPTIVE_PURSUIT,
            SelectionStrategy.UCB,
            SelectionStrategy.SOFTMAX,
        ],
    )
    def test_strategy_performance(
        self, small_campus, bounds_small, comparison_sa_config, comparison_ga_config, strategy
    ):
        """Test performance of each selection strategy."""
        print(f"\n🎯 Testing {strategy.value} strategy...")

        np.random.seed(42)
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=comparison_sa_config,
            ga_config=comparison_ga_config,
            selection_strategy=strategy,
            enable_adaptive=True,
        )

        start = time.perf_counter()
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start

        print(f"  Fitness: {result['fitness']:.4f}")
        print(f"  Time:    {elapsed:.2f}s")

        assert result["fitness"] > 0


@pytest.mark.slow
class TestLargeScaleComparison:
    """Large-scale performance comparison."""

    def test_scaling_behavior(self, comparison_sa_config, comparison_ga_config):
        """Test how both algorithms scale with problem size."""
        print("\n" + "=" * 70)
        print("📊 SCALING BEHAVIOR COMPARISON")
        print("=" * 70)

        problem_sizes = [5, 10, 15]
        results = {"original": [], "adaptive": []}

        for n_buildings in problem_sizes:
            print(f"\n🔹 Problem size: {n_buildings} buildings")

            # Create campus
            campus = [
                Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(n_buildings)
            ]

            # Calculate bounds
            total_area = sum(b.area * b.floors for b in campus)
            side = np.sqrt(total_area * 20)  # 20x for spacing
            bounds = (0, 0, side, side)

            # Original
            np.random.seed(42)
            start = time.perf_counter()
            opt_orig = HybridSAGA(
                campus, bounds, sa_config=comparison_sa_config, ga_config=comparison_ga_config
            )
            res_orig = opt_orig.optimize()
            time_orig = time.perf_counter() - start

            # Adaptive
            np.random.seed(42)
            start = time.perf_counter()
            opt_adap = AdaptiveHSAGA(
                campus,
                bounds,
                sa_config=comparison_sa_config,
                ga_config=comparison_ga_config,
                enable_adaptive=True,
            )
            res_adap = opt_adap.optimize()
            time_adap = time.perf_counter() - start

            results["original"].append(
                {"size": n_buildings, "fitness": res_orig["fitness"], "time": time_orig}
            )
            results["adaptive"].append(
                {"size": n_buildings, "fitness": res_adap["fitness"], "time": time_adap}
            )

            print(f"  Original: {res_orig['fitness']:.4f} in {time_orig:.2f}s")
            print(f"  Adaptive: {res_adap['fitness']:.4f} in {time_adap:.2f}s")

        # Summary
        print("\n" + "=" * 70)
        print("SCALING SUMMARY")
        print("=" * 70)
        print("Size | Orig Time | Adap Time | Overhead")
        print("-" * 50)

        for i, size in enumerate(problem_sizes):
            orig = results["original"][i]
            adap = results["adaptive"][i]
            overhead = ((adap["time"] / orig["time"]) - 1) * 100
            print(f"{size:>4} | {orig['time']:>9.2f}s | {adap['time']:>9.2f}s | {overhead:>+6.1f}%")

        print("\n" + "=" * 70)
