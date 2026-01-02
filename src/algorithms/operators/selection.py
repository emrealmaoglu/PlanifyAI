"""
GA Selection Operators
=======================

Operators for selecting individuals for reproduction in Genetic Algorithms.

Created: 2026-01-02 (Week 4 Day 3)
"""

from typing import List

import numpy as np

from ..solution import Solution
from .base import SelectionOperator


class TournamentSelection(SelectionOperator):
    """
    Tournament selection: Select best from random subset.

    Randomly selects k individuals, returns the best.
    Creates selection pressure while maintaining diversity.

    Args:
        tournament_size: Number of individuals per tournament (default 3)
    """

    def __init__(self, tournament_size: int = 3):
        """Initialize tournament selection."""
        self.tournament_size = tournament_size

    def select(
        self,
        population: List[Solution],
        n_select: int = 1,
    ) -> List[Solution]:
        """
        Select individuals via tournament selection.

        Returns deep copies to avoid reference issues.
        """
        if self.tournament_size > len(population):
            raise ValueError(
                f"Tournament size ({self.tournament_size}) cannot exceed "
                f"population size ({len(population)})"
            )

        selected = []

        for _ in range(n_select):
            # Randomly select tournament candidates
            indices = np.random.choice(len(population), self.tournament_size, replace=False)
            candidates = [population[i] for i in indices]

            # Select best (highest fitness)
            valid_candidates = [s for s in candidates if s.fitness is not None]
            if not valid_candidates:
                winner = candidates[0]
            else:
                winner = max(valid_candidates, key=lambda s: s.fitness)

            # Deep copy
            selected_solution = Solution(
                positions={bid: pos for bid, pos in winner.positions.items()}
            )
            selected_solution.fitness = winner.fitness
            if hasattr(winner, "objectives"):
                selected_solution.objectives = winner.objectives.copy()

            selected.append(selected_solution)

        return selected


class RouletteWheelSelection(SelectionOperator):
    """
    Roulette wheel selection: Fitness-proportional selection.

    Probability of selection proportional to fitness.
    Better for problems with large fitness variance.

    Args:
        scaling_factor: Fitness scaling factor to prevent domination (default 1.0)
    """

    def __init__(self, scaling_factor: float = 1.0):
        """Initialize roulette wheel selection."""
        self.scaling_factor = scaling_factor

    def select(
        self,
        population: List[Solution],
        n_select: int = 1,
    ) -> List[Solution]:
        """
        Select individuals via roulette wheel selection.

        Fitness-proportional selection with optional scaling.
        """
        # Extract fitness values
        fitnesses = np.array([s.fitness if s.fitness is not None else 0.0 for s in population])

        # Handle negative fitness (shift to positive)
        if fitnesses.min() < 0:
            fitnesses = fitnesses - fitnesses.min() + 1e-6

        # Apply scaling
        fitnesses = fitnesses**self.scaling_factor

        # Calculate selection probabilities
        total_fitness = fitnesses.sum()
        if total_fitness == 0:
            # Uniform selection if all fitness is 0
            probabilities = np.ones(len(population)) / len(population)
        else:
            probabilities = fitnesses / total_fitness

        # Select individuals
        indices = np.random.choice(len(population), size=n_select, p=probabilities)

        selected = []
        for idx in indices:
            winner = population[idx]

            # Deep copy
            selected_solution = Solution(
                positions={bid: pos for bid, pos in winner.positions.items()}
            )
            selected_solution.fitness = winner.fitness
            if hasattr(winner, "objectives"):
                selected_solution.objectives = winner.objectives.copy()

            selected.append(selected_solution)

        return selected
