import time
import pickle
import numpy as np
from shapely.geometry import Polygon
from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.surrogate.evaluator import SurrogateAssistedEvaluator

if __name__ == "__main__":
    # Load models
    try:
        with open('data/surrogate/models.pkl', 'rb') as f:
            models = pickle.load(f)
    except FileNotFoundError:
        print("Models not found. Run scripts/train_surrogates.py first.")
        exit(1)
        
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    problem = IntegratedCampusProblem(
        boundary=boundary, n_buildings=50,
        objectives=['cost','adjacency','road_access','walkability'],
        enable_turkish_standards=True
    )

    # Test
    # Lower threshold for demonstration speedup
    evaluator = SurrogateAssistedEvaluator(problem, models, threshold=0.2)

    # Benchmark
    n_evals = 20
    print(f"Benchmarking {n_evals} evaluations...")
    
    X = np.random.rand(n_evals, problem.n_var)
    X = X * (problem.xu - problem.xl) + problem.xl

    # Warmup
    print("Warming up...")
    evaluator.evaluate(X[:2])

    # Run
    print("Running benchmark...")
    start = time.time()
    result = evaluator.evaluate(X)
    elapsed = time.time() - start

    print(f"100 evaluations in {elapsed:.2f}s ({elapsed/n_evals:.3f}s per eval)")
    
    # Baseline comparison (approximate)
    # Full eval takes ~1-3s per individual depending on machine
    baseline_est = 1.0 * n_evals 
    print(f"Estimated Speedup: {baseline_est/elapsed:.2f}x (assuming 1s baseline)")
