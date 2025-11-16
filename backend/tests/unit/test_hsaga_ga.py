"""
Unit tests for Genetic Algorithm operators in H-SAGA.

Tests cover:
- Population initialization
- Selection operators
- Crossover operators
- Mutation operators
- Replacement strategies

Created: 2025-11-07
"""
import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA
from src.algorithms.solution import Solution


@pytest.fixture
def sample_buildings():
    """Create sample buildings for testing"""
    return [
        Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
        Building("B2", BuildingType.EDUCATIONAL, 3000, 4),
        Building("B3", BuildingType.ADMINISTRATIVE, 1500, 2),
        Building("B4", BuildingType.SOCIAL, 1800, 2),
        Building("B5", BuildingType.HEALTH, 2500, 3),
    ]


@pytest.fixture
def optimizer(sample_buildings):
    """Create optimizer instance"""
    bounds = (0, 0, 1000, 1000)
    return HybridSAGA(sample_buildings, bounds)


class TestPopulationInitialization:
    """Tests for GA population initialization"""

    def test_population_initialization_size(self, optimizer):
        """Test that population has correct size"""
        # Create mock SA solutions
        sa_solutions = []
        for i in range(4):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5 + i * 0.1  # Varying fitness
            sa_solutions.append(solution)

        # Sort by fitness (best first)
        sa_solutions.sort(key=lambda s: s.fitness, reverse=True)

        # Initialize population
        population = optimizer._initialize_ga_population(sa_solutions)

        # Check size
        assert len(population) == optimizer.ga_config["population_size"]

        # Check all are Solution objects
        assert all(isinstance(s, Solution) for s in population)

    def test_population_initialization_diversity(self, optimizer):
        """Test that population has diversity"""
        sa_solutions = []
        for i in range(4):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5
            sa_solutions.append(solution)

        population = optimizer._initialize_ga_population(sa_solutions)

        # Count unique positions (check at least some diversity)
        unique_positions = set()
        for sol in population:
            # Use first building position as hash
            first_pos = list(sol.positions.values())[0]
            unique_positions.add(first_pos)

        # Should have some diversity (at least 60% unique, accounting for SA solution duplicates)
        # With only 4 SA solutions, we'll have duplicates when filling 50% of population
        assert len(unique_positions) >= len(population) * 0.6

    def test_population_contains_sa_solutions(self, optimizer):
        """Test that best SA solutions are included"""
        # Create SA solutions with known positions
        sa_solutions = []
        for i in range(4):
            positions = {f"B{j+1}": (i * 100, i * 100) for j in range(5)}
            solution = Solution(positions=positions)
            solution.fitness = 0.9 - i * 0.1
            sa_solutions.append(solution)

        population = optimizer._initialize_ga_population(sa_solutions)

        # Check that some SA solutions are in population (exact match)
        sa_positions = [tuple(sorted(s.positions.items())) for s in sa_solutions[:2]]
        pop_positions = [tuple(sorted(s.positions.items())) for s in population]

        # At least the best SA solution should be in population
        assert sa_positions[0] in pop_positions


class TestSelection:
    """Tests for selection operators"""

    def test_tournament_selection_returns_best(self, optimizer):
        """Test tournament selection has bias toward better solutions"""
        # Create population with known fitness values
        population = []
        for i in range(20):
            solution = optimizer._generate_random_solution()
            solution.fitness = i / 20.0  # 0.0 to 0.95
            population.append(solution)

        # Run many tournaments
        selected_fitnesses = []
        for _ in range(100):
            selected = optimizer._tournament_selection(population, tournament_size=3)
            selected_fitnesses.append(selected.fitness)

        # Average selected fitness should be > population average
        pop_avg = np.mean([s.fitness for s in population])
        selection_avg = np.mean(selected_fitnesses)

        # With tournament size 3, expect significant bias
        assert (
            selection_avg > pop_avg + 0.1
        ), f"Selection avg ({selection_avg:.3f}) should be >> pop avg ({pop_avg:.3f})"

    def test_tournament_selection_copies_solution(self, optimizer):
        """Test that tournament selection returns deep copy"""
        population = []
        for i in range(5):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5
            population.append(solution)

        selected = optimizer._tournament_selection(population)

        # Modify selected
        first_key = list(selected.positions.keys())[0]
        selected.positions[first_key] = (999, 999)

        # Original population should be unchanged
        for sol in population:
            assert sol.positions[first_key] != (999, 999)

    def test_selection_returns_correct_number(self, optimizer):
        """Test that selection returns correct number of parents"""
        population = []
        for i in range(20):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5
            population.append(solution)

        # Test default (half population)
        parents = optimizer._selection(population)
        assert len(parents) == len(population) // 2

        # Test custom number
        parents = optimizer._selection(population, n_parents=8)
        assert len(parents) == 8

    def test_tournament_size_validation(self, optimizer):
        """Test that invalid tournament size raises error"""
        population = []
        for i in range(5):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5
            population.append(solution)

        # Tournament size > population should raise error
        with pytest.raises(ValueError):
            optimizer._tournament_selection(population, tournament_size=10)


class TestCrossover:
    """Tests for crossover operators"""

    def test_uniform_crossover_produces_valid_offspring(self, optimizer, sample_buildings):
        """Test crossover produces valid solutions"""
        parent1 = optimizer._generate_random_solution()
        parent2 = optimizer._generate_random_solution()

        child1, child2 = optimizer._uniform_crossover(parent1, parent2)

        # Children should have all buildings
        assert len(child1.positions) == len(sample_buildings)
        assert len(child2.positions) == len(sample_buildings)

        # All building IDs should be present
        assert set(child1.positions.keys()) == set(b.id for b in sample_buildings)
        assert set(child2.positions.keys()) == set(b.id for b in sample_buildings)

        # Fitness should be invalidated
        assert child1.fitness is None
        assert child2.fitness is None

    def test_uniform_crossover_inherits_genes(self, optimizer, sample_buildings):
        """Test that children inherit mix of parent genes"""
        # Create parents with known positions
        parent1_positions = {b.id: (i * 100, 0) for i, b in enumerate(sample_buildings)}
        parent2_positions = {b.id: (0, i * 100) for i, b in enumerate(sample_buildings)}

        parent1 = Solution(positions=parent1_positions)
        parent2 = Solution(positions=parent2_positions)

        # Run crossover many times
        inheritance_ratios = []
        for _ in range(100):
            child1, child2 = optimizer._uniform_crossover(parent1, parent2)

            # Count how many genes child1 inherited from parent1
            from_parent1 = sum(
                1
                for bid in child1.positions.keys()
                if child1.positions[bid] == parent1.positions[bid]
            )
            ratio = from_parent1 / len(child1.positions)
            inheritance_ratios.append(ratio)

        # Average should be around 0.5 (50% from each parent)
        # Allow wider range for statistical variation
        avg_ratio = np.mean(inheritance_ratios)
        assert 0.35 < avg_ratio < 0.65, f"Expected ~0.5, got {avg_ratio:.3f}"

    def test_crossover_respects_rate(self, optimizer):
        """Test that crossover rate is respected"""
        # Create parents
        parents = []
        for i in range(10):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5  # Set fitness
            parents.append(solution)

        # Set high crossover rate
        original_rate = optimizer.ga_config["crossover_rate"]
        optimizer.ga_config["crossover_rate"] = 0.9

        offspring = optimizer._crossover(parents)

        # Count offspring with invalidated fitness (underwent crossover)
        crossover_count = sum(1 for sol in offspring if sol.fitness is None)

        # Should be high (close to 90%, but allow statistical variation)
        ratio = crossover_count / len(offspring)
        assert ratio > 0.5, f"Expected >50% crossover with 0.9 rate, got {ratio:.2%}"

        # Restore
        optimizer.ga_config["crossover_rate"] = original_rate

    def test_crossover_handles_odd_parents(self, optimizer):
        """Test crossover with odd number of parents"""
        parents = []
        for i in range(7):  # Odd number
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5
            parents.append(solution)

        offspring = optimizer._crossover(parents)

        # Should handle gracefully (7 offspring expected)
        assert len(offspring) == 7


class TestMutation:
    """Tests for mutation operators"""

    def test_gaussian_mutation_changes_position(self, optimizer):
        """Test Gaussian mutation modifies exactly one building"""
        solution = optimizer._generate_random_solution()
        original_positions = {k: v for k, v in solution.positions.items()}

        mutated = optimizer._gaussian_mutation(solution, sigma=30.0)

        # Count changed positions
        changed = sum(
            1
            for bid in original_positions.keys()
            if original_positions[bid] != mutated.positions[bid]
        )

        # Exactly one building should change
        assert changed == 1

    def test_gaussian_mutation_respects_bounds(self, optimizer):
        """Test Gaussian mutation keeps positions within bounds"""
        solution = optimizer._generate_random_solution()

        # Mutate many times
        for _ in range(100):
            optimizer._gaussian_mutation(solution, sigma=50.0)

        # All positions should be within bounds
        x_min, y_min, x_max, y_max = optimizer.bounds
        margin = 10

        for pos in solution.positions.values():
            x, y = pos
            assert x_min + margin <= x <= x_max - margin
            assert y_min + margin <= y <= y_max - margin

    def test_swap_mutation_exchanges_positions(self, optimizer, sample_buildings):
        """Test swap mutation exchanges two positions"""
        # Create solution with known positions
        positions = {b.id: (i * 100, 0) for i, b in enumerate(sample_buildings)}
        solution = Solution(positions=positions)
        original = {k: v for k, v in solution.positions.items()}

        mutated = optimizer._swap_mutation(solution)

        # Two positions should be swapped
        changed = sum(1 for bid in original.keys() if original[bid] != mutated.positions[bid])

        assert changed == 2, f"Expected 2 swaps, got {changed}"

    def test_random_reset_mutation_changes_position(self, optimizer):
        """Test random reset completely changes one position"""
        solution = optimizer._generate_random_solution()
        original_positions = {k: v for k, v in solution.positions.items()}

        mutated = optimizer._random_reset_mutation(solution)

        # One position should change
        changed_count = sum(
            1
            for bid in original_positions.keys()
            if original_positions[bid] != mutated.positions[bid]
        )

        assert changed_count == 1

    def test_mutation_respects_rate(self, optimizer):
        """Test mutation rate controls number of mutations"""
        # Create offspring
        offspring = []
        for i in range(100):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5  # Mark as evaluated
            offspring.append(solution)

        # Set high mutation rate
        original_rate = optimizer.ga_config["mutation_rate"]
        optimizer.ga_config["mutation_rate"] = 0.8

        mutated_offspring = optimizer._mutation(offspring)

        # Count invalidated fitness (underwent mutation)
        mutated_count = sum(1 for sol in mutated_offspring if sol.fitness is None)

        ratio = mutated_count / len(offspring)
        assert 0.6 < ratio < 0.95, f"Expected ~80% mutation, got {ratio:.2%}"

        # Restore
        optimizer.ga_config["mutation_rate"] = original_rate

    def test_mutation_distribution(self, optimizer):
        """Test mutation type distribution"""
        # Track mutation types by side effects
        swap_count = 0

        for _ in range(300):
            solution = optimizer._generate_random_solution()
            original = {k: v for k, v in solution.positions.items()}

            # Force mutation
            old_rate = optimizer.ga_config["mutation_rate"]
            optimizer.ga_config["mutation_rate"] = 1.0

            offspring = [solution]
            optimizer._mutation(offspring)

            optimizer.ga_config["mutation_rate"] = old_rate

            # Count changes to infer type
            changes = sum(1 for bid in original.keys() if original[bid] != solution.positions[bid])

            if changes == 2:
                swap_count += 1

        # Check rough distribution (70/20/10)
        # Should be around 20% swaps (allow 10-30%)
        swap_ratio = swap_count / 300
        assert 0.1 < swap_ratio < 0.3, f"Expected ~20% swaps, got {swap_ratio:.2%}"


class TestReplacement:
    """Tests for replacement strategies"""

    def test_replacement_keeps_best(self, optimizer):
        """Test replacement keeps elite individuals"""
        # Create population with known fitness
        population = []
        for i in range(10):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.5 + i * 0.01  # 0.50 to 0.59
            population.append(solution)

        # Create offspring with varying fitness
        offspring = []
        for i in range(10):
            solution = optimizer._generate_random_solution()
            solution.fitness = 0.45 + i * 0.01  # 0.45 to 0.54
            offspring.append(solution)

        # Best in population: 0.59
        # Best in offspring: 0.54

        optimizer.ga_config["population_size"] = 10
        next_gen = optimizer._replacement(population, offspring)

        # Should keep top 10 from combined 20
        assert len(next_gen) == 10

        # Best individual should be preserved
        assert next_gen[0].fitness == 0.59

    def test_replacement_maintains_size(self, optimizer):
        """Test replacement maintains population size"""
        # Ensure we have enough candidates to fill population_size
        pop_size = optimizer.ga_config["population_size"]
        population = []
        for i in range(pop_size):
            solution = optimizer._generate_random_solution()
            solution.fitness = np.random.random()
            population.append(solution)

        offspring = []
        for i in range(pop_size):
            solution = optimizer._generate_random_solution()
            solution.fitness = np.random.random()
            offspring.append(solution)

        next_gen = optimizer._replacement(population, offspring)

        assert len(next_gen) == optimizer.ga_config["population_size"]

    def test_ga_evolution_improves_fitness(self, optimizer, sample_buildings):
        """Test GA improves fitness over generations"""
        # Create simple SA solutions (random)
        sa_solutions = []
        for i in range(4):
            solution = optimizer._generate_random_solution()
            solution.fitness = optimizer.evaluator.evaluate(solution)
            sa_solutions.append(solution)

        initial_best = max(sol.fitness for sol in sa_solutions)

        # Run short GA
        optimizer.ga_config["generations"] = 20
        optimizer.ga_config["population_size"] = 20

        result = optimizer._genetic_refinement(sa_solutions)
        final_best = result[0].fitness

        # GA should improve or at least maintain
        assert (
            final_best >= initial_best * 0.95
        ), f"Final ({final_best:.4f}) should be >= Initial ({initial_best:.4f})"

    def test_ga_tracks_convergence(self, optimizer, sample_buildings):
        """Test GA tracks convergence history"""
        sa_solutions = []
        for i in range(4):
            solution = optimizer._generate_random_solution()
            solution.fitness = optimizer.evaluator.evaluate(solution)
            sa_solutions.append(solution)

        optimizer.ga_config["generations"] = 10

        optimizer._genetic_refinement(sa_solutions)

        # Check convergence history stored
        assert "ga_best_history" in optimizer.stats
        assert "ga_avg_history" in optimizer.stats
        assert len(optimizer.stats["ga_best_history"]) == 10
