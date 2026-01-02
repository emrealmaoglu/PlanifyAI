"""
Accessibility Objective for Campus Planning
============================================

Maximizes spatial accessibility using 2SFCA (Two-Step Floating Catchment Area).

This objective ensures that demand buildings (dorms, academic) have good access
to service buildings (library, dining, health).

References:
    - Luo & Wang (2003): Measures of spatial accessibility
    - Research: "Campus Planning Standards"

Created: 2026-01-01
"""

from typing import TYPE_CHECKING, List

from backend.core.metrics.accessibility import calculate_accessibility_scores

if TYPE_CHECKING:
    from backend.core.optimization.building import Building
    from backend.core.optimization.solution import Solution


def maximize_accessibility(
    solution: "Solution",
    buildings: List["Building"],
    catchment_radius: float = 400.0,
) -> float:
    """
    Maximize campus-wide spatial accessibility using 2SFCA.

    Higher score = better access to services for all demand points.

    Args:
        solution: Solution with building positions
        buildings: List of Building objects
        catchment_radius: Maximum walkable distance (meters, default: 400m)

    Returns:
        Accessibility score [0, 1] where 1 = perfect accessibility

    Example:
        >>> solution = Solution(positions={'LIB': (0, 0), 'DORM': (200, 0)})
        >>> score = maximize_accessibility(solution, buildings)
        >>> # Higher score if DORM has good access to LIB
    """
    # Assign positions from solution to buildings
    positioned_buildings = []

    for building in buildings:
        if building.id in solution.positions:
            # Create copy with position
            b_copy = building.copy() if hasattr(building, "copy") else building
            b_copy.position = solution.positions[building.id]
            positioned_buildings.append(b_copy)

    # Calculate 2SFCA scores
    scores = calculate_accessibility_scores(
        positioned_buildings,
        catchment_radius=catchment_radius,
    )

    if not scores:
        return 0.0

    # Aggregate to single score (mean accessibility)
    mean_score = sum(scores.values()) / len(scores)

    # Normalize to [0, 1] range
    # Typical accessibility scores range from 0 to ~2.0
    # We'll normalize assuming max score of 2.0
    normalized_score = min(1.0, mean_score / 2.0)

    return float(normalized_score)
