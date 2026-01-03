"""
NSGA-III Multi-Objective Optimization
======================================

Reference-point based evolutionary algorithm for many-objective optimization.

Based on:
Deb, K., & Jain, H. (2014). "An Evolutionary Many-Objective Optimization
Algorithm Using Reference-Point-Based Nondominated Sorting Approach,
Part I: Solving Problems With Box Constraints."
IEEE Transactions on Evolutionary Computation, 18(4), 577-601.

Created: 2026-01-02 (Week 4 Day 4)
"""

from .niching import (
    adaptive_nadir_estimation,
    associate_to_reference_points,
    compute_ideal_point,
    compute_nadir_point,
    niche_preserving_selection,
    normalize_objectives,
    perpendicular_distance,
)
from .nondominated_sort import (
    crowding_distance,
    dominates_objective,
    fast_nondominated_sort,
    pareto_front_2d_indices,
    select_best_solutions,
)
from .nsga3 import NSGA3
from .reference_points import (
    count_reference_points,
    generate_reference_points,
    generate_two_layer_reference_points,
    get_recommended_partitions,
)

__all__ = [
    # Main optimizer
    "NSGA3",
    # Reference points
    "generate_reference_points",
    "generate_two_layer_reference_points",
    "count_reference_points",
    "get_recommended_partitions",
    # Non-dominated sorting
    "fast_nondominated_sort",
    "dominates_objective",
    "crowding_distance",
    "select_best_solutions",
    "pareto_front_2d_indices",
    # Niching
    "normalize_objectives",
    "associate_to_reference_points",
    "perpendicular_distance",
    "niche_preserving_selection",
    "compute_ideal_point",
    "compute_nadir_point",
    "adaptive_nadir_estimation",
]
