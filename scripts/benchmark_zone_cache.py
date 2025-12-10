"""Benchmark zone-based caching."""

import time
import numpy as np
from shapely.geometry import Polygon

from backend.core.integration import IntegratedCampusProblem

def benchmark_with_cache(n_buildings, n_generations=10):
    """Benchmark with zone cache enabled."""
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    
    problem = IntegratedCampusProblem(
        boundary=boundary,
        n_buildings=n_buildings,
        objectives=['cost','adjacency','road_access'],
        enable_adaptive_roads=False,  # DISABLE ADAPTIVE ROADS FOR CACHE TEST
        enable_turkish_standards=True,
        enable_zone_cache=True  # ENABLE CACHE
    )
    
    times = []
    pop_size = 50
    
    for gen in range(n_generations):
        # Simulate evolution (increasing similarity)
        if gen == 0:
            X = np.random.rand(pop_size, problem.n_var)
        else:
            # Mutate previous (high similarity)
            # Perturb only 10% of variables to simulate inheritance/local search
            mask = np.random.rand(*X.shape) < 0.1
            noise = np.random.randn(*X.shape) * 0.001  # Smaller noise (1m)
            X[mask] += noise[mask]
        
        # Clip to bounds
        X = np.clip(X, 0, 1) # Normalized space
        
        # Scale to problem bounds
        X_scaled = X * (problem.xu - problem.xl) + problem.xl
        
        start = time.time()
        out = {}
        problem._evaluate(X_scaled, out)
        elapsed = time.time() - start
        
        times.append(elapsed / pop_size)
    
    return times, problem._zone_cache.get_statistics()

def benchmark_without_cache(n_buildings):
    """Benchmark without cache (Phase 1 behavior)."""
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    
    problem = IntegratedCampusProblem(
        boundary=boundary,
        n_buildings=n_buildings,
        objectives=['cost','adjacency','road_access'],
        enable_adaptive_roads=False,  # DISABLE ADAPTIVE ROADS FOR CACHE TEST
        enable_turkish_standards=True,
        enable_zone_cache=False  # DISABLE CACHE
    )
    
    pop_size = 50
    X = np.random.rand(pop_size, problem.n_var)
    X = X * (problem.xu - problem.xl) + problem.xl
    
    start = time.time()
    out = {}
    problem._evaluate(X, out)
    elapsed = time.time() - start
    
    return elapsed / pop_size

if __name__ == "__main__":
    print("=" * 60)
    print("Zone-Based Caching Benchmark")
    print("=" * 60)

    for n in [50]:
        print(f"\n{n} Buildings:")
        
        # Benchmark without cache
        time_no_cache = benchmark_without_cache(n)
        print(f"  Without cache: {time_no_cache:.3f}s")
        
        # Benchmark with cache
        times_with_cache, stats = benchmark_with_cache(n, n_generations=10)
        
        print(f"\n  With cache (by generation):")
        for i, t in enumerate(times_with_cache):
            speedup = time_no_cache / t if t > 0 else float('inf')
            print(f"    Gen {i:2d}: {t:.3f}s ({speedup:.1f}x)")
        
        avg_time = np.mean(times_with_cache[1:])  # Skip gen 0 (cold cache)
        avg_speedup = time_no_cache / avg_time
        
        print(f"\n  Average (warm cache): {avg_time:.3f}s ({avg_speedup:.1f}x)")
        
        # Cache statistics
        print(f"\n  Cache Statistics:")
        print(f"    Hit rate: {stats['hit_rate']:.1%}")
        print(f"    Full cache hits: {stats['full_cache_hit_rate']:.1%}")
        print(f"    Partial hits: {stats['partial_cache_hit_rate']:.1%}")
        print(f"    Cache size: {stats['size']}/{stats['capacity']}")
