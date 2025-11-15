"""
Fitness Evaluation Module
==========================
Multi-objective fitness evaluation for spatial planning solutions.

Classes:
    FitnessEvaluator: Main fitness evaluation class

Functions:
    profile_time: Decorator for performance profiling

Created: 2025-11-03
"""

import functools
import logging
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.spatial.distance import cdist

from .building import Building

# Import research-based objectives
from .objectives import maximize_adjacency_satisfaction, minimize_cost, minimize_walking_distance
from .solution import Solution

logger = logging.getLogger(__name__)


def profile_time(func):
    """Decorator to profile function execution time"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} took {elapsed:.3f}s")
        return result

    return wrapper


class FitnessEvaluator:
    """
    Multi-objective fitness evaluator for spatial planning solutions.

    Updated Day 3: Now uses research-based objectives:
    - Construction cost minimization
    - Walking distance minimization (15-minute city)
    - Adjacency satisfaction maximization

    Backwards compatible with Day 1-2 code.

    Attributes:
        buildings: List of Building objects
        bounds: Area bounds (x_min, y_min, x_max, y_max)
        weights: Dict of objective weights (default: cost=0.33, walking=0.34, adjacency=0.33)
        safety_margin: Minimum distance between buildings (default: 5m)

    Example:
        >>> evaluator = FitnessEvaluator(buildings, bounds)
        >>> fitness = evaluator.evaluate(solution)
        >>> print(f"Fitness: {fitness:.4f}")
    """

    def __init__(
        self,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        weights: Optional[Dict[str, float]] = None,
        safety_margin: float = 5.0,
    ):
        """
        Initialize fitness evaluator.

        Args:
            buildings: List of Building objects to evaluate
            bounds: Site boundaries (x_min, y_min, x_max, y_max)
            weights: Objective weights dict (default: cost=0.33, walking=0.34, adjacency=0.33)
            safety_margin: Minimum clearance between buildings in meters

        Raises:
            ValueError: If buildings list is empty, bounds invalid, or weights don't sum to 1.0
        """
        # Validate buildings
        if not buildings:
            raise ValueError("buildings list cannot be empty")

        # Validate bounds
        if len(bounds) != 4:
            raise ValueError(
                f"bounds must be (x_min, y_min, x_max, y_max), got {len(bounds)} values"
            )
        x_min, y_min, x_max, y_max = bounds
        if x_min >= x_max or y_min >= y_max:
            raise ValueError(
                f"Invalid bounds: x_min={x_min} >= x_max={x_max} or "
                f"y_min={y_min} >= y_max={y_max}"
            )

        # Check for oversized footprints
        site_area = (x_max - x_min) * (y_max - y_min)
        for building in buildings:
            if building.footprint > 0.8 * site_area:
                raise ValueError(
                    f"Building {building.id} footprint ({building.footprint}m²) "
                    f"exceeds 80% of site area"
                )

        # Store parameters
        self.buildings = buildings
        self.bounds = bounds
        self.safety_margin = safety_margin
        self.min_distance_between_buildings = 20.0  # Minimum 20m separation

        # Build building dict for legacy methods
        self.building_dict = {b.id: b for b in buildings}

        # Set default weights if None (Day 3 research-based)
        if weights is None:
            weights = {"cost": 0.33, "walking": 0.34, "adjacency": 0.33}

        # Validate weights sum to 1.0 (with tolerance)
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum:.4f}")

        self.weights = weights
        self.site_area = site_area

    @profile_time
    def evaluate(self, solution: Solution) -> float:
        """
        Evaluate fitness of a solution (backwards compatible).

        Uses research-based objectives (Day 3 update):
        - Construction cost minimization (lower is better)
        - Walking distance satisfaction (higher is better)
        - Adjacency satisfaction (higher is better)

        Formula: fitness = 1.0 - (w1*cost + w2*(1-walking) + w3*(1-adjacency))

        Args:
            solution: Solution object with building positions

        Returns:
            Weighted fitness score ∈ [0, 1] (higher is better)

        Raises:
            ValueError: If solution has missing positions or invalid data
        """
        # Validate solution has all positions
        for building in self.buildings:
            if building.id not in solution.positions:
                raise ValueError(f"Solution missing position for building {building.id}")

        # Check for overlapping buildings (penalty)
        overlap_penalty = self._calculate_overlap_penalty(solution)

        # Evaluate new objectives
        objectives = {
            "cost": minimize_cost(solution, self.buildings),
            "walking": minimize_walking_distance(solution, self.buildings),
            "adjacency": maximize_adjacency_satisfaction(solution, self.buildings),
        }

        # Convert satisfaction scores to "cost" scores for minimization
        # cost: already a cost (lower is better)
        # walking: satisfaction (higher is better) -> convert to cost (1.0 - satisfaction)
        # adjacency: satisfaction (higher is better) -> convert to cost (1.0 - satisfaction)
        cost_scores = {
            "cost": objectives["cost"],
            "walking": 1.0 - objectives["walking"],
            "adjacency": 1.0 - objectives["adjacency"],
        }

        # Weighted sum (all converted to minimization)
        weighted_sum = sum(self.weights.get(obj, 0.0) * score for obj, score in cost_scores.items())

        # Apply overlap penalty (reduce fitness by up to 50%)
        if overlap_penalty > 0.0:
            weighted_sum = weighted_sum * (1.0 + 0.5 * overlap_penalty)

        # Invert to make higher-is-better for SA compatibility
        # Lower objective scores → higher fitness
        fitness = 1.0 - weighted_sum
        fitness = np.clip(fitness, 0.0, 1.0)

        # Store objectives in solution (store satisfaction scores as-is for display)
        solution.objectives = objectives

        logger.debug(
            f"fitness: cost={objectives['cost']:.3f}, "
            f"walking={objectives['walking']:.3f}, "
            f"adjacency={objectives['adjacency']:.3f}, "
            f"overlap_penalty={overlap_penalty:.3f}, "
            f"weighted_sum={weighted_sum:.3f}, fitness={fitness:.3f}"
        )

        return fitness

    def _calculate_overlap_penalty(self, solution: Solution) -> float:
        """
        Calculate penalty for overlapping buildings.

        Returns:
            Penalty from 0.0 (no overlap) to 1.0 (complete overlap)
        """
        if len(self.buildings) < 2:
            return 0.0

        penalty = 0.0
        pair_count = 0

        for i, b1 in enumerate(self.buildings):
            for b2 in self.buildings[i + 1 :]:
                pos1 = np.array(solution.positions[b1.id])
                pos2 = np.array(solution.positions[b2.id])
                distance = np.linalg.norm(pos1 - pos2)

                # Calculate building radii (approximate as circles)
                radius1 = np.sqrt(b1.footprint / np.pi)
                radius2 = np.sqrt(b2.footprint / np.pi)
                min_required_distance = radius1 + radius2 + self.min_distance_between_buildings

                if distance < min_required_distance:
                    # Penalty increases as buildings get closer
                    violation = (min_required_distance - distance) / min_required_distance
                    penalty += violation
                    pair_count += 1

        if pair_count == 0:
            return 0.0

        # Average penalty across all overlapping pairs
        avg_penalty = penalty / pair_count
        return float(np.clip(avg_penalty, 0.0, 1.0))

    def _compactness_score(self, solution: Solution) -> float:
        """
        Calculate compactness score based on inter-building distances.

        Research basis: EPA Walkability Index adaptation (15-Minute City Optimization)
        Ideal distance: 50-150m between buildings

        Formula: score = exp(-abs(avg_distance - ideal) / ideal)

        Args:
            solution: Solution with positions

        Returns:
            Score in [0,1] range (1.0 = ideal, 0.0 = very poor)
        """
        # Extract all positions as numpy array
        positions = np.array(list(solution.positions.values()))

        # Handle edge case: single building
        if len(positions) < 2:
            return 1.0

        # Calculate pairwise distances using cdist
        distances = cdist(positions, positions)

        # Remove diagonal (self-distances)
        mask = distances > 0
        if not mask.any():
            return 1.0

        # Calculate average distance
        avg_distance = np.mean(distances[mask])

        # Ideal distance = 100m
        ideal_distance = 100.0

        # Score = exp(-abs(avg - ideal) / ideal)
        score = np.exp(-abs(avg_distance - ideal_distance) / ideal_distance)

        return float(np.clip(score, 0.0, 1.0))

    def _accessibility_score(self, solution: Solution) -> float:
        """
        Calculate accessibility score (pre-Week 2: centroid distance).

        Week 2+: Will use tensor field-based road network access.
        Current: Distance to site centroid (normalized).

        Formula: score = 1 - (avg_distance_to_centroid / max_distance)

        Args:
            solution: Solution with positions

        Returns:
            Score in [0,1] range
        """
        x_min, y_min, x_max, y_max = self.bounds

        # Calculate site centroid
        centroid = np.array([(x_min + x_max) / 2, (y_min + y_max) / 2])

        # For each building, calculate distance to centroid
        distances = []
        for building in self.buildings:
            position = np.array(solution.positions[building.id])
            dist = np.linalg.norm(position - centroid)
            distances.append(dist)

        # Calculate average distance
        avg_distance = np.mean(distances)

        # Calculate max possible distance (corner to centroid)
        max_distance = np.linalg.norm(np.array([x_max, y_max]) - centroid)

        # Score = 1 - (avg / max)
        if max_distance == 0:
            return 1.0

        score = 1.0 - (avg_distance / max_distance)

        return float(np.clip(score, 0.0, 1.0))

    def _calculate_penalties(self, solution: Solution) -> float:
        """
        Calculate penalty for constraint violations.

        Penalties:
        - Out-of-bounds: 1000 per building
        - Overlaps: 500 per overlap pair
        - Safety margin violations: 100 per violation

        Args:
            solution: Solution to check

        Returns:
            Total penalty (always >= 0)
        """
        x_min, y_min, x_max, y_max = self.bounds
        total_penalty = 0.0

        # Check bounds violations (1000 each)
        for building in self.buildings:
            x, y = solution.positions[building.id]
            margin = building.radius

            if x - margin < x_min or x + margin > x_max or y - margin < y_min or y + margin > y_max:
                total_penalty += 1000.0

        # Check overlaps and safety margin violations
        for i, b1 in enumerate(self.buildings):
            b1.position = solution.positions[b1.id]
            for b2 in self.buildings[i + 1 :]:
                b2.position = solution.positions[b2.id]

                # Check if buildings overlap
                if b1.overlaps_with(b2, safety_margin=0.0):
                    total_penalty += 500.0

                # Check safety margin violation
                elif b1.overlaps_with(b2, safety_margin=self.safety_margin):
                    total_penalty += 100.0

        return total_penalty
