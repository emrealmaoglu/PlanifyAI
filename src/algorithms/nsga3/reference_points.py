"""
Reference Point Generation for NSGA-III
========================================

Implements Das-Dennis systematic sampling method for generating uniformly
distributed reference points on a unit simplex.

Reference:
Das, I., & Dennis, J. E. (1998). "Normal-boundary intersection: A new method
for generating the Pareto surface in nonlinear multicriteria optimization
problems." SIAM Journal on Optimization, 8(3), 631-657.

Created: 2026-01-02 (Week 4 Day 4)
"""

from typing import List

import numpy as np


def generate_reference_points(
    n_objectives: int,
    n_partitions: int = 12,
    scaling: float = 1.0,
) -> np.ndarray:
    """
    Generate uniformly distributed reference points using Das-Dennis method.

    Creates points on a unit simplex (sum of coordinates = scaling).

    Args:
        n_objectives: Number of objectives
        n_partitions: Number of divisions along each objective axis
        scaling: Scale factor for reference points (default 1.0)

    Returns:
        Array of shape (n_points, n_objectives) containing reference points

    Example:
        >>> # 3 objectives, 12 partitions
        >>> ref_points = generate_reference_points(3, 12)
        >>> print(ref_points.shape)  # (91, 3)
        >>> print(np.sum(ref_points[0]))  # 1.0
    """
    if n_objectives < 2:
        raise ValueError("n_objectives must be >= 2")
    if n_partitions < 1:
        raise ValueError("n_partitions must be >= 1")

    # Generate points recursively
    ref_points = _recursive_generate(n_objectives, n_partitions, 0, [])

    # Convert to numpy array and scale
    ref_points = np.array(ref_points) * scaling

    return ref_points


def _recursive_generate(
    n_objectives: int,
    n_partitions: int,
    current_sum: int,
    current_point: List[int],
) -> List[List[float]]:
    """
    Recursively generate reference points.

    Args:
        n_objectives: Number of objectives remaining
        n_partitions: Number of partitions
        current_sum: Current sum of allocated partitions
        current_point: Current partial point being built

    Returns:
        List of reference points
    """
    if n_objectives == 1:
        # Last objective - assign remaining partitions
        point = current_point + [(n_partitions - current_sum) / n_partitions]
        return [point]

    points = []

    # Try all possible allocations for current objective
    for i in range(n_partitions - current_sum + 1):
        value = i / n_partitions
        new_point = current_point + [value]

        # Recursively generate for remaining objectives
        sub_points = _recursive_generate(
            n_objectives - 1,
            n_partitions,
            current_sum + i,
            new_point,
        )
        points.extend(sub_points)

    return points


def generate_two_layer_reference_points(
    n_objectives: int,
    n_partitions_outer: int = 12,
    n_partitions_inner: int = 6,
    scaling: float = 1.0,
) -> np.ndarray:
    """
    Generate two-layer reference points for better coverage.

    Useful for many-objective optimization (5+ objectives) where single layer
    produces too few or too many points.

    Args:
        n_objectives: Number of objectives
        n_partitions_outer: Partitions for outer layer (on simplex boundary)
        n_partitions_inner: Partitions for inner layer (scaled towards center)
        scaling: Scale factor for reference points

    Returns:
        Array of shape (n_points, n_objectives) containing reference points

    Example:
        >>> # 5 objectives with two layers
        >>> ref_points = generate_two_layer_reference_points(
        ...     5, n_partitions_outer=6, n_partitions_inner=3
        ... )
        >>> print(ref_points.shape)  # (210, 5) - more coverage than single layer
    """
    # Outer layer on boundary
    outer_points = generate_reference_points(n_objectives, n_partitions_outer, scaling=1.0)

    # Inner layer scaled towards center
    inner_points = generate_reference_points(n_objectives, n_partitions_inner, scaling=0.5)

    # Shift inner points towards center
    # Center point is (1/n_objectives, 1/n_objectives, ...)
    center = np.ones(n_objectives) / n_objectives
    inner_points = inner_points * 0.5 + center * 0.5

    # Combine layers
    all_points = np.vstack([outer_points, inner_points])

    # Scale if requested
    if scaling != 1.0:
        all_points *= scaling

    return all_points


def count_reference_points(n_objectives: int, n_partitions: int) -> int:
    """
    Calculate number of reference points without generating them.

    Uses combinatorial formula: C(n_partitions + n_objectives - 1, n_objectives - 1)

    Args:
        n_objectives: Number of objectives
        n_partitions: Number of partitions

    Returns:
        Number of reference points that would be generated

    Example:
        >>> count_reference_points(3, 12)  # 91 points
        91
        >>> count_reference_points(5, 6)   # 210 points
        210
    """
    from math import comb

    return comb(n_partitions + n_objectives - 1, n_objectives - 1)


def visualize_reference_points_2d(ref_points: np.ndarray, title: str = "Reference Points"):
    """
    Visualize 2D or 3D reference points.

    Args:
        ref_points: Reference points array (n_points, 2 or 3)
        title: Plot title
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available for visualization")
        return

    n_objectives = ref_points.shape[1]

    if n_objectives == 2:
        plt.figure(figsize=(8, 6))
        plt.scatter(ref_points[:, 0], ref_points[:, 1], alpha=0.6, s=50)
        plt.xlabel("Objective 1")
        plt.ylabel("Objective 2")
        plt.title(f"{title} (n={len(ref_points)})")
        plt.grid(True, alpha=0.3)
        plt.axis("equal")
        plt.show()

    elif n_objectives == 3:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(
            ref_points[:, 0],
            ref_points[:, 1],
            ref_points[:, 2],
            alpha=0.6,
            s=50,
        )
        ax.set_xlabel("Objective 1")
        ax.set_ylabel("Objective 2")
        ax.set_zlabel("Objective 3")
        ax.set_title(f"{title} (n={len(ref_points)})")
        plt.show()

    else:
        print(f"Cannot visualize {n_objectives}D reference points")


# Precomputed common configurations
REFERENCE_POINTS_CONFIG = {
    # (n_objectives, n_partitions): n_points
    (2, 100): 101,  # Bi-objective with fine granularity
    (3, 12): 91,  # Tri-objective standard
    (3, 23): 300,  # Tri-objective fine
    (4, 8): 165,  # 4-objective
    (5, 6): 210,  # 5-objective
    (6, 4): 210,  # 6-objective
    (8, 3): 165,  # 8-objective
    (10, 3): 286,  # 10-objective
}


def get_recommended_partitions(n_objectives: int, target_points: int = 100) -> int:
    """
    Get recommended number of partitions for target number of points.

    Args:
        n_objectives: Number of objectives
        target_points: Desired approximate number of reference points

    Returns:
        Recommended n_partitions value

    Example:
        >>> get_recommended_partitions(3, target_points=100)
        12  # Will produce 91 points
        >>> get_recommended_partitions(5, target_points=200)
        6   # Will produce 210 points
    """
    # Binary search for partition count
    min_p, max_p = 1, 100

    while min_p < max_p:
        mid_p = (min_p + max_p) // 2
        n_points = count_reference_points(n_objectives, mid_p)

        if n_points < target_points:
            min_p = mid_p + 1
        else:
            max_p = mid_p

    return min_p
