"""
Research-Based Objective Functions for Campus Planning
=====================================================

Implements three core objectives based on research synthesis:

1. minimize_cost: Construction cost minimization
2. minimize_walking_distance: 15-minute city accessibility
3. maximize_adjacency_satisfaction: Building type compatibility

Research Sources:
- Construction_Cost_and_NPV_Optimization_Guide.docx
- 15-Minute_City_Optimization_Analysis.docx
- Building_Typology_Spatial_Optimization_Research.docx

Created: 2025-11-06 (Day 3)
Author: PlanifyAI Team
"""

import logging
from typing import Dict, List, Optional

import numpy as np
from scipy.spatial.distance import cdist

from .building import Building, BuildingType
from .solution import Solution

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS (from research)
# ============================================================================


class CostRates:
    """Construction cost rates (TL/m²)"""

    RATES = {
        BuildingType.RESIDENTIAL: 1500,
        BuildingType.EDUCATIONAL: 2000,
        BuildingType.ADMINISTRATIVE: 1800,
        BuildingType.HEALTH: 2500,
        BuildingType.SOCIAL: 1600,
        BuildingType.COMMERCIAL: 2200,
        BuildingType.LIBRARY: 2300,
        BuildingType.SPORTS: 1900,
        BuildingType.DINING: 1700,
    }
    DEFAULT = 1500
    REFERENCE_TOTAL = 100_000_000  # TL


class WalkingDistance:
    """15-minute city parameters (meters)"""

    IDEAL = 200.0
    MAX_ACCEPTABLE = 800.0


class AdjacencyParams:
    """Building adjacency parameters"""

    REFERENCE_DISTANCE = 100.0  # meters
    MAX_DISTANCE = 500.0  # meters (cutoff for efficiency)

    MATRIX = {
        (BuildingType.RESIDENTIAL, BuildingType.EDUCATIONAL): 5.0,
        (BuildingType.RESIDENTIAL, BuildingType.SOCIAL): 4.0,
        (BuildingType.RESIDENTIAL, BuildingType.HEALTH): -3.0,
        (BuildingType.EDUCATIONAL, BuildingType.ADMINISTRATIVE): 3.0,
        (BuildingType.EDUCATIONAL, BuildingType.SOCIAL): 2.0,
        (BuildingType.EDUCATIONAL, BuildingType.LIBRARY): 4.0,
        (BuildingType.HEALTH, BuildingType.HEALTH): -5.0,
        (BuildingType.COMMERCIAL, BuildingType.RESIDENTIAL): 3.0,
        (BuildingType.DINING, BuildingType.RESIDENTIAL): 4.0,
        (BuildingType.DINING, BuildingType.EDUCATIONAL): 3.0,
    }


# ============================================================================
# OBJECTIVE FUNCTIONS
# ============================================================================


def minimize_cost(
    solution: Solution, buildings: List[Building], params: Optional[Dict] = None
) -> float:
    """
    Minimize total construction cost.

    Formula:
        total = Σ(area_i × rate_i)
        normalized = total / reference_total
        return clip(normalized, 0, 1)

    Args:
        solution: Solution (positions needed for validation only)
        buildings: List of buildings with type and area
        params: Optional params (reference_total override)

    Returns:
        Cost score ∈ [0, 1], lower is better

    Example:
        >>> buildings = [Building("B1", BuildingType.RESIDENTIAL, 1000, 2)]
        >>> solution = Solution(positions={"B1": (100, 100)})
        >>> cost = minimize_cost(solution, buildings)
        >>> print(f"Cost: {cost:.4f}")
        Cost: 0.0150
    """
    if params is None:
        params = {}

    reference = params.get("reference_total", CostRates.REFERENCE_TOTAL)

    # Calculate total cost (vectorized)
    total_cost = sum(
        building.area * CostRates.RATES.get(building.type, CostRates.DEFAULT)
        for building in buildings
    )

    # Normalize and clip
    normalized = np.clip(total_cost / reference, 0.0, 1.0)

    logger.debug(f"cost: total={total_cost:.0f} TL, normalized={normalized:.4f}")

    return float(normalized)


def minimize_walking_distance(
    solution: Solution, buildings: List[Building], params: Optional[Dict] = None
) -> float:
    """
    Minimize average walking distance (Residential ↔ Educational).

    Formula:
        avg_dist = mean(cdist(residential, educational))
        normalized = (avg_dist - 200) / (800 - 200)
        return clip(normalized, 0, 1)

    Args:
        solution: Solution with positions
        buildings: List of buildings
        params: Optional params (ideal/max override)

    Returns:
        Distance score ∈ [0, 1], lower is better

    Example:
        >>> buildings = [
        ...     Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
        ...     Building("E1", BuildingType.EDUCATIONAL, 1000, 2)
        ... ]
        >>> solution = Solution(positions={"R1": (0, 0), "E1": (200, 0)})
        >>> dist = minimize_walking_distance(solution, buildings)
        >>> print(f"Distance: {dist:.4f}")
        Distance: 0.0000
    """
    if params is None:
        params = {}

    ideal = params.get("ideal", WalkingDistance.IDEAL)
    max_dist = params.get("max", WalkingDistance.MAX_ACCEPTABLE)

    # Filter by type
    residential = [b for b in buildings if b.type == BuildingType.RESIDENTIAL]
    educational = [b for b in buildings if b.type == BuildingType.EDUCATIONAL]

    # Early return if no pairs
    if not residential or not educational:
        logger.debug(f"walking: no pairs (res={len(residential)}, edu={len(educational)})")
        return 0.0

    # Extract positions
    res_pos = np.array([solution.positions[b.id] for b in residential])
    edu_pos = np.array([solution.positions[b.id] for b in educational])

    # Calculate pairwise distances using cdist (optimized)
    distances = cdist(res_pos, edu_pos, metric="euclidean")
    avg_dist = np.mean(distances)

    # Normalize
    normalized = (avg_dist - ideal) / (max_dist - ideal)
    normalized = np.clip(normalized, 0.0, 1.0)

    logger.debug(f"walking: avg={avg_dist:.1f}m, normalized={normalized:.4f}")

    return float(normalized)


def maximize_adjacency_satisfaction(
    solution: Solution, buildings: List[Building], params: Optional[Dict] = None
) -> float:
    """
    Maximize building type adjacency satisfaction.

    Formula:
        For positive weight: sat = weight / (1 + dist/100)
        For negative weight: sat = |weight| * (dist/100)

        ratio = Σ(sat) / Σ(|weight|)
        dissatisfaction = 1 - ratio
        return clip(dissatisfaction, 0, 1)

    Args:
        solution: Solution with positions
        buildings: List of buildings
        params: Optional params (adjacency_matrix override)

    Returns:
        Dissatisfaction score ∈ [0, 1], lower is better

    Example:
        >>> buildings = [
        ...     Building("R1", BuildingType.RESIDENTIAL, 1000, 2),
        ...     Building("E1", BuildingType.EDUCATIONAL, 1000, 2)
        ... ]
        >>> solution = Solution(positions={"R1": (0, 0), "E1": (100, 0)})
        >>> adj = maximize_adjacency_satisfaction(solution, buildings)
        >>> print(f"Adjacency: {adj:.4f}")
        Adjacency: 0.1667
    """
    if params is None:
        params = {}

    matrix = params.get("adjacency_matrix", AdjacencyParams.MATRIX)
    ref_dist = params.get("reference_distance", AdjacencyParams.REFERENCE_DISTANCE)
    max_dist = params.get("max_distance", AdjacencyParams.MAX_DISTANCE)

    # Build lookup (sorted keys for consistent access)
    lookup = {}
    for (t1, t2), weight in matrix.items():
        # Sort by enum value (name) for consistent keys
        key = tuple(sorted([t1, t2], key=lambda x: x.value))
        lookup[key] = weight

    # Calculate all pairwise distances once (optimized)
    positions = np.array([solution.positions[b.id] for b in buildings])
    dist_matrix = cdist(positions, positions, metric="euclidean")

    total_satisfaction = 0.0
    max_satisfaction = 0.0
    pairs_considered = 0

    # Iterate upper triangle only (avoid duplicate pairs)
    for i in range(len(buildings)):
        for j in range(i + 1, len(buildings)):
            b1, b2 = buildings[i], buildings[j]
            distance = dist_matrix[i, j]

            # Skip if too far (optimization)
            if distance > max_dist:
                continue

            # Get weight (sort by enum value for consistent lookup)
            key = tuple(sorted([b1.type, b2.type], key=lambda x: x.value))
            weight = lookup.get(key, 0.0)

            if abs(weight) < 1e-6:
                continue

            # Calculate satisfaction based on weight sign
            if weight > 0:
                # Positive: closer is better
                # Formula: satisfaction = weight / (1 + distance / reference_distance)
                satisfaction = weight / (1.0 + distance / ref_dist)
            else:
                # Negative: farther is better
                # Formula: satisfaction = |weight| * (distance / reference_distance)
                satisfaction = abs(weight) * (distance / ref_dist)

            total_satisfaction += satisfaction
            max_satisfaction += abs(weight)
            pairs_considered += 1

    # Handle no valid pairs
    if max_satisfaction < 1e-6:
        logger.debug("adjacency: no valid pairs")
        return 0.0

    # Calculate dissatisfaction (to minimize)
    ratio = total_satisfaction / max_satisfaction
    dissatisfaction = 1.0 - ratio
    dissatisfaction = np.clip(dissatisfaction, 0.0, 1.0)

    logger.debug(
        f"adjacency: pairs={pairs_considered}, ratio={ratio:.3f}, " f"diss={dissatisfaction:.4f}"
    )

    return float(dissatisfaction)
