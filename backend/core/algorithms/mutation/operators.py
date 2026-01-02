"""
Mutation Operators
==================

Extracted from backend/core/optimization/hsaga.py to follow
Single Responsibility Principle and improve testability.

Mutation operators provide genetic diversity in evolutionary algorithms
by introducing random changes to solutions.

References:
- Deb, K., & Goyal, M. (1996). A combined genetic adaptive search (GeneAS)
  for engineering design. Computer Science and informatics, 26, 30-45.
- Mühlenbein, H., & Schlierkamp-Voosen, D. (1993). Predictive models for
  the breeder genetic algorithm. Evolutionary computation, 1(1), 25-49.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Tuple, TypeVar

import numpy as np

# Generic type for solutions
T = TypeVar("T")


class MutationOperator(ABC, Generic[T]):
    """
    Base class for mutation operators.

    Provides common interface for different mutation strategies.
    All mutation operators should implement the mutate() method.
    """

    def __init__(
        self, mutation_rate: float = 0.15, random_state: Optional[np.random.RandomState] = None
    ):
        """
        Initialize mutation operator.

        Args:
            mutation_rate: Probability of applying mutation (default: 0.15)
            random_state: Random number generator (None = use default)

        Raises:
            ValueError: If mutation_rate not in [0, 1]
        """
        if not 0 <= mutation_rate <= 1:
            raise ValueError("Mutation rate must be between 0 and 1")

        self.mutation_rate = mutation_rate
        self.random_state = random_state or np.random.RandomState()

    @abstractmethod
    def mutate(self, solution: T) -> T:
        """
        Apply mutation to a solution.

        Args:
            solution: Solution to mutate

        Returns:
            Mutated solution (may be same object or new object)
        """
        pass

    def apply_to_population(self, solutions: List[T]) -> List[T]:
        """
        Apply mutation to a population of solutions.

        Each solution is mutated with probability mutation_rate.

        Args:
            solutions: List of solutions to potentially mutate

        Returns:
            List of solutions (some mutated, some unchanged)
        """
        mutated_count = 0

        for solution in solutions:
            if self.random_state.random() < self.mutation_rate:
                self.mutate(solution)
                mutated_count += 1

                # Invalidate fitness if solution has fitness attribute
                if hasattr(solution, "fitness"):
                    solution.fitness = None

        return solutions


class GaussianMutation(MutationOperator[T]):
    """
    Gaussian mutation operator.

    Perturbs one random building position using Gaussian distribution.
    Provides local search capability and fine-tuning.

    Attributes:
        mutation_rate: Probability of applying mutation
        sigma: Standard deviation for Gaussian perturbation (meters)
        bounds: Spatial bounds (x_min, y_min, x_max, y_max)
        margin: Safety margin from bounds edges (meters)
        random_state: Random number generator

    Example:
        >>> mutation = GaussianMutation(
        ...     mutation_rate=0.15,
        ...     sigma=30.0,
        ...     bounds=(0, 0, 1000, 1000)
        ... )
        >>> solutions = [solution1, solution2, solution3]
        >>> mutated = mutation.apply_to_population(solutions)
    """

    def __init__(
        self,
        mutation_rate: float = 0.15,
        sigma: float = 30.0,
        bounds: Tuple[float, float, float, float] = (0, 0, 1000, 1000),
        margin: float = 10.0,
        random_state: Optional[np.random.RandomState] = None,
    ):
        """
        Initialize Gaussian mutation operator.

        Args:
            mutation_rate: Probability of applying mutation (default: 0.15)
            sigma: Standard deviation for Gaussian perturbation (default: 30.0 meters)
            bounds: Spatial bounds (x_min, y_min, x_max, y_max)
            margin: Safety margin from bounds (default: 10.0 meters)
            random_state: Random number generator (None = use default)

        Raises:
            ValueError: If sigma <= 0 or margin < 0
        """
        super().__init__(mutation_rate=mutation_rate, random_state=random_state)

        if sigma <= 0:
            raise ValueError("Sigma must be positive")
        if margin < 0:
            raise ValueError("Margin must be non-negative")

        self.sigma = sigma
        self.bounds = bounds
        self.margin = margin

    def mutate(self, solution: T) -> T:
        """
        Apply Gaussian mutation to one random building position.

        Perturbs position with Gaussian noise and clips to bounds.

        Args:
            solution: Solution to mutate (modified in-place)

        Returns:
            Mutated solution (same object)

        Raises:
            AttributeError: If solution doesn't have positions attribute
        """
        if not hasattr(solution, "positions"):
            raise AttributeError("Solution must have 'positions' attribute for Gaussian mutation")

        # Select random building
        building_ids = list(solution.positions.keys())
        if not building_ids:
            return solution

        building_id = self.random_state.choice(building_ids)
        x, y = solution.positions[building_id]

        # Gaussian perturbation
        dx = self.random_state.normal(0, self.sigma)
        dy = self.random_state.normal(0, self.sigma)

        # Apply bounds with margin
        x_min, y_min, x_max, y_max = self.bounds
        new_x = np.clip(x + dx, x_min + self.margin, x_max - self.margin)
        new_y = np.clip(y + dy, y_min + self.margin, y_max - self.margin)

        # Update position
        solution.positions[building_id] = (new_x, new_y)

        return solution


class SwapMutation(MutationOperator[T]):
    """
    Swap mutation operator.

    Exchanges positions of two random buildings. Provides large-scale
    exploration without leaving valid solution space.

    Attributes:
        mutation_rate: Probability of applying mutation
        random_state: Random number generator

    Example:
        >>> mutation = SwapMutation(mutation_rate=0.15)
        >>> solutions = [solution1, solution2, solution3]
        >>> mutated = mutation.apply_to_population(solutions)
    """

    def mutate(self, solution: T) -> T:
        """
        Swap positions of two random buildings.

        Args:
            solution: Solution to mutate (modified in-place)

        Returns:
            Mutated solution (same object)

        Raises:
            AttributeError: If solution doesn't have positions attribute
        """
        if not hasattr(solution, "positions"):
            raise AttributeError("Solution must have 'positions' attribute for swap mutation")

        building_ids = list(solution.positions.keys())

        # Need at least 2 buildings to swap
        if len(building_ids) < 2:
            return solution

        # Select two random buildings
        id1, id2 = self.random_state.choice(building_ids, 2, replace=False)

        # Swap positions
        solution.positions[id1], solution.positions[id2] = (
            solution.positions[id2],
            solution.positions[id1],
        )

        return solution


class RandomResetMutation(MutationOperator[T]):
    """
    Random reset mutation operator.

    Completely randomizes one building position within bounds.
    Provides escape mechanism from local optima.

    Attributes:
        mutation_rate: Probability of applying mutation
        bounds: Spatial bounds (x_min, y_min, x_max, y_max)
        margin: Safety margin from bounds edges (meters)
        random_state: Random number generator

    Example:
        >>> mutation = RandomResetMutation(
        ...     mutation_rate=0.15,
        ...     bounds=(0, 0, 1000, 1000)
        ... )
        >>> solutions = [solution1, solution2, solution3]
        >>> mutated = mutation.apply_to_population(solutions)
    """

    def __init__(
        self,
        mutation_rate: float = 0.15,
        bounds: Tuple[float, float, float, float] = (0, 0, 1000, 1000),
        margin: float = 10.0,
        random_state: Optional[np.random.RandomState] = None,
    ):
        """
        Initialize random reset mutation operator.

        Args:
            mutation_rate: Probability of applying mutation (default: 0.15)
            bounds: Spatial bounds (x_min, y_min, x_max, y_max)
            margin: Safety margin from bounds (default: 10.0 meters)
            random_state: Random number generator (None = use default)

        Raises:
            ValueError: If margin < 0
        """
        super().__init__(mutation_rate=mutation_rate, random_state=random_state)

        if margin < 0:
            raise ValueError("Margin must be non-negative")

        self.bounds = bounds
        self.margin = margin

    def mutate(self, solution: T) -> T:
        """
        Completely randomize one building position.

        Generates new random position within bounds.

        Args:
            solution: Solution to mutate (modified in-place)

        Returns:
            Mutated solution (same object)

        Raises:
            AttributeError: If solution doesn't have positions attribute
        """
        if not hasattr(solution, "positions"):
            raise AttributeError(
                "Solution must have 'positions' attribute for random reset mutation"
            )

        # Select random building
        building_ids = list(solution.positions.keys())
        if not building_ids:
            return solution

        building_id = self.random_state.choice(building_ids)

        # Generate completely new random position
        x_min, y_min, x_max, y_max = self.bounds
        new_x = self.random_state.uniform(x_min + self.margin, x_max - self.margin)
        new_y = self.random_state.uniform(y_min + self.margin, y_max - self.margin)

        solution.positions[building_id] = (new_x, new_y)

        return solution
