"""
Unit tests for Tournament Selection Operator

Tests extracted selection logic from hsaga.py to verify correctness
and ensure proper behavior in isolation.
"""

import numpy as np
import pytest

from backend.core.algorithms.selection import BinaryTournamentSelector, TournamentSelector


# Mock Individual class for testing
class MockIndividual:
    def __init__(self, fitness, crowding_distance=None, dominance_rank=None):
        self.fitness = fitness
        self.crowding_distance = crowding_distance
        self.dominance_rank = dominance_rank


class TestTournamentSelector:
    """Test TournamentSelector class."""

    def test_initialization(self):
        """Test selector initialization."""
        selector = TournamentSelector(tournament_size=3)

        assert selector.tournament_size == 3
        assert selector.random_state is not None

    def test_invalid_tournament_size(self):
        """Test that invalid tournament size raises error."""
        with pytest.raises(ValueError, match="Tournament size must be at least 1"):
            TournamentSelector(tournament_size=0)

        with pytest.raises(ValueError, match="Tournament size must be at least 1"):
            TournamentSelector(tournament_size=-1)

    def test_select_from_empty_population(self):
        """Test that selecting from empty population raises error."""
        selector = TournamentSelector()

        with pytest.raises(ValueError, match="Cannot select from empty population"):
            selector.select([])

    def test_select_with_crowding_distance(self):
        """Test selection using crowding distance."""
        # Create population with varying crowding distances
        population = [
            MockIndividual(fitness=[0.5], crowding_distance=1.0),
            MockIndividual(fitness=[0.3], crowding_distance=2.5),  # Best
            MockIndividual(fitness=[0.8], crowding_distance=0.5),
        ]

        selector = TournamentSelector(tournament_size=3, random_state=np.random.RandomState(42))

        # With tournament size = 3, should select individual with highest crowding distance
        selected = selector.select(population)

        assert selected.crowding_distance == 2.5

    def test_select_with_dominance_rank(self):
        """Test selection using dominance rank (lower is better)."""
        # Create population with varying dominance ranks
        population = [
            MockIndividual(fitness=[0.5], dominance_rank=2),
            MockIndividual(fitness=[0.3], dominance_rank=0),  # Best (rank 0)
            MockIndividual(fitness=[0.8], dominance_rank=1),
        ]

        selector = TournamentSelector(tournament_size=3, random_state=np.random.RandomState(42))

        selected = selector.select(population)

        assert selected.dominance_rank == 0

    def test_select_many(self):
        """Test selecting multiple individuals."""
        population = [MockIndividual(fitness=[i], crowding_distance=i) for i in range(10)]

        selector = TournamentSelector(tournament_size=2)

        selected = selector.select_many(population, n=5)

        assert len(selected) == 5
        assert all(ind in population for ind in selected)

    def test_select_many_invalid_n(self):
        """Test that invalid n raises error."""
        selector = TournamentSelector()
        population = [MockIndividual(fitness=[0.5])]

        with pytest.raises(ValueError, match="Must select at least 1 individual"):
            selector.select_many(population, n=0)

    def test_tournament_smaller_than_population(self):
        """Test tournament when population is smaller than tournament size."""
        population = [MockIndividual(fitness=[i], crowding_distance=i) for i in range(3)]

        selector = TournamentSelector(tournament_size=5)  # Larger than population

        # Should work without error (uses entire population as tournament)
        selected = selector.select(population)

        assert selected in population

    def test_reproducibility_with_random_state(self):
        """Test that results are reproducible with same random state."""
        population = [MockIndividual(fitness=[i], crowding_distance=i) for i in range(10)]

        selector1 = TournamentSelector(tournament_size=3, random_state=np.random.RandomState(42))
        selector2 = TournamentSelector(tournament_size=3, random_state=np.random.RandomState(42))

        selected1 = [selector1.select(population) for _ in range(5)]
        selected2 = [selector2.select(population) for _ in range(5)]

        # With same random seed, selections should be identical
        assert selected1 == selected2


class TestBinaryTournamentSelector:
    """Test BinaryTournamentSelector (tournament_size=2)."""

    def test_initialization(self):
        """Test binary tournament selector initialization."""
        selector = BinaryTournamentSelector()

        assert selector.tournament_size == 2

    def test_select_binary(self):
        """Test binary tournament selection."""
        population = [
            MockIndividual(fitness=[0.5], crowding_distance=1.0),
            MockIndividual(fitness=[0.3], crowding_distance=2.5),  # Best
        ]

        selector = BinaryTournamentSelector(random_state=np.random.RandomState(42))

        # With binary tournament, should compare just 2 individuals
        selected = selector.select(population)

        assert selected in population


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_individual_population(self):
        """Test selection from population of size 1."""
        population = [MockIndividual(fitness=[0.5], crowding_distance=1.0)]

        selector = TournamentSelector(tournament_size=2)

        selected = selector.select(population)

        # Should return the only individual
        assert selected == population[0]

    def test_all_individuals_same_fitness(self):
        """Test selection when all individuals have same crowding distance."""
        population = [MockIndividual(fitness=[0.5], crowding_distance=1.0) for _ in range(5)]

        selector = TournamentSelector(tournament_size=3)

        selected = selector.select(population)

        # Should select one (any is valid since all are equal)
        assert selected in population
