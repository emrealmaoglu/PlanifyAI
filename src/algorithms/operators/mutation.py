"""
GA Mutation Operators
======================

Operators for mutating solutions in Genetic Algorithms.

Created: 2026-01-02 (Week 4 Day 3)
"""

from typing import List, Tuple

import numpy as np

from ..building import Building
from ..solution import Solution
from .base import MutationOperator


class GaussianMutation(MutationOperator):
    """
    Gaussian mutation: Perturb one building position with Gaussian noise.

    Args:
        sigma: Standard deviation for Gaussian (default 30.0 meters)
        margin: Distance from boundary edges (default 10.0)
    """

    def __init__(self, sigma: float = 30.0, margin: float = 10.0):
        """Initialize Gaussian mutation."""
        self.sigma = sigma
        self.margin = margin

    def mutate(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
    ) -> Solution:
        """
        Mutate solution via Gaussian perturbation.

        Modifies solution in-place.
        """
        # Select random building
        building_id = np.random.choice(list(solution.positions.keys()))
        x, y = solution.positions[building_id]

        # Gaussian perturbation
        dx = np.random.normal(0, self.sigma)
        dy = np.random.normal(0, self.sigma)

        # Apply bounds
        x_min, y_min, x_max, y_max = bounds
        new_x = np.clip(x + dx, x_min + self.margin, x_max - self.margin)
        new_y = np.clip(y + dy, y_min + self.margin, y_max - self.margin)

        # Update position
        solution.positions[building_id] = (new_x, new_y)

        return solution


class SwapMutation(MutationOperator):
    """
    Swap mutation: Exchange positions of two random buildings.

    Provides large-scale exploration without leaving valid space.
    """

    def mutate(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
    ) -> Solution:
        """
        Mutate solution via position swap.

        Modifies solution in-place.
        """
        if len(solution.positions) < 2:
            return solution  # Can't swap with <2 buildings

        # Select two random buildings
        building_ids = list(solution.positions.keys())
        id1, id2 = np.random.choice(building_ids, 2, replace=False)

        # Swap positions
        solution.positions[id1], solution.positions[id2] = (
            solution.positions[id2],
            solution.positions[id1],
        )

        return solution


class RandomResetMutation(MutationOperator):
    """
    Random reset: Completely randomize one building position.

    Provides escape from local optima.

    Args:
        margin: Distance from boundary edges (default 10.0)
    """

    def __init__(self, margin: float = 10.0):
        """Initialize random reset mutation."""
        self.margin = margin

    def mutate(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
    ) -> Solution:
        """
        Mutate solution via random reset.

        Modifies solution in-place.
        """
        # Select random building
        building_id = np.random.choice(list(solution.positions.keys()))

        # Generate completely new random position
        x_min, y_min, x_max, y_max = bounds
        new_x = np.random.uniform(x_min + self.margin, x_max - self.margin)
        new_y = np.random.uniform(y_min + self.margin, y_max - self.margin)

        solution.positions[building_id] = (new_x, new_y)

        return solution
