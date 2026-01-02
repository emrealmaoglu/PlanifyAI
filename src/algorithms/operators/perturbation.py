"""
SA Perturbation Operators
==========================

Operators for generating neighbor solutions in Simulated Annealing.

Created: 2026-01-02 (Week 4 Day 3)
"""

from typing import List, Tuple

import numpy as np

from ..building import Building
from ..solution import Solution
from .base import PerturbationOperator


class GaussianPerturbation(PerturbationOperator):
    """
    Gaussian perturbation: Perturb one building position with Gaussian noise.

    Temperature-adaptive: σ = T / scale_factor

    Args:
        scale_factor: Temperature divisor for sigma (default 10.0)
        min_sigma: Minimum sigma value (default 0.1)
    """

    def __init__(self, scale_factor: float = 10.0, min_sigma: float = 0.1):
        """Initialize Gaussian perturbation."""
        self.scale_factor = scale_factor
        self.min_sigma = min_sigma

    def perturb(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        temperature: float,
    ) -> Solution:
        """
        Generate neighbor via Gaussian move.

        Selects one random building and perturbs its position with
        Gaussian noise. Step size adapts to temperature.
        """
        new_solution = solution.copy()
        new_positions = new_solution.positions.copy()

        # Select random building
        building_id = np.random.choice(list(new_positions.keys()))
        x, y = new_positions[building_id]

        # Temperature-adaptive sigma
        sigma = max(temperature / self.scale_factor, self.min_sigma)

        # Gaussian perturbation
        dx = np.random.normal(0, sigma)
        dy = np.random.normal(0, sigma)

        # Clip to bounds
        x_min, y_min, x_max, y_max = bounds
        building = next(b for b in buildings if b.id == building_id)
        margin = building.radius + 5.0

        new_x = np.clip(x + dx, x_min + margin, x_max - margin)
        new_y = np.clip(y + dy, y_min + margin, y_max - margin)

        new_positions[building_id] = (new_x, new_y)
        new_solution.positions = new_positions

        return new_solution


class SwapPerturbation(PerturbationOperator):
    """
    Swap perturbation: Exchange positions of two random buildings.

    Provides large-scale exploration while maintaining validity.
    """

    def perturb(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        temperature: float,
    ) -> Solution:
        """Generate neighbor via position swap."""
        new_solution = solution.copy()
        new_positions = new_solution.positions.copy()

        building_ids = list(new_positions.keys())
        if len(building_ids) >= 2:
            id1, id2 = np.random.choice(building_ids, size=2, replace=False)
            new_positions[id1], new_positions[id2] = (
                new_positions[id2],
                new_positions[id1],
            )

        new_solution.positions = new_positions
        return new_solution


class RandomResetPerturbation(PerturbationOperator):
    """
    Random reset: Completely randomize one building position.

    Provides escape mechanism from local optima.

    Args:
        margin: Distance from boundary edges (default 10.0)
    """

    def __init__(self, margin: float = 10.0):
        """Initialize random reset perturbation."""
        self.margin = margin

    def perturb(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        temperature: float,
    ) -> Solution:
        """Generate neighbor via random reset."""
        new_solution = solution.copy()
        new_positions = new_solution.positions.copy()

        # Select random building
        building_id = np.random.choice(list(new_positions.keys()))
        building = next(b for b in buildings if b.id == building_id)

        # Random position within bounds
        x_min, y_min, x_max, y_max = bounds
        margin = building.radius + self.margin

        x = np.random.uniform(x_min + margin, x_max - margin)
        y = np.random.uniform(y_min + margin, y_max - margin)

        new_positions[building_id] = (x, y)
        new_solution.positions = new_positions

        return new_solution
