"""
Uniform Crossover Operator
===========================

Extracted from backend/core/optimization/hsaga.py to follow
Single Responsibility Principle and improve testability.

Uniform crossover selects each gene (building position) randomly from
one of two parents with equal probability.

References:
- Syswerda, G. (1989). Uniform crossover in genetic algorithms.
  In Proceedings of the 3rd International Conference on Genetic Algorithms.
- Spears, W. M., & De Jong, K. A. (1991). On the virtues of parameterized
  uniform crossover. In Proceedings of the 4th International Conference
  on Genetic Algorithms.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Tuple, TypeVar

import numpy as np

# Generic type for solutions (can be any class with positions attribute)
T = TypeVar("T")


class CrossoverOperator(ABC, Generic[T]):
    """
    Base class for crossover operators.

    Provides common interface for different crossover strategies.
    All crossover operators should implement the cross() method.
    """

    def __init__(
        self, crossover_rate: float = 0.8, random_state: Optional[np.random.RandomState] = None
    ):
        """
        Initialize crossover operator.

        Args:
            crossover_rate: Probability of applying crossover (default: 0.8)
            random_state: Random number generator (None = use default)

        Raises:
            ValueError: If crossover_rate not in [0, 1]
        """
        if not 0 <= crossover_rate <= 1:
            raise ValueError("Crossover rate must be between 0 and 1")

        self.crossover_rate = crossover_rate
        self.random_state = random_state or np.random.RandomState()

    @abstractmethod
    def cross(self, parent1: T, parent2: T) -> Tuple[T, T]:
        """
        Apply crossover to two parents to create offspring.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Tuple of two offspring
        """
        pass

    def apply_to_population(self, parents: List[T]) -> List[T]:
        """
        Apply crossover to a population of parents.

        Pairs up parents and applies crossover based on crossover_rate.
        If crossover doesn't occur, parents are copied to offspring.

        Args:
            parents: List of parent solutions

        Returns:
            List of offspring solutions (approximately same size as parents)
        """
        offspring = []

        # Pair up parents (iterate by 2)
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]

            if self.random_state.random() < self.crossover_rate:
                # Apply crossover
                child1, child2 = self.cross(parent1, parent2)
            else:
                # No crossover - copy parents
                child1 = self._copy_parent(parent1)
                child2 = self._copy_parent(parent2)

            offspring.extend([child1, child2])

        # Handle odd number of parents (last one just gets copied)
        if len(parents) % 2 == 1:
            offspring.append(self._copy_parent(parents[-1]))

        return offspring

    def _copy_parent(self, parent: T) -> T:
        """
        Create a copy of the parent solution.

        This method can be overridden for custom copy logic.
        Default implementation assumes parent has a copy() method.

        Args:
            parent: Parent solution to copy

        Returns:
            Copy of parent
        """
        if hasattr(parent, "copy"):
            return parent.copy()
        else:
            raise NotImplementedError(
                f"Parent type {type(parent)} must implement copy() method "
                "or override _copy_parent() in crossover operator"
            )


class UniformCrossover(CrossoverOperator[T]):
    """
    Uniform crossover operator for genetic algorithms.

    For each gene (e.g., building position), randomly selects from parent1 or parent2
    with equal probability. This maintains diversity while combining parent traits.

    Attributes:
        crossover_rate: Probability of applying crossover
        random_state: Random number generator for reproducibility
        swap_probability: Probability of swapping genes (default: 0.5)

    Example:
        >>> crossover = UniformCrossover(crossover_rate=0.8)
        >>> parents = [solution1, solution2, solution3, solution4]
        >>> offspring = crossover.apply_to_population(parents)
        >>> # Returns list of ~4 offspring created via uniform crossover
    """

    def __init__(
        self,
        crossover_rate: float = 0.8,
        swap_probability: float = 0.5,
        random_state: Optional[np.random.RandomState] = None,
    ):
        """
        Initialize uniform crossover operator.

        Args:
            crossover_rate: Probability of applying crossover (default: 0.8)
            swap_probability: Probability of gene swap (default: 0.5)
            random_state: Random number generator (None = use default)

        Raises:
            ValueError: If swap_probability not in [0, 1]
        """
        super().__init__(crossover_rate=crossover_rate, random_state=random_state)

        if not 0 <= swap_probability <= 1:
            raise ValueError("Swap probability must be between 0 and 1")

        self.swap_probability = swap_probability

    def cross(self, parent1: T, parent2: T) -> Tuple[T, T]:
        """
        Apply uniform crossover to two parents.

        For each gene (building position), randomly select from parent1 or parent2.
        Creates two complementary offspring.

        Args:
            parent1: First parent solution
            parent2: Second parent solution

        Returns:
            Tuple of two offspring solutions

        Raises:
            AttributeError: If parents don't have positions attribute
            ValueError: If parents have different building sets
        """
        if not hasattr(parent1, "positions") or not hasattr(parent2, "positions"):
            raise AttributeError("Parents must have 'positions' attribute for uniform crossover")

        # Verify same buildings
        if set(parent1.positions.keys()) != set(parent2.positions.keys()):
            raise ValueError("Parents must have the same set of buildings")

        # Create offspring positions
        child1_positions = {}
        child2_positions = {}

        for building_id in parent1.positions.keys():
            if self.random_state.random() < self.swap_probability:
                # Child1 gets parent1's gene, child2 gets parent2's
                child1_positions[building_id] = parent1.positions[building_id]
                child2_positions[building_id] = parent2.positions[building_id]
            else:
                # Swap: Child1 gets parent2's gene, child2 gets parent1's
                child1_positions[building_id] = parent2.positions[building_id]
                child2_positions[building_id] = parent1.positions[building_id]

        # Create offspring solutions
        # Assumes Solution class constructor: Solution(positions=dict)
        child1 = type(parent1)(positions=child1_positions)
        child2 = type(parent2)(positions=child2_positions)

        # Reset fitness (needs re-evaluation)
        if hasattr(child1, "fitness"):
            child1.fitness = None
        if hasattr(child2, "fitness"):
            child2.fitness = None

        return child1, child2
