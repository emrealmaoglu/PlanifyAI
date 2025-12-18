import time
import numpy as np
from shapely.geometry import Polygon
from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.optimizer import AdvancedOptimizer

def benchmark(n_buildings, use_parallel):
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    
    problem = IntegratedCampusProblem(
        boundary=boundary, n_buildings=n_buildings,
        objectives=['cost','adjacency','road_access'],
        enable_turkish_standards=True
    )
    
    optimizer = AdvancedOptimizer(
        problem, population_size=20, n_generations=5,
        use_hsaga=False, use_parallel=use_parallel
    )
    
    start = time.time()
    result = optimizer.optimize()
    elapsed = time.time() - start
    
    n_solutions = len(result.F) if result.F is not None else 0
    return elapsed, n_solutions

if __name__ == "__main__":
    # Run benchmarks
    print("=" * 60)
    print("Parallelization Benchmark")
    print("=" * 60)

    for n in [20, 50, 100]:
        print(f"\nTesting {n} buildings...")
        try:
            serial_time, _ = benchmark(n, use_parallel=False)
            parallel_time, solutions = benchmark(n, use_parallel=True)
            speedup = serial_time / parallel_time
            
            print(f"  Serial:   {serial_time:.1f}s")
            print(f"  Parallel: {parallel_time:.1f}s")
            print(f"  Speedup:  {speedup:.2f}x")
        except Exception as e:
            print(f"  Failed: {e}")
            import traceback
            traceback.print_exc()
