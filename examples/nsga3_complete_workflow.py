"""
NSGA-III Complete Workflow Example
===================================

Demonstrates the complete workflow:
1. Run NSGA-III optimization
2. Generate visualizations
3. Analyze trade-offs

This example shows how to use the PlanifyAI multi-objective optimization
system with NSGA-III algorithm and visualization tools.

Usage:
    python examples/nsga3_complete_workflow.py

Requirements:
    - matplotlib
    - numpy
    - Backend API running (optional for REST API examples)

Created: 2026-01-03
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.optimization.nsga3_runner import NSGA3Runner, NSGA3RunnerConfig
from src.algorithms import Building, BuildingType, ProfileType, get_profile
from src.visualization import ParetoVisualizer, TradeOffAnalyzer


def create_sample_buildings():
    """Create sample buildings for optimization."""
    print("📦 Creating sample buildings...")
    buildings = [
        Building(id="library", type=BuildingType.LIBRARY, area=3000, floors=3),
        Building(id="dorm_a", type=BuildingType.RESIDENTIAL, area=4000, floors=5),
        Building(id="dorm_b", type=BuildingType.RESIDENTIAL, area=4000, floors=5),
        Building(id="cafeteria", type=BuildingType.DINING, area=1500, floors=2),
        Building(id="sports_center", type=BuildingType.SPORTS, area=2500, floors=2),
        Building(id="admin", type=BuildingType.ADMINISTRATIVE, area=2000, floors=3),
    ]
    print(f"   ✓ Created {len(buildings)} buildings")
    return buildings


def run_optimization(buildings, bounds, profile_type=ProfileType.RESEARCH_ENHANCED):
    """
    Run NSGA-III optimization with given profile.

    Args:
        buildings: List of Building objects
        bounds: Site boundaries (x_min, y_min, x_max, y_max)
        profile_type: Objective profile type

    Returns:
        Optimization result dictionary
    """
    print(f"\n🚀 Running NSGA-III optimization with {profile_type.value} profile...")

    # Get profile information
    profile = get_profile(profile_type)
    print(f"   Profile: {profile.name}")
    print(f"   Enhanced objectives: {profile.use_enhanced}")
    print(f"   Weights: {profile.weights}")

    # Configure optimization
    config = NSGA3RunnerConfig(
        population_size=50,
        n_generations=50,
        n_partitions=12,
        objective_profile=profile_type,
        seed=42,
        verbose=False,
    )

    # Run optimization
    runner = NSGA3Runner(buildings, bounds, config)
    result = runner.run()

    print(f"   ✓ Optimization complete!")
    print(f"   ✓ Pareto front size: {len(result['pareto_front'])}")
    print(f"   ✓ Number of objectives: {result['pareto_objectives'].shape[1]}")
    print(f"   ✓ Runtime: {runner.stats['runtime']:.2f}s")
    print(f"   ✓ Evaluations: {result['statistics']['evaluations']}")

    return result


def analyze_results(result):
    """
    Analyze optimization results.

    Args:
        result: Optimization result dictionary
    """
    print("\n📊 Analyzing results...")

    objectives = result["pareto_objectives"]

    # Compute statistics
    stats = TradeOffAnalyzer.compute_statistics(objectives)
    print("\n   Statistics:")
    print(f"   • Min: {stats['min']}")
    print(f"   • Max: {stats['max']}")
    print(f"   • Mean: {stats['mean']}")
    print(f"   • Std: {stats['std']}")

    # Compute correlations
    correlations = TradeOffAnalyzer.compute_correlations(objectives)
    print("\n   Correlation Matrix:")
    print(correlations)

    # Find extreme solutions
    extremes = TradeOffAnalyzer.find_extreme_solutions(objectives)
    print("\n   Extreme Solutions (minimizing each objective):")
    for obj_key, (idx, values) in extremes.items():
        print(f"   • {obj_key}: Solution #{idx}, Values: {values}")

    # Compute hypervolume
    hypervolume = TradeOffAnalyzer.compute_hypervolume_approximation(objectives)
    print(f"\n   Hypervolume (approximation): {hypervolume:.2f}")

    # Best compromise
    if result["best_compromise"]:
        best = result["best_compromise"]
        print("\n   Best Compromise Solution:")
        print(f"   • Index: {best['index']}")
        print(f"   • Objectives: {best['objectives']}")
        print(f"   • Normalized: {best['normalized_objectives']}")


def visualize_results(result, obj_names, output_dir="examples/output"):
    """
    Generate visualizations of results.

    Args:
        result: Optimization result dictionary
        obj_names: List of objective names
        output_dir: Output directory for plots
    """
    print(f"\n🎨 Generating visualizations...")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    objectives = result["pareto_objectives"]
    best_idx = result["best_compromise"]["index"] if result["best_compromise"] else None

    visualizer = ParetoVisualizer(figsize=(10, 8), dpi=150)

    n_objectives = objectives.shape[1]

    # 1. Parallel Coordinates (works for any number of objectives)
    print("   • Generating parallel coordinates plot...")
    fig1 = visualizer.plot_parallel_coordinates(
        objectives,
        obj_names=obj_names,
        best_idx=best_idx,
        title="Pareto Front - Parallel Coordinates",
        save_path=f"{output_dir}/parallel_coordinates.png",
        show=False,
    )
    print(f"     ✓ Saved to {output_dir}/parallel_coordinates.png")

    # 2. Objective Matrix
    print("   • Generating objective trade-off matrix...")
    fig2 = visualizer.plot_objective_matrix(
        objectives,
        obj_names=obj_names,
        best_idx=best_idx,
        title="Objective Trade-off Matrix",
        save_path=f"{output_dir}/objective_matrix.png",
        show=False,
    )
    print(f"     ✓ Saved to {output_dir}/objective_matrix.png")

    # 3. 2D plots for each pair (if we have enough objectives)
    if n_objectives >= 2:
        print("   • Generating 2D Pareto front (first 2 objectives)...")
        fig3 = visualizer.plot_pareto_front_2d(
            objectives[:, :2],
            obj_names=obj_names[:2],
            best_idx=best_idx,
            title=f"Pareto Front - {obj_names[0]} vs {obj_names[1]}",
            save_path=f"{output_dir}/pareto_2d.png",
            show=False,
        )
        print(f"     ✓ Saved to {output_dir}/pareto_2d.png")

    # 4. 3D plot (if we have 3+ objectives)
    if n_objectives >= 3:
        print("   • Generating 3D Pareto front (first 3 objectives)...")
        fig4 = visualizer.plot_pareto_front_3d(
            objectives[:, :3],
            obj_names=obj_names[:3],
            best_idx=best_idx,
            title="Pareto Front - 3D View",
            save_path=f"{output_dir}/pareto_3d.png",
            show=False,
        )
        print(f"     ✓ Saved to {output_dir}/pareto_3d.png")

    print(f"\n   ✅ All visualizations saved to {output_dir}/")


def print_best_solution(result, buildings):
    """
    Print detailed information about the best solution.

    Args:
        result: Optimization result dictionary
        buildings: List of Building objects
    """
    if not result["best_compromise"]:
        print("\n⚠️  No best compromise solution found")
        return

    print("\n🏆 Best Compromise Solution Details:")
    print("=" * 60)

    best = result["best_compromise"]
    solution = best["solution"]

    print(f"\nSolution Index: {best['index']}")
    print(f"Objective Values: {best['objectives']}")
    print(f"Normalized Values: {best['normalized_objectives']}")

    print("\nBuilding Placements:")
    print("-" * 60)
    for building in buildings:
        pos = solution.positions.get(building.id)
        if pos:
            print(
                f"  {building.id:20} ({building.type.value:15}): " f"({pos[0]:7.2f}, {pos[1]:7.2f})"
            )

    print("=" * 60)


def main():
    """Main workflow execution."""
    print("=" * 70)
    print("NSGA-III Multi-Objective Optimization - Complete Workflow")
    print("=" * 70)

    # 1. Setup
    buildings = create_sample_buildings()
    bounds = (0, 0, 500, 500)  # 500m x 500m site

    # 2. Run optimization with Research-Enhanced profile
    result = run_optimization(buildings, bounds, ProfileType.RESEARCH_ENHANCED)

    # 3. Analyze results
    analyze_results(result)

    # 4. Generate visualizations
    obj_names = ["Cost", "Walking Distance", "Adjacency", "Diversity"]
    visualize_results(result, obj_names)

    # 5. Print best solution
    print_best_solution(result, buildings)

    # 6. Compare different profiles
    print("\n" + "=" * 70)
    print("Comparing Different Objective Profiles")
    print("=" * 70)

    profiles_to_compare = [
        ProfileType.STANDARD,
        ProfileType.RESEARCH_ENHANCED,
        ProfileType.FIFTEEN_MINUTE_CITY,
        ProfileType.CAMPUS_PLANNING,
    ]

    print("\nProfile Comparison:")
    print("-" * 70)
    for profile_type in profiles_to_compare:
        profile = get_profile(profile_type)
        print(f"\n{profile.name}:")
        print(f"  Enhanced: {profile.use_enhanced}")
        print(f"  Weights: {profile.weights}")
        print(f"  Description: {profile.description}")

    print("\n" + "=" * 70)
    print("✅ Workflow Complete!")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Check the generated plots in examples/output/")
    print("  2. Try different profiles by modifying the script")
    print("  3. Experiment with different building configurations")
    print("  4. Use the REST API for web-based workflows")
    print("\nFor REST API examples, see:")
    print("  - examples/api_usage_examples.py")
    print("  - Documentation at /docs (when API server is running)")
    print("=" * 70)


if __name__ == "__main__":
    main()
