"""Benchmark hierarchical constraint evaluation."""

import time
import numpy as np
from shapely.geometry import Polygon

from backend.core.integration import IntegratedCampusProblem

def benchmark_phase(n_buildings, n_generations=5):
    """Benchmark hierarchical evaluation across generations."""
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
    
    times_per_gen = []
    
    # Use smaller population for benchmark speed
    pop_size = 20
    
    for gen in range(n_generations):
        # Simulate generation (random → convergence)
        if gen == 0:
            # Random population (high violation rate)
            X = np.random.rand(pop_size, problem.n_var)
        else:
            # Semi-converged (lower violation rate)
            # Perturb towards feasible region (center of bounds)
            center = (problem.xu + problem.xl) / 2
            noise = (np.random.rand(pop_size, problem.n_var) - 0.5) * (1.0 / (gen + 1))
            X = center + noise * (problem.xu - problem.xl)
            
            # Clip to bounds
            X = np.clip(X, problem.xl, problem.xu)
        
        X = X * (problem.xu - problem.xl) + problem.xl
        
        # Benchmark
        start = time.time()
        out = {}
        problem._evaluate(X, out)
        elapsed = time.time() - start
        
        times_per_gen.append(elapsed / pop_size)
    
    return times_per_gen, problem

if __name__ == "__main__":
    print("=" * 60)
    print("Hierarchical Constraint Evaluation Benchmark")
    print("=" * 60)

    for n in [50]:
        print(f"\n{n} Buildings:")
        times, problem = benchmark_phase(n, n_generations=5)
        
        for i, t in enumerate(times):
            print(f"  Gen {i}: {t:.3f}s per eval")
        
        print(f"  Average: {np.mean(times):.3f}s")
        print(f"  Best (early gen): {min(times):.3f}s")
        print(f"  Worst (late gen): {max(times):.3f}s")

    # Print statistics
    print("\nConstraint Rejection Statistics:")
    evaluator = problem._hierarchical_evaluator if hasattr(problem, '_hierarchical_evaluator') else None
    if evaluator:
        stats = evaluator.get_statistics()
        print(f"  Green space rejects: {stats['green_space_reject_rate']:.1%}")
        print(f"  Density rejects: {stats['density_reject_rate']:.1%}")
        print(f"  Boundary rejects: {stats['boundary_reject_rate']:.1%}")
        print(f"  Spacing rejects: {stats['spacing_reject_rate']:.1%}")
        print(f"  Road overlap checks: {stats['road_overlap_rate']:.1%}")
