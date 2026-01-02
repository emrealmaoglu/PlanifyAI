"""
Network Connectivity Objective for Campus Planning
===================================================

Maximizes road network connectivity using Kansky indices.

This objective ensures the generated road network has good topology:
- Multiple paths between locations (redundancy)
- Efficient average road length
- High connectivity ratio

References:
    - Kansky, K. J. (1963): Structure of transportation networks
    - Research: "Campus Planning Standards"

Created: 2026-01-01
"""

from typing import TYPE_CHECKING, Dict, List

import numpy as np

from backend.core.metrics.connectivity import (
    calculate_network_connectivity,
    connectivity_quality_score,
)

if TYPE_CHECKING:
    from backend.core.optimization.building import Building
    from backend.core.optimization.solution import Solution


def maximize_network_connectivity(
    solution: "Solution",
    buildings: List["Building"],
    road_network_data: Dict = None,
) -> float:
    """
    Maximize road network connectivity using Kansky indices.

    Higher score = better connected, more redundant road network.

    Args:
        solution: Solution with building positions
        buildings: List of Building objects
        road_network_data: Optional dict with 'major_roads' and 'minor_roads'
                          If None, assumes roads are stored in solution

    Returns:
        Connectivity score [0, 1] where 1 = excellent connectivity

    Example:
        >>> solution = Solution(positions={...})
        >>> solution.major_roads = [road1, road2, ...]
        >>> solution.minor_roads = [road3, road4, ...]
        >>> score = maximize_network_connectivity(solution, buildings)
    """
    # Get road network
    if road_network_data is not None:
        major_roads = road_network_data.get("major_roads", [])
        minor_roads = road_network_data.get("minor_roads", [])
    elif hasattr(solution, "major_roads") and hasattr(solution, "minor_roads"):
        major_roads = solution.major_roads
        minor_roads = solution.minor_roads
    else:
        # No road network available - return neutral score
        return 0.5

    if not major_roads and not minor_roads:
        # Empty network - return low score
        return 0.1

    # Calculate Kansky indices
    indices = calculate_network_connectivity(major_roads, minor_roads)

    # Convert to quality score
    score = connectivity_quality_score(indices)

    return float(score)


def penalize_disconnected_buildings(
    solution: "Solution",
    buildings: List["Building"],
    max_distance_to_road: float = 100.0,
) -> float:
    """
    Penalize buildings that are too far from road network.

    Returns penalty [0, 1] where 0 = all buildings connected, 1 = many disconnected.

    Args:
        solution: Solution with building positions
        buildings: List of Building objects
        max_distance_to_road: Maximum acceptable distance (meters, default: 100m)

    Returns:
        Penalty score [0, 1]
    """
    # Get road network
    if not hasattr(solution, "major_roads") or not hasattr(solution, "minor_roads"):
        # No road network - assume all buildings disconnected
        return 1.0

    major_roads = solution.major_roads
    minor_roads = solution.minor_roads
    all_roads = major_roads + minor_roads

    if not all_roads:
        return 1.0

    # Check each building's distance to nearest road
    disconnected_count = 0

    for building in buildings:
        if building.id not in solution.positions:
            continue

        bx, by = solution.positions[building.id]

        # Find minimum distance to any road
        min_distance = float("inf")

        for road in all_roads:
            if len(road) < 2:
                continue

            # Calculate distance to road polyline
            for i in range(len(road) - 1):
                p1 = road[i]
                p2 = road[i + 1]

                # Distance from point to line segment
                distance = _point_to_segment_distance((bx, by), p1, p2)
                min_distance = min(min_distance, distance)

        # Check if building is disconnected
        if min_distance > max_distance_to_road:
            disconnected_count += 1

    # Calculate penalty ratio
    if len(buildings) == 0:
        return 0.0

    penalty = disconnected_count / len(buildings)

    return float(penalty)


def _point_to_segment_distance(point, seg_start, seg_end) -> float:
    """
    Calculate minimum distance from point to line segment.

    Args:
        point: (x, y) tuple
        seg_start: (x, y) tuple
        seg_end: (x, y) tuple

    Returns:
        Minimum distance in same units as coordinates
    """
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end

    # Vector from seg_start to seg_end
    dx = x2 - x1
    dy = y2 - y1

    # If segment has zero length, return distance to point
    seg_length_sq = dx * dx + dy * dy
    if seg_length_sq < 1e-10:
        return np.sqrt((px - x1) ** 2 + (py - y1) ** 2)

    # Calculate projection parameter t
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / seg_length_sq))

    # Find closest point on segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Distance to closest point
    distance = np.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

    return float(distance)
