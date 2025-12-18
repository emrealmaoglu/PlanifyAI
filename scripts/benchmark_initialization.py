from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.optimizer import AdvancedOptimizer
from shapely.geometry import Polygon
import time
import numpy as np

if __name__ == "__main__":
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])

    print("Comparing Random vs Smart Initialization")
    print("=" * 60)

    for n in [20, 50, 100]:
        print(f"\\n{n} buildings:")
        
        # Random initialization
        problem_random = IntegratedCampusProblem(
            boundary=boundary, n_buildings=n,
            objectives=['cost','adjacency','road_access'],
            enable_turkish_standards=True,
            use_smart_init=False
        )
        
        optimizer_random = AdvancedOptimizer(problem_random, n_generations=10) # Reduced generations for speed
        start = time.time()
        result_random = optimizer_random.optimize()
        time_random = time.time() - start
        
        # Check if result_random.CV is None or empty
        if result_random.CV is None or len(result_random.CV) == 0:
            feasible_random = 0
        else:
            feasible_random = sum(1 for cv in result_random.CV if cv[0] <= 0)
        
        # Smart initialization
        problem_smart = IntegratedCampusProblem(
            boundary=boundary, n_buildings=n,
            objectives=['cost','adjacency','road_access'],
            enable_turkish_standards=True,
            use_smart_init=True
        )
        
        optimizer_smart = AdvancedOptimizer(problem_smart, n_generations=10)
        start = time.time()
        result_smart = optimizer_smart.optimize()
        time_smart = time.time() - start
        
        if result_smart.CV is None or len(result_smart.CV) == 0:
            feasible_smart = 0
        else:
            feasible_smart = sum(1 for cv in result_smart.CV if cv[0] <= 0)
        
        print(f"  Random: {feasible_random} feasible in {time_random:.1f}s")
        print(f"  Smart:  {feasible_smart} feasible in {time_smart:.1f}s")
