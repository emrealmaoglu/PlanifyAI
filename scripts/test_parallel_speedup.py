from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.parallel import SharedMemoryEvaluator
from shapely.geometry import Polygon
import time
import numpy as np

if __name__ == "__main__":
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    n_buildings = 50
    
    problem = IntegratedCampusProblem(
        boundary=boundary, 
        n_buildings=n_buildings,
        enable_turkish_standards=True,
        use_smart_init=True
    )
    
    # Generate population
    pop_size = 20
    X = problem.get_initial_population(pop_size)
    
    print(f"Evaluating {pop_size} individuals with {n_buildings} buildings...")
    
    # Serial Evaluation
    print("\nSerial Evaluation:")
    start = time.time()
    problem._evaluate(X, {})
    serial_time = time.time() - start
    print(f"Time: {serial_time:.2f}s")
    
    # Parallel Evaluation
    print("\nParallel Evaluation (Shared Memory):")
    evaluator = SharedMemoryEvaluator(problem)
    problem.parallel_evaluator = evaluator
    
    start = time.time()
    problem._evaluate(X, {})
    parallel_time = time.time() - start
    print(f"Time: {parallel_time:.2f}s")
    
    print(f"\nSpeedup: {serial_time / parallel_time:.2f}x")
