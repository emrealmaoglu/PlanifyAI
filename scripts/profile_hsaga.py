"""
Profile H-SAGA performance to identify bottlenecks.

Usage: python scripts/profile_hsaga.py
"""
import cProfile
import io
import os
import pstats
import sys
from pathlib import Path
from pstats import SortKey

# Add project root to path (must be before other imports)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np  # noqa: E402

from src.algorithms.building import Building, BuildingType  # noqa: E402
from src.algorithms.hsaga import HybridSAGA  # noqa: E402


def profile_optimization():
    """Profile a typical optimization run"""
    # Create test case
    np.random.seed(42)
    buildings = []
    types = list(BuildingType)

    for i in range(10):
        btype = np.random.choice(types)
        area = np.random.uniform(1500, 3500)
        floors = np.random.randint(2, 5)
        buildings.append(Building(f"B{i:02d}", btype, area, floors))

    optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

    # Profile
    profiler = cProfile.Profile()
    profiler.enable()

    optimizer.optimize()

    profiler.disable()

    # Print results
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats(SortKey.CUMULATIVE)
    ps.print_stats(30)  # Top 30 functions

    print("\n" + "=" * 70)
    print("🔍 PROFILING RESULTS (Top 30 functions by cumulative time)")
    print("=" * 70 + "\n")
    print(s.getvalue())

    # Save to file
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/profile_results.txt", "w") as f:
        ps = pstats.Stats(profiler, stream=f).sort_stats(SortKey.CUMULATIVE)
        ps.print_stats(50)

    print("\n✅ Full profile saved to outputs/profile_results.txt")

    # Analyze hotspots
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats(SortKey.TIME)
    ps.print_stats(10)

    print("\n" + "=" * 70)
    print("🔥 HOTSPOTS (Top 10 functions by internal time)")
    print("=" * 70 + "\n")
    print(s.getvalue())


if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    profile_optimization()
