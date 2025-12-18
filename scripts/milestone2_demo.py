"""
Demo: Coupled optimization with adaptive roads.
"""

import numpy as np
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.integration import (
    IntegratedCampusProblem,
    CoupledOptimizer
)
from backend.core.integration.visualization import visualize_integrated_layout


def main():
    """Run coupled optimization demo."""
    print("=== Milestone 2: Coupled Optimization Demo ===\n")
    
    # Define campus
    boundary = Polygon([(0, 0), (800, 0), (800, 800), (0, 800)])
    
    # Create problem with coupled objectives
    problem = IntegratedCampusProblem(
        boundary=boundary,
        n_grids=3,
        n_radials=2,
        n_buildings=30,
        objectives=['cost', 'adjacency', 'road_access', 'road_coverage'],
        enable_adaptive_roads=True  # KEY: Enable coupling
    )
    
    print(f"Objectives: {problem.objective_names}")
    print(f"Adaptive roads: {problem.enable_adaptive_roads}\n")
    
    # Run optimization
    optimizer = CoupledOptimizer(
        problem=problem,
        population_size=8,
        n_generations=5
    )
    
    print("Running optimization...\n")
    result = optimizer.optimize()
    
    # Extract best solution
    best = optimizer.extract_best_solution(result)
    
    # Decode to roads and buildings
    # For adaptive roads, we need to regenerate the field from the buildings
    # because the genotype's tensor params are ignored in adaptive mode
    if problem.enable_adaptive_roads:
        tensor_field = problem.adaptive_generator.generate_from_buildings(
            best.building_layout.positions, boundary
        )
        roads = problem._generate_roads_from_field(tensor_field)
        buildings = best.building_layout.to_building_list()
    else:
        roads, buildings = best.decode(boundary)
        tensor_field = best.tensor_params.to_tensor_field()
    
    print(f"\nResults:")
    print(f"  Roads generated: {len(roads)}")
    print(f"  Buildings placed: {len(buildings)}")
    if len(result.F) > 0:
        print(f"  Objective values (Best): {result.F[0]}")
    
    # Visualize
    fig = visualize_integrated_layout(
        roads=roads,
        buildings=buildings,
        boundary=boundary,
        tensor_field=tensor_field,
        title="Milestone 2: Coupled Optimization Result"
    )
    
    output_path = '/tmp/milestone2_coupled_result.png'
    fig.savefig(output_path, dpi=150)
    print(f"\n✅ Visualization saved: {output_path}")


if __name__ == '__main__':
    main()
