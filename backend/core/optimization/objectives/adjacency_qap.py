"""
Quadratic Assignment Problem (QAP) for Building Adjacency
==========================================================

Implements QAP-based adjacency optimization to ensure preferred buildings
are placed near each other (e.g., library near classrooms, dorms near dining).

QAP formulation minimizes the weighted sum of distances between building pairs
where weights represent desired proximity strength.

References:
    - Koopmans & Beckmann (1957): Assignment problem formulation
    - Burkard et al. (2012): QAPLIB benchmark problems
    - Research: "Building Typology Spatial Optimization Research.docx"

Mathematical Formulation:
    minimize: Σ_ij w_ij * d_ij
    where:
        w_ij = adjacency weight between building types i and j
        d_ij = Euclidean distance between buildings i and j

Adjacency Matrix (w_ij):
    Higher weight = stronger desire for proximity
    Example: w[library, classroom] = 1.0 (high)
             w[library, warehouse] = 0.1 (low)

Created: 2026-01-01
"""

from typing import TYPE_CHECKING, Dict, List

import numpy as np

if TYPE_CHECKING:
    from backend.core.optimization.building import Building
    from backend.core.optimization.solution import Solution


# Adjacency preference matrix (symmetric)
# Values: 0.0 (no preference) to 1.0 (strong preference for proximity)
ADJACENCY_MATRIX = {
    # Academic buildings should be near each other
    ("academic", "academic"): 0.8,
    ("academic", "library"): 1.0,  # Strong preference
    ("academic", "research"): 0.9,
    ("academic", "administrative"): 0.7,
    # Residential near services
    ("residential", "dining"): 1.0,  # Critical
    ("residential", "library"): 0.7,
    ("residential", "health"): 0.8,
    ("residential", "social"): 0.9,
    ("residential", "sports"): 0.6,
    # Library central to academic activities
    ("library", "research"): 0.9,
    ("library", "administrative"): 0.5,
    # Dining near social spaces
    ("dining", "social"): 0.8,
    ("dining", "sports"): 0.5,
    # Health near residential
    ("health", "administrative"): 0.6,
    # Sports separate from academic
    ("sports", "academic"): 0.3,
    ("sports", "library"): 0.2,
    # Administrative central location
    ("administrative", "social"): 0.6,
    # Low-priority pairings
    ("residential", "warehouse"): 0.1,
    ("academic", "warehouse"): 0.1,
}


def get_adjacency_weight(type1: str, type2: str) -> float:
    """
    Get adjacency preference weight between two building types.

    Args:
        type1: First building type
        type2: Second building type

    Returns:
        Weight in [0, 1] where 1 = strong preference for proximity
    """
    # Check both orderings (matrix is symmetric)
    key1 = (type1, type2)
    key2 = (type2, type1)

    if key1 in ADJACENCY_MATRIX:
        return ADJACENCY_MATRIX[key1]
    elif key2 in ADJACENCY_MATRIX:
        return ADJACENCY_MATRIX[key2]
    else:
        # Default: neutral (0.5)
        return 0.5


def calculate_qap_cost(
    solution: "Solution",
    buildings: List["Building"],
) -> float:
    """
    Calculate QAP objective: weighted sum of distances.

    Lower cost = better adjacency satisfaction (preferred buildings are closer).

    Args:
        solution: Solution with building positions
        buildings: List of Building objects

    Returns:
        QAP cost (lower is better)

    Example:
        >>> solution = Solution(positions={'LIB': (0, 0), 'CLASS': (100, 0)})
        >>> cost = calculate_qap_cost(solution, buildings)
        >>> # High adjacency weight * 100m distance = high cost
    """
    total_cost = 0.0
    n_pairs = 0

    # For each pair of buildings
    for i, building_i in enumerate(buildings):
        if building_i.id not in solution.positions:
            continue

        pos_i = solution.positions[building_i.id]

        for j in range(i + 1, len(buildings)):
            building_j = buildings[j]

            if building_j.id not in solution.positions:
                continue

            pos_j = solution.positions[building_j.id]

            # Get adjacency weight
            weight = get_adjacency_weight(
                building_i.type.value,
                building_j.type.value,
            )

            # Calculate Euclidean distance
            distance = np.sqrt((pos_i[0] - pos_j[0]) ** 2 + (pos_i[1] - pos_j[1]) ** 2)

            # Add weighted distance to cost
            total_cost += weight * distance
            n_pairs += 1

    # Normalize by number of pairs to make score comparable across different problem sizes
    if n_pairs > 0:
        total_cost /= n_pairs

    return float(total_cost)


def maximize_adjacency_satisfaction(
    solution: "Solution",
    buildings: List["Building"],
) -> float:
    """
    Maximize adjacency satisfaction (QAP objective for optimization).

    Converts QAP cost to maximization objective normalized to [0, 1].

    Args:
        solution: Solution with building positions
        buildings: List of Building objects

    Returns:
        Satisfaction score [0, 1] where 1 = perfect adjacency

    Notes:
        - Uses QAP cost and normalizes based on typical campus dimensions
        - Assumes campus size ~1000m x 1000m
        - Max possible average distance ≈ 1000m (diagonal)
        - Typical good layout: average weighted distance ~300m
    """
    qap_cost = calculate_qap_cost(solution, buildings)

    # Normalize to [0, 1]
    # Lower cost = higher satisfaction
    # Assume max reasonable average weighted distance = 1000m (campus diagonal)
    # Assume ideal average weighted distance = 100m (buildings close)
    max_distance = 1000.0
    ideal_distance = 100.0

    if qap_cost <= ideal_distance:
        # Perfect score
        satisfaction = 1.0
    elif qap_cost >= max_distance:
        # Worst score
        satisfaction = 0.0
    else:
        # Linear interpolation
        satisfaction = 1.0 - (qap_cost - ideal_distance) / (max_distance - ideal_distance)

    return float(np.clip(satisfaction, 0.0, 1.0))


def get_adjacency_report(
    solution: "Solution",
    buildings: List["Building"],
) -> Dict:
    """
    Generate detailed adjacency analysis report for explainability.

    This provides transparency into QAP objective for user understanding.

    Args:
        solution: Solution with building positions
        buildings: List of Building objects

    Returns:
        Dictionary with adjacency statistics and pair-wise analysis

    Example:
        >>> report = get_adjacency_report(solution, buildings)
        >>> print(f"Overall satisfaction: {report['satisfaction']:.2f}")
        >>> for pair in report['critical_pairs']:
        ...     print(f"{pair['buildings']}: {pair['distance']:.0f}m (weight={pair['weight']:.1f})")
    """
    qap_cost = calculate_qap_cost(solution, buildings)
    satisfaction = maximize_adjacency_satisfaction(solution, buildings)

    # Collect pair-wise data
    pairs = []

    for i, building_i in enumerate(buildings):
        if building_i.id not in solution.positions:
            continue

        pos_i = solution.positions[building_i.id]

        for j in range(i + 1, len(buildings)):
            building_j = buildings[j]

            if building_j.id not in solution.positions:
                continue

            pos_j = solution.positions[building_j.id]

            # Get adjacency weight
            weight = get_adjacency_weight(
                building_i.type.value,
                building_j.type.value,
            )

            # Calculate distance
            distance = np.sqrt((pos_i[0] - pos_j[0]) ** 2 + (pos_i[1] - pos_j[1]) ** 2)

            pairs.append(
                {
                    "buildings": f"{building_i.id} - {building_j.id}",
                    "types": f"{building_i.type.value} - {building_j.type.value}",
                    "weight": weight,
                    "distance": distance,
                    "cost": weight * distance,
                }
            )

    # Sort by cost (worst pairs first)
    pairs.sort(key=lambda p: p["cost"], reverse=True)

    # Identify critical pairs (high weight + high distance = problem)
    critical_pairs = [p for p in pairs if p["weight"] >= 0.8 and p["distance"] > 300.0]

    # Identify good pairs (high weight + low distance = success)
    good_pairs = [p for p in pairs if p["weight"] >= 0.8 and p["distance"] <= 200.0]

    return {
        "qap_cost": qap_cost,
        "satisfaction": satisfaction,
        "n_pairs": len(pairs),
        "critical_pairs": critical_pairs,  # Problematic (need attention)
        "good_pairs": good_pairs,  # Successful (praise)
        "all_pairs": pairs,
        "summary": {
            "avg_distance": np.mean([p["distance"] for p in pairs]) if pairs else 0.0,
            "avg_weighted_distance": qap_cost,
            "n_critical_violations": len(critical_pairs),
            "n_good_placements": len(good_pairs),
        },
    }
