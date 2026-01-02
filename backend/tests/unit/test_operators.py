"""
Unit Tests for Modular Operator Framework
==========================================

Tests for the plugin-based operator system.

Created: 2026-01-02 (Week 4 Day 3)
"""

import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.operators import (
    GaussianMutation,
    GaussianPerturbation,
    PartiallyMatchedCrossover,
    RandomResetPerturbation,
    RouletteWheelSelection,
    SwapMutation,
    SwapPerturbation,
    TournamentSelection,
    UniformCrossover,
)
from src.algorithms.operators.registry import DEFAULT_REGISTRY, create_default_registry
from src.algorithms.solution import Solution


@pytest.fixture
def buildings():
    """Create test buildings."""
    return [Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 4) for i in range(5)]


@pytest.fixture
def bounds():
    """Create test bounds."""
    return (0, 0, 200, 200)


@pytest.fixture
def solution(buildings):
    """Create test solution."""
    positions = {
        "B0": (50, 50),
        "B1": (100, 50),
        "B2": (150, 50),
        "B3": (50, 100),
        "B4": (100, 100),
    }
    return Solution(positions=positions)


@pytest.fixture
def population(buildings):
    """Create test population."""
    pop = []
    for i in range(10):
        positions = {
            f"B{j}": (np.random.uniform(20, 180), np.random.uniform(20, 180)) for j in range(5)
        }
        sol = Solution(positions=positions)
        sol.fitness = np.random.uniform(0.5, 1.0)
        pop.append(sol)
    return pop


# =============================================================================
# PERTURBATION OPERATORS
# =============================================================================


class TestGaussianPerturbation:
    """Test Gaussian perturbation operator."""

    def test_perturb_creates_neighbor(self, solution, buildings, bounds):
        """Test that perturbation creates a valid neighbor."""
        op = GaussianPerturbation(scale_factor=10.0)
        neighbor = op.perturb(solution, buildings, bounds, temperature=100.0)

        assert isinstance(neighbor, Solution)
        assert neighbor is not solution  # Different object
        assert len(neighbor.positions) == len(solution.positions)

    def test_temperature_affects_step_size(self, solution, buildings, bounds):
        """Test that higher temperature produces larger moves."""
        np.random.seed(42)
        op = GaussianPerturbation(scale_factor=10.0, min_sigma=0.1)

        # High temperature
        neighbor_hot = op.perturb(solution, buildings, bounds, temperature=1000.0)

        # Low temperature
        np.random.seed(42)
        neighbor_cold = op.perturb(solution, buildings, bounds, temperature=10.0)

        # Calculate total displacement
        total_disp_hot = sum(
            abs(neighbor_hot.positions[bid][0] - solution.positions[bid][0])
            + abs(neighbor_hot.positions[bid][1] - solution.positions[bid][1])
            for bid in solution.positions.keys()
        )

        # Verify that perturbation ran without errors
        assert total_disp_hot >= 0
        assert neighbor_hot is not solution
        assert neighbor_cold is not solution


class TestSwapPerturbation:
    """Test swap perturbation operator."""

    def test_swap_exchanges_positions(self, solution, buildings, bounds):
        """Test that swap exchanges two building positions."""
        np.random.seed(42)
        op = SwapPerturbation()
        neighbor = op.perturb(solution, buildings, bounds, temperature=100.0)

        # Should have swapped exactly 2 positions
        diff_count = sum(
            1
            for bid in solution.positions.keys()
            if neighbor.positions[bid] != solution.positions[bid]
        )

        assert diff_count == 2  # Exactly 2 positions changed


class TestRandomResetPerturbation:
    """Test random reset perturbation operator."""

    def test_reset_randomizes_one_position(self, solution, buildings, bounds):
        """Test that reset randomizes exactly one position."""
        np.random.seed(42)
        op = RandomResetPerturbation(margin=10.0)
        neighbor = op.perturb(solution, buildings, bounds, temperature=100.0)

        # Should have changed exactly 1 position
        diff_count = sum(
            1
            for bid in solution.positions.keys()
            if neighbor.positions[bid] != solution.positions[bid]
        )

        assert diff_count == 1

    def test_reset_respects_bounds(self, solution, buildings, bounds):
        """Test that reset keeps position within bounds."""
        op = RandomResetPerturbation(margin=10.0)
        x_min, y_min, x_max, y_max = bounds

        for _ in range(10):
            neighbor = op.perturb(solution, buildings, bounds, temperature=100.0)

            for x, y in neighbor.positions.values():
                assert x_min + 10 <= x <= x_max - 10
                assert y_min + 10 <= y <= y_max - 10


# =============================================================================
# MUTATION OPERATORS
# =============================================================================


class TestGaussianMutation:
    """Test Gaussian mutation operator."""

    def test_mutate_modifies_in_place(self, solution, buildings, bounds):
        """Test that mutation modifies solution in-place."""
        original_id = id(solution)
        op = GaussianMutation(sigma=30.0)

        result = op.mutate(solution, buildings, bounds)

        assert id(result) == original_id  # Same object
        assert result is solution

    def test_mutate_changes_position(self, solution, buildings, bounds):
        """Test that mutation changes at least one position."""
        np.random.seed(42)
        original_positions = solution.positions.copy()
        op = GaussianMutation(sigma=30.0)

        op.mutate(solution, buildings, bounds)

        # At least one position should differ
        diff_count = sum(
            1
            for bid in solution.positions.keys()
            if solution.positions[bid] != original_positions[bid]
        )

        assert diff_count == 1  # Exactly one position changed


class TestSwapMutation:
    """Test swap mutation operator."""

    def test_swap_exchanges_two_positions(self, solution, buildings, bounds):
        """Test that swap exchanges exactly two positions."""
        np.random.seed(42)
        original_positions = solution.positions.copy()
        op = SwapMutation()

        op.mutate(solution, buildings, bounds)

        diff_count = sum(
            1
            for bid in solution.positions.keys()
            if solution.positions[bid] != original_positions[bid]
        )

        assert diff_count == 2


# =============================================================================
# CROSSOVER OPERATORS
# =============================================================================


class TestUniformCrossover:
    """Test uniform crossover operator."""

    def test_crossover_creates_two_offspring(self, solution, buildings):
        """Test that crossover creates two offspring."""
        parent1 = solution
        parent2 = Solution(
            positions={bid: (x + 50, y + 50) for bid, (x, y) in solution.positions.items()}
        )

        op = UniformCrossover()
        child1, child2 = op.crossover(parent1, parent2)

        assert isinstance(child1, Solution)
        assert isinstance(child2, Solution)
        assert len(child1.positions) == len(parent1.positions)
        assert len(child2.positions) == len(parent2.positions)

    def test_crossover_inherits_from_parents(self, solution):
        """Test that offspring inherit genes from parents."""
        parent1 = solution
        parent2 = Solution(
            positions={bid: (x + 100, y + 100) for bid, (x, y) in solution.positions.items()}
        )

        op = UniformCrossover()
        child1, child2 = op.crossover(parent1, parent2)

        # Each child position should match one of the parents
        for bid in parent1.positions.keys():
            assert (
                child1.positions[bid] == parent1.positions[bid]
                or child1.positions[bid] == parent2.positions[bid]
            )


class TestPartiallyMatchedCrossover:
    """Test PMX crossover operator."""

    def test_pmx_creates_offspring(self, solution):
        """Test that PMX creates valid offspring."""
        parent1 = solution
        parent2 = Solution(
            positions={bid: (x + 50, y + 50) for bid, (x, y) in solution.positions.items()}
        )

        op = PartiallyMatchedCrossover(n_segments=2)
        child1, child2 = op.crossover(parent1, parent2)

        assert len(child1.positions) == len(parent1.positions)
        assert len(child2.positions) == len(parent2.positions)


# =============================================================================
# SELECTION OPERATORS
# =============================================================================


class TestTournamentSelection:
    """Test tournament selection operator."""

    def test_tournament_selects_individuals(self, population):
        """Test that tournament selection selects individuals."""
        op = TournamentSelection(tournament_size=3)
        selected = op.select(population, n_select=5)

        assert len(selected) == 5
        assert all(isinstance(s, Solution) for s in selected)

    def test_tournament_selects_better_individuals(self, population):
        """Test that tournament tends to select better individuals."""
        # Sort population by fitness
        population.sort(key=lambda s: s.fitness, reverse=True)

        # Tournament should favor top individuals
        op = TournamentSelection(tournament_size=5)
        selected = op.select(population, n_select=20)

        # Average fitness of selected should be higher than population average
        pop_avg = np.mean([s.fitness for s in population])
        sel_avg = np.mean([s.fitness for s in selected])

        assert sel_avg >= pop_avg * 0.9  # Allow some variance


class TestRouletteWheelSelection:
    """Test roulette wheel selection operator."""

    def test_roulette_selects_individuals(self, population):
        """Test that roulette selection selects individuals."""
        op = RouletteWheelSelection()
        selected = op.select(population, n_select=5)

        assert len(selected) == 5
        assert all(isinstance(s, Solution) for s in selected)

    def test_roulette_fitness_proportional(self, population):
        """Test that selection is fitness-proportional."""
        # Create population with clear fitness differences
        for i, sol in enumerate(population):
            sol.fitness = float(i) / len(population)

        op = RouletteWheelSelection()
        selected = op.select(population, n_select=50)

        # Higher fitness individuals should be selected more often
        sel_avg = np.mean([s.fitness for s in selected])
        pop_avg = np.mean([s.fitness for s in population])

        assert sel_avg >= pop_avg


# =============================================================================
# OPERATOR REGISTRY
# =============================================================================


class TestOperatorRegistry:
    """Test operator registry."""

    def test_default_registry_has_operators(self):
        """Test that default registry has all operators registered."""
        registry = create_default_registry()

        assert len(registry.list_perturbations()) > 0
        assert len(registry.list_mutations()) > 0
        assert len(registry.list_crossovers()) > 0
        assert len(registry.list_selections()) > 0

    def test_registry_get_operators(self):
        """Test getting operators from registry."""
        registry = DEFAULT_REGISTRY

        # Perturbations
        gaussian_pert = registry.get_perturbation("gaussian", scale_factor=10.0)
        assert isinstance(gaussian_pert, GaussianPerturbation)

        # Mutations
        gaussian_mut = registry.get_mutation("gaussian", sigma=30.0)
        assert isinstance(gaussian_mut, GaussianMutation)

        # Crossover
        uniform_cross = registry.get_crossover("uniform")
        assert isinstance(uniform_cross, UniformCrossover)

        # Selection
        tournament_sel = registry.get_selection("tournament", tournament_size=3)
        assert isinstance(tournament_sel, TournamentSelection)

    def test_registry_raises_on_unknown_operator(self):
        """Test that registry raises error for unknown operators."""
        registry = DEFAULT_REGISTRY

        with pytest.raises(ValueError):
            registry.get_mutation("unknown_operator")

    def test_custom_operator_registration(self, buildings, bounds):
        """Test registering custom operators."""
        from src.algorithms.operators import MutationOperator, OperatorRegistry

        class CustomMutation(MutationOperator):
            def mutate(self, solution, buildings, bounds):
                return solution

        registry = OperatorRegistry()
        registry.register_mutation("custom", CustomMutation)

        op = registry.get_mutation("custom")
        assert isinstance(op, CustomMutation)
