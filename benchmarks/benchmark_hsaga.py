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
    all_passed = all(r["runtime"] < targets.get(r["n_buildings"], float("inf")) for r in results)

    if all_passed:
        print("✅ ALL PERFORMANCE TARGETS MET!")
    else:
        print("❌ Some targets not met. Consider optimization.")

    print("\n" + "=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
