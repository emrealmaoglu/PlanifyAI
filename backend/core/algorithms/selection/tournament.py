"""
Tournament Selection Operator

Extracted from backend/core/optimization/hsaga.py to follow
Single Responsibility Principle and improve testability.

Tournament selection is a genetic algorithm selection method where
k individuals are randomly chosen from the population and the best
individual from this group is selected.

References:
- Goldberg, D. E., & Deb, K. (1991). A comparative analysis of selection schemes
  used in genetic algorithms. Foundations of genetic algorithms, 1, 69-93.
"""

import random
from typing import List, Optional, TypeVar

import numpy as np

# Generic type for individuals (can be any class with fitness attribute)
T = TypeVar("T")


class TournamentSelector:
    """
    Tournament selection operator for evolutionary algorithms.

    Attributes:
        tournament_size: Number of individuals in each tournament (default: 2)
        random_state: Random number generator for reproducibility

    Example:
        >>> selector = TournamentSelector(tournament_size=3)
        >>> population = [Individual(fitness=[0.5, 0.3]), Individual(fitness=[0.2, 0.8]), ...]
        >>> selected = selector.select(population)
        >>> # Returns best individual from random tournament of size 3
    """

    def __init__(
        self, tournament_size: int = 2, random_state: Optional[np.random.RandomState] = None
    ):
        """
        Initialize tournament selector.

        Args:
            tournament_size: Number of individuals competing in each tournament
            random_state: Random number generator (None = use default)

        Raises:
            ValueError: If tournament_size < 1
        """
        if tournament_size < 1:
            raise ValueError("Tournament size must be at least 1")

        self.tournament_size = tournament_size
        self.random_state = random_state or np.random.RandomState()

    def select(self, population: List[T]) -> T:
        """
        Select one individual via tournament selection.

        Args:
            population: List of individuals to select from

        Returns:
            Selected individual (best from tournament)

        Raises:
            ValueError: If population is empty or smaller than tournament size
        """
        if not population:
            raise ValueError("Cannot select from empty population")

        if len(population) < self.tournament_size:
            # If population smaller than tournament, use entire population
            tournament = population
        else:
            # Randomly select tournament_size individuals
            tournament_indices = self.random_state.choice(
                len(population), size=self.tournament_size, replace=False
            )
            tournament = [population[i] for i in tournament_indices]

        # Return best individual from tournament
        # Assumes individuals have dominance comparison or fitness attribute
        return self._select_best(tournament)

    def select_many(self, population: List[T], n: int) -> List[T]:
        """
        Select n individuals via repeated tournament selection.

        Args:
            population: List of individuals to select from
            n: Number of individuals to select

        Returns:
            List of n selected individuals

        Raises:
            ValueError: If n < 1
        """
        if n < 1:
            raise ValueError("Must select at least 1 individual")

        return [self.select(population) for _ in range(n)]

    def _select_best(self, tournament: List[T]) -> T:
        """
        Select best individual from tournament.

        This method can be overridden for different comparison criteria.
        Default: Uses crowding distance if available, else random.

        Args:
            tournament: List of individuals in tournament

        Returns:
            Best individual
        """
        # Priority: dominance_rank > crowding_distance > random

        # If individuals have dominance_rank, use it (lower is better)
        if hasattr(tournament[0], "dominance_rank") and tournament[0].dominance_rank is not None:
            return min(tournament, key=lambda x: x.dominance_rank)

        # If individuals have crowding_distance attribute, use it
        if (
            hasattr(tournament[0], "crowding_distance")
            and tournament[0].crowding_distance is not None
        ):
            return max(tournament, key=lambda x: x.crowding_distance)

        # Fallback: Random selection
        return random.choice(tournament)


class BinaryTournamentSelector(TournamentSelector):
    """
    Binary tournament selection (most common variant).

    Simplified interface for tournament size = 2.
    """

    def __init__(self, random_state: Optional[np.random.RandomState] = None):
        """Initialize binary tournament selector (size=2)."""
        super().__init__(tournament_size=2, random_state=random_state)
