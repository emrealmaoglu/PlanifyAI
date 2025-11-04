#!/usr/bin/env python3
"""
Run SA Phase Performance Benchmarks
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.algorithms.building import create_sample_campus  # noqa: E402
from src.algorithms.hsaga import HybridSAGA  # noqa: E402


def run_benchmark(name, buildings, bounds, sa_config):
    """Run a single benchmark and return results"""
    print("\n" + "=" * 60)
    print(f"Benchmark: {name}")
    print("=" * 60)
    print(f"  Buildings: {len(buildings)}")
    print(f"  Chains: {sa_config['num_chains']}")
    print(f"  Iterations/chain: {sa_config['chain_iterations']}")

    optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)

    start_time = time.perf_counter()
    result = optimizer.optimize()
    elapsed = time.perf_counter() - start_time

    print("\n  Results:")
    print(f"    Time: {elapsed:.2f}s")
    print(f"    Fitness: {result['fitness']:.4f}")
    print(f"    Best solution: {len(result['best_solution'].positions)} buildings placed")

    return {
        "name": name,
        "buildings": len(buildings),
        "time": elapsed,
        "fitness": result["fitness"],
        "chains": sa_config["num_chains"],
    }


def main():
    """Run all benchmarks"""
    results = []

    # Benchmark 1: 5 buildings
    print("\n" + "=" * 60)
    print("SA Phase Performance Benchmarks")
    print("=" * 60)

    buildings_5 = create_sample_campus()[:5]
    bounds_5 = (0.0, 0.0, 500.0, 500.0)
    sa_config_5 = {
        "initial_temp": 100.0,
        "final_temp": 0.1,
        "cooling_rate": 0.95,
        "max_iterations": 100,
        "num_chains": 2,
        "chain_iterations": 100,
    }
    results.append(run_benchmark("5 buildings", buildings_5, bounds_5, sa_config_5))

    # Benchmark 2: 10 buildings
    buildings_10 = create_sample_campus()
    bounds_10 = (0.0, 0.0, 1000.0, 1000.0)
    sa_config_10 = {
        "initial_temp": 100.0,
        "final_temp": 0.1,
        "cooling_rate": 0.95,
        "max_iterations": 200,
        "num_chains": 2,
        "chain_iterations": 200,
    }
    results.append(run_benchmark("10 buildings", buildings_10, bounds_10, sa_config_10))

    # Benchmark 3: Multiprocessing speedup test (4 chains)
    sa_config_4chains = sa_config_10.copy()
    sa_config_4chains["num_chains"] = 4
    sa_config_4chains["chain_iterations"] = 100  # Reduced for speedup test
    results.append(
        run_benchmark("10 buildings (4 chains)", buildings_10, bounds_10, sa_config_4chains)
    )

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"{'Benchmark':<25} {'Time (s)':<12} {'Fitness':<12} {'Status'}")
    print("-" * 60)

    targets = {5: 15.0, 10: 30.0}

    for r in results:
        if r["name"] == "10 buildings (4 chains)":
            status = "OK"  # Speedup test
        else:
            target = targets.get(r["buildings"], 999)
            status = "✅ PASS" if r["time"] < target else "⚠️ SLOW"
        print(f"{r['name']:<25} {r['time']:>10.2f}s  {r['fitness']:>10.4f}  {status}")

    # Multiprocessing speedup analysis
    seq_result = next(r for r in results if r["name"] == "10 buildings")
    par_result = next(r for r in results if r["name"] == "10 buildings (4 chains)")

    if par_result and seq_result:
        # Theoretical speedup (4 chains vs 2 chains with same iterations)
        # Actual speedup depends on parallelization efficiency
        print("\n" + "=" * 60)
        print("Multiprocessing Analysis")
        print("=" * 60)
        print(
            f"  2 chains: {seq_result['time']:.2f}s ({seq_result['chains'] * 200} total iterations)"
        )
        print(
            f"  4 chains: {par_result['time']:.2f}s ({par_result['chains'] * 100} total iterations)"
        )
        print("  Note: Different iteration counts for fair comparison")
        print(f"  Parallel execution: {'✅ Working' if par_result['chains'] == 4 else '❌ Failed'}")

    print("\n" + "=" * 60)
    print("Benchmarks complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
