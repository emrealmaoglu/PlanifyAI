"""
Performance benchmark for objective functions.

Run: python benchmarks/benchmark_objectives.py

Created: 2025-11-06
"""
import sys
import time
from pathlib import Path

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.algorithms.objectives import (
    minimize_cost,
    minimize_walking_distance,
    maximize_adjacency_satisfaction
)
from src.algorithms.building import Building, BuildingType
from src.algorithms.solution import Solution


def generate_campus(n_buildings: int, seed: int = 42):
    """Generate synthetic campus for benchmarking"""
    np.random.seed(seed)
    
    types = list(BuildingType)
    buildings = []
    positions = {}
    
    for i in range(n_buildings):
        b_type = np.random.choice(types)
        area = np.random.uniform(1000, 5000)
        floors = np.random.randint(2, 5)
        
        bid = f"B{i:03d}"
        buildings.append(Building(bid, b_type, area, floors))
        
        x = np.random.uniform(50, 950)
        y = np.random.uniform(50, 950)
        positions[bid] = (x, y)
    
    solution = Solution(positions)
    return solution, buildings


def benchmark_objective(func, solution, buildings, n_runs=5):
    """Benchmark an objective function"""
    times = []
    
    for _ in range(n_runs):
        start = time.perf_counter()
        _ = func(solution, buildings)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)
    
    return np.median(times), times


def main():
    print("=" * 60)
    print("Objective Functions Performance Benchmark")
    print("=" * 60)
    print()
    
    # Performance targets (milliseconds)
    targets = {
        50: {"cost": 1.0, "walking": 3.0, "adjacency": 8.0},
        100: {"cost": 1.0, "walking": 5.0, "adjacency": 15.0},
    }
    
    results = []
    
    for n_buildings in [50, 100]:
        print(f"Testing with {n_buildings} buildings...")
        solution, buildings = generate_campus(n_buildings)
        
        objectives = [
            ("cost", minimize_cost),
            ("walking", minimize_walking_distance),
            ("adjacency", maximize_adjacency_satisfaction),
        ]
        
        for name, func in objectives:
            median, times = benchmark_objective(func, solution, buildings)
            target = targets[n_buildings][name]
            passed = median <= target
            
            status = "✓" if passed else "✗"
            print(f"  {name:12s}: {median:6.2f}ms (target: {target:.1f}ms) {status}")
            
            results.append({
                "n": n_buildings,
                "obj": name,
                "time": median,
                "target": target,
                "passed": passed
            })
        
        print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    all_passed = all(r["passed"] for r in results)
    
    if all_passed:
        print("✓ All performance targets met!")
    else:
        failed = [r for r in results if not r["passed"]]
        print(f"✗ {len(failed)} tests failed:")
        for r in failed:
            print(f"  - {r['obj']} (n={r['n']}): {r['time']:.2f}ms > {r['target']:.1f}ms")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

