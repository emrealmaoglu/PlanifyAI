"""
Genetic Algorithm Refiner
==========================

Phase 2 of H-SAGA: Local refinement via evolutionary operators.

Extracted from hsaga.py to follow Single Responsibility Principle.
This module handles all GA-specific logic including:
- Population initialization
- Selection (tournament)
- Crossover (uniform)
- Mutation (composite: Gaussian, Swap, Reset)
- Replacement (elitism)
- Convergence tracking

References:
    - Li et al. (2025): Reverse hybrid approach (GA for refinement)
    - Deb & Goyal (1996): Combined genetic adaptive search
    - Mühlenbein & Schlierkamp-Voosen (1993): Breeder GA

Created: 2026-01-01
"""

import logging
from typing import List, Optional

import numpy as np

from backend.core.algorithms.crossover.uniform import UniformCrossover
from backend.core.algorithms.mutation.operators import (
    GaussianMutation,
    RandomResetMutation,
    SwapMutation,
)
from backend.core.algorithms.selection.tournament import TournamentSelector

from .building import Building
from .fitness import FitnessEvaluator
from .solution import Solution

logger = logging.getLogger(__name__)


class GAConfig:
    """Configuration for Genetic Algorithm phase."""

    def __init__(
        self,
        population_size: int = 50,
        generations: int = 50,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.15,
        elite_size: int = 5,
        tournament_size: int = 3,
        random_seed: Optional[int] = None,
    ):
        """
        Initialize GA configuration.

        Args:
            population_size: Number of individuals in population (default: 50)
            generations: Number of evolutionary generations (default: 50)
            crossover_rate: Probability of crossover (default: 0.8)
            mutation_rate: Probability of mutation per individual (default: 0.15)
            elite_size: Number of elite solutions to preserve (default: 5)
            tournament_size: Tournament selection size (default: 3)
            random_seed: Seed for reproducibility (default: None)
        """
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.random_seed = random_seed


class GARefiner:
    """
    Genetic Algorithm Refiner for local optimization.

    Takes diverse SA solutions and refines them using evolutionary operators
    to find high-quality local optima.
    """

    def __init__(
        self,
        config: GAConfig,
        evaluator: FitnessEvaluator,
        buildings: List[Building],
        bounds: tuple,
    ):
        """
        Initialize GA Refiner.

        Args:
            config: GA configuration parameters
            evaluator: Fitness evaluation function
            buildings: List of buildings to place
            bounds: Spatial bounds (x_min, y_min, x_max, y_max)
        """
        self.config = config
        self.evaluator = evaluator
        self.buildings = buildings
        self.bounds = bounds

        # Statistics
        self.stats = {"evaluations": 0, "best_history": [], "avg_history": []}

        # Random state (shared across operators for reproducibility)
        self._random_state = np.random.RandomState(config.random_seed)

        # Initialize GA operators
        self._setup_operators()

    def _setup_operators(self) -> None:
        """Initialize evolutionary operators with shared random state."""
        # Selection operator
        self._tournament_selector = TournamentSelector(
            tournament_size=self.config.tournament_size,
            random_state=self._random_state,
        )

        # Crossover operator
        self._crossover_operator = UniformCrossover(
            crossover_rate=self.config.crossover_rate,
            swap_probability=0.5,
            random_state=self._random_state,
        )

        # Mutation operators (composite strategy: 70% Gaussian, 20% Swap, 10% Reset)
        self._gaussian_mutation = GaussianMutation(
            mutation_rate=self.config.mutation_rate,
            sigma=30.0,
            bounds=self.bounds,
            margin=10.0,
            random_state=self._random_state,
        )

        self._swap_mutation = SwapMutation(
            mutation_rate=self.config.mutation_rate,
            random_state=self._random_state,
        )

        self._random_reset_mutation = RandomResetMutation(
            mutation_rate=self.config.mutation_rate,
            bounds=self.bounds,
            margin=10.0,
            random_state=self._random_state,
        )

    def refine(self, seed_solutions: List[Solution]) -> List[Solution]:
        """
        Refine SA solutions using genetic algorithm.

        Args:
            seed_solutions: Best solutions from SA phase

        Returns:
            Top 10 solutions from GA evolution (sorted by fitness)
        """
        logger.info("🧬 Starting GA refinement...")

        # Initialize population (50% SA, 30% perturbed, 20% random)
        population = self._initialize_population(seed_solutions)
        self._evaluate_population(population)

        # Track convergence
        self.stats["best_history"] = []
        self.stats["avg_history"] = []

        # Evolution loop
        for generation in range(self.config.generations):
            # Standard GA cycle: Selection → Crossover → Mutation → Replacement
            parents = self._selection(population)
            offspring = self._crossover(parents)
            offspring = self._mutation(offspring)
            self._evaluate_population(offspring)
            population = self._replacement(population, offspring)

            # Track convergence statistics
            fitnesses = [s.fitness for s in population if s.fitness is not None]
            self.stats["best_history"].append(max(fitnesses) if fitnesses else 0.0)
            self.stats["avg_history"].append(np.mean(fitnesses) if fitnesses else 0.0)

            # Log progress every 10 generations
            if generation % 10 == 0:
                logger.info(
                    f"  Gen {generation}: Best={self.stats['best_history'][-1]:.4f}, "
                    f"Avg={self.stats['avg_history'][-1]:.4f}"
                )

        # Log completion
        improvement = self.stats["best_history"][-1] - self.stats["best_history"][0]
        logger.info(
            f"✅ GA refinement complete. Best: {self.stats['best_history'][-1]:.4f}, "
            f"Improvement: {improvement:+.4f}"
        )

        # Return top 10 solutions
        population.sort(
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"),
            reverse=True,
        )
        return population[:10]

    def _initialize_population(self, sa_solutions: List[Solution]) -> List[Solution]:
        """
        Initialize GA population: 50% SA solutions, 30% perturbed, 20% random.

        Args:
            sa_solutions: Best solutions from SA phase

        Returns:
            Initial GA population
        """
        population = []
        pop_size = self.config.population_size

        # 1. Best SA solutions (50%)
        n_sa = min(pop_size // 2, len(sa_solutions))
        for i in range(n_sa):
            solution = Solution(
                positions={bid: pos for bid, pos in sa_solutions[i].positions.items()}
            )
            solution.fitness = sa_solutions[i].fitness
            if hasattr(sa_solutions[i], "objectives"):
                solution.objectives = sa_solutions[i].objectives.copy()
            population.append(solution)

        # 2. Perturbed SA solutions (30%)
        for _ in range(int(pop_size * 0.3)):
            base = sa_solutions[self._random_state.randint(0, min(5, len(sa_solutions)))]
            solution = Solution(positions={bid: pos for bid, pos in base.positions.items()})
            # Light perturbation (T=50 equivalent)
            self._light_perturbation(solution)
            solution.fitness = None
            population.append(solution)

        # 3. Random solutions (20%)
        for _ in range(pop_size - len(population)):
            solution = self._generate_random_solution()
            solution.fitness = None
            population.append(solution)

        logger.info(
            f"GA init: {n_sa} SA + {int(pop_size*0.3)} perturbed + "
            f"{pop_size-len(population)} random = {len(population)} total"
        )
        return population

    def _generate_random_solution(self) -> Solution:
        """Generate random solution within bounds."""
        x_min, y_min, x_max, y_max = self.bounds
        margin = 10.0

        positions = {}
        for building in self.buildings:
            x = self._random_state.uniform(x_min + margin, x_max - margin)
            y = self._random_state.uniform(y_min + margin, y_max - margin)
            positions[building.id] = (x, y)

        return Solution(positions=positions)

    def _light_perturbation(self, solution: Solution) -> None:
        """Apply light Gaussian perturbation to solution."""
        # Equivalent to SA perturbation at T=50
        sigma = 5.0
        building_ids = list(solution.positions.keys())
        if not building_ids:
            return

        building_id = self._random_state.choice(building_ids)
        x, y = solution.positions[building_id]

        dx = self._random_state.normal(0, sigma)
        dy = self._random_state.normal(0, sigma)

        x_min, y_min, x_max, y_max = self.bounds
        margin = 10.0
        new_x = np.clip(x + dx, x_min + margin, x_max - margin)
        new_y = np.clip(y + dy, y_min + margin, y_max - margin)

        solution.positions[building_id] = (new_x, new_y)

    def _evaluate_population(self, population: List[Solution]) -> None:
        """Evaluate all solutions with None fitness."""
        for solution in population:
            if solution.fitness is None:
                solution.fitness = self.evaluator.evaluate(solution)
                self.stats["evaluations"] += 1

    def _selection(
        self, population: List[Solution], n_parents: Optional[int] = None
    ) -> List[Solution]:
        """
        Select parents for reproduction using tournament selection.

        Args:
            population: Current population (must have fitness evaluated)
            n_parents: Number of parents to select (default: len(population) // 2)

        Returns:
            List of selected parent solutions
        """
        if n_parents is None:
            n_parents = len(population) // 2

        parents = []
        for _ in range(n_parents):
            # Use extracted tournament selector
            parent = self._tournament_selector.select(population)

            # Deep copy to avoid reference issues
            selected = Solution(positions={bid: pos for bid, pos in parent.positions.items()})
            selected.fitness = parent.fitness
            if hasattr(parent, "objectives"):
                selected.objectives = parent.objectives.copy()

            parents.append(selected)

        logger.debug(f"Selected {len(parents)} parents via tournament selection")
        return parents

    def _crossover(self, parents: List[Solution]) -> List[Solution]:
        """
        Create offspring via uniform crossover.

        Args:
            parents: Selected parent solutions

        Returns:
            Offspring solutions (approximately same size as parents)
        """
        # Use extracted crossover operator
        offspring = self._crossover_operator.apply_to_population(parents)

        logger.debug(f"Crossover: Created {len(offspring)} offspring from {len(parents)} parents")
        return offspring

    def _mutation(self, offspring: List[Solution]) -> List[Solution]:
        """
        Apply mutation to offspring population.

        Uses composite mutation strategy (extracted operators):
        - Gaussian: 70% (local search)
        - Swap: 20% (exploration)
        - Random reset: 10% (escape mechanism)

        Args:
            offspring: Offspring solutions to potentially mutate

        Returns:
            Mutated offspring
        """
        mutated_count = 0

        for solution in offspring:
            if self._random_state.random() < self.config.mutation_rate:
                # Select mutation type based on research-backed distribution
                mut_type = self._random_state.choice(
                    ["gaussian", "swap", "reset"], p=[0.7, 0.2, 0.1]
                )

                if mut_type == "gaussian":
                    self._gaussian_mutation.mutate(solution)
                elif mut_type == "swap":
                    self._swap_mutation.mutate(solution)
                else:  # reset
                    self._random_reset_mutation.mutate(solution)

                # Invalidate fitness (needs re-evaluation)
                solution.fitness = None
                mutated_count += 1

        logger.debug(f"Mutation: Mutated {mutated_count}/{len(offspring)} offspring")
        return offspring

    def _replacement(self, population: List[Solution], offspring: List[Solution]) -> List[Solution]:
        """
        Replace population using elitism (keep best solutions).

        Args:
            population: Current population
            offspring: New offspring

        Returns:
            Next generation population
        """
        # Combine parent and offspring populations
        combined = population + offspring

        # Sort by fitness (descending)
        combined.sort(
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"),
            reverse=True,
        )

        # Select top N (elitism)
        next_gen = combined[: self.config.population_size]

        logger.debug(f"Replacement: Selected top {len(next_gen)} from {len(combined)} candidates")

        return next_gen
