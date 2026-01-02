"""
NSGA-III Optimizer
==================

Non-dominated Sorting Genetic Algorithm III for many-objective optimization.

NSGA-III uses reference points instead of crowding distance for better
diversity preservation in many-objective problems (4+ objectives).

Key Features:
- Reference-point based selection
- Adaptive normalization
- Fast non-dominated sorting
- Genetic operators (crossover, mutation)

Reference:
Deb, K., & Jain, H. (2014). "An Evolutionary Many-Objective Optimization
Algorithm Using Reference-Point-Based Nondominated Sorting Approach."

Created: 2026-01-02 (Week 4 Day 4)
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..base import Optimizer
from ..building import Building
from ..fitness import FitnessEvaluator
from ..operators.registry import OperatorRegistry, create_default_registry
from ..solution import Solution
from .niching import (
    adaptive_nadir_estimation,
    associate_to_reference_points,
    compute_ideal_point,
    niche_preserving_selection,
    normalize_objectives,
)
from .nondominated_sort import fast_nondominated_sort
from .reference_points import generate_reference_points

logger = logging.getLogger(__name__)


class NSGA3(Optimizer):
    """
    NSGA-III optimizer for many-objective spatial planning.

    Optimizes multiple objectives simultaneously and returns Pareto front
    of non-dominated solutions.

    Example:
        >>> from src.algorithms import NSGA3, Building, BuildingType
        >>> buildings = [
        ...     Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
        ...     Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        ... ]
        >>> optimizer = NSGA3(
        ...     buildings=buildings,
        ...     bounds=(0, 0, 500, 500),
        ...     population_size=100,
        ...     n_generations=100,
        ...     n_partitions=12,  # For 3 objectives
        ... )
        >>> result = optimizer.optimize()
        >>> pareto_front = result["pareto_front"]  # List of non-dominated solutions
    """

    def __init__(
        self,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        population_size: int = 100,
        n_generations: int = 100,
        n_partitions: int = 12,
        crossover_rate: float = 0.9,
        mutation_rate: float = 0.1,
        tournament_size: int = 2,
        reference_points: Optional[np.ndarray] = None,
        use_two_layer: bool = False,
        n_partitions_inner: int = 6,
        registry: Optional[OperatorRegistry] = None,
    ):
        """
        Initialize NSGA-III optimizer.

        Args:
            buildings: List of buildings to place
            bounds: Site boundaries (x_min, y_min, x_max, y_max)
            population_size: Population size (should be close to number of reference points)
            n_generations: Number of generations
            n_partitions: Number of partitions for reference point generation
            crossover_rate: Probability of crossover
            mutation_rate: Probability of mutation
            tournament_size: Tournament size for selection
            reference_points: Custom reference points (optional)
            use_two_layer: Use two-layer reference points for many objectives
            n_partitions_inner: Inner layer partitions (if use_two_layer=True)
            registry: Operator registry (uses default if None)
        """
        self.buildings = buildings
        self.bounds = bounds
        self.population_size = population_size
        self.n_generations = n_generations
        self.n_partitions = n_partitions
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.use_two_layer = use_two_layer
        self.n_partitions_inner = n_partitions_inner

        # Initialize evaluator
        self.evaluator = FitnessEvaluator(buildings=buildings, bounds=bounds)

        # Get number of objectives from evaluator
        self.n_objectives = len(self.evaluator.get_objective_names())

        # Generate reference points
        if reference_points is not None:
            self.reference_points = reference_points
        elif use_two_layer:
            from .reference_points import generate_two_layer_reference_points

            self.reference_points = generate_two_layer_reference_points(
                n_objectives=self.n_objectives,
                n_partitions_outer=n_partitions,
                n_partitions_inner=n_partitions_inner,
            )
        else:
            self.reference_points = generate_reference_points(
                n_objectives=self.n_objectives,
                n_partitions=n_partitions,
            )

        logger.info(
            f"Generated {len(self.reference_points)} reference points "
            f"for {self.n_objectives} objectives"
        )

        # Operator registry
        self.registry = registry or create_default_registry()

        # Statistics
        self.stats = {
            "evaluations": 0,
            "generations": 0,
        }

    def optimize(self) -> Dict:
        """
        Run NSGA-III optimization.

        Returns:
            Dict containing:
            - pareto_front: List of non-dominated solutions
            - population: Final population
            - pareto_objectives: Objectives of Pareto front solutions
            - reference_points: Reference points used
            - statistics: Optimization statistics
            - convergence: Convergence history
        """
        logger.info("=" * 70)
        logger.info("🚀 NSGA-III OPTIMIZATION START")
        logger.info("=" * 70)
        logger.info(f"🏢 Buildings: {len(self.buildings)}")
        logger.info(f"📍 Bounds: {self.bounds}")
        logger.info(f"🎯 Objectives: {self.n_objectives}")
        logger.info(f"📊 Reference points: {len(self.reference_points)}")
        logger.info(f"👥 Population size: {self.population_size}")
        logger.info(f"🔄 Generations: {self.n_generations}")
        logger.info("=" * 70)

        # Initialize population
        population = self._initialize_population()
        population = self._evaluate_population(population)

        # Track convergence
        convergence_history = {
            "hypervolume": [],
            "n_pareto_front": [],
            "ideal_point": [],
        }

        # Main evolution loop
        for generation in range(self.n_generations):
            # Generate offspring
            offspring = self._generate_offspring(population)
            offspring = self._evaluate_population(offspring)

            # Combine parent and offspring
            combined = population + offspring

            # Extract objectives for all solutions
            objectives = self._extract_objectives(combined)

            # Non-dominated sorting
            fronts, ranks = fast_nondominated_sort(objectives)

            # Compute ideal and nadir points
            ideal_point = compute_ideal_point(objectives)
            nadir_point = adaptive_nadir_estimation(objectives, fronts[0], self.reference_points)

            # Normalize objectives
            normalized_objectives = normalize_objectives(objectives, ideal_point, nadir_point)

            # Associate solutions to reference points
            associations, distances = associate_to_reference_points(
                normalized_objectives,
                self.reference_points,
            )

            # Environmental selection
            population = self._environmental_selection(
                combined,
                fronts,
                associations,
                distances,
            )

            # Track convergence
            convergence_history["n_pareto_front"].append(len(fronts[0]))
            convergence_history["ideal_point"].append(ideal_point)

            if generation % 10 == 0 or generation == self.n_generations - 1:
                logger.info(
                    f"Gen {generation}/{self.n_generations}: "
                    f"Pareto front size={len(fronts[0])}, "
                    f"Ideal point={ideal_point}"
                )

        # Final evaluation
        final_objectives = self._extract_objectives(population)
        fronts, ranks = fast_nondominated_sort(final_objectives)

        # Extract Pareto front
        pareto_front = [population[i] for i in fronts[0]]
        pareto_objectives = final_objectives[fronts[0]]

        logger.info("=" * 70)
        logger.info("✅ NSGA-III OPTIMIZATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"🏆 Pareto front size: {len(pareto_front)}")
        logger.info(f"📊 Total evaluations: {self.stats['evaluations']}")
        logger.info("=" * 70)

        return {
            "pareto_front": pareto_front,
            "population": population,
            "pareto_objectives": pareto_objectives,
            "reference_points": self.reference_points,
            "statistics": self.stats,
            "convergence": convergence_history,
        }

    def _initialize_population(self) -> List[Solution]:
        """Initialize random population."""
        population = []

        for _ in range(self.population_size):
            solution = self._generate_random_solution()
            population.append(solution)

        return population

    def _generate_random_solution(self) -> Solution:
        """Generate random valid solution."""
        x_min, y_min, x_max, y_max = self.bounds
        max_attempts = 100

        for _ in range(max_attempts):
            positions = {}
            for building in self.buildings:
                x = np.random.uniform(x_min, x_max)
                y = np.random.uniform(y_min, y_max)
                positions[building.id] = (x, y)

            solution = Solution(positions=positions)
            solution.fitness = None
            return solution

        raise RuntimeError(f"Failed to generate valid solution after {max_attempts} attempts")

    def _evaluate_population(self, population: List[Solution]) -> List[Solution]:
        """Evaluate all solutions that don't have fitness yet."""
        for solution in population:
            if solution.fitness is None:
                self.evaluate_solution(solution)

        return population

    def evaluate_solution(self, solution: Solution) -> float:
        """
        Evaluate solution and store multi-objective values.

        For NSGA-III, we store all objective values in solution.objectives
        and use weighted sum as solution.fitness for compatibility.
        """
        # Get detailed objective breakdown
        objectives_dict = self.evaluator.evaluate_detailed(solution)

        # Extract objective values in consistent order
        objective_names = self.evaluator.get_objective_names()
        objective_values = np.array([objectives_dict[name] for name in objective_names])

        # Store multi-objective values
        solution.objectives = objective_values

        # Store weighted sum as fitness (for backward compatibility)
        solution.fitness = self.evaluator.evaluate(solution)

        self.stats["evaluations"] += 1

        return solution.fitness

    def _extract_objectives(self, population: List[Solution]) -> np.ndarray:
        """Extract objective values from population."""
        return np.array([sol.objectives for sol in population])

    def _generate_offspring(self, population: List[Solution]) -> List[Solution]:
        """Generate offspring using genetic operators."""
        offspring = []

        while len(offspring) < self.population_size:
            # Tournament selection
            parent1 = self._tournament_selection(population)
            parent2 = self._tournament_selection(population)

            # Crossover
            if np.random.random() < self.crossover_rate:
                crossover_op = self.registry.get_crossover("uniform")
                child1, child2 = crossover_op.crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            # Mutation
            for child in [child1, child2]:
                if np.random.random() < self.mutation_rate:
                    mutation_op = self.registry.get_mutation("gaussian", sigma=30.0)
                    mutation_op.mutate(child, self.buildings, self.bounds)

                child.fitness = None
                child.objectives = None

            offspring.extend([child1, child2])

        return offspring[: self.population_size]

    def _tournament_selection(self, population: List[Solution]) -> Solution:
        """Binary tournament selection."""
        indices = np.random.choice(len(population), self.tournament_size, replace=False)
        tournament = [population[i] for i in indices]

        # Compare using fitness (weighted sum)
        best = max(tournament, key=lambda s: s.fitness if s.fitness is not None else -np.inf)
        return best

    def _environmental_selection(
        self,
        population: List[Solution],
        fronts: List[List[int]],
        associations: np.ndarray,
        distances: np.ndarray,
    ) -> List[Solution]:
        """
        Environmental selection using reference-point based niching.

        Fills next generation by:
        1. Adding complete fronts until population size is reached
        2. Using niche-preserving selection for last front
        """
        selected = []

        for front in fronts:
            if len(selected) + len(front) <= self.population_size:
                # Add entire front
                selected.extend([population[i] for i in front])
            else:
                # Need to select from this front using niching
                n_remaining = self.population_size - len(selected)

                selected_from_front = niche_preserving_selection(
                    front=front,
                    associations=associations,
                    distances=distances,
                    reference_points=self.reference_points,
                    n_select=n_remaining,
                )

                selected.extend([population[i] for i in selected_from_front])
                break

        return selected
