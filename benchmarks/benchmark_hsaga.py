"""
Performance benchmark for H-SAGA optimization.

Measures runtime and solution quality for different building counts.

Run: python benchmarks/benchmark_hsaga.py
"""
import sys
import time
from pathlib import Path

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psutil
except ImportError:
    psutil = None

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

from src.algorithms.building import Building, BuildingType  # noqa: E402
from src.algorithms.hsaga import HybridSAGA  # noqa: E402


def generate_test_campus(n_buildings, seed=42):
    """Generate random campus for benchmarking"""
    np.random.seed(seed)
    types = list(BuildingType)
    buildings = []

    for i in range(n_buildings):
        btype = np.random.choice(types)
        area = np.random.uniform(1500, 3500)
        floors = np.random.randint(2, 5)
        buildings.append(Building(f"B{i:03d}", btype, area, floors))

    return buildings


def benchmark_hsaga(n_buildings, config_override=None):
    """Run H-SAGA benchmark"""
    print(f"\n{'='*70}")
    print(f"🏢 Benchmarking H-SAGA: {n_buildings} buildings")
    print(f"{'='*70}\n")

    # Generate campus
    buildings = generate_test_campus(n_buildings)
    bounds = (0, 0, 1000, 1000)

    # Create optimizer
    optimizer = HybridSAGA(buildings, bounds)

    # Apply config overrides if provided
    if config_override:
        optimizer.sa_config.update(config_override.get("sa", {}))
        optimizer.ga_config.update(config_override.get("ga", {}))

    # Get process info
    mem_before = 0
    mem_after = 0
    if psutil:
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

    # Run optimization
    start = time.time()
    result = optimizer.optimize()
    elapsed = time.time() - start

    mem_used = 0
    if psutil:
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_used = mem_after - mem_before

    # Print results
    print(f"\n{'='*70}")
    print("📊 BENCHMARK RESULTS")
    print(f"{'='*70}")
    print(f"⏱️  Runtime: {elapsed:.2f}s")
    if psutil:
        print(f"💾 Memory: {mem_used:.1f} MB")
    print(f"🏆 Fitness: {result['fitness']:.4f}")
    print(f"📈 Evaluations: {result['statistics']['evaluations']:,}")
    print()
    print("Objectives:")
    for obj, score in result["objectives"].items():
        print(f"  • {obj.capitalize():<12}: {score:.4f}")
    print(f"{'='*70}\n")

    return {
        "n_buildings": n_buildings,
        "runtime": elapsed,
        "memory_mb": mem_used,
        "fitness": result["fitness"],
        "evaluations": result["statistics"]["evaluations"],
        "objectives": result["objectives"],
    }


def benchmark_multiple_scales():
    """Benchmark with 10, 20, 50 buildings"""
    print("\n" + "=" * 70)
    print("🚀 H-SAGA MULTI-SCALE BENCHMARK")
    print("=" * 70 + "\n")

    results = []

    # Test cases: (n_buildings, target_time)
    test_cases = [(10, 30.0), (20, 60.0), (50, 120.0)]

    for n_buildings, target_time in test_cases:
        print(f"\n📊 Testing {n_buildings} buildings (target: <{target_time}s)...")
        print("-" * 70)

        # Generate campus
        buildings = generate_test_campus(n_buildings, seed=42)
        bounds = (0, 0, 1000, 1000)

        # Create optimizer
        optimizer = HybridSAGA(buildings, bounds)

        # Adjust config for larger scales
        if n_buildings >= 20:
            optimizer.ga_config["generations"] = 75
            optimizer.ga_config["population_size"] = 75
        if n_buildings >= 50:
            optimizer.ga_config["generations"] = 100
            optimizer.ga_config["population_size"] = 100

        # Measure memory
        mem_before = 0
        mem_after = 0
        if psutil:
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024

        # Run optimization
        start = time.time()
        result = optimizer.optimize()
        elapsed = time.time() - start

        mem_used = 0
        if psutil:
            mem_after = process.memory_info().rss / 1024 / 1024
            mem_used = mem_after - mem_before

        # Store results
        status = "✅" if elapsed < target_time else "❌"
        results.append(
            {
                "buildings": n_buildings,
                "runtime": elapsed,
                "target": target_time,
                "status": status,
                "fitness": result["fitness"],
                "evaluations": result["statistics"]["evaluations"],
                "memory_mb": mem_used,
            }
        )

        print(f"\n{status} Runtime: {elapsed:.2f}s (target: <{target_time}s)")
        print(f"   Fitness: {result['fitness']:.4f}")
        print(f"   Evaluations: {result['statistics']['evaluations']:,}")
        print(f"   Memory: {mem_used:.1f} MB")

    # Summary table
    print("\n" + "=" * 70)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 70 + "\n")

    if tabulate:
        table_data = []
        for r in results:
            table_data.append(
                [
                    r["buildings"],
                    f"{r['runtime']:.1f}s",
                    f"<{r['target']:.0f}s",
                    r["status"],
                    f"{r['fitness']:.4f}",
                    f"{r['evaluations']:,}",
                    f"{r['memory_mb']:.1f} MB",
                ]
            )

        headers = [
            "Buildings",
            "Runtime",
            "Target",
            "Status",
            "Fitness",
            "Evals",
            "Memory",
        ]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        # Simple table without tabulate
        for r in results:
            status_str = r["status"]
            runtime = r["runtime"]
            target = r["target"]
            buildings = r["buildings"]
            print(
                f"{buildings} buildings: {runtime:.1f}s "
                f"(target: <{target:.0f}s) {status_str}"
            )

    # Performance scaling analysis
    print("\n" + "=" * 70)
    print("📈 SCALING ANALYSIS")
    print("=" * 70 + "\n")

    # Check if scaling is approximately linear
    if len(results) >= 2:
        r10 = results[0]
        r20 = results[1]

        time_ratio = r20["runtime"] / r10["runtime"]
        building_ratio = r20["buildings"] / r10["buildings"]

        print("10→20 buildings:")
        print(f"  Time ratio: {time_ratio:.2f}x (expected: ~2x for linear)")
        print(f"  Building ratio: {building_ratio:.1f}x")

        efficiency = building_ratio / time_ratio
        if efficiency >= 0.8:
            print(f"  ✅ Good scaling (efficiency: {efficiency:.2f})")
        elif efficiency >= 0.5:
            print(f"  ⚠️  Acceptable scaling (efficiency: {efficiency:.2f})")
        else:
            print(
                f"  ❌ Poor scaling - needs optimization (efficiency: {efficiency:.2f})"
            )

    if len(results) >= 3:
        r20 = results[1]
        r50 = results[2]

        time_ratio = r50["runtime"] / r20["runtime"]
        building_ratio = r50["buildings"] / r20["buildings"]

        print("\n20→50 buildings:")
        print(f"  Time ratio: {time_ratio:.2f}x (expected: ~2.5x for linear)")
        print(f"  Building ratio: {building_ratio:.1f}x")

        efficiency = building_ratio / time_ratio
        if efficiency >= 0.8:
            print(f"  ✅ Good scaling (efficiency: {efficiency:.2f})")
        elif efficiency >= 0.5:
            print(f"  ⚠️  Acceptable scaling (efficiency: {efficiency:.2f})")
        else:
            print(
                f"  ❌ Poor scaling - needs optimization (efficiency: {efficiency:.2f})"
            )

    print("\n" + "=" * 70 + "\n")

    # Overall assessment
    all_passed = all(r["status"] == "✅" for r in results)
    if all_passed:
        print("✅ ALL PERFORMANCE TARGETS MET!")
    else:
        print("⚠️  Some targets not met. Consider optimization.")

    return results


def main():
    """Run benchmark suite"""
    print("\n" + "=" * 70)
    print("🚀 H-SAGA PERFORMANCE BENCHMARK SUITE")
    print("=" * 70)

    # Performance targets
    targets = {
        10: 30.0,  # 10 buildings: <30s
        20: 60.0,  # 20 buildings: <60s
        50: 120.0,  # 50 buildings: <2min
    }

    results = []

    # Test configurations
    test_cases = [
        {
            "n_buildings": 10,
            "config": None,  # Use default config
        },
        # Uncomment for extended benchmarking:
        # {
        #     'n_buildings': 20,
        #     'config': None
        # },
        # {
        #     'n_buildings': 50,
        #     'config': {
        #         'sa': {'chain_iterations': 15},
        #         'ga': {'generations': 75, 'population_size': 75}
        #     }
        # }
    ]

    for test_case in test_cases:
        n_buildings = test_case["n_buildings"]
        config = test_case["config"]

        result = benchmark_hsaga(n_buildings, config)
        results.append(result)

        # Check target
        target = targets.get(n_buildings)
        if target:
            status = "✅" if result["runtime"] < target else "❌"
            print(f"{status} Target: <{target}s")

    # Summary table
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70 + "\n")

    if tabulate:
        table_data = []
        for r in results:
            n = r["n_buildings"]
            target = targets.get(n, "-")
            status = "✅" if r["runtime"] < target else "❌"

            row = [
                n,
                f"{r['runtime']:.1f}s",
                f"<{target}s" if target != "-" else "-",
                status,
                f"{r['fitness']:.4f}",
            ]
            if psutil:
                row.append(f"{r['memory_mb']:.1f} MB")
            table_data.append(row)

        headers = ["Buildings", "Runtime", "Target", "Status", "Fitness"]
        if psutil:
            headers.append("Memory")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        # Simple table without tabulate
        for r in results:
            n = r["n_buildings"]
            target = targets.get(n, "-")
            status = "✅" if r["runtime"] < target else "❌"
            print(f"{n} buildings: {r['runtime']:.1f}s (target: <{target}s) {status}")

    # Overall result
    print()
    all_passed = all(
        r["runtime"] < targets.get(r["n_buildings"], float("inf")) for r in results
    )

    if all_passed:
        print("✅ ALL PERFORMANCE TARGETS MET!")
    else:
        print("❌ Some targets not met. Consider optimization.")

    print("\n" + "=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    # Run multi-scale benchmark
    results = benchmark_multiple_scales()

    # Exit with appropriate code
    all_passed = all(r["status"] == "✅" for r in results)
    sys.exit(0 if all_passed else 1)
