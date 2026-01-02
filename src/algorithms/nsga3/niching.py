"""
Niche Preservation for NSGA-III
================================

Reference-point based niching for maintaining diversity in many-objective optimization.

This is the key difference between NSGA-II and NSGA-III:
- NSGA-II: Crowding distance (poor for many objectives)
- NSGA-III: Reference point association (scales to many objectives)

Reference:
Deb, K., & Jain, H. (2014). "An Evolutionary Many-Objective Optimization
Algorithm Using Reference-Point-Based Nondominated Sorting Approach."

Created: 2026-01-02 (Week 4 Day 4)
"""

from typing import List, Tuple

import numpy as np


def normalize_objectives(
    objectives: np.ndarray,
    ideal_point: np.ndarray,
    nadir_point: np.ndarray,
    epsilon: float = 1e-10,
) -> np.ndarray:
    """
    Normalize objectives to [0, 1] range using ideal and nadir points.

    Args:
        objectives: Array of shape (n_solutions, n_objectives)
        ideal_point: Best values for each objective (array of shape (n_objectives,))
        nadir_point: Worst values for each objective (array of shape (n_objectives,))
        epsilon: Small value to avoid division by zero

    Returns:
        Normalized objectives array of same shape

    Example:
        >>> objectives = np.array([[1, 5], [2, 4], [3, 3]])
        >>> ideal = np.array([1, 3])
        >>> nadir = np.array([3, 5])
        >>> norm = normalize_objectives(objectives, ideal, nadir)
        >>> print(norm)  # [[0, 1], [0.5, 0.5], [1, 0]]
    """
    # Avoid division by zero
    ranges = np.maximum(nadir_point - ideal_point, epsilon)

    # Normalize: (obj - ideal) / (nadir - ideal)
    normalized = (objectives - ideal_point) / ranges

    return normalized


def associate_to_reference_points(
    normalized_objectives: np.ndarray,
    reference_points: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Associate each solution to its closest reference point.

    Uses perpendicular distance from solution to reference line.

    Args:
        normalized_objectives: Array of shape (n_solutions, n_objectives)
        reference_points: Array of shape (n_ref_points, n_objectives)

    Returns:
        Tuple of (associations, distances) where:
        - associations: Array of shape (n_solutions,) with reference point indices
        - distances: Array of shape (n_solutions,) with perpendicular distances

    Example:
        >>> objectives = np.array([[0.5, 0.5], [0.8, 0.2]])
        >>> ref_points = np.array([[1, 0], [0, 1], [0.5, 0.5]])
        >>> associations, distances = associate_to_reference_points(objectives, ref_points)
    """
    n_solutions = len(normalized_objectives)
    n_ref_points = len(reference_points)

    associations = np.zeros(n_solutions, dtype=int)
    distances = np.zeros(n_solutions)

    for i in range(n_solutions):
        min_dist = np.inf
        min_ref = 0

        for j in range(n_ref_points):
            # Calculate perpendicular distance from solution to reference line
            dist = perpendicular_distance(
                normalized_objectives[i],
                reference_points[j],
            )

            if dist < min_dist:
                min_dist = dist
                min_ref = j

        associations[i] = min_ref
        distances[i] = min_dist

    return associations, distances


def perpendicular_distance(point: np.ndarray, reference_direction: np.ndarray) -> float:
    """
    Calculate perpendicular distance from point to reference line.

    The reference line passes through origin in direction of reference_direction.

    Args:
        point: Point in objective space
        reference_direction: Reference direction vector

    Returns:
        Perpendicular distance

    Example:
        >>> point = np.array([1, 1])
        >>> ref_dir = np.array([1, 0])  # x-axis
        >>> dist = perpendicular_distance(point, ref_dir)
        >>> print(dist)  # 1.0 (distance from (1,1) to x-axis)
    """
    # Normalize reference direction
    ref_norm = np.linalg.norm(reference_direction)
    if ref_norm < 1e-10:
        return np.linalg.norm(point)

    ref_unit = reference_direction / ref_norm

    # Project point onto reference line
    projection_length = np.dot(point, ref_unit)
    projection = projection_length * ref_unit

    # Perpendicular distance is distance from point to projection
    perp_dist = np.linalg.norm(point - projection)

    return perp_dist


def niche_preserving_selection(
    front: List[int],
    associations: np.ndarray,
    distances: np.ndarray,
    reference_points: np.ndarray,
    n_select: int,
) -> np.ndarray:
    """
    Select solutions from a front using reference-point based niching.

    This is the key NSGA-III survivor selection mechanism:
    1. Count how many solutions are associated with each reference point
    2. Select from under-represented niches first
    3. Within each niche, select solution closest to reference point

    Args:
        front: List of solution indices in the front
        associations: Array mapping solution index to reference point index
        distances: Array of perpendicular distances to reference points
        reference_points: Reference points array
        n_select: Number of solutions to select from front

    Returns:
        Array of selected solution indices

    Example:
        >>> front = [0, 1, 2, 3]
        >>> associations = np.array([0, 0, 1, 2])
        >>> distances = np.array([0.1, 0.2, 0.15, 0.05])
        >>> ref_points = np.array([[1, 0], [0, 1], [0.5, 0.5]])
        >>> selected = niche_preserving_selection(
        ...     front, associations, distances, ref_points, n_select=2
        ... )
    """
    if n_select >= len(front):
        return np.array(front, dtype=int)

    n_ref_points = len(reference_points)

    # Count solutions associated with each reference point
    niche_counts = np.zeros(n_ref_points, dtype=int)
    for idx in front:
        niche_counts[associations[idx]] += 1

    selected = []

    while len(selected) < n_select:
        # Find niche with minimum count
        min_count = np.min(niche_counts)
        min_niches = np.where(niche_counts == min_count)[0]

        # If multiple niches have same minimum count, choose randomly
        if len(min_niches) > 1:
            chosen_niche = np.random.choice(min_niches)
        else:
            chosen_niche = min_niches[0]

        # Find solutions in this niche that haven't been selected yet
        niche_solutions = [
            idx for idx in front if associations[idx] == chosen_niche and idx not in selected
        ]

        if len(niche_solutions) == 0:
            # This niche is exhausted, set count to infinity
            niche_counts[chosen_niche] = np.inf
            continue

        # Select solution closest to reference point
        best_sol = min(niche_solutions, key=lambda idx: distances[idx])
        selected.append(best_sol)

        # Increment niche count
        niche_counts[chosen_niche] += 1

    return np.array(selected, dtype=int)


def compute_ideal_point(objectives: np.ndarray) -> np.ndarray:
    """
    Compute ideal point (best value for each objective).

    Args:
        objectives: Array of shape (n_solutions, n_objectives)

    Returns:
        Ideal point array of shape (n_objectives,)

    Example:
        >>> objectives = np.array([[1, 5], [2, 4], [3, 3]])
        >>> ideal = compute_ideal_point(objectives)
        >>> print(ideal)  # [3, 5] (max of each column for maximization)
    """
    return np.max(objectives, axis=0)


def compute_nadir_point(
    objectives: np.ndarray,
    front_indices: List[int],
) -> np.ndarray:
    """
    Compute nadir point (worst value among non-dominated solutions).

    Args:
        objectives: Array of shape (n_solutions, n_objectives)
        front_indices: Indices of solutions in first Pareto front

    Returns:
        Nadir point array of shape (n_objectives,)

    Example:
        >>> objectives = np.array([[3, 1], [2, 2], [1, 3], [0, 0]])
        >>> front = [0, 1, 2]  # Non-dominated solutions
        >>> nadir = compute_nadir_point(objectives, front)
        >>> print(nadir)  # [1, 1] (worst among non-dominated)
    """
    if len(front_indices) == 0:
        return np.min(objectives, axis=0)

    front_objectives = objectives[front_indices]
    return np.min(front_objectives, axis=0)


def adaptive_nadir_estimation(
    objectives: np.ndarray,
    front_indices: List[int],
    reference_points: np.ndarray,
) -> np.ndarray:
    """
    Estimate nadir point using extreme points method (more robust).

    Finds extreme points (solutions with best value in each objective)
    and estimates nadir from their worst values.

    Args:
        objectives: Array of shape (n_solutions, n_objectives)
        front_indices: Indices of solutions in first Pareto front
        reference_points: Reference points for scaling

    Returns:
        Estimated nadir point

    Example:
        >>> objectives = np.array([[3, 1], [2, 2], [1, 3]])
        >>> front = [0, 1, 2]
        >>> ref_points = np.array([[1, 0], [0, 1]])
        >>> nadir = adaptive_nadir_estimation(objectives, front, ref_points)
    """
    n_objectives = objectives.shape[1]
    front_objectives = objectives[front_indices]

    # Find extreme points (best in each objective)
    extreme_points = np.zeros((n_objectives, n_objectives))

    for m in range(n_objectives):
        # Find solution with maximum value for objective m
        best_idx = np.argmax(front_objectives[:, m])
        extreme_points[m] = front_objectives[best_idx]

    # Nadir is worst value among extreme points
    nadir = np.min(extreme_points, axis=0)

    return nadir
