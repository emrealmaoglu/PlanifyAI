"""
Coupled objectives that connect roads and buildings.
"""

import numpy as np
from typing import List, Dict, Any


def calculate_road_accessibility(
    buildings: List[Dict[str, Any]],
    roads: List[np.ndarray],
    penalty_per_meter: float = 0.1
) -> float:
    """
    Calculate road accessibility objective.
    
    Measures average distance from buildings to nearest road.
    Lower is better (buildings closer to roads).
    
    Args:
        buildings: List of building dicts with 'position' key
        roads: List of road polylines (np.ndarray)
        penalty_per_meter: Weight for distance penalty
        
    Returns:
        Accessibility score (minimize)
    """
    if not roads or not buildings:
        return 1e6  # Penalty for invalid configuration
    
    # Collect all road points
    try:
        road_points = np.vstack(roads)
    except ValueError:
        return 1e6 # Handle case where roads list contains empty arrays or is malformed

    if len(road_points) == 0:
         return 1e6
    
    total_distance = 0.0
    
    for building in buildings:
        pos = building['position']
        
        # Find nearest road point
        distances = np.linalg.norm(road_points - pos, axis=1)
        min_distance = np.min(distances)
        
        total_distance += min_distance
    
    # Average distance with penalty
    avg_distance = total_distance / len(buildings)
    
    return avg_distance * penalty_per_meter


def calculate_road_coverage(
    buildings: List[Dict[str, Any]],
    roads: List[np.ndarray],
    max_service_distance: float = 100.0
) -> float:
    """
    Calculate percentage of buildings within service distance of roads.
    
    Higher is better (more buildings serviced).
    
    Args:
        buildings: List of building dicts
        roads: List of road polylines
        max_service_distance: Maximum acceptable distance (meters)
        
    Returns:
        Coverage ratio in [0, 1] (maximize = minimize negative)
    """
    if not roads or not buildings:
        return 0.0
    
    try:
        road_points = np.vstack(roads)
    except ValueError:
        return 0.0

    if len(road_points) == 0:
        return 0.0
    
    serviced_count = 0
    
    for building in buildings:
        pos = building['position']
        distances = np.linalg.norm(road_points - pos, axis=1)
        min_distance = np.min(distances)
        
        if min_distance <= max_service_distance:
            serviced_count += 1
    
    coverage = serviced_count / len(buildings)
    
    # Return negative for minimization framework
    return -coverage


def calculate_road_efficiency(
    roads: List[np.ndarray],
    buildings: List[Dict[str, Any]]
) -> float:
    """
    Calculate road network efficiency.
    
    Penalizes excessive road length relative to building count.
    Lower is better (efficient road usage).
    
    Args:
        roads: List of road polylines
        buildings: List of building dicts
        
    Returns:
        Efficiency score (minimize)
    """
    if not roads:
        return 1e6
    
    # Total road length
    total_length = 0.0
    for road in roads:
        if len(road) > 1:
            segments = np.diff(road, axis=0)
            total_length += np.sum(np.linalg.norm(segments, axis=1))
    
    # Buildings per km of road (higher is better)
    if total_length > 0:
        efficiency = len(buildings) / (total_length / 1000)
        return -efficiency  # Negative for maximization
    else:
        return 1e6

def calculate_walkability_score(buildings, roads):
    """Combines accessibility + clustering."""
    access = calculate_road_accessibility(buildings, roads)
    
    if len(buildings) >= 2:
        positions = np.array([b['position'] for b in buildings])
        dists = np.linalg.norm(positions[:, None] - positions[None, :], axis=2)
        mask = ~np.eye(len(buildings), dtype=bool)
        clustering = np.mean(dists[mask])
    else:
        clustering = 0
    
    return 0.7 * access + 0.3 * clustering

def calculate_solar_exposure(buildings):
    """Penalizes non-south orientations."""
    if not buildings:
        return 0
    
    optimal = np.pi  # South
    total = sum(
        min(abs(b.get('orientation', 0) - optimal),
            abs(b.get('orientation', 0) - optimal + 2*np.pi))
        for b in buildings
    )
    return total / len(buildings)
