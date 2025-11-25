import time
from shapely.geometry import Polygon
from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.optimizer import AdvancedOptimizer
from backend.core.integration.visualization import visualize_integrated_layout
import matplotlib.pyplot as plt

def main():
    boundary = Polygon([(0, 0), (800, 0), (800, 800), (0, 800)])

    objectives = ['cost', 'adjacency', 'green_space', 
                  'road_access', 'road_coverage', 'walkability']

    print("Initializing Integrated Campus Problem with Turkish Standards...")
    problem = IntegratedCampusProblem(
        boundary=boundary, n_grids=3, n_radials=2, n_buildings=50,
        objectives=objectives, enable_adaptive_roads=True,
        enable_turkish_standards=True
    )

    print("Initializing Advanced Optimizer (NSGA-III + H-SAGA)...")
    optimizer = AdvancedOptimizer(problem, population_size=130, 
                                 n_generations=5, use_hsaga=True)

    print("Starting optimization...")
    start = time.time()
    result = optimizer.optimize()
    elapsed = time.time() - start

    print(f"Optimization Complete!")
    
    if result.F is None:
        print("No feasible solution found (Constraints not satisfied).")
        print("Extracting best infeasible solution from population...")
        # Sort by constraint violation (CV) then by objectives
        pop = result.pop
        # Pymoo Individual objects have .CV and .F attributes
        # We want to minimize CV.
        # Let's just take the one with min CV.
        best_ind = min(pop, key=lambda ind: ind.CV.sum())
        print(f"Best CV: {best_ind.CV.sum()}")
        
        from backend.core.integration.composite_genotype import CompositeGenotype
        best = CompositeGenotype.from_flat_array(
            best_ind.X,
            problem.n_grids,
            problem.n_radials,
            problem.n_buildings
        )
    else:
        print(f"Runtime: {elapsed:.1f}s | Pareto solutions: {len(result.F)}")
        best = optimizer.extract_best_solution(result)

    roads, buildings = best.decode(boundary)

    total_v, details = problem.standards_validator.calculate_constraint_violations(
        buildings, roads
    )

    print(f"Compliance: {'✅ PASS' if total_v == 0 else f'⚠️ {total_v:.1f}'}")
    print("Constraint Details:", details)

    # Visualize
    print("Generating visualization...")
    tensor_field = problem.adaptive_generator.generate_from_buildings(
        best.building_layout.positions, boundary
    )
    fig = visualize_integrated_layout(roads, buildings, boundary, tensor_field)
    output_path = '/tmp/milestone3_production.png'
    fig.savefig(output_path, dpi=150)
    print(f"Visualization saved to {output_path}")

if __name__ == "__main__":
    main()
