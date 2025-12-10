"""Combined Phase 1A + 1B benchmark."""

import time
import numpy as np
from shapely.geometry import Polygon

from backend.core.integration import IntegratedCampusProblem

def benchmark_combined(n_buildings):
    """Benchmark complete Phase 1 optimizations."""
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    
    problem = IntegratedCampusProblem(
        boundary=boundary,
        n_buildings=n_buildings,
        objectives=['cost','adjacency','road_access'],
        enable_turkish_standards=True,
        enable_adaptive_roads=True,
        use_smart_init=False,
        use_adaptive_constraints=True
    )
    
    # Simulate realistic generation mix
    results = []
    pop_size = 50
    
    for gen_type in ['random', 'semi_converged', 'elite']:
        if gen_type == 'random':
            X = np.random.rand(pop_size, problem.n_var)
        elif gen_type == 'semi_converged':
            center = (problem.xu + problem.xl) / 2
            noise = (np.random.rand(pop_size, problem.n_var) - 0.5) * 0.5
            X = center + noise * (problem.xu - problem.xl)
        else:  # elite
            center = (problem.xu + problem.xl) / 2
            noise = (np.random.rand(pop_size, problem.n_var) - 0.5) * 0.1
            X = center + noise * (problem.xu - problem.xl)
        
        X = np.clip(X, problem.xl, problem.xu)
        X = X * (problem.xu - problem.xl) + problem.xl
        
        start = time.time()
        out = {}
        problem._evaluate(X, out)
        elapsed = time.time() - start
        
        results.append((gen_type, elapsed / pop_size))
    
    return results

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1 COMBINED BENCHMARK (1A + 1B)")
    print("=" * 60)

    baselines = {20: 5.0, 50: 10.0, 100: 30.0}

    for n in [20, 50, 100]:
        print(f"\n{n} Buildings:")
        print(f"  Baseline: {baselines[n]:.1f}s")
        
        try:
            results = benchmark_combined(n)
            
            avg_time = np.mean([t for _, t in results])
            avg_speedup = baselines[n] / avg_time
            
            for gen_type, time_per_eval in results:
                speedup = baselines[n] / time_per_eval
                print(f"  {gen_type:15s}: {time_per_eval:.2f}s ({speedup:.1f}x)")
            
            print(f"  Average: {avg_time:.2f}s ({avg_speedup:.1f}x speedup)")
            
            if avg_speedup >= 5.0:
                print("  ✅ TARGET ACHIEVED (5x)")
            else:
                print(f"  ⚠️  Target missed (need 5x, got {avg_speedup:.1f}x)")
        except Exception as e:
            print(f"  Error: {e}")
