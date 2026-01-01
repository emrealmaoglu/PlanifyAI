"""
Pareto Front Analysis for Multi-Objective Optimization
=======================================================

Implements Pareto dominance analysis and quality indicators for
multi-objective campus planning optimization.

Key Metrics:
    - Hypervolume: Volume dominated by Pareto front
    - Spread: Distribution of solutions along front
    - Convergence: Distance to true Pareto front
    - Spacing: Uniformity of solution distribution

References:
    - Deb et al. (2002): NSGA-II - Fast non-dominated sorting
    - Zitzler & Thiele (1999): Hypervolume indicator
    - Zitzler et al. (2003): Performance assessment of MOEAs
    - Research: "Multi-Objective Campus Planning.docx"

Created: 2026-01-01
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def is_dominated(obj1: np.ndarray, obj2: np.ndarray) -> bool:
    """
    Check if obj1 is dominated by obj2 (assuming minimization).

    For maximization objectives, negate before calling.

    Args:
        obj1: Objective vector 1 (shape: [n_objectives])
        obj2: Objective vector 2 (shape: [n_objectives])

    Returns:
        True if obj1 is dominated by obj2, False otherwise

    Notes:
        obj2 dominates obj1 if:
        - obj2 is better or equal in all objectives
        - obj2 is strictly better in at least one objective
    """
    better_or_equal = np.all(obj2 <= obj1)
    strictly_better = np.any(obj2 < obj1)
    return better_or_equal and strictly_better


def compute_hypervolume(
    pareto_front: np.ndarray,
    reference_point: np.ndarray,
) -> float:
    """
    Compute hypervolume indicator (S-metric) for Pareto front.

    Hypervolume = volume of objective space dominated by Pareto front.
    Higher is better.

    Args:
        pareto_front: Array of objective vectors (shape: [n_solutions, n_objectives])
        reference_point: Worst acceptable point (shape: [n_objectives])

    Returns:
        Hypervolume value (higher = better quality front)

    Example:
        >>> front = np.array([[1.0, 5.0], [2.0, 3.0], [4.0, 1.0]])
        >>> ref = np.array([5.0, 6.0])
        >>> hv = compute_hypervolume(front, ref)
        >>> # Volume dominated by these 3 solutions

    Notes:
        - Assumes minimization (for maximization, negate objectives)
        - Uses efficient WFG algorithm for 2D, brute force for higher dimensions
        - Reference point should be worse than all Pareto front points
    """
    if len(pareto_front) == 0:
        return 0.0

    n_objectives = pareto_front.shape[1]

    # Verify reference point is worse than all front points
    if not np.all(pareto_front <= reference_point):
        raise ValueError(
            "Reference point must be worse than all Pareto front points " "(for minimization)"
        )

    if n_objectives == 2:
        # Efficient 2D algorithm
        return _hypervolume_2d(pareto_front, reference_point)
    else:
        # General algorithm (slower for higher dimensions)
        return _hypervolume_recursive(pareto_front, reference_point)


def _hypervolume_2d(front: np.ndarray, ref: np.ndarray) -> float:
    """Efficient 2D hypervolume calculation."""
    # Sort by first objective
    sorted_front = front[np.argsort(front[:, 0])]

    hv = 0.0
    prev_x = 0.0

    for point in sorted_front:
        x, y = point
        # Rectangle from (prev_x, y) to (x, ref[1])
        width = x - prev_x
        height = ref[1] - y
        hv += width * height
        prev_x = x

    # Final rectangle
    last_x = sorted_front[-1, 0]
    last_y = sorted_front[-1, 1]
    hv += (ref[0] - last_x) * (ref[1] - last_y)

    return hv


def _hypervolume_recursive(front: np.ndarray, ref: np.ndarray) -> float:
    """
    Recursive hypervolume calculation for arbitrary dimensions.

    Uses inclusion-exclusion principle (slower for high dimensions).
    """
    if len(front) == 0:
        return 0.0

    if len(front) == 1:
        # Volume of single box
        return np.prod(ref - front[0])

    # Recursive inclusion-exclusion
    # HV(A ∪ B) = HV(A) + HV(B) - HV(A ∩ B)
    pivot = front[0]
    rest = front[1:]

    # Volume dominated by pivot alone
    v_pivot = np.prod(ref - pivot)

    # Volume dominated by rest
    v_rest = _hypervolume_recursive(rest, ref)

    # Volume dominated by both (intersection)
    # Create new reference point for intersection
    intersection_ref = np.minimum(ref, pivot)
    dominated_rest = rest[np.all(rest <= intersection_ref, axis=1)]
    v_intersection = (
        _hypervolume_recursive(dominated_rest, intersection_ref) if len(dominated_rest) > 0 else 0.0
    )

    return v_pivot + v_rest - v_intersection


def compute_spread(pareto_front: np.ndarray) -> float:
    """
    Compute spread metric (Δ) measuring diversity of solutions.

    Lower is better (0 = uniform distribution).

    Args:
        pareto_front: Array of objective vectors (shape: [n_solutions, n_objectives])

    Returns:
        Spread value (0 = perfect uniform distribution)

    Formula:
        Δ = (d_f + d_l + Σ|d_i - d̄|) / (d_f + d_l + (N-1)d̄)

        where:
        - d_f, d_l = distance to extreme solutions
        - d_i = distance between consecutive solutions
        - d̄ = mean distance
    """
    if len(pareto_front) <= 1:
        return 0.0

    # Normalize objectives to [0, 1]
    normalized = (pareto_front - pareto_front.min(axis=0)) / (
        pareto_front.max(axis=0) - pareto_front.min(axis=0) + 1e-10
    )

    # Sort by first objective
    sorted_indices = np.argsort(normalized[:, 0])
    sorted_front = normalized[sorted_indices]

    # Compute distances between consecutive solutions
    distances = []
    for i in range(len(sorted_front) - 1):
        dist = np.linalg.norm(sorted_front[i + 1] - sorted_front[i])
        distances.append(dist)

    distances = np.array(distances)
    mean_dist = np.mean(distances)

    # Distance to extremes (approximation)
    d_f = np.linalg.norm(sorted_front[0])
    d_l = np.linalg.norm(sorted_front[-1] - np.ones(sorted_front.shape[1]))

    # Spread metric
    numerator = d_f + d_l + np.sum(np.abs(distances - mean_dist))
    denominator = d_f + d_l + (len(sorted_front) - 1) * mean_dist + 1e-10

    spread = numerator / denominator

    return float(spread)


def compute_spacing(pareto_front: np.ndarray) -> float:
    """
    Compute spacing metric (S) measuring uniformity of solution distribution.

    Lower is better (0 = perfectly uniform).

    Args:
        pareto_front: Array of objective vectors (shape: [n_solutions, n_objectives])

    Returns:
        Spacing value (0 = perfectly uniform spacing)

    Formula:
        S = sqrt((1/N) * Σ(d̄ - d_i)²)

        where:
        - d_i = distance to nearest neighbor
        - d̄ = mean nearest neighbor distance
    """
    if len(pareto_front) <= 1:
        return 0.0

    # Normalize objectives
    normalized = (pareto_front - pareto_front.min(axis=0)) / (
        pareto_front.max(axis=0) - pareto_front.min(axis=0) + 1e-10
    )

    # Compute nearest neighbor distances
    nearest_distances = []

    for i, point in enumerate(normalized):
        # Find distance to nearest other point
        other_points = np.delete(normalized, i, axis=0)
        distances = np.linalg.norm(other_points - point, axis=1)
        nearest_dist = np.min(distances)
        nearest_distances.append(nearest_dist)

    nearest_distances = np.array(nearest_distances)
    mean_dist = np.mean(nearest_distances)

    # Spacing metric (standard deviation of nearest neighbor distances)
    spacing = np.sqrt(np.mean((nearest_distances - mean_dist) ** 2))

    return float(spacing)


@dataclass
class ParetoQualityMetrics:
    """
    Quality indicators for Pareto front.

    Attributes:
        hypervolume: Volume dominated by front (higher = better)
        spread: Solution diversity (lower = better)
        spacing: Distribution uniformity (lower = better)
        n_solutions: Number of solutions in front
        coverage: Percentage of objective space covered
    """

    hypervolume: float
    spread: float
    spacing: float
    n_solutions: int
    coverage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hypervolume": self.hypervolume,
            "spread": self.spread,
            "spacing": self.spacing,
            "n_solutions": self.n_solutions,
            "coverage": self.coverage,
            "quality_score": self.quality_score,
        }

    @property
    def quality_score(self) -> float:
        """
        Aggregate quality score [0, 1] where 1 = excellent.

        Combines hypervolume (positive), spread (negative), spacing (negative).
        """
        # Normalize hypervolume (assume max reasonable is 1.0)
        hv_score = min(1.0, self.hypervolume)

        # Penalize spread and spacing (lower is better)
        # Assume spread and spacing in [0, 1] range
        spread_score = max(0.0, 1.0 - self.spread)
        spacing_score = max(0.0, 1.0 - self.spacing)

        # Weighted combination
        score = 0.5 * hv_score + 0.25 * spread_score + 0.25 * spacing_score

        return float(np.clip(score, 0.0, 1.0))


class ParetoFront:
    """
    Pareto front manager for multi-objective optimization.

    Maintains non-dominated solutions and computes quality metrics.

    Usage:
        >>> front = ParetoFront(n_objectives=3)
        >>> front.add_solution(objectives=[0.5, 0.3, 0.7], data={'id': 'sol1'})
        >>> front.add_solution(objectives=[0.6, 0.2, 0.8], data={'id': 'sol2'})
        >>> metrics = front.compute_metrics(reference_point=[1.0, 1.0, 1.0])
        >>> print(f"Hypervolume: {metrics.hypervolume:.4f}")
    """

    def __init__(self, n_objectives: int, minimize: Optional[List[bool]] = None):
        """
        Initialize Pareto front.

        Args:
            n_objectives: Number of objectives
            minimize: List of booleans indicating if each objective should be
                      minimized (True) or maximized (False). Default: all minimized
        """
        self.n_objectives = n_objectives
        self.minimize = minimize or [True] * n_objectives

        self.solutions: List[np.ndarray] = []  # Objective vectors
        self.data: List[Dict[str, Any]] = []  # Associated solution data

    def add_solution(
        self,
        objectives: List[float],
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add solution to Pareto front (if non-dominated).

        Args:
            objectives: Objective values
            data: Associated solution data (positions, etc.)

        Returns:
            True if solution was added (non-dominated), False otherwise
        """
        obj = np.array(objectives)

        # Convert maximization to minimization
        for i, is_min in enumerate(self.minimize):
            if not is_min:
                obj[i] = -obj[i]

        # Check if dominated by existing solutions
        for existing_obj in self.solutions:
            if is_dominated(obj, existing_obj):
                return False  # Dominated, don't add

        # Remove solutions dominated by new solution
        non_dominated_indices = []
        for i, existing_obj in enumerate(self.solutions):
            if not is_dominated(existing_obj, obj):
                non_dominated_indices.append(i)

        self.solutions = [self.solutions[i] for i in non_dominated_indices]
        self.data = [self.data[i] for i in non_dominated_indices]

        # Add new solution
        self.solutions.append(obj)
        self.data.append(data or {})

        return True

    def get_front(self) -> np.ndarray:
        """Get Pareto front as numpy array."""
        if not self.solutions:
            return np.array([])
        return np.array(self.solutions)

    def get_solutions_with_data(self) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
        """Get solutions with associated data."""
        return list(zip(self.solutions, self.data))

    def compute_metrics(
        self,
        reference_point: Optional[List[float]] = None,
    ) -> ParetoQualityMetrics:
        """
        Compute quality metrics for current Pareto front.

        Args:
            reference_point: Worst acceptable point for hypervolume.
                             If None, uses 1.1 * max values.

        Returns:
            ParetoQualityMetrics object
        """
        front = self.get_front()

        if len(front) == 0:
            return ParetoQualityMetrics(
                hypervolume=0.0,
                spread=0.0,
                spacing=0.0,
                n_solutions=0,
                coverage=0.0,
            )

        # Determine reference point
        if reference_point is None:
            # Use 1.1 * max values as reference
            ref_point = np.max(front, axis=0) * 1.1
        else:
            ref_point = np.array(reference_point)
            # Convert maximization objectives
            for i, is_min in enumerate(self.minimize):
                if not is_min:
                    ref_point[i] = -ref_point[i]

        # Compute metrics
        hypervolume = compute_hypervolume(front, ref_point)
        spread = compute_spread(front)
        spacing = compute_spacing(front)

        # Coverage (percentage of reference box filled)
        ref_volume = np.prod(ref_point - np.min(front, axis=0))
        coverage = hypervolume / (ref_volume + 1e-10)

        return ParetoQualityMetrics(
            hypervolume=hypervolume,
            spread=spread,
            spacing=spacing,
            n_solutions=len(front),
            coverage=coverage,
        )

    def get_extreme_solutions(self) -> Dict[int, Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Get extreme solutions for each objective.

        Returns:
            Dictionary mapping objective_index -> (objectives, data)
        """
        front = self.get_front()

        if len(front) == 0:
            return {}

        extremes = {}

        for obj_idx in range(self.n_objectives):
            # Find solution with best value for this objective
            best_idx = np.argmin(front[:, obj_idx])
            extremes[obj_idx] = (self.solutions[best_idx], self.data[best_idx])

        return extremes

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive Pareto front report."""
        metrics = self.compute_metrics()
        extremes = self.get_extreme_solutions()

        # Format extreme solutions
        extreme_solutions = {}
        for obj_idx, (obj_vec, data) in extremes.items():
            extreme_solutions[f"objective_{obj_idx}"] = {
                "objectives": obj_vec.tolist(),
                "data": data,
            }

        return {
            "metrics": metrics.to_dict(),
            "n_solutions": len(self.solutions),
            "extreme_solutions": extreme_solutions,
            "front": self.get_front().tolist(),
        }
