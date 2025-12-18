"""
Diagnostic script for objective functions.
Run: python scripts/diagnose_objectives.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from algorithms.building import Building, BuildingType
from algorithms.objectives import (
    maximize_adjacency_satisfaction,
    minimize_cost,
    minimize_walking_distance,
)
from algorithms.solution import Solution

# Create test solution
buildings = [
    Building("B00", BuildingType.RESIDENTIAL, 2000, 3),
    Building("B01", BuildingType.EDUCATIONAL, 2500, 4),
    Building("B02", BuildingType.LIBRARY, 3000, 2),
    Building("B03", BuildingType.RESIDENTIAL, 1800, 3),
    Building("B04", BuildingType.SPORTS, 3500, 2),
]

positions = {
    "B00": (100, 100),
    "B01": (200, 200),
    "B02": (300, 100),
    "B03": (100, 300),
    "B04": (250, 250),
}

solution = Solution(positions)

# Test objectives individually
print("=" * 60)
print("OBJECTIVE FUNCTION DIAGNOSTICS")
print("=" * 60)

# 1. Cost
cost_score = minimize_cost(solution, buildings)
print("\n1. Cost Objective:")
print(f"   Raw score: {cost_score:.4f}")
print("   Expected: 0.5-0.9 (lower construction cost = higher score)")

# 2. Walking Distance
walking_score = minimize_walking_distance(solution, buildings)
print("\n2. Walking Distance Objective:")
print(f"   Raw score: {walking_score:.4f}")
print("   Expected: 0.5-0.9 (shorter distances = higher score)")
print("   ⚠️  WARNING: If 0.0, function is broken!")

# Calculate centroid manually for verification
positions_array = np.array(list(positions.values()))
centroid = positions_array.mean(axis=0)
distances = np.linalg.norm(positions_array - centroid, axis=1)
avg_distance = distances.mean()
max_distance = distances.max()

print("\n   Manual Calculation:")
print(f"   - Centroid: ({centroid[0]:.1f}, {centroid[1]:.1f})")
print(f"   - Avg distance: {avg_distance:.1f} m")
print(f"   - Max distance: {max_distance:.1f} m")
print(f"   - Normalized score: {1.0 - (avg_distance / 1000.0):.4f}")

# 3. Adjacency
adjacency_score = maximize_adjacency_satisfaction(solution, buildings)
print("\n3. Adjacency Objective:")
print(f"   Raw score: {adjacency_score:.4f}")
print("   Expected: 0.3-0.7 (better type compatibility = higher score)")
print("   ⚠️  WARNING: If 0.0, function is broken!")

# Check building type pairs
print("\n   Building Type Pairs:")
for i, b1 in enumerate(buildings):
    for b2 in buildings[i + 1 :]:
        pos1 = positions[b1.id]
        pos2 = positions[b2.id]
        distance = np.linalg.norm(np.array(pos1) - np.array(pos2))
        print(f"   - {b1.type.name} <-> {b2.type.name}: {distance:.1f}m")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
