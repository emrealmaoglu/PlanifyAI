"""
Non-Dominated Sorting for NSGA-III
===================================

Implements fast non-dominated sorting algorithm for multi-objective optimization.

Reference:
Deb, K., Pratap, A., Agarwal, S., & Meyarivan, T. (2002). "A fast and elitist
multiobjective genetic algorithm: NSGA-II." IEEE Transactions on Evolutionary
Computation, 6(2), 182-197.

Created: 2026-01-02 (Week 4 Day 4)
"""

from typing import List, Tuple

import numpy as np


def fast_nondominated_sort(objectives: np.ndarray) -> Tuple[List[List[int]], np.ndarray]:
    """
    Fast non-dominated sorting algorithm.

    Assigns each solution to a Pareto front based on dominance relationships.

    Args:
        objectives: Array of shape (n_solutions, n_objectives)
                   where objectives[i] is the objective vector for solution i

    Returns:
        Tuple of (fronts, ranks) where:
        - fronts: List of lists, fronts[i] contains indices of solutions in front i
        - ranks: Array of shape (n_solutions,) where ranks[i] is the front rank
                of solution i (0 = Pareto optimal, higher = dominated)

    Example:
        >>> objectives = np.array([[1.0, 2.0], [2.0, 1.0], [3.0, 3.0]])
        >>> fronts, ranks = fast_nondominated_sort(objectives)
        >>> print(fronts)  # [[0, 1], [2]] - first 2 solutions non-dominated
        >>> print(ranks)   # [0, 0, 1]
    """
    n_solutions = len(objectives)

    # For each solution, track:
    # - dominated_by_count: how many solutions dominate it
    # - dominates: which solutions it dominates
    dominated_by_count = np.zeros(n_solutions, dtype=int)
    dominates = [[] for _ in range(n_solutions)]

    # Compare all pairs
    for i in range(n_solutions):
        for j in range(i + 1, n_solutions):
            dom_ij = dominates_objective(objectives[i], objectives[j])
            dom_ji = dominates_objective(objectives[j], objectives[i])

            if dom_ij:
                # i dominates j
                dominates[i].append(j)
                dominated_by_count[j] += 1
            elif dom_ji:
                # j dominates i
                dominates[j].append(i)
                dominated_by_count[i] += 1

    # Build fronts
    fronts = []
    ranks = np.full(n_solutions, -1, dtype=int)

    # Front 0: solutions not dominated by anyone
    current_front = []
    for i in range(n_solutions):
        if dominated_by_count[i] == 0:
            current_front.append(i)
            ranks[i] = 0

    front_index = 0
    fronts.append(current_front)

    # Build subsequent fronts
    while len(current_front) > 0:
        next_front = []

        for i in current_front:
            # Remove i from domination count of solutions it dominates
            for j in dominates[i]:
                dominated_by_count[j] -= 1

                # If j is no longer dominated, add to next front
                if dominated_by_count[j] == 0:
                    next_front.append(j)
                    ranks[j] = front_index + 1

        if len(next_front) > 0:
            fronts.append(next_front)
            front_index += 1

        current_front = next_front

    return fronts, ranks


def dominates_objective(obj1: np.ndarray, obj2: np.ndarray) -> bool:
    """
    Check if obj1 dominates obj2 (maximization).

    For maximization:
    - obj1 dominates obj2 if obj1[i] >= obj2[i] for all i
    - AND obj1[j] > obj2[j] for at least one j

    Args:
        obj1: Objective vector 1
        obj2: Objective vector 2

    Returns:
        True if obj1 dominates obj2, False otherwise

    Example:
        >>> dominates_objective(np.array([2, 3]), np.array([1, 2]))
        True  # Dominates in both objectives
        >>> dominates_objective(np.array([2, 1]), np.array([1, 2]))
        False  # Trade-off - neither dominates
    """
    # All objectives >= (at least as good)
    all_better_or_equal = np.all(obj1 >= obj2)

    # At least one objective strictly > (strictly better)
    at_least_one_strictly_better = np.any(obj1 > obj2)

    return all_better_or_equal and at_least_one_strictly_better


def crowding_distance(objectives: np.ndarray, front: List[int]) -> np.ndarray:
    """
    Calculate crowding distance for solutions in a front.

    Crowding distance measures density of solutions around a point.
    Used in NSGA-II for diversity preservation.

    Args:
        objectives: Array of shape (n_solutions, n_objectives)
        front: List of solution indices in the front

    Returns:
        Array of shape (len(front),) containing crowding distances

    Example:
        >>> objectives = np.array([[1, 1], [2, 2], [3, 3]])
        >>> front = [0, 1, 2]
        >>> distances = crowding_distance(objectives, front)
        >>> # Extreme points get infinite distance
    """
    n_front = len(front)
    n_objectives = objectives.shape[1]

    if n_front <= 2:
        # All solutions on boundary for small fronts
        return np.full(n_front, np.inf)

    # Initialize crowding distances
    crowding_dist = np.zeros(n_front)

    # For each objective
    for m in range(n_objectives):
        # Sort front by objective m
        sorted_indices = np.argsort([objectives[i][m] for i in front])

        # Boundary solutions get infinite distance
        crowding_dist[sorted_indices[0]] = np.inf
        crowding_dist[sorted_indices[-1]] = np.inf

        # Calculate range
        obj_min = objectives[front[sorted_indices[0]]][m]
        obj_max = objectives[front[sorted_indices[-1]]][m]
        obj_range = obj_max - obj_min

        if obj_range == 0:
            continue

        # Calculate crowding distance for interior points
        for i in range(1, n_front - 1):
            idx = sorted_indices[i]
            idx_prev = sorted_indices[i - 1]
            idx_next = sorted_indices[i + 1]

            # Distance = (next - prev) / range
            distance = (objectives[front[idx_next]][m] - objectives[front[idx_prev]][m]) / obj_range

            crowding_dist[idx] += distance

    return crowding_dist


def select_best_solutions(
    objectives: np.ndarray,
    n_select: int,
) -> np.ndarray:
    """
    Select best n_select solutions using non-dominated sorting and crowding distance.

    Used in NSGA-II survivor selection.

    Args:
        objectives: Array of shape (n_solutions, n_objectives)
        n_select: Number of solutions to select

    Returns:
        Array of selected solution indices

    Example:
        >>> objectives = np.array([[3, 1], [2, 2], [1, 3], [0, 0]])
        >>> selected = select_best_solutions(objectives, n_select=2)
        >>> # Should select non-dominated solutions
    """
    n_solutions = len(objectives)

    if n_select >= n_solutions:
        return np.arange(n_solutions)

    # Non-dominated sorting
    fronts, ranks = fast_nondominated_sort(objectives)

    selected = []

    for front in fronts:
        if len(selected) + len(front) <= n_select:
            # Include entire front
            selected.extend(front)
        else:
            # Need to select from this front
            n_remaining = n_select - len(selected)

            # Calculate crowding distance
            crowding_dist = crowding_distance(objectives, front)

            # Sort by crowding distance (descending)
            sorted_indices = np.argsort(-crowding_dist)

            # Select most crowded solutions
            selected.extend([front[i] for i in sorted_indices[:n_remaining]])
            break

    return np.array(selected, dtype=int)


def pareto_front_2d_indices(objectives: np.ndarray) -> np.ndarray:
    """
    Fast 2D Pareto front extraction (for 2 objectives only).

    More efficient than full non-dominated sorting for bi-objective problems.

    Args:
        objectives: Array of shape (n_solutions, 2)

    Returns:
        Indices of solutions on Pareto front, sorted by first objective

    Example:
        >>> objectives = np.array([[1, 3], [2, 2], [3, 1], [0.5, 0.5]])
        >>> front_indices = pareto_front_2d_indices(objectives)
        >>> # Returns indices of non-dominated solutions
    """
    if objectives.shape[1] != 2:
        raise ValueError("pareto_front_2d_indices requires exactly 2 objectives")

    # Sort by first objective (descending for maximization)
    sorted_indices = np.argsort(-objectives[:, 0])

    pareto_front = []
    max_obj2 = -np.inf

    for idx in sorted_indices:
        obj2_value = objectives[idx, 1]

        # If this solution's obj2 is better than any seen so far, it's non-dominated
        if obj2_value > max_obj2:
            pareto_front.append(idx)
            max_obj2 = obj2_value

    return np.array(pareto_front, dtype=int)
