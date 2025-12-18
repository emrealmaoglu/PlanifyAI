"""Debug zone cache hashing."""

import numpy as np
from shapely.geometry import Polygon
from backend.core.integration import IntegratedCampusProblem

def debug_hashing():
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    problem = IntegratedCampusProblem(
        boundary=boundary,
        n_buildings=50,
        enable_zone_cache=True
    )
    
    # Gen 0
    X = np.random.rand(50, problem.n_var)
    X_scaled = X * (problem.xu - problem.xl) + problem.xl
    
    # Mini-benchmark with static roads
    problem.enable_adaptive_roads = False
    
    print("\nRunning Mini-Benchmark (Static Roads)...")
    
    # Warmup
    out = {}
    problem._evaluate(X_scaled, out)
    
    # Measure Baseline (Force cache miss by clearing or disabling?)
    # We can't easily disable cache on the fly without hacking.
    # But we can measure "First Eval" (Miss) vs "Second Eval" (Hit).
    
    # 1. Full Eval (Cache Miss)
    # We need to clear cache or use new inputs.
    # Let's use a new random individual.
    X_new = np.random.rand(1, problem.n_var)
    X_new_scaled = X_new * (problem.xu - problem.xl) + problem.xl
    
    start = time.time()
    problem._evaluate(X_new_scaled, out)
    t_miss = time.time() - start
    print(f"Cache Miss (Full): {t_miss:.4f}s")
    
    # 2. Cache Hit (Same individual)
    start = time.time()
    problem._evaluate(X_new_scaled, out)
    t_hit = time.time() - start
    print(f"Cache Hit (Full):  {t_hit:.4f}s")
    
    # 3. Partial Hit (Move 1 building)
    X_mut = X_new.copy()
    X_mut[0, 0] += 0.001 # Small move
    X_mut_scaled = X_mut * (problem.xu - problem.xl) + problem.xl
    
    start = time.time()
    problem._evaluate(X_mut_scaled, out)
    t_partial = time.time() - start
    print(f"Partial Hit:       {t_partial:.4f}s")
    
    stats = problem._zone_cache.get_statistics()
    print("\nStats:", stats)

if __name__ == "__main__":
    debug_hashing()
