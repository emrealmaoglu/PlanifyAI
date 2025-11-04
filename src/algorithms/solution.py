"""
Solution Data Structure
=======================

Represents a spatial planning solution (layout).

Created: 2025-11-03
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from .building import Building


class Solution:
    """
    Spatial planning solution

    A solution is a specific layout: each building has a position.

    Attributes:
        positions: Dict mapping building_id -> (x, y) coordinates
        fitness: Fitness score (higher is better)
        objectives: Individual objective scores
        metadata: Additional solution metadata
    """

    def __init__(
        self,
        positions: Dict[str, Tuple[float, float]],
        fitness: Optional[float] = None,
        objectives: Optional[Dict] = None,
    ):
        """
        Initialize solution

        Args:
            positions: Building ID -> (x, y) coordinate mapping
            fitness: Optional fitness score
            objectives: Optional objective scores dict
        """
        self.positions = positions
        self.fitness = fitness
        self.objectives = objectives or {}
        self.metadata = {}

    def copy(self) -> "Solution":
        """
        Create deep copy of solution

        Returns:
            New Solution instance with copied data
        """
        new_sol = Solution(
            positions=self.positions.copy(),
            fitness=self.fitness,
            objectives=self.objectives.copy() if self.objectives else None,
        )
        new_sol.metadata = self.metadata.copy()
        return new_sol

    def get_position(self, building_id: str) -> Tuple[float, float]:
        """Get position of a building"""
        return self.positions[building_id]

    def set_position(self, building_id: str, position: Tuple[float, float]):
        """Set position of a building"""
        self.positions[building_id] = position
        # Invalidate fitness cache
        self.fitness = None

    def get_all_coordinates(self) -> np.ndarray:
        """
        Get all coordinates as NumPy array

        Returns:
            Array of shape (n_buildings, 2)
        """
        return np.array(list(self.positions.values()))

    def compute_centroid(self) -> Tuple[float, float]:
        """
        Compute centroid of all buildings

        Returns:
            (x, y) coordinates of centroid
        """
        coords = self.get_all_coordinates()
        return tuple(coords.mean(axis=0))

    def compute_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Compute bounding box of layout

        Returns:
            (x_min, y_min, x_max, y_max)
        """
        coords = self.get_all_coordinates()
        x_min, y_min = coords.min(axis=0)
        x_max, y_max = coords.max(axis=0)
        return x_min, y_min, x_max, y_max

    def is_valid(self, buildings: List[Building], bounds: Tuple) -> bool:
        """
        Check if solution is valid

        Checks:
        - All buildings within bounds
        - No overlaps

        Args:
            buildings: List of Building objects
            bounds: (x_min, y_min, x_max, y_max)

        Returns:
            True if solution is valid
        """
        x_min, y_min, x_max, y_max = bounds

        # Check bounds
        for building in buildings:
            if building.id not in self.positions:
                return False

            x, y = self.positions[building.id]
            margin = building.radius

            if x - margin < x_min or x + margin > x_max or y - margin < y_min or y + margin > y_max:
                return False

        # Check overlaps
        for i, b1 in enumerate(buildings):
            b1.position = self.positions[b1.id]
            for b2 in buildings[i + 1 :]:
                b2.position = self.positions[b2.id]
                if b1.overlaps_with(b2):
                    return False

        return True

    def __repr__(self) -> str:
        fitness_str = f"{self.fitness:.4f}" if self.fitness else "unscored"
        return f"Solution({len(self.positions)} buildings, fitness={fitness_str})"
