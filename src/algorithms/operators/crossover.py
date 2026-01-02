"""
GA Crossover Operators
=======================

Operators for combining parent solutions in Genetic Algorithms.

Created: 2026-01-02 (Week 4 Day 3)
"""

from typing import Tuple

import numpy as np

from ..solution import Solution
from .base import CrossoverOperator


class UniformCrossover(CrossoverOperator):
    """
    Uniform crossover: Each gene has 50% chance from each parent.

    For each building, randomly select position from parent1 or parent2.
    Maintains diversity while combining parent traits.

    Args:
        swap_probability: Probability of swapping gene (default 0.5)
    """

    def __init__(self, swap_probability: float = 0.5):
        """Initialize uniform crossover."""
        self.swap_probability = swap_probability

    def crossover(
        self,
        parent1: Solution,
        parent2: Solution,
    ) -> Tuple[Solution, Solution]:
        """
        Create offspring via uniform crossover.

        Each gene (building position) independently inherits from parent1 or parent2.
        """
        child1_positions = {}
        child2_positions = {}

        for building_id in parent1.positions.keys():
            if np.random.random() < self.swap_probability:
                # Child1 gets parent1's gene, child2 gets parent2's
                child1_positions[building_id] = parent1.positions[building_id]
                child2_positions[building_id] = parent2.positions[building_id]
            else:
                # Swap
                child1_positions[building_id] = parent2.positions[building_id]
                child2_positions[building_id] = parent1.positions[building_id]

        child1 = Solution(positions=child1_positions)
        child2 = Solution(positions=child2_positions)

        # Fitness needs re-evaluation
        child1.fitness = None
        child2.fitness = None

        return child1, child2


class PartiallyMatchedCrossover(CrossoverOperator):
    """
    Partially Matched Crossover (PMX): Position-based crossover.

    Divides buildings into segments and swaps segments between parents.
    Useful for preserving spatial relationships.

    Args:
        n_segments: Number of segments to divide buildings into (default 2)
    """

    def __init__(self, n_segments: int = 2):
        """Initialize PMX crossover."""
        self.n_segments = n_segments

    def crossover(
        self,
        parent1: Solution,
        parent2: Solution,
    ) -> Tuple[Solution, Solution]:
        """
        Create offspring via partially matched crossover.

        Divides buildings into segments and swaps segments between parents.
        """
        building_ids = list(parent1.positions.keys())
        n_buildings = len(building_ids)

        # Divide into segments
        segment_size = max(1, n_buildings // self.n_segments)

        # Randomly select segment to swap
        segment_start = np.random.randint(0, max(1, n_buildings - segment_size + 1))
        segment_end = min(segment_start + segment_size, n_buildings)

        # Create children
        child1_positions = parent1.positions.copy()
        child2_positions = parent2.positions.copy()

        # Swap segment
        for i in range(segment_start, segment_end):
            building_id = building_ids[i]
            child1_positions[building_id] = parent2.positions[building_id]
            child2_positions[building_id] = parent1.positions[building_id]

        child1 = Solution(positions=child1_positions)
        child2 = Solution(positions=child2_positions)

        # Invalidate fitness
        child1.fitness = None
        child2.fitness = None

        return child1, child2
