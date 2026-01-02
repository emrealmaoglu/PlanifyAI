"""
Adaptive H-SAGA Optimizer
==========================

H-SAGA with adaptive operator selection and parameter tuning.

Uses modular operator framework with intelligent selection based on performance.

Key Features:
- Adaptive operator selection (Multi-Armed Bandit inspired)
- Self-tuning parameters (mutation rate, temperature, etc.)
- Modular operator framework (Strategy pattern)
- Performance tracking and credit assignment

Created: 2026-01-02 (Week 4 Day 3)
"""

import logging
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np

from .adaptive import AdaptiveOperatorSelector, AdaptiveParameterTuner, SelectionStrategy
from .base import Optimizer
from .building import Building
from .fitness import FitnessEvaluator
from .operators.registry import create_default_registry
from .solution import Solution

if TYPE_CHECKING:
    from ..constraints.spatial_constraints import ConstraintManager
    from ..data.campus_data import CampusData

logger = logging.getLogger(__name__)


class AdaptiveHSAGA(Optimizer):
    """
    Adaptive H-SAGA optimizer with intelligent operator selection.

    Extends base H-SAGA with:
    - Adaptive operator selection based on performance
    - Self-tuning parameters
    - Credit assignment system
    - Modular operator framework

    Example:
        >>> optimizer = AdaptiveHSAGA(
        ...     buildings,
        ...     bounds,
        ...     strategy=SelectionStrategy.ADAPTIVE_PURSUIT
        ... )
        >>> result = optimizer.optimize()
        >>> print(f"Best fitness: {result['fitness']:.4f}")
        >>> print(f"Operator statistics: {result['operator_stats']}")
    """

    def __init__(
        self,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        campus_data: Optional["CampusData"] = None,
        constraint_manager: Optional["ConstraintManager"] = None,
        constraints: Optional[Dict] = None,
        sa_config: Optional[Dict] = None,
        ga_config: Optional[Dict] = None,
        selection_strategy: SelectionStrategy = SelectionStrategy.ADAPTIVE_PURSUIT,
        enable_adaptive: bool = True,
    ):
        """
        Initialize Adaptive H-SAGA optimizer.

        Args:
            buildings: List of Building objects to place
            bounds: Site boundaries (x_min, y_min, x_max, y_max)
            campus_data: Optional campus data
            constraint_manager: Optional constraint manager
            constraints: Optional constraints dict (legacy)
            sa_config: Optional SA configuration override
            ga_config: Optional GA configuration override
            selection_strategy: Operator selection strategy
            enable_adaptive: Enable adaptive operator selection
        """
        # Validate inputs
        if not buildings:
            raise ValueError("buildings list cannot be empty")

        if len(bounds) != 4:
            raise ValueError(
                f"bounds must be (x_min, y_min, x_max, y_max), got {len(bounds)} values"
            )
        x_min, y_min, x_max, y_max = bounds
        if x_min >= x_max or y_min >= y_max:
            raise ValueError(f"Invalid bounds: {bounds}")

        # Initialize parent Optimizer
        super().__init__(buildings, bounds, config={})

        # Store configuration
        self.campus_data = campus_data
        self.constraint_manager = constraint_manager
        self.constraints = constraints or {}
        self.enable_adaptive = enable_adaptive

        # Initialize fitness evaluator
        self.evaluator = FitnessEvaluator(buildings, bounds)

        # Cache building properties
        self._building_dict = {b.id: b for b in buildings}
        self._building_ids = [b.id for b in buildings]

        # SA configuration
        self.sa_config = sa_config or {
            "initial_temp": 1000.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 500,
            "num_chains": 4,
            "chain_iterations": 500,
        }

        # GA configuration
        self.ga_config = ga_config or {
            "population_size": 50,
            "generations": 50,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 5,
            "tournament_size": 3,
        }

        # Initialize operator framework
        self.registry = create_default_registry()

        # Initialize adaptive operator selector
        self.operator_selector = AdaptiveOperatorSelector(
            registry=self.registry,
            strategy=selection_strategy,
            min_probability=0.05,
            exploration_rate=0.1,
        )

        # Register operators
        if enable_adaptive:
            self._register_operators()

        # Initialize parameter tuner
        self.parameter_tuner = AdaptiveParameterTuner()
        if enable_adaptive:
            self._setup_parameter_schedules()

    def _register_operators(self) -> None:
        """Register all operators for adaptive selection."""
        # Perturbation operators (SA)
        self.operator_selector.register_perturbation("gaussian", scale_factor=10.0, min_sigma=0.1)
        self.operator_selector.register_perturbation("swap")
        self.operator_selector.register_perturbation("reset", margin=10.0)

        # Mutation operators (GA)
        self.operator_selector.register_mutation("gaussian", sigma=30.0, margin=10.0)
        self.operator_selector.register_mutation("swap")
        self.operator_selector.register_mutation("reset", margin=10.0)

        # Crossover operators (GA)
        self.operator_selector.register_crossover("uniform", swap_probability=0.5)
        self.operator_selector.register_crossover("pmx", n_segments=2)

        # Selection operators (GA)
        self.operator_selector.register_selection("tournament", tournament_size=3)
        self.operator_selector.register_selection("roulette", scaling_factor=1.0)

        logger.info("Registered adaptive operators")

    def _setup_parameter_schedules(self) -> None:
        """Setup parameter tuning schedules."""
        # Mutation rate: High exploration → Low exploration
        self.parameter_tuner.add_linear(
            "mutation_rate",
            start_value=self.ga_config["mutation_rate"] * 2,  # 0.3
            end_value=self.ga_config["mutation_rate"] * 0.3,  # 0.045
        )

        # Temperature: Exponential cooling
        self.parameter_tuner.add_exponential(
            "temperature",
            start_value=self.sa_config["initial_temp"],
            end_value=self.sa_config["final_temp"],
            decay_rate=self.sa_config["cooling_rate"],
        )

        # Crossover rate: Slight decrease over time
        self.parameter_tuner.add_linear(
            "crossover_rate",
            start_value=self.ga_config["crossover_rate"],
            end_value=self.ga_config["crossover_rate"] * 0.7,  # 0.56
        )

        logger.info("Setup parameter schedules")

    def optimize(self) -> Dict:
        """
        Complete adaptive H-SAGA optimization pipeline.

        Returns:
            Dict with optimization results including operator statistics
        """
        # Print header
        print("\n" + "=" * 70)
        print("🚀 ADAPTIVE H-SAGA OPTIMIZATION START")
        print("=" * 70)
        print(f"📍 Area: {self.bounds}")
        print(f"🏢 Buildings: {len(self.buildings)}")
        print("⚙️  Configuration:")
        print(f"   SA Chains: {self.sa_config['num_chains']}")
        print(f"   SA Iterations/Chain: {self.sa_config['chain_iterations']}")
        print(f"   GA Population: {self.ga_config['population_size']}")
        print(f"   GA Generations: {self.ga_config['generations']}")
        print(f"   Adaptive: {self.enable_adaptive}")
        if self.enable_adaptive:
            print(f"   Strategy: {self.operator_selector.strategy.value}")
        print("=" * 70)
        print()

        # Initialize statistics
        self.stats["evaluations"] = 0
        start_time = time.perf_counter()

        # Stage 1: Simulated Annealing
        print("🔥 STAGE 1: SIMULATED ANNEALING")
        print("-" * 70)
        sa_start = time.perf_counter()

        sa_solutions = self._simulated_annealing_adaptive()

        sa_time = time.perf_counter() - sa_start
        sa_best_fitness = max(sol.fitness for sol in sa_solutions if sol.fitness is not None)

        print(f"✅ SA Phase complete in {sa_time:.2f}s")
        print(f"   Best fitness: {sa_best_fitness:.4f}")
        print(f"   Solutions: {len(sa_solutions)}")
        print()

        # Stage 2: Genetic Algorithm
        print("🧬 STAGE 2: GENETIC ALGORITHM")
        print("-" * 70)
        ga_start = time.perf_counter()

        ga_solutions = self._genetic_refinement_adaptive(sa_solutions)

        ga_time = time.perf_counter() - ga_start
        ga_best_fitness = max(sol.fitness for sol in ga_solutions if sol.fitness is not None)

        print(f"✅ GA Phase complete in {ga_time:.2f}s")
        print(f"   Best fitness: {ga_best_fitness:.4f}")
        print(f"   Improvement: {ga_best_fitness - sa_best_fitness:+.4f}")
        print()

        # Select best overall
        all_solutions = sa_solutions + ga_solutions
        best_solution = max(
            all_solutions,
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"),
        )

        total_time = time.perf_counter() - start_time

        # Print final results
        print("=" * 70)
        print("✅ ADAPTIVE H-SAGA OPTIMIZATION COMPLETE")
        print("=" * 70)
        print(f"🏆 Best fitness: {best_solution.fitness:.4f}")
        print(f"⏱️  Total runtime: {total_time:.2f}s")
        print(f"   └─ SA: {sa_time:.2f}s ({sa_time/total_time*100:.1f}%)")
        print(f"   └─ GA: {ga_time:.2f}s ({ga_time/total_time*100:.1f}%)")
        print()

        # Print operator statistics if adaptive enabled
        if self.enable_adaptive:
            print("📊 Operator Performance:")
            self._print_operator_statistics()
            print()

        # Get objectives
        objectives = getattr(best_solution, "objectives", {}) or {
            "cost": 0.0,
            "walking": 0.0,
            "adjacency": 0.0,
        }

        print("📊 Objective Breakdown:")
        for obj_name, score in objectives.items():
            print(f"   • {obj_name.capitalize():<12}: {score:.4f}")
        print()

        print("📈 Statistics:")
        print(f"   • Total evaluations: {self.stats.get('evaluations', 0):,}")
        print(f"   • SA iterations: {self.stats.get('iterations', 0):,}")
        print(f"   • GA generations: {self.ga_config['generations']}")
        print("=" * 70)
        print()

        # Prepare result dictionary
        result = {
            "best_solution": best_solution,
            "fitness": best_solution.fitness,
            "objectives": objectives,
            "statistics": {
                "runtime": total_time,
                "sa_time": sa_time,
                "ga_time": ga_time,
                "iterations": self.stats.get("iterations", 0),
                "evaluations": self.stats.get("evaluations", 0),
                "sa_chains": self.sa_config["num_chains"],
                "ga_generations": self.ga_config["generations"],
            },
            "convergence": {
                "sa_history": self.stats.get("convergence_history", []),
                "ga_best_history": self.stats.get("ga_best_history", []),
                "ga_avg_history": self.stats.get("ga_avg_history", []),
            },
            "all_solutions": all_solutions,
        }

        # Add operator statistics if adaptive
        if self.enable_adaptive:
            result["operator_stats"] = self.operator_selector.get_all_statistics()
            result["selection_probabilities"] = self.operator_selector.get_selection_probabilities()

        return result

    def _print_operator_statistics(self) -> None:
        """Print operator performance statistics."""
        stats = self.operator_selector.get_all_statistics()

        for op_type, op_stats in stats.items():
            if not op_stats:
                continue

            print(f"  {op_type.capitalize()}:")
            for name, data in op_stats.items():
                if data["uses"] > 0:
                    print(
                        f"    • {name:<12}: "
                        f"Uses={data['uses']:>4}, "
                        f"Success={data['success_rate']:>5.1%}, "
                        f"Avg Δ={data['avg_improvement']:>+7.4f}"
                    )

    def _simulated_annealing_adaptive(self) -> List[Solution]:
        """
        Run SA phase with adaptive operator selection.

        Returns:
            List of best solutions from each SA chain
        """
        num_chains = self.sa_config.get("num_chains", 4)

        if num_chains == 1:
            solution = self._run_sa_chain_adaptive(0)
            return [solution]

        # Sequential execution (parallel would need picklable operators)
        logger.info(f"Running {num_chains} SA chains with adaptive operators")

        solutions = []
        for seed in range(num_chains):
            np.random.seed(seed)
            solution = self._run_sa_chain_adaptive(seed)
            solutions.append(solution)
            logger.info(f"Chain {seed} completed: fitness={solution.fitness:.4f}")

        solutions.sort(key=lambda s: s.fitness, reverse=True)
        logger.info(f"SA chains completed. Best fitness: {solutions[0].fitness:.4f}")
        return solutions

    def _run_sa_chain_adaptive(self, seed: int) -> Solution:
        """Run single SA chain with adaptive operator selection."""
        # Generate initial solution
        current = self._generate_random_solution()
        current.fitness = self.evaluator.evaluate(current)
        best = current.copy()

        temperature = self.sa_config["initial_temp"]
        final_temp = self.sa_config["final_temp"]
        cooling_rate = self.sa_config["cooling_rate"]
        max_iter = self.sa_config["chain_iterations"]

        chain_history = []

        # SA loop
        for iteration in range(max_iter):
            # Select perturbation operator adaptively
            if self.enable_adaptive:
                op_name, perturbation_op = self.operator_selector.select_perturbation()
            else:
                # Fallback to gaussian
                op_name, perturbation_op = (
                    "gaussian",
                    self.registry.get_perturbation("gaussian", scale_factor=10.0),
                )

            # Generate neighbor
            neighbor = perturbation_op.perturb(current, self.buildings, self.bounds, temperature)
            neighbor.fitness = self.evaluator.evaluate(neighbor)

            # Calculate delta
            delta = neighbor.fitness - current.fitness

            # Metropolis criterion
            accepted = delta > 0 or np.random.random() < np.exp(delta / temperature)

            if accepted:
                # Update credit for successful perturbation
                if self.enable_adaptive:
                    improvement = delta
                    success = delta > 0
                    self.operator_selector.update_perturbation_credit(op_name, improvement, success)

                current = neighbor
                if current.fitness > best.fitness:
                    best = current.copy()

            # Cool down
            temperature *= cooling_rate

            # Track convergence
            if iteration % 50 == 0:
                chain_history.append(best.fitness)

            # Early stopping
            if temperature < final_temp:
                break

        return best

    def _genetic_refinement_adaptive(self, sa_solutions: List[Solution]) -> List[Solution]:
        """
        GA phase with adaptive operator selection.

        Args:
            sa_solutions: Solutions from SA phase

        Returns:
            Best solutions from GA evolution
        """
        logger.info("🧬 Starting adaptive GA phase")

        # Initialize population
        population = self._initialize_ga_population(sa_solutions)
        logger.info(f"  Initial population: {len(population)} individuals")

        # Evaluate initial population
        population = self._evaluate_population_parallel(population)

        # Track convergence
        best_fitness_history = []
        avg_fitness_history = []

        generations = self.ga_config["generations"]

        # Evolution loop
        for generation in range(generations):
            # Get adaptive parameters
            params = self.parameter_tuner.get_parameters(generation, generations)

            # Selection
            parents = self._selection_adaptive(population, params)

            # Crossover
            offspring = self._crossover_adaptive(parents, params)

            # Mutation
            offspring = self._mutation_adaptive(offspring, params)

            # Evaluate offspring
            offspring = self._evaluate_population_parallel(offspring)

            # Replacement (elitism)
            population = self._replacement(population, offspring)

            # Track statistics
            fitnesses = [s.fitness for s in population if s.fitness is not None]
            if fitnesses:
                best_fitness = max(fitnesses)
                avg_fitness = np.mean(fitnesses)
            else:
                best_fitness = 0.0
                avg_fitness = 0.0

            best_fitness_history.append(best_fitness)
            avg_fitness_history.append(avg_fitness)

            # Log progress
            if generation % 10 == 0:
                logger.info(
                    f"  Gen {generation}/{generations}: "
                    f"Best={best_fitness:.4f}, "
                    f"Avg={avg_fitness:.4f}, "
                    f"MutRate={params.get('mutation_rate', 0.15):.3f}"
                )

        # Final stats
        best = max(population, key=lambda s: s.fitness if s.fitness is not None else float("-inf"))
        logger.info("✅ Adaptive GA phase complete")
        logger.info(f"  Final best fitness: {best.fitness:.4f}")

        # Store convergence history
        self.stats["ga_best_history"] = best_fitness_history
        self.stats["ga_avg_history"] = avg_fitness_history

        # Return top solutions
        population.sort(
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"), reverse=True
        )
        return population[:10]

    def _selection_adaptive(self, population: List[Solution], params: Dict) -> List[Solution]:
        """Selection with adaptive operator."""
        n_parents = len(population) // 2

        if self.enable_adaptive:
            _, selection_op = self.operator_selector.select_selection()
        else:
            _, selection_op = "tournament", self.registry.get_selection(
                "tournament", tournament_size=3
            )

        parents = selection_op.select(population, n_select=n_parents)
        return parents

    def _crossover_adaptive(self, parents: List[Solution], params: Dict) -> List[Solution]:
        """Crossover with adaptive operator and rate."""
        offspring = []
        crossover_rate = params.get("crossover_rate", self.ga_config["crossover_rate"])

        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]

            if np.random.random() < crossover_rate:
                if self.enable_adaptive:
                    _, crossover_op = self.operator_selector.select_crossover()
                else:
                    _, crossover_op = "uniform", self.registry.get_crossover("uniform")

                child1, child2 = crossover_op.crossover(parent1, parent2)
                offspring.extend([child1, child2])
            else:
                # No crossover - copy parents
                child1 = parent1.copy()
                child2 = parent2.copy()
                offspring.extend([child1, child2])

        # Handle odd parent
        if len(parents) % 2 == 1:
            offspring.append(parents[-1].copy())

        return offspring

    def _mutation_adaptive(self, offspring: List[Solution], params: Dict) -> List[Solution]:
        """Mutation with adaptive operator and rate."""
        mutation_rate = params.get("mutation_rate", self.ga_config["mutation_rate"])

        for solution in offspring:
            if np.random.random() < mutation_rate:
                if self.enable_adaptive:
                    _, mutation_op = self.operator_selector.select_mutation()
                else:
                    _, mutation_op = "gaussian", self.registry.get_mutation("gaussian", sigma=30.0)

                mutation_op.mutate(solution, self.buildings, self.bounds)
                solution.fitness = None  # Invalidate fitness

        return offspring

    # Helper methods from original H-SAGA

    def _generate_random_solution(self) -> Solution:
        """Generate random valid solution."""
        x_min, y_min, x_max, y_max = self.bounds
        max_attempts = 100

        for attempt in range(max_attempts):
            positions = {}
            valid = True

            for building in self.buildings:
                margin = building.radius + 5.0
                x = np.random.uniform(x_min + margin, x_max - margin)
                y = np.random.uniform(y_min + margin, y_max - margin)
                positions[building.id] = (x, y)

                building.position = (x, y)
                for other_id, other_pos in positions.items():
                    if other_id == building.id:
                        continue
                    other_building = next(b for b in self.buildings if b.id == other_id)
                    other_building.position = other_pos
                    if building.overlaps_with(other_building):
                        valid = False
                        break

                if not valid:
                    break

            if valid:
                return Solution(positions)

        raise RuntimeError(f"Failed to generate valid solution after {max_attempts} attempts")

    def _initialize_ga_population(self, sa_solutions: List[Solution]) -> List[Solution]:
        """Initialize GA population from SA results."""
        pop_size = self.ga_config["population_size"]
        population = []

        # Add best SA solutions (50%)
        n_sa = min(pop_size // 2, len(sa_solutions))
        for i in range(n_sa):
            solution = Solution(
                positions={bid: pos for bid, pos in sa_solutions[i].positions.items()}
            )
            solution.fitness = sa_solutions[i].fitness
            population.append(solution)

        # Add perturbations (30%)
        n_perturb = int(pop_size * 0.3)
        for i in range(n_perturb):
            idx = np.random.randint(0, min(5, len(sa_solutions)))
            base = sa_solutions[idx]
            solution = Solution(positions={bid: pos for bid, pos in base.positions.items()})
            solution.fitness = None
            population.append(solution)

        # Add random solutions (20%)
        n_random = pop_size - len(population)
        for i in range(n_random):
            solution = self._generate_random_solution()
            solution.fitness = None
            population.append(solution)

        return population

    def _evaluate_population_parallel(
        self,
        solutions: List[Solution],
        max_workers: Optional[int] = None,
        parallel_threshold: int = 50,
    ) -> List[Solution]:
        """Evaluate multiple solutions with smart parallelization."""
        to_evaluate = [s for s in solutions if s.fitness is None]

        if not to_evaluate:
            return solutions

        # Sequential for small batches
        if len(to_evaluate) < parallel_threshold:
            for solution in to_evaluate:
                solution.fitness = self.evaluator.evaluate(solution)
                self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1
            return solutions

        # Parallel evaluation
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            if max_workers is None:
                max_workers = min(len(to_evaluate) // 10, 4)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_solution = {
                    executor.submit(self.evaluator.evaluate, sol): sol for sol in to_evaluate
                }

                for future in as_completed(future_to_solution):
                    solution = future_to_solution[future]
                    try:
                        fitness = future.result()
                        solution.fitness = fitness
                        self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1
                    except Exception as e:
                        logger.warning(f"Thread evaluation failed: {e}")
                        solution.fitness = self.evaluator.evaluate(solution)
                        self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1

        except Exception as e:
            logger.warning(f"Parallel evaluation failed: {e}. Using sequential.")
            for solution in to_evaluate:
                solution.fitness = self.evaluator.evaluate(solution)
                self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1

        return solutions

    def _replacement(self, population: List[Solution], offspring: List[Solution]) -> List[Solution]:
        """Elitist replacement strategy."""
        combined = population + offspring
        combined.sort(
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"), reverse=True
        )
        return combined[: self.ga_config["population_size"]]

    def evaluate_solution(self, solution: Solution) -> float:
        """Evaluate fitness of a solution."""
        if solution.fitness is None:
            solution.fitness = self.evaluator.evaluate(solution)
        return solution.fitness
