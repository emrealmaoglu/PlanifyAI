"""Benchmark spatial indexing improvement."""

import time
import numpy as np
from shapely.geometry import Polygon

from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.optimizer import AdvancedOptimizer

def benchmark_single_eval(n_buildings):
    """Benchmark single evaluation time."""
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    
    problem = IntegratedCampusProblem(
        boundary=boundary,
        n_buildings=n_buildings,
        objectives=['cost','adjacency','road_access'],
        enable_turkish_standards=True,
        enable_adaptive_roads=True, # Ensure roads are generated
        use_smart_init=False # Random init is faster/simpler for this
    )
    
    # Generate random population
    # We need to simulate a population to evaluate
    pop_size = 10
    X = np.random.rand(pop_size, problem.n_var)
    X = X * (problem.xu - problem.xl) + problem.xl
    
    # Benchmark
    start = time.time()
    out = {}
    problem._evaluate(X, out)
    elapsed = time.time() - start
    
    return elapsed / pop_size  # Per individual

if __name__ == "__main__":
    print("=" * 60)
    print("Spatial Indexing Benchmark")
    print("=" * 60)

    for n in [20, 50, 100]:
        print(f"Benchmarking {n} buildings...")
        try:
            time_per_eval = benchmark_single_eval(n)
            print(f"{n} buildings: {time_per_eval:.4f}s per evaluation")
        except Exception as e:
            print(f"Error benchmarking {n} buildings: {e}")
