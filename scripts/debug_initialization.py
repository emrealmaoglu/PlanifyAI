from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.initialization import SmartInitializer
from shapely.geometry import Polygon
import numpy as np
import time

def analyze_population(problem, X, name):
    print(f"\nAnalyzing {name} Population (Size: {len(X)})")
    
    pop_size = len(X)
    G = np.zeros((pop_size, problem.n_constr))
    
    start = time.time()
    # Evaluate sequentially for debugging
    for i in range(pop_size):
        genotype = problem._decode_individual(X[i])
        roads, buildings = problem._resolve_layout(genotype)
        G[i] = problem._calculate_constraints(buildings, roads)
    duration = time.time() - start
    
    print(f"Evaluation took {duration:.2f}s")
    
    # Analyze constraints
    # 0: green_space, 1: density, 2: spacing, 3: boundary, 4: road_overlap
    constraint_names = ['Green Space', 'Density', 'Spacing', 'Boundary', 'Road Overlap']
    
    for j in range(problem.n_constr):
        violations = G[:, j]
        n_viol = np.sum(violations > 0)
        avg_viol = np.mean(violations[violations > 0]) if n_viol > 0 else 0
        print(f"  {constraint_names[j]}: {n_viol} violations (Avg: {avg_viol:.4f})")
        
    total_feasible = np.sum(np.all(G <= 0, axis=1))
    print(f"  Total Feasible: {total_feasible}")

if __name__ == "__main__":
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    n_buildings = 50
    
    problem = IntegratedCampusProblem(
        boundary=boundary, 
        n_buildings=n_buildings,
        enable_turkish_standards=True,
        use_smart_init=True
    )
    
    # 1. Smart Initialization
    print("Generating Smart Population...")
    X_smart = problem.get_initial_population(10)
    analyze_population(problem, X_smart, "Smart")
    
    # 2. Random Initialization
    print("\nGenerating Random Population...")
    # Manually generate random population
    X_random = []
    for _ in range(10):
        # Create random individual
        # We can use the problem's bounds to generate random values
        x = np.random.uniform(problem.xl, problem.xu)
        X_random.append(x)
    X_random = np.array(X_random)
    
    analyze_population(problem, X_random, "Random")
