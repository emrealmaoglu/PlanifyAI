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
    Minimize average walking distance to campus centroid (accessibility).

    Lower average distance = higher score (0.0 to 1.0)

    Args:
        solution: Building placement solution
        buildings: List of buildings
        params: Optional params (campus_size override)

    Returns:
        Score from 0.0 (worst) to 1.0 (best)

    Example:
        - 50m avg distance → 0.95 score (excellent)
        - 200m avg distance → 0.80 score (good)
        - 500m avg distance → 0.50 score (poor)
    """
    if params is None:
        params = {}

    campus_size = params.get("campus_size", 1000.0)

    if not solution.positions:
        return 0.0

    # Calculate campus centroid
    positions = np.array(list(solution.positions.values()))
    centroid = positions.mean(axis=0)

    # Calculate distances to centroid
    distances = np.linalg.norm(positions - centroid, axis=1)
    avg_distance = distances.mean()
    max_distance = distances.max()

    # Normalize: closer = better
    # Use exponential decay for better discrimination
    normalized_avg = np.clip(avg_distance / campus_size, 0.0, 1.0)
    normalized_max = np.clip(max_distance / (campus_size * 1.5), 0.0, 1.0)

    # Weighted combination (avg more important than max)
    score = 0.7 * (1.0 - normalized_avg) + 0.3 * (1.0 - normalized_max)

    logger.debug(f"walking: avg={avg_distance:.1f}m, max={max_distance:.1f}m, score={score:.4f}")

    return float(np.clip(score, 0.0, 1.0))


def maximize_adjacency_satisfaction(
    solution: Solution, buildings: List[Building], params: Optional[Dict] = None
) -> float:
    """
    Maximize adjacency satisfaction based on building type compatibility.

    Buildings with high compatibility should be closer together.
    Compatibility based on semantic relationships (research-based).

    Args:
        solution: Building placement solution
        buildings: List of buildings
        params: Optional params (ideal_distance override)

    Returns:
        Score from 0.0 (worst) to 1.0 (best)

    Compatibility Matrix (research-based):
        RESIDENTIAL <-> EDUCATIONAL: 0.8 (students near classes)
        RESIDENTIAL <-> SPORTS: 0.7 (recreation nearby)
        RESIDENTIAL <-> HEALTH: 0.6 (healthcare access)
        RESIDENTIAL <-> LIBRARY: 0.7 (study resources)
        EDUCATIONAL <-> LIBRARY: 0.9 (study resources)
        EDUCATIONAL <-> ADMINISTRATIVE: 0.7 (academic admin)
        SPORTS <-> HEALTH: 0.6 (fitness + wellness)
        All others: 0.3 (neutral)
    """
    if params is None:
        params = {}

    ideal_distance = params.get("ideal_distance", 100.0)

    if len(buildings) < 2:
        return 1.0

    # Compatibility matrix (symmetric)
    compatibility = {
        (BuildingType.RESIDENTIAL, BuildingType.EDUCATIONAL): 0.8,
        (BuildingType.RESIDENTIAL, BuildingType.SPORTS): 0.7,
        (BuildingType.RESIDENTIAL, BuildingType.HEALTH): 0.6,
        (BuildingType.RESIDENTIAL, BuildingType.LIBRARY): 0.7,
        (BuildingType.EDUCATIONAL, BuildingType.LIBRARY): 0.9,
        (BuildingType.EDUCATIONAL, BuildingType.ADMINISTRATIVE): 0.7,
        (BuildingType.SPORTS, BuildingType.HEALTH): 0.6,
        (BuildingType.LIBRARY, BuildingType.ADMINISTRATIVE): 0.5,
    }

    total_satisfaction = 0.0
    pair_count = 0

    # Calculate satisfaction for each building pair
    for i, b1 in enumerate(buildings):
        for b2 in buildings[i + 1 :]:
            # Get positions
            pos1 = np.array(solution.positions[b1.id])
            pos2 = np.array(solution.positions[b2.id])
            distance = np.linalg.norm(pos1 - pos2)

            # Get compatibility (check both directions)
            comp = compatibility.get((b1.type, b2.type), compatibility.get((b2.type, b1.type), 0.3))

            # Distance satisfaction (Gaussian decay)
            # Ideal distance = 100m, compatible buildings should be close
            distance_satisfaction = np.exp(
                -((distance - ideal_distance) ** 2) / (2 * (ideal_distance * 0.5) ** 2)
            )

            # Combined satisfaction
            satisfaction = comp * distance_satisfaction
            total_satisfaction += satisfaction
            pair_count += 1

    # Normalize by number of pairs
    if pair_count == 0:
        return 1.0

    avg_satisfaction = total_satisfaction / pair_count

    # Scale to [0, 1] (max possible satisfaction ≈ 0.9 * 1.0 = 0.9)
    score = np.clip(avg_satisfaction / 0.9, 0.0, 1.0)

    logger.debug(
        f"adjacency: pairs={pair_count}, avg_satisfaction={avg_satisfaction:.3f}, score={score:.4f}"
    )

    return float(score)
