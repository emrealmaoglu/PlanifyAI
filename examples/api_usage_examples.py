"""
REST API Usage Examples
========================

Examples of using the PlanifyAI REST API for multi-objective optimization
and visualization.

Prerequisites:
    1. Start the API server:
       cd backend && uvicorn api.main:app --reload

    2. Install requests:
       pip install requests

Usage:
    python examples/api_usage_examples.py

API Documentation:
    - http://localhost:8000/docs (Swagger UI)
    - http://localhost:8000/redoc (ReDoc)

Created: 2026-01-03
"""

import base64
import os
import time

import requests

# API base URL
BASE_URL = "http://localhost:8000"


def check_api_health():
    """Check if API is running and healthy."""
    print("🔍 Checking API health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ API Status: {data['status']}")
            print(f"   ✓ Service: {data['service']}")
            return True
        else:
            print(f"   ✗ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ✗ API not reachable: {e}")
        print("\n   Please start the API server:")
        print("   cd backend && uvicorn api.main:app --reload")
        return False


def list_objective_profiles():
    """List available objective profiles."""
    print("\n📋 Listing available objective profiles...")
    response = requests.get(f"{BASE_URL}/api/nsga3/profiles")

    if response.status_code == 200:
        data = response.json()
        profiles = data["profiles"]
        print(f"   ✓ Found {len(profiles)} profiles:\n")
        for name, description in profiles.items():
            print(f"   • {name}")
            print(f"     {description}\n")
        return profiles
    else:
        print(f"   ✗ Failed to fetch profiles: {response.status_code}")
        return None


def run_nsga3_optimization(
    buildings: List[Dict],
    bounds: List[float],
    profile: str = "research_enhanced",
    population_size: int = 30,
    n_generations: int = 30,
):
    """
    Run NSGA-III optimization via API.

    Args:
        buildings: List of building specifications
        bounds: Site boundaries [x_min, y_min, x_max, y_max]
        profile: Objective profile name
        population_size: Population size
        n_generations: Number of generations

    Returns:
        Optimization result or None if failed
    """
    print(f"\n🚀 Running NSGA-III optimization...")
    print(f"   Profile: {profile}")
    print(f"   Population: {population_size}")
    print(f"   Generations: {n_generations}")

    request_data = {
        "buildings": buildings,
        "bounds": bounds,
        "population_size": population_size,
        "n_generations": n_generations,
        "objective_profile": profile,
        "seed": 42,
        "verbose": False,
    }

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/nsga3/optimize", json=request_data)
    elapsed = time.time() - start_time

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Optimization complete in {elapsed:.2f}s")
        print(f"   ✓ Pareto front size: {data['pareto_size']}")
        print(f"   ✓ Number of objectives: {data['n_objectives']}")
        print(f"   ✓ Evaluations: {data['evaluations']}")
        print(f"   ✓ Runtime: {data['runtime']:.2f}s")
        return data
    else:
        print(f"   ✗ Optimization failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def generate_visualization(
    objectives: List[List[float]],
    obj_names: List[str],
    best_index: int,
    viz_type: str = "parallel-coordinates",
    output_file: str = None,
):
    """
    Generate visualization via API.

    Args:
        objectives: Objective values
        obj_names: Objective names
        best_index: Index of best solution
        viz_type: Type of visualization
        output_file: Optional output file path

    Returns:
        True if successful, False otherwise
    """
    print(f"\n🎨 Generating {viz_type} visualization...")

    request_data = {
        "objectives": objectives,
        "objective_names": obj_names,
        "best_index": best_index,
        "title": f"Pareto Front - {viz_type.replace('-', ' ').title()}",
    }

    response = requests.post(f"{BASE_URL}/api/visualize/{viz_type}", json=request_data)

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Visualization generated")
        print(f"   ✓ Image size: {data['width']}x{data['height']}")

        if output_file:
            # Decode and save image
            img_data = base64.b64decode(data["image_base64"])
            with open(output_file, "wb") as f:
                f.write(img_data)
            print(f"   ✓ Saved to {output_file}")

        return True
    else:
        print(f"   ✗ Visualization failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def get_statistics(objectives: List[List[float]]):
    """
    Get statistical analysis via API.

    Args:
        objectives: Objective values

    Returns:
        Statistics data or None if failed
    """
    print(f"\n📊 Computing statistics...")

    request_data = {"objectives": objectives}

    response = requests.post(f"{BASE_URL}/api/visualize/statistics", json=request_data)

    if response.status_code == 200:
        data = response.json()
        stats = data["statistics"]

        print(f"   ✓ Statistics computed")
        print(f"\n   Min: {stats['min']}")
        print(f"   Max: {stats['max']}")
        print(f"   Mean: {stats['mean']}")
        print(f"   Std: {stats['std']}")
        print(f"   Median: {stats['median']}")
        print(f"\n   Hypervolume: {data['hypervolume']:.2f}")

        print(f"\n   Extreme Solutions:")
        for obj_key, sol_data in data["extreme_solutions"].items():
            print(f"   • {obj_key}: Solution #{sol_data['solution_index']}")

        return data
    else:
        print(f"   ✗ Statistics computation failed: {response.status_code}")
        return None


def main():
    """Main execution."""
    print("=" * 70)
    print("PlanifyAI REST API Usage Examples")
    print("=" * 70)

    # Check API health
    if not check_api_health():
        return

    # List available profiles
    list_objective_profiles()

    # Define sample buildings
    buildings = [
        {"name": "Library", "building_type": "EDUCATIONAL", "area": 2000, "floors": 3},
        {"name": "Dorm_A", "building_type": "RESIDENTIAL", "area": 3000, "floors": 5},
        {"name": "Dorm_B", "building_type": "RESIDENTIAL", "area": 3000, "floors": 5},
        {"name": "Cafeteria", "building_type": "DINING", "area": 1500, "floors": 2},
    ]

    bounds = [0, 0, 400, 400]

    # Run optimization
    result = run_nsga3_optimization(
        buildings=buildings,
        bounds=bounds,
        profile="research_enhanced",
        population_size=30,
        n_generations=30,
    )

    if not result:
        print("\n❌ Optimization failed, stopping workflow")
        return

    # Extract objectives
    objectives = result["pareto_objectives"]
    best_idx = result["best_compromise"]["index"] if result["best_compromise"] else 0
    obj_names = ["Cost", "Walking Distance", "Adjacency", "Diversity"]

    # Generate visualizations
    import os

    output_dir = "examples/api_output"
    os.makedirs(output_dir, exist_ok=True)

    # 1. Parallel coordinates
    generate_visualization(
        objectives=objectives,
        obj_names=obj_names,
        best_index=best_idx,
        viz_type="parallel-coordinates",
        output_file=f"{output_dir}/api_parallel.png",
    )

    # 2. Objective matrix
    generate_visualization(
        objectives=objectives,
        obj_names=obj_names,
        best_index=best_idx,
        viz_type="objective-matrix",
        output_file=f"{output_dir}/api_matrix.png",
    )

    # 3. 2D plot (first 2 objectives)
    objectives_2d = [obj[:2] for obj in objectives]
    generate_visualization(
        objectives=objectives_2d,
        obj_names=obj_names[:2],
        best_index=best_idx,
        viz_type="pareto-2d",
        output_file=f"{output_dir}/api_2d.png",
    )

    # 4. 3D plot (first 3 objectives)
    objectives_3d = [obj[:3] for obj in objectives]
    generate_visualization(
        objectives=objectives_3d,
        obj_names=obj_names[:3],
        best_index=best_idx,
        viz_type="pareto-3d",
        output_file=f"{output_dir}/api_3d.png",
    )

    # Get statistics
    stats = get_statistics(objectives=objectives)

    # Print best solution
    if result["best_compromise"]:
        print("\n🏆 Best Compromise Solution:")
        best = result["best_compromise"]
        print(f"   Index: {best['index']}")
        print(f"   Objectives: {best['objectives']}")
        print(f"   Normalized: {best['normalized_objectives']}")

        print(f"\n   Building Positions:")
        for building_data in best["buildings"]:
            print(
                f"   • {building_data['name']:15} "
                f"({building_data['x']:.2f}, {building_data['y']:.2f})"
            )

    print("\n" + "=" * 70)
    print("✅ API Workflow Complete!")
    print("=" * 70)
    print(f"\nGenerated files in {output_dir}/:")
    print("  • api_parallel.png - Parallel coordinates plot")
    print("  • api_matrix.png - Objective trade-off matrix")
    print("  • api_2d.png - 2D Pareto front")
    print("  • api_3d.png - 3D Pareto front")
    print("\nAPI Documentation:")
    print("  • http://localhost:8000/docs (Swagger UI)")
    print("  • http://localhost:8000/redoc (ReDoc)")
    print("=" * 70)


if __name__ == "__main__":
    main()
