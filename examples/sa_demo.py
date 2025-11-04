"""
Example: Using H-SAGA SA Phase with Performance Profiling
"""
import cProfile
import logging
import os
import pstats
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.algorithms.building import create_sample_campus  # noqa: E402
from src.algorithms.hsaga import HybridSAGA  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create sample campus
buildings = create_sample_campus()
bounds = (0.0, 0.0, 1000.0, 1000.0)

# Configure SA
sa_config = {
    "initial_temp": 1000.0,
    "final_temp": 0.1,
    "cooling_rate": 0.95,
    "max_iterations": 100,
    "num_chains": 2,  # Reduced for demo
    "chain_iterations": 100,  # Reduced for demo
}

# Run optimization with profiling
print("Starting H-SAGA SA optimization...")

# Profile the optimization
profiler = cProfile.Profile()
profiler.enable()

optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
result = optimizer.optimize()

profiler.disable()

# Save profile
os.makedirs("outputs", exist_ok=True)
profile_file = "outputs/sa_demo_profile.prof"
profiler.dump_stats(profile_file)
print(f"\nProfile saved to {profile_file}")

# Print top 20 functions
print("\n" + "=" * 60)
print("Performance Profile (Top 20 functions by cumulative time):")
print("=" * 60)
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(20)

print("\nResults:")
print(f"Best fitness: {result['fitness']:.4f}")
print(f"Time: {result['time']:.2f}s")
print(f"Solution: {result['best_solution']}")

# Display building positions
print("\nBuilding positions:")
for building_id, position in result["best_solution"].positions.items():
    print(f"  {building_id}: ({position[0]:.2f}, {position[1]:.2f})")
