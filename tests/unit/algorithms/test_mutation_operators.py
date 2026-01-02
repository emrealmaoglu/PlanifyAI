"""
Unit tests for Mutation Operators

Tests mutation operators extracted from hsaga.py to ensure correct
behavior and genetic diversity maintenance.

Created: 2025-12-31
"""

import numpy as np
import pytest


class MockSolution:
    """Mock solution class for testing mutation operators."""

    def __init__(self, positions: dict, fitness=None):
        self.positions = positions
        self.fitness = fitness

    def copy(self):
        """Create a copy of this solution."""
        return MockSolution(positions=self.positions.copy(), fitness=self.fitness)


class TestGaussianMutation:
    """Test suite for GaussianMutation operator."""

    def test_initialization(self):
        """Test Gaussian mutation initialization."""
        from backend.core.algorithms.mutation import GaussianMutation

        mutation = GaussianMutation(
            mutation_rate=0.2, sigma=25.0, bounds=(0, 0, 500, 500), margin=5.0
        )
        assert mutation.mutation_rate == 0.2
        assert mutation.sigma == 25.0
        assert mutation.bounds == (0, 0, 500, 500)
        assert mutation.margin == 5.0
        assert mutation.random_state is not None

    def test_invalid_mutation_rate(self):
        """Test that invalid mutation rates raise ValueError."""
        from backend.core.algorithms.mutation import GaussianMutation

        with pytest.raises(ValueError, match="Mutation rate must be between 0 and 1"):
            GaussianMutation(mutation_rate=1.5)

        with pytest.raises(ValueError, match="Mutation rate must be between 0 and 1"):
            GaussianMutation(mutation_rate=-0.1)

    def test_invalid_sigma(self):
        """Test that invalid sigma raises ValueError."""
        from backend.core.algorithms.mutation import GaussianMutation

        with pytest.raises(ValueError, match="Sigma must be positive"):
            GaussianMutation(sigma=0.0)

        with pytest.raises(ValueError, match="Sigma must be positive"):
            GaussianMutation(sigma=-10.0)

    def test_invalid_margin(self):
        """Test that invalid margin raises ValueError."""
        from backend.core.algorithms.mutation import GaussianMutation

        with pytest.raises(ValueError, match="Margin must be non-negative"):
            GaussianMutation(margin=-5.0)

    def test_mutate_perturbs_position(self):
        """Test that mutation perturbs building position."""
        from backend.core.algorithms.mutation import GaussianMutation

        solution = MockSolution(positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0)})
        original_b1 = solution.positions["b1"]

        mutation = GaussianMutation(
            sigma=10.0, bounds=(0, 0, 500, 500), random_state=np.random.RandomState(42)
        )
        mutated = mutation.mutate(solution)

        # Position should be changed (but same object)
        assert mutated is solution
        assert solution.positions["b1"] != original_b1

    def test_mutate_respects_bounds(self):
        """Test that mutation respects spatial bounds."""
        from backend.core.algorithms.mutation import GaussianMutation

        # Position near edge
        solution = MockSolution(positions={"b1": (495.0, 495.0)})

        mutation = GaussianMutation(
            sigma=100.0,  # Large sigma to test bounds
            bounds=(0, 0, 500, 500),
            margin=10.0,
            random_state=np.random.RandomState(42),
        )

        for _ in range(10):
            mutation.mutate(solution)
            x, y = solution.positions["b1"]
            # Should stay within bounds with margin
            assert 10.0 <= x <= 490.0
            assert 10.0 <= y <= 490.0

    def test_mutate_single_random_building(self):
        """Test that only one random building is mutated."""
        from backend.core.algorithms.mutation import GaussianMutation

        solution = MockSolution(
            positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0), "b3": (300.0, 300.0)}
        )
        original_positions = solution.positions.copy()

        mutation = GaussianMutation(
            sigma=10.0, bounds=(0, 0, 500, 500), random_state=np.random.RandomState(42)
        )
        mutation.mutate(solution)

        # Exactly one building should be mutated
        changed_count = sum(
            1 for bid in solution.positions if solution.positions[bid] != original_positions[bid]
        )
        assert changed_count == 1

    def test_mutate_empty_solution(self):
        """Test mutation with empty solution."""
        from backend.core.algorithms.mutation import GaussianMutation

        solution = MockSolution(positions={})
        mutation = GaussianMutation()

        # Should handle gracefully
        mutated = mutation.mutate(solution)
        assert mutated is solution
        assert len(mutated.positions) == 0

    def test_mutate_no_positions_attribute_raises_error(self):
        """Test that mutation without positions attribute raises AttributeError."""
        from backend.core.algorithms.mutation import GaussianMutation

        class InvalidSolution:
            pass

        solution = InvalidSolution()
        mutation = GaussianMutation()

        with pytest.raises(
            AttributeError, match="Solution must have 'positions' attribute for Gaussian mutation"
        ):
            mutation.mutate(solution)

    def test_apply_to_population(self):
        """Test applying mutation to population."""
        from backend.core.algorithms.mutation import GaussianMutation

        solutions = [
            MockSolution(positions={"b1": (100.0, 100.0)}, fitness=0.8),
            MockSolution(positions={"b1": (200.0, 200.0)}, fitness=0.6),
            MockSolution(positions={"b1": (300.0, 300.0)}, fitness=0.7),
        ]

        mutation = GaussianMutation(
            mutation_rate=1.0,  # Mutate all
            sigma=10.0,
            bounds=(0, 0, 500, 500),
            random_state=np.random.RandomState(42),
        )

        mutated = mutation.apply_to_population(solutions)

        # All solutions should be mutated
        assert len(mutated) == 3
        # Fitness should be invalidated
        assert all(s.fitness is None for s in mutated)

    def test_reproducibility_with_random_state(self):
        """Test that same random state produces same results."""
        from backend.core.algorithms.mutation import GaussianMutation

        solution1 = MockSolution(positions={"b1": (100.0, 100.0)})
        solution2 = MockSolution(positions={"b1": (100.0, 100.0)})

        mutation1 = GaussianMutation(sigma=10.0, random_state=np.random.RandomState(123))
        mutation1.mutate(solution1)

        mutation2 = GaussianMutation(sigma=10.0, random_state=np.random.RandomState(123))
        mutation2.mutate(solution2)

        # Results should be identical
        assert solution1.positions == solution2.positions


class TestSwapMutation:
    """Test suite for SwapMutation operator."""

    def test_initialization(self):
        """Test swap mutation initialization."""
        from backend.core.algorithms.mutation import SwapMutation

        mutation = SwapMutation(mutation_rate=0.2)
        assert mutation.mutation_rate == 0.2
        assert mutation.random_state is not None

    def test_mutate_swaps_two_positions(self):
        """Test that swap mutation exchanges two building positions."""
        from backend.core.algorithms.mutation import SwapMutation

        solution = MockSolution(positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0)})
        original_b1 = solution.positions["b1"]
        original_b2 = solution.positions["b2"]

        mutation = SwapMutation(random_state=np.random.RandomState(42))
        mutated = mutation.mutate(solution)

        # Positions should be swapped
        assert mutated is solution
        assert solution.positions["b1"] == original_b2
        assert solution.positions["b2"] == original_b1

    def test_mutate_with_multiple_buildings(self):
        """Test swap with multiple buildings."""
        from backend.core.algorithms.mutation import SwapMutation

        solution = MockSolution(
            positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0), "b3": (300.0, 300.0)}
        )
        original_positions = solution.positions.copy()

        mutation = SwapMutation(random_state=np.random.RandomState(42))
        mutation.mutate(solution)

        # Exactly two buildings should have swapped positions
        changed_count = sum(
            1 for bid in solution.positions if solution.positions[bid] != original_positions[bid]
        )
        assert changed_count == 2

        # All original positions should still exist
        assert set(solution.positions.values()) == set(original_positions.values())

    def test_mutate_with_single_building(self):
        """Test that swap with single building does nothing."""
        from backend.core.algorithms.mutation import SwapMutation

        solution = MockSolution(positions={"b1": (100.0, 100.0)})
        original_pos = solution.positions["b1"]

        mutation = SwapMutation()
        mutation.mutate(solution)

        # Should remain unchanged
        assert solution.positions["b1"] == original_pos

    def test_mutate_empty_solution(self):
        """Test swap with empty solution."""
        from backend.core.algorithms.mutation import SwapMutation

        solution = MockSolution(positions={})
        mutation = SwapMutation()

        # Should handle gracefully
        mutated = mutation.mutate(solution)
        assert mutated is solution

    def test_mutate_no_positions_attribute_raises_error(self):
        """Test that mutation without positions attribute raises AttributeError."""
        from backend.core.algorithms.mutation import SwapMutation

        class InvalidSolution:
            pass

        solution = InvalidSolution()
        mutation = SwapMutation()

        with pytest.raises(
            AttributeError, match="Solution must have 'positions' attribute for swap mutation"
        ):
            mutation.mutate(solution)

    def test_reproducibility_with_random_state(self):
        """Test that same random state produces same swaps."""
        from backend.core.algorithms.mutation import SwapMutation

        solution1 = MockSolution(
            positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0), "b3": (300.0, 300.0)}
        )
        solution2 = MockSolution(
            positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0), "b3": (300.0, 300.0)}
        )

        mutation1 = SwapMutation(random_state=np.random.RandomState(123))
        mutation1.mutate(solution1)

        mutation2 = SwapMutation(random_state=np.random.RandomState(123))
        mutation2.mutate(solution2)

        # Results should be identical
        assert solution1.positions == solution2.positions


class TestRandomResetMutation:
    """Test suite for RandomResetMutation operator."""

    def test_initialization(self):
        """Test random reset mutation initialization."""
        from backend.core.algorithms.mutation import RandomResetMutation

        mutation = RandomResetMutation(mutation_rate=0.1, bounds=(0, 0, 500, 500), margin=5.0)
        assert mutation.mutation_rate == 0.1
        assert mutation.bounds == (0, 0, 500, 500)
        assert mutation.margin == 5.0
        assert mutation.random_state is not None

    def test_invalid_margin(self):
        """Test that invalid margin raises ValueError."""
        from backend.core.algorithms.mutation import RandomResetMutation

        with pytest.raises(ValueError, match="Margin must be non-negative"):
            RandomResetMutation(margin=-5.0)

    def test_mutate_resets_position(self):
        """Test that mutation completely resets building position."""
        from backend.core.algorithms.mutation import RandomResetMutation

        solution = MockSolution(positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0)})
        original_b1 = solution.positions["b1"]

        mutation = RandomResetMutation(
            bounds=(0, 0, 500, 500), margin=10.0, random_state=np.random.RandomState(42)
        )
        mutated = mutation.mutate(solution)

        # Position should be completely different (very unlikely to match)
        assert mutated is solution
        assert solution.positions["b1"] != original_b1

    def test_mutate_respects_bounds(self):
        """Test that random reset respects spatial bounds."""
        from backend.core.algorithms.mutation import RandomResetMutation

        solution = MockSolution(positions={"b1": (250.0, 250.0)})

        mutation = RandomResetMutation(
            bounds=(0, 0, 500, 500), margin=10.0, random_state=np.random.RandomState(42)
        )

        # Test multiple mutations
        for _ in range(20):
            mutation.mutate(solution)
            x, y = solution.positions["b1"]
            # Should stay within bounds with margin
            assert 10.0 <= x <= 490.0
            assert 10.0 <= y <= 490.0

    def test_mutate_single_random_building(self):
        """Test that only one random building is reset."""
        from backend.core.algorithms.mutation import RandomResetMutation

        solution = MockSolution(
            positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0), "b3": (300.0, 300.0)}
        )
        original_positions = solution.positions.copy()

        mutation = RandomResetMutation(
            bounds=(0, 0, 500, 500), random_state=np.random.RandomState(42)
        )
        mutation.mutate(solution)

        # Exactly one building should be reset
        changed_count = sum(
            1 for bid in solution.positions if solution.positions[bid] != original_positions[bid]
        )
        assert changed_count == 1

    def test_mutate_empty_solution(self):
        """Test mutation with empty solution."""
        from backend.core.algorithms.mutation import RandomResetMutation

        solution = MockSolution(positions={})
        mutation = RandomResetMutation()

        # Should handle gracefully
        mutated = mutation.mutate(solution)
        assert mutated is solution
        assert len(mutated.positions) == 0

    def test_mutate_no_positions_attribute_raises_error(self):
        """Test that mutation without positions attribute raises AttributeError."""
        from backend.core.algorithms.mutation import RandomResetMutation

        class InvalidSolution:
            pass

        solution = InvalidSolution()
        mutation = RandomResetMutation()

        with pytest.raises(
            AttributeError,
            match="Solution must have 'positions' attribute for random reset mutation",
        ):
            mutation.mutate(solution)

    def test_reproducibility_with_random_state(self):
        """Test that same random state produces same results."""
        from backend.core.algorithms.mutation import RandomResetMutation

        solution1 = MockSolution(positions={"b1": (100.0, 100.0)})
        solution2 = MockSolution(positions={"b1": (100.0, 100.0)})

        mutation1 = RandomResetMutation(
            bounds=(0, 0, 500, 500), random_state=np.random.RandomState(123)
        )
        mutation1.mutate(solution1)

        mutation2 = RandomResetMutation(
            bounds=(0, 0, 500, 500), random_state=np.random.RandomState(123)
        )
        mutation2.mutate(solution2)

        # Results should be identical
        assert solution1.positions == solution2.positions


class TestMutationOperatorBase:
    """Test suite for MutationOperator base class."""

    def test_apply_to_population_invalidates_fitness(self):
        """Test that mutation invalidates fitness."""
        from backend.core.algorithms.mutation import SwapMutation

        solutions = [
            MockSolution(positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0)}, fitness=0.8),
            MockSolution(positions={"b1": (150.0, 150.0), "b2": (250.0, 250.0)}, fitness=0.6),
        ]

        mutation = SwapMutation(mutation_rate=1.0, random_state=np.random.RandomState(42))
        mutated = mutation.apply_to_population(solutions)

        # All fitness values should be None
        assert all(s.fitness is None for s in mutated)

    def test_apply_with_zero_mutation_rate(self):
        """Test that mutation_rate=0 changes nothing."""
        from backend.core.algorithms.mutation import SwapMutation

        solutions = [
            MockSolution(positions={"b1": (100.0, 100.0), "b2": (200.0, 200.0)}, fitness=0.8),
            MockSolution(positions={"b1": (150.0, 150.0), "b2": (250.0, 250.0)}, fitness=0.6),
        ]
        original_positions = [s.positions.copy() for s in solutions]

        mutation = SwapMutation(mutation_rate=0.0, random_state=np.random.RandomState(42))
        mutated = mutation.apply_to_population(solutions)

        # Positions should be unchanged
        for i, sol in enumerate(mutated):
            assert sol.positions == original_positions[i]
            assert sol.fitness == [0.8, 0.6][i]  # Fitness not invalidated
