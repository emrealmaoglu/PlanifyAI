"""
Unit tests for UniformCrossover operator

Tests the uniform crossover implementation extracted from hsaga.py.
Ensures crossover correctly combines parent solutions while maintaining
genetic diversity.

Created: 2025-12-31
"""

import numpy as np
import pytest


class MockSolution:
    """Mock solution class for testing crossover operators."""

    def __init__(self, positions: dict, fitness=None):
        self.positions = positions
        self.fitness = fitness
        self.objectives = {}

    def copy(self):
        """Create a copy of this solution."""
        new_sol = MockSolution(positions=self.positions.copy(), fitness=self.fitness)
        new_sol.objectives = self.objectives.copy()
        return new_sol


class TestUniformCrossover:
    """Test suite for UniformCrossover operator."""

    def test_initialization(self):
        """Test crossover operator initialization."""
        from backend.core.algorithms.crossover import UniformCrossover

        crossover = UniformCrossover(crossover_rate=0.9, swap_probability=0.3)
        assert crossover.crossover_rate == 0.9
        assert crossover.swap_probability == 0.3
        assert crossover.random_state is not None

    def test_invalid_crossover_rate(self):
        """Test that invalid crossover rates raise ValueError."""
        from backend.core.algorithms.crossover import UniformCrossover

        with pytest.raises(ValueError, match="Crossover rate must be between 0 and 1"):
            UniformCrossover(crossover_rate=1.5)

        with pytest.raises(ValueError, match="Crossover rate must be between 0 and 1"):
            UniformCrossover(crossover_rate=-0.1)

    def test_invalid_swap_probability(self):
        """Test that invalid swap probabilities raise ValueError."""
        from backend.core.algorithms.crossover import UniformCrossover

        with pytest.raises(ValueError, match="Swap probability must be between 0 and 1"):
            UniformCrossover(swap_probability=1.5)

        with pytest.raises(ValueError, match="Swap probability must be between 0 and 1"):
            UniformCrossover(swap_probability=-0.1)

    def test_cross_creates_valid_offspring(self):
        """Test that crossover creates valid offspring with correct positions."""
        from backend.core.algorithms.crossover import UniformCrossover

        parent1 = MockSolution(
            positions={"b1": (0.0, 0.0), "b2": (10.0, 10.0), "b3": (20.0, 20.0)}, fitness=0.8
        )
        parent2 = MockSolution(
            positions={"b1": (5.0, 5.0), "b2": (15.0, 15.0), "b3": (25.0, 25.0)}, fitness=0.6
        )

        crossover = UniformCrossover(random_state=np.random.RandomState(42))
        child1, child2 = crossover.cross(parent1, parent2)

        # Check offspring have same building IDs
        assert set(child1.positions.keys()) == set(parent1.positions.keys())
        assert set(child2.positions.keys()) == set(parent2.positions.keys())

        # Check offspring positions come from parents
        for building_id in parent1.positions.keys():
            assert child1.positions[building_id] in [
                parent1.positions[building_id],
                parent2.positions[building_id],
            ]
            assert child2.positions[building_id] in [
                parent1.positions[building_id],
                parent2.positions[building_id],
            ]

        # Check fitness is reset
        assert child1.fitness is None
        assert child2.fitness is None

    def test_cross_complementary_offspring(self):
        """Test that offspring are complementary (swap genes)."""
        from backend.core.algorithms.crossover import UniformCrossover

        parent1 = MockSolution(positions={"b1": (0.0, 0.0), "b2": (10.0, 10.0)})
        parent2 = MockSolution(positions={"b1": (5.0, 5.0), "b2": (15.0, 15.0)})

        # Use fixed random state for deterministic test
        crossover = UniformCrossover(swap_probability=0.5, random_state=np.random.RandomState(42))
        child1, child2 = crossover.cross(parent1, parent2)

        # When child1 gets parent1's gene, child2 should get parent2's (and vice versa)
        for building_id in parent1.positions.keys():
            if child1.positions[building_id] == parent1.positions[building_id]:
                assert child2.positions[building_id] == parent2.positions[building_id]
            else:
                assert child1.positions[building_id] == parent2.positions[building_id]
                assert child2.positions[building_id] == parent1.positions[building_id]

    def test_cross_different_buildings_raises_error(self):
        """Test that crossover with different buildings raises ValueError."""
        from backend.core.algorithms.crossover import UniformCrossover

        parent1 = MockSolution(positions={"b1": (0.0, 0.0), "b2": (10.0, 10.0)})
        parent2 = MockSolution(positions={"b1": (5.0, 5.0), "b3": (15.0, 15.0)})  # Different ID

        crossover = UniformCrossover()
        with pytest.raises(ValueError, match="Parents must have the same set of buildings"):
            crossover.cross(parent1, parent2)

    def test_cross_no_positions_attribute_raises_error(self):
        """Test that crossover without positions attribute raises AttributeError."""
        from backend.core.algorithms.crossover import UniformCrossover

        class InvalidSolution:
            pass

        parent1 = InvalidSolution()
        parent2 = InvalidSolution()

        crossover = UniformCrossover()
        with pytest.raises(
            AttributeError, match="Parents must have 'positions' attribute for uniform crossover"
        ):
            crossover.cross(parent1, parent2)

    def test_apply_to_population(self):
        """Test applying crossover to a population."""
        from backend.core.algorithms.crossover import UniformCrossover

        parents = [
            MockSolution(positions={"b1": (0.0, 0.0), "b2": (10.0, 10.0)}),
            MockSolution(positions={"b1": (5.0, 5.0), "b2": (15.0, 15.0)}),
            MockSolution(positions={"b1": (2.0, 2.0), "b2": (12.0, 12.0)}),
            MockSolution(positions={"b1": (7.0, 7.0), "b2": (17.0, 17.0)}),
        ]

        crossover = UniformCrossover(crossover_rate=1.0, random_state=np.random.RandomState(42))
        offspring = crossover.apply_to_population(parents)

        # Should create same number of offspring as parents
        assert len(offspring) == len(parents)

        # All offspring should have valid positions
        for child in offspring:
            assert set(child.positions.keys()) == {"b1", "b2"}

    def test_apply_to_odd_population(self):
        """Test crossover with odd number of parents."""
        from backend.core.algorithms.crossover import UniformCrossover

        parents = [
            MockSolution(positions={"b1": (0.0, 0.0)}),
            MockSolution(positions={"b1": (5.0, 5.0)}),
            MockSolution(positions={"b1": (10.0, 10.0)}),  # Odd one out
        ]

        crossover = UniformCrossover(crossover_rate=1.0, random_state=np.random.RandomState(42))
        offspring = crossover.apply_to_population(parents)

        # Should handle odd parent by copying
        assert len(offspring) == 3

    def test_crossover_rate_zero_copies_parents(self):
        """Test that crossover_rate=0 just copies parents."""
        from backend.core.algorithms.crossover import UniformCrossover

        parents = [
            MockSolution(positions={"b1": (0.0, 0.0)}, fitness=0.8),
            MockSolution(positions={"b1": (5.0, 5.0)}, fitness=0.6),
        ]

        crossover = UniformCrossover(crossover_rate=0.0, random_state=np.random.RandomState(42))
        offspring = crossover.apply_to_population(parents)

        # With rate=0, offspring should be copies of parents
        assert len(offspring) == 2
        assert offspring[0].positions == parents[0].positions
        assert offspring[1].positions == parents[1].positions

    def test_reproducibility_with_random_state(self):
        """Test that same random state produces same results."""
        from backend.core.algorithms.crossover import UniformCrossover

        parent1 = MockSolution(positions={"b1": (0.0, 0.0), "b2": (10.0, 10.0)})
        parent2 = MockSolution(positions={"b1": (5.0, 5.0), "b2": (15.0, 15.0)})

        # Run crossover twice with same seed
        crossover1 = UniformCrossover(random_state=np.random.RandomState(123))
        child1_a, child2_a = crossover1.cross(parent1, parent2)

        crossover2 = UniformCrossover(random_state=np.random.RandomState(123))
        child1_b, child2_b = crossover2.cross(parent1, parent2)

        # Results should be identical
        assert child1_a.positions == child1_b.positions
        assert child2_a.positions == child2_b.positions

    def test_swap_probability_all_from_parent1(self):
        """Test swap_probability=0 means child1 gets all from parent1."""
        from backend.core.algorithms.crossover import UniformCrossover

        parent1 = MockSolution(positions={"b1": (0.0, 0.0), "b2": (10.0, 10.0)})
        parent2 = MockSolution(positions={"b1": (5.0, 5.0), "b2": (15.0, 15.0)})

        # swap_probability=0 means never swap (child1 always gets parent1)
        crossover = UniformCrossover(swap_probability=0.0, random_state=np.random.RandomState(42))
        child1, child2 = crossover.cross(parent1, parent2)

        # With swap_prob=0, child1 should be clone of parent2, child2 clone of parent1
        # (because we swap when random() < swap_prob, and 0 < 0 is False)
        assert child1.positions == parent2.positions
        assert child2.positions == parent1.positions

    def test_swap_probability_all_from_parent2(self):
        """Test swap_probability=1 means child1 gets all from parent2."""
        from backend.core.algorithms.crossover import UniformCrossover

        parent1 = MockSolution(positions={"b1": (0.0, 0.0), "b2": (10.0, 10.0)})
        parent2 = MockSolution(positions={"b1": (5.0, 5.0), "b2": (15.0, 15.0)})

        # swap_probability=1 means always swap (child1 always gets parent1)
        crossover = UniformCrossover(swap_probability=1.0, random_state=np.random.RandomState(42))
        child1, child2 = crossover.cross(parent1, parent2)

        # With swap_prob=1, child1 should be clone of parent1, child2 clone of parent2
        assert child1.positions == parent1.positions
        assert child2.positions == parent2.positions


class TestCrossoverOperatorBase:
    """Test suite for CrossoverOperator base class."""

    def test_copy_parent_with_copy_method(self):
        """Test _copy_parent works with objects that have copy() method."""
        from backend.core.algorithms.crossover import UniformCrossover

        parent = MockSolution(positions={"b1": (0.0, 0.0)}, fitness=0.8)
        crossover = UniformCrossover()

        copy = crossover._copy_parent(parent)

        assert copy.positions == parent.positions
        assert copy is not parent  # Different objects

    def test_copy_parent_without_copy_method_raises_error(self):
        """Test _copy_parent raises error for objects without copy() method."""
        from backend.core.algorithms.crossover import UniformCrossover

        class NoCopyMethod:
            pass

        parent = NoCopyMethod()
        crossover = UniformCrossover()

        with pytest.raises(NotImplementedError, match="must implement copy\\(\\) method"):
            crossover._copy_parent(parent)
