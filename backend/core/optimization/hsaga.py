"""
Hybrid Simulated Annealing - Genetic Algorithm
===============================================
H-SAGA optimizer implementing Li et al. 2025 reverse hybrid approach.

SA Phase (Day 2): Global exploration with parallel chains
GA Phase (Day 3): Local refinement

Created: 2025-11-03
"""
import logging
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np

from backend.core.algorithms.crossover.uniform import UniformCrossover
from backend.core.algorithms.mutation.operators import (
    GaussianMutation,
    RandomResetMutation,
    SwapMutation,
)

# Genetic algorithm operators (extracted for modularity and testability)
from backend.core.algorithms.selection.tournament import TournamentSelector

from .base import Optimizer
from .building import Building
from .fitness import FitnessEvaluator
from .solution import Solution

if TYPE_CHECKING:
    from ..constraints.spatial_constraints import ConstraintManager
    from ..data.campus_data import CampusData

logger = logging.getLogger(__name__)


# Module-level function for multiprocessing (must be picklable)
def _run_sa_chain_worker(
    buildings: List[Building],
    bounds: Tuple[float, float, float, float],
    seed: int,
    config: Dict,
) -> Solution:
    """
    Module-level worker function for running SA chain in parallel.

    This function is picklable and can be used with multiprocessing.

    Args:
        buildings: List of Building objects (picklable)
        bounds: Site boundaries (x_min, y_min, x_max, y_max)
        seed: Random seed for reproducibility
        config: SA configuration dict

    Returns:
        Best Solution found in this chain
    """
    # Set random seed for this worker
    np.random.seed(seed)

    # Create fitness evaluator
    evaluator = FitnessEvaluator(buildings, bounds)

    # Generate random solution
    x_min, y_min, x_max, y_max = bounds
    max_attempts = 100

    current = None
    for attempt in range(max_attempts):
        positions = {}
        valid = True

        for building in buildings:
            margin = building.radius + 5.0
            x = np.random.uniform(x_min + margin, x_max - margin)
            y = np.random.uniform(y_min + margin, y_max - margin)
            positions[building.id] = (x, y)

            building.position = (x, y)
            for other_id, other_pos in positions.items():
                if other_id == building.id:
                    continue
                other_building = next(b for b in buildings if b.id == other_id)
                other_building.position = other_pos
                if building.overlaps_with(other_building):
                    valid = False
                    break

            if not valid:
                break

        if valid:
            current = Solution(positions)
            break

    if current is None:
        raise RuntimeError(f"Failed to generate valid solution after {max_attempts} attempts")

    # Initialize SA state
    current.fitness = evaluator.evaluate(current)
    best = current.copy()

    temperature = config["initial_temp"]
    final_temp = config["final_temp"]
    cooling_rate = config["cooling_rate"]
    max_iter = config["chain_iterations"]

    # SA loop
    for iteration in range(max_iter):
        # Generate neighbor
        neighbor = _perturb_solution_worker(current, buildings, bounds, temperature)
        neighbor.fitness = evaluator.evaluate(neighbor)

        # Calculate delta
        delta = neighbor.fitness - current.fitness

        # Metropolis criterion
        if delta > 0 or np.random.random() < np.exp(delta / temperature):
            current = neighbor
            if current.fitness > best.fitness:
                best = current.copy()

        # Cool down
        temperature *= cooling_rate

        # Early stopping if temperature too low
        if temperature < final_temp:
            break

    return best


def _perturb_solution_worker(
    solution: Solution,
    buildings: List[Building],
    bounds: Tuple[float, float, float, float],
    temperature: float,
) -> Solution:
    """
    Module-level perturbation function for multiprocessing.

    Args:
        solution: Current solution
        buildings: List of Building objects (for radius lookup)
        bounds: Site boundaries
        temperature: Current SA temperature

    Returns:
        New Solution (neighbor)
    """
    new_solution = solution.copy()
    new_positions = new_solution.positions.copy()

    # Select perturbation operator
    rand = np.random.random()

    if rand < 0.80:
        # Gaussian move (80%)
        building_id = np.random.choice(list(new_positions.keys()))
        x, y = new_positions[building_id]

        sigma = max(temperature / 10.0, 0.1)
        dx = np.random.normal(0, sigma)
        dy = np.random.normal(0, sigma)

        x_min, y_min, x_max, y_max = bounds
        building = next(b for b in buildings if b.id == building_id)
        margin = building.radius + 5.0

        new_x = np.clip(x + dx, x_min + margin, x_max - margin)
        new_y = np.clip(y + dy, y_min + margin, y_max - margin)
        new_positions[building_id] = (new_x, new_y)

    elif rand < 0.95:
        # Swap buildings (15%)
        building_ids = list(new_positions.keys())
        if len(building_ids) >= 2:
            id1, id2 = np.random.choice(building_ids, size=2, replace=False)
            new_positions[id1], new_positions[id2] = (
                new_positions[id2],
                new_positions[id1],
            )

    else:
        # Random reset (5%)
        building_id = np.random.choice(list(new_positions.keys()))
        x_min, y_min, x_max, y_max = bounds
        building = next(b for b in buildings if b.id == building_id)
        margin = building.radius + 5.0

        x = np.random.uniform(x_min + margin, x_max - margin)
        y = np.random.uniform(y_min + margin, y_max - margin)
        new_positions[building_id] = (x, y)

    new_solution.positions = new_positions
    return new_solution


class HybridSAGA(Optimizer):
    """
    Hybrid Simulated Annealing + Genetic Algorithm optimizer.

    Algorithm: Li et al. 2025 reverse hybrid
    - Stage 1 (SA): Global exploration with parallel chains (200 iterations)
    - Stage 2 (GA): Local refinement (100 generations) - Day 3

    SA Configuration (Day 2):
    - Initial temperature: 1000.0
    - Final temperature: 0.1
    - Cooling rate: 0.95 (geometric)
    - Max iterations: 500 per chain
    - Parallel chains: 4 (M1 performance cores)

    Perturbation Operators:
    - Gaussian move (80%): σ = T/10, single building position jitter
    - Swap buildings (15%): Exchange positions of two buildings
    - Random reset (5%): Completely randomize one building position

    Example:
        >>> optimizer = HybridSAGA(buildings, bounds)
        >>> result = optimizer.optimize()
        >>> print(f"Best fitness: {result['fitness']:.4f}")
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
    ):
        """
        Initialize H-SAGA optimizer.

        Args:
            buildings: List of Building objects to place
            bounds: Site boundaries (x_min, y_min, x_max, y_max)
            campus_data: Optional campus data (if provided, bounds can be derived)
            constraint_manager: Optional constraint manager for spatial constraints
            constraints: Optional constraints dict (legacy, for backwards compatibility)
            sa_config: Optional SA configuration override
            ga_config: Optional GA configuration (for Day 3)

        Raises:
            ValueError: If buildings empty, bounds invalid, or oversized footprints
        """
        # Validate buildings
        if not buildings:
            raise ValueError("buildings list cannot be empty")

        # Handle campus_data and bounds
        if campus_data is not None:
            # Use bounds from campus_data if bounds not explicitly provided
            # For now, we still require bounds, but can derive from campus_data if needed
            if bounds is None or bounds == (0, 0, 0, 0):
                bounds = campus_data.get_bounds()

        # Validate bounds
        if len(bounds) != 4:
            raise ValueError(
                f"bounds must be (x_min, y_min, x_max, y_max), got {len(bounds)} values"
            )
        x_min, y_min, x_max, y_max = bounds
        if x_min >= x_max or y_min >= y_max:
            raise ValueError(
                f"Invalid bounds: x_min={x_min} >= x_max={x_max} or "
                f"y_min={y_min} >= y_max={y_max}"
            )

        # Check for oversized footprints
        site_area = (x_max - x_min) * (y_max - y_min)
        for building in buildings:
            if building.footprint > 0.8 * site_area:
                raise ValueError(
                    f"Building {building.id} footprint ({building.footprint}m²) "
                    f"exceeds 80% of site area"
                )

        # Initialize parent Optimizer
        super().__init__(buildings, bounds, config={})

        # Initialize fitness evaluator
        self.evaluator = FitnessEvaluator(buildings, bounds)

        # Store campus data and constraint manager
        self.campus_data = campus_data
        self.constraint_manager = constraint_manager

        # Store legacy constraints (for backwards compatibility)
        self.constraints = constraints or {}

        # Cache building properties for faster access (Day 5 optimization)
        self._building_dict = {b.id: b for b in buildings}
        self._building_ids = [b.id for b in buildings]
        self._building_types = np.array([b.type.value for b in buildings])
        self._building_areas = np.array([b.area for b in buildings])
        self._building_floors = np.array([b.floors for b in buildings])

        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Cached building properties for {len(buildings)} buildings")

        # SA configuration (Li et al. 2025 + research synthesis)
        self.sa_config = sa_config or {
            "initial_temp": 1000.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,  # Geometric schedule
            "max_iterations": 500,
            "num_chains": 4,  # M1: 4 performance cores
            "chain_iterations": 500,
        }

        # GA configuration (Day 4)
        self.ga_config = ga_config or {
            "population_size": 50,  # Population size
            "generations": 50,  # Number of generations
            "crossover_rate": 0.8,  # Probability of crossover
            "mutation_rate": 0.15,  # Probability of mutation
            "elite_size": 5,  # Number of elite individuals
            "tournament_size": 3,  # Tournament selection size
        }

        # Initialize GA operators (extracted for modularity and testability)
        # All operators share a single random state for reproducibility
        self._random_state = np.random.RandomState()

        # Selection operator
        self._tournament_selector = TournamentSelector(
            tournament_size=self.ga_config["tournament_size"],
            random_state=self._random_state,
        )

        # Crossover operator
        self._crossover_operator = UniformCrossover(
            crossover_rate=self.ga_config["crossover_rate"],
            swap_probability=0.5,
            random_state=self._random_state,
        )

        # Mutation operators (composite strategy: 70% Gaussian, 20% Swap, 10% Reset)
        self._gaussian_mutation = GaussianMutation(
            mutation_rate=self.ga_config["mutation_rate"],
            sigma=30.0,
            bounds=self.bounds,
            margin=10.0,
            random_state=self._random_state,
        )

        self._swap_mutation = SwapMutation(
            mutation_rate=self.ga_config["mutation_rate"],
            random_state=self._random_state,
        )

        self._random_reset_mutation = RandomResetMutation(
            mutation_rate=self.ga_config["mutation_rate"],
            bounds=self.bounds,
            margin=10.0,
            random_state=self._random_state,
        )

    def _print_optimization_header(self) -> None:
        """Print H-SAGA optimization start header."""
        print("\n" + "=" * 70)
        print("🚀 H-SAGA OPTIMIZATION START")
        print("=" * 70)
        print(f"📍 Area: {self.bounds}")
        print(f"🏢 Buildings: {len(self.buildings)}")
        print("⚙️  Configuration:")
        print(f"   SA Chains: {self.sa_config['num_chains']}")
        print(f"   SA Iterations/Chain: {self.sa_config['chain_iterations']}")
        print(f"   GA Population: {self.ga_config['population_size']}")
        print(f"   GA Generations: {self.ga_config['generations']}")
        print("=" * 70)
        print()

    def _print_final_results(
        self, best_solution: Solution, total_time: float, sa_time: float, ga_time: float
    ) -> None:
        """Print final optimization results and statistics."""
        print("=" * 70)
        print("✅ H-SAGA OPTIMIZATION COMPLETE")
        print("=" * 70)
        print(f"🏆 Best fitness: {best_solution.fitness:.4f}")
        print(f"⏱️  Total runtime: {total_time:.2f}s")
        print(f"   └─ SA: {sa_time:.2f}s ({sa_time/total_time*100:.1f}%)")
        print(f"   └─ GA: {ga_time:.2f}s ({ga_time/total_time*100:.1f}%)")
        print()

        # Get objectives if available
        objectives = {}
        if hasattr(best_solution, "objectives") and best_solution.objectives:
            objectives = best_solution.objectives.copy()
        else:
            objectives = {"cost": 0.0, "walking": 0.0, "adjacency": 0.0}

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

    def _generate_road_network(self, best_solution: Solution) -> Tuple[List, List, Dict]:
        """
        Generate road network from optimized building positions.

        Args:
            best_solution: Best solution with building positions

        Returns:
            Tuple of (major_roads, minor_roads, road_stats)
        """
        print("🛣️  Generating road network...")
        road_start = time.perf_counter()

        # Get buildings with positions from best solution
        buildings_with_positions = []
        for building in self.buildings:
            if building.id in best_solution.positions:
                building_copy = Building(
                    id=building.id,
                    type=building.type,
                    area=building.area,
                    floors=building.floors,
                    position=best_solution.positions[building.id],
                    constraints=building.constraints.copy() if building.constraints else {},
                )
                buildings_with_positions.append(building_copy)

        # Generate road network
        major_roads = []
        minor_roads = []
        road_stats = {}

        try:
            from src.spatial.road_network import RoadNetworkConfig, RoadNetworkGenerator

            road_config = RoadNetworkConfig(
                n_major_roads=4,
                major_road_max_length=500.0,
                n_agents_per_building=2,
                agent_max_steps=30,
            )

            road_generator = RoadNetworkGenerator(
                bounds=self.bounds,
                config=road_config,
            )

            major_roads, minor_roads = road_generator.generate(buildings_with_positions)
            road_stats = road_generator.get_stats()

            road_time = time.perf_counter() - road_start
            print(f"✅ Road network generated in {road_time:.2f}s")
            print(f"   Major roads: {road_stats.get('n_major_roads', 0)}")
            print(f"   Minor roads: {road_stats.get('n_minor_roads', 0)}")
            print(f"   Total length: {road_stats.get('total_length_m', 0):.0f}m")
        except Exception as e:
            logger.warning(f"Road generation failed: {e}")

        return major_roads, minor_roads, road_stats

    def _prepare_result(
        self,
        best_solution: Solution,
        all_solutions: List[Solution],
        total_time: float,
        sa_time: float,
        ga_time: float,
        major_roads: List,
        minor_roads: List,
        road_stats: Dict,
    ) -> Dict:
        """
        Prepare final optimization result dictionary.

        Args:
            best_solution: Best solution found
            all_solutions: All final solutions (SA + GA)
            total_time: Total optimization time
            sa_time: SA phase time
            ga_time: GA phase time
            major_roads: Major road segments
            minor_roads: Minor road segments
            road_stats: Road network statistics

        Returns:
            Complete result dictionary
        """
        # Get objectives
        objectives = {}
        if hasattr(best_solution, "objectives") and best_solution.objectives:
            objectives = best_solution.objectives.copy()
        else:
            objectives = {"cost": 0.0, "walking": 0.0, "adjacency": 0.0}

        # Calculate constraint information if available
        constraint_info = {}
        if self.constraint_manager is not None and self.campus_data is not None:
            constraint_info = {
                "satisfied": self.constraint_manager.check_all(
                    best_solution, self.campus_data, self.buildings
                ),
                "violations": self.constraint_manager.violations(
                    best_solution, self.campus_data, self.buildings
                ),
                "penalty": self.constraint_manager.total_penalty(
                    best_solution, self.campus_data, self.buildings
                ),
            }

        return {
            "best_solution": best_solution,
            "fitness": best_solution.fitness,
            "objectives": objectives,
            "constraints": constraint_info,
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
            "major_roads": major_roads,
            "minor_roads": minor_roads,
            "road_stats": road_stats,
        }

    def optimize(self) -> Dict:
        """
        Complete H-SAGA optimization pipeline.

        Two-stage approach (Li et al. 2025):
        1. Stage 1: Simulated Annealing (global exploration)
        2. Stage 2: Genetic Algorithm (local refinement)

        Returns:
            Dictionary with complete optimization results:
            {
                'best_solution': Solution,           # Best solution found
                'fitness': float,                    # Best fitness value
                'objectives': {                      # Individual objectives
                    'cost': float,
                    'walking': float,
                    'adjacency': float
                },
                'statistics': {                      # Runtime statistics
                    'runtime': float,                # Total time (seconds)
                    'sa_time': float,                # SA phase time
                    'ga_time': float,                # GA phase time
                    'iterations': int,               # Total SA iterations
                    'evaluations': int,              # Total fitness evaluations
                    'sa_chains': int,                # Number of SA chains
                    'ga_generations': int            # Number of GA generations
                },
                'convergence': {                     # Convergence tracking
                    'sa_history': List[float],       # SA best fitness per temp
                    'ga_best_history': List[float],  # GA best fitness per gen
                    'ga_avg_history': List[float]    # GA avg fitness per gen
                },
                'all_solutions': List[Solution]     # All final solutions (for analysis)
            }

        Example:
            >>> optimizer = HybridSAGA(buildings, bounds)
            >>> result = optimizer.optimize()
            >>> print(f"Best fitness: {result['fitness']:.4f}")
            >>> print(f"Runtime: {result['statistics']['runtime']:.1f}s")
        """
        # Print optimization start header
        self._print_optimization_header()

        # Initialize statistics
        self.stats["evaluations"] = 0
        start_time = time.perf_counter()

        # ========================================
        # STAGE 1: SIMULATED ANNEALING
        # ========================================
        print("🔥 STAGE 1: SIMULATED ANNEALING")
        print("-" * 70)
        sa_start = time.perf_counter()

        sa_solutions = self._simulated_annealing()

        sa_time = time.perf_counter() - sa_start
        sa_best_fitness = max(sol.fitness for sol in sa_solutions if sol.fitness is not None)

        print(f"✅ SA Phase complete in {sa_time:.2f}s")
        print(f"   Best fitness: {sa_best_fitness:.4f}")
        print(f"   Solutions: {len(sa_solutions)}")
        print()

        # ========================================
        # STAGE 2: GENETIC ALGORITHM
        # ========================================
        print("🧬 STAGE 2: GENETIC ALGORITHM")
        print("-" * 70)
        ga_start = time.perf_counter()

        ga_solutions = self._genetic_refinement(sa_solutions)

        ga_time = time.perf_counter() - ga_start
        ga_best_fitness = max(sol.fitness for sol in ga_solutions if sol.fitness is not None)

        print(f"✅ GA Phase complete in {ga_time:.2f}s")
        print(f"   Best fitness: {ga_best_fitness:.4f}")
        print(f"   Improvement: {ga_best_fitness - sa_best_fitness:+.4f}")
        print()

        # ========================================
        # SELECT BEST OVERALL
        # ========================================
        all_solutions = sa_solutions + ga_solutions
        best_solution = max(
            all_solutions,
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"),
        )

        total_time = time.perf_counter() - start_time

        # Print final results and statistics
        self._print_final_results(best_solution, total_time, sa_time, ga_time)

        # Generate road network
        major_roads, minor_roads, road_stats = self._generate_road_network(best_solution)

        # Prepare and return result dictionary
        return self._prepare_result(
            best_solution,
            all_solutions,
            total_time,
            sa_time,
            ga_time,
            major_roads,
            minor_roads,
            road_stats,
        )

    def _simulated_annealing(self) -> List[Solution]:
        """
        Run parallel SA chains with fallback.

        Uses multiprocessing for M1's 4 performance cores.
        Falls back to sequential if num_chains=1 (for debugging).

        Returns:
            List of best Solution from each SA chain (sorted by fitness)
        """
        num_chains = self.sa_config.get("num_chains", 4)

        if num_chains == 1:
            # Sequential fallback for debugging
            logger.info("Running single SA chain (sequential)")
            solution = self._run_sa_chain(0, self.sa_config)
            return [solution]

        # Parallel execution
        logger.info(f"Running {num_chains} parallel SA chains")
        logger.info(
            f"  Configuration: {self.sa_config['chain_iterations']} iterations/chain, "
            f"T0={self.sa_config['initial_temp']:.1f}, "
            f"T_final={self.sa_config['final_temp']:.2f}"
        )

        # Use multiprocessing with module-level worker function
        try:
            # Use concurrent.futures for better error handling
            from concurrent.futures import ProcessPoolExecutor, as_completed

            with ProcessPoolExecutor(max_workers=num_chains) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(
                        _run_sa_chain_worker,
                        self.buildings,
                        self.bounds,
                        seed,
                        self.sa_config,
                    ): seed
                    for seed in range(num_chains)
                }

                # Collect results
                solutions = []
                completed = 0
                for future in as_completed(futures):
                    seed = futures[future]
                    try:
                        solution = future.result()
                        solutions.append(solution)
                        completed += 1
                        logger.info(
                            f"Chain {seed} completed ({completed}/{num_chains}): "
                            f"fitness={solution.fitness:.4f}"
                        )
                    except Exception as e:
                        logger.warning(f"Chain {seed} failed: {e}. Continuing with other chains.")
                        # Fallback: run this chain sequentially
                        np.random.seed(seed)
                        solution = self._run_sa_chain(seed, self.sa_config)
                        solutions.append(solution)
                        completed += 1

        except Exception as e:
            logger.warning(f"Multiprocessing failed: {e}. Falling back to sequential execution.")
            # Sequential fallback
            solutions = []
            for seed in range(num_chains):
                np.random.seed(seed)
                solution = self._run_sa_chain(seed, self.sa_config)
                solutions.append(solution)

        # Sort by fitness (descending)
        solutions.sort(key=lambda s: s.fitness, reverse=True)

        logger.info(f"SA chains completed. Best fitness: {solutions[0].fitness:.4f}")
        return solutions

    def _run_sa_chain(self, seed: int, config: Dict) -> Solution:
        """
        Run a single SA chain.

        Args:
            seed: Random seed for reproducibility
            config: SA configuration dict

        Returns:
            Best Solution found in this chain
        """
        # Initialize
        current = self._generate_random_solution()
        current.fitness = self.evaluator.evaluate(current)
        best = current.copy()

        temperature = config["initial_temp"]
        final_temp = config["final_temp"]
        cooling_rate = config["cooling_rate"]
        max_iter = config["chain_iterations"]

        # Track convergence for this chain
        chain_history = []

        # SA loop
        for iteration in range(max_iter):
            # Generate neighbor
            neighbor = self._perturb_solution(current, temperature)
            neighbor.fitness = self.evaluator.evaluate(neighbor)

            # Calculate delta
            delta = neighbor.fitness - current.fitness

            # Metropolis criterion
            if delta > 0 or np.random.random() < np.exp(delta / temperature):
                current = neighbor
                if current.fitness > best.fitness:
                    best = current.copy()

            # Cool down
            temperature *= cooling_rate

            # Track convergence (every 50 iterations)
            if iteration % 50 == 0:
                chain_history.append(best.fitness)
                logger.debug(
                    f"Chain {seed}, Iter {iteration}: T={temperature:.2f}, "
                    f"fitness={best.fitness:.4f}"
                )

            # Early stopping if temperature too low
            if temperature < final_temp:
                break

        # Update global convergence history (average across chains)
        if not hasattr(self, "_chain_histories"):
            self._chain_histories = []
        self._chain_histories.append(chain_history)

        return best

    def _generate_random_solution(self) -> Solution:
        """
        Generate random valid solution with collision detection.

        Retry logic: Max 100 attempts to generate valid solution.

        Returns:
            Valid Solution object

        Raises:
            RuntimeError: If unable to generate valid solution after 100 attempts
        """
        x_min, y_min, x_max, y_max = self.bounds
        max_attempts = 100

        for attempt in range(max_attempts):
            positions = {}
            valid = True

            for building in self.buildings:
                # Calculate required margin
                margin = building.radius + 5.0  # safety margin

                # Random position within bounds
                x = np.random.uniform(x_min + margin, x_max - margin)
                y = np.random.uniform(y_min + margin, y_max - margin)
                positions[building.id] = (x, y)

                # Check collision with previously placed buildings
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
                solution = Solution(positions)
                return solution

        # If we get here, generation failed
        raise RuntimeError(f"Failed to generate valid solution after {max_attempts} attempts")

    def _evaluate_if_needed(self, solution: Solution) -> float:
        """
        Evaluate solution only if fitness is None (lazy evaluation optimization).

        Applies constraint penalties if constraint_manager is available.

        Args:
            solution: Solution to evaluate

        Returns:
            Fitness value (with constraint penalties applied)
        """
        if solution.fitness is None:
            # Evaluate base fitness
            base_fitness = self.evaluator.evaluate(solution)

            # Apply constraint penalties if constraint_manager exists
            if self.constraint_manager is not None and self.campus_data is not None:
                constraint_penalty = self.constraint_manager.total_penalty(
                    solution, self.campus_data, self.buildings
                )
                # Apply penalty: max 50% reduction in fitness
                penalty_factor = min(constraint_penalty, 0.5)
                solution.fitness = base_fitness * (1.0 - penalty_factor)
            else:
                solution.fitness = base_fitness

            self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1
        return solution.fitness

    def _perturb_solution(self, solution: Solution, temperature: float) -> Solution:
        """
        Generate neighbor solution via temperature-adaptive perturbation (SA phase).

        Applies one of three perturbation operators using extracted mutation operators:
        - Gaussian move (80%): σ = T/10, temperature-adaptive
        - Swap buildings (15%): Exchange positions
        - Random reset (5%): Completely randomize position

        Step size adapts to temperature: large moves when hot, fine-tuning when cold.

        Args:
            solution: Current solution
            temperature: Current SA temperature

        Returns:
            New Solution (neighbor)
        """
        new_solution = solution.copy()
        rand = self._random_state.random()

        if rand < 0.80:
            # Gaussian move with temperature-adaptive sigma
            sigma = max(temperature / 10.0, 0.1)
            temp_gaussian = GaussianMutation(
                mutation_rate=1.0,  # Always apply
                sigma=sigma,
                bounds=self.bounds,
                margin=5.0,
                random_state=self._random_state,
            )
            temp_gaussian.mutate(new_solution)

        elif rand < 0.95:
            # Swap mutation
            self._swap_mutation.mutate(new_solution)

        else:
            # Random reset
            self._random_reset_mutation.mutate(new_solution)

        return new_solution

    def _initialize_ga_population(self, sa_solutions: List[Solution]) -> List[Solution]:
        """
        Initialize GA population from SA results.

        Strategy (research-based from Li et al. 2025):
        - 50% from best SA solutions (exploitation)
        - 30% perturbations of SA solutions (exploration)
        - 20% random solutions (diversity)

        This hybrid initialization balances:
        - Quality (SA solutions are already optimized)
        - Diversity (random + perturbations prevent premature convergence)

        Args:
            sa_solutions: Best solutions from SA phase (sorted by fitness)

        Returns:
            Initial GA population of size self.ga_config['population_size']
        """
        pop_size = self.ga_config["population_size"]
        population = []

        # 1. Add best SA solutions (50%)
        n_sa = min(pop_size // 2, len(sa_solutions))
        for i in range(n_sa):
            # Deep copy to avoid reference issues
            solution = Solution(
                positions={bid: pos for bid, pos in sa_solutions[i].positions.items()}
            )
            solution.fitness = sa_solutions[i].fitness
            if hasattr(sa_solutions[i], "objectives"):
                solution.objectives = sa_solutions[i].objectives.copy()
            population.append(solution)

        logger.info(f"GA init: Added {n_sa} SA solutions")

        # 2. Add perturbations of SA solutions (30%)
        n_perturb = int(pop_size * 0.3)
        for i in range(n_perturb):
            # Select random SA solution (biased toward best)
            idx = np.random.randint(0, min(5, len(sa_solutions)))
            base = sa_solutions[idx]

            # Create copy
            solution = Solution(positions={bid: pos for bid, pos in base.positions.items()})

            # Perturb with moderate temperature
            solution = self._perturb_solution(solution, temperature=50.0)
            solution.fitness = None  # Invalidate fitness
            population.append(solution)

        logger.info(f"GA init: Added {n_perturb} perturbed solutions")

        # 3. Add random solutions (20%)
        n_random = pop_size - len(population)
        for i in range(n_random):
            solution = self._generate_random_solution()
            solution.fitness = None
            population.append(solution)

        logger.info(f"GA init: Added {n_random} random solutions")
        logger.info(f"GA init: Total population size = {len(population)}")

        return population

    def _selection(
        self, population: List[Solution], n_parents: Optional[int] = None
    ) -> List[Solution]:
        """
        Select parents for reproduction using tournament selection.

        Uses TournamentSelector operator (extracted for testability).
        Default selects population_size // 2 parents.

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

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Selected {len(parents)} parents via tournament selection")

        return parents

    def _crossover(self, parents: List[Solution]) -> List[Solution]:
        """
        Create offspring via uniform crossover.

        Uses UniformCrossover operator (extracted for testability).
        Pairs up parents and applies crossover based on crossover_rate.

        Args:
            parents: Selected parent solutions

        Returns:
            Offspring solutions (approximately same size as parents)
        """
        # Use extracted crossover operator
        offspring = self._crossover_operator.apply_to_population(parents)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Crossover: Created {len(offspring)} offspring from {len(parents)} parents"
            )

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
            if self._random_state.random() < self.ga_config["mutation_rate"]:
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

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Mutation: Mutated {mutated_count}/{len(offspring)} offspring")

        return offspring

    def _replacement(self, population: List[Solution], offspring: List[Solution]) -> List[Solution]:
        """
        Elitist replacement strategy.

        Combines population + offspring, keeps best individuals.
        This ensures we never lose the best solutions (elitism).

        Args:
            population: Current population
            offspring: New offspring

        Returns:
            Next generation population (size: population_size)
        """
        # Combine all candidates
        combined = population + offspring

        # Sort by fitness (best first)
        # Handle None fitness values by treating them as worst
        combined.sort(
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"),
            reverse=True,
        )

        # Keep top population_size individuals
        next_gen = combined[: self.ga_config["population_size"]]

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Replacement: Selected top {len(next_gen)} " f"from {len(combined)} candidates"
            )

        return next_gen

    def _genetic_refinement(self, sa_solutions: List[Solution]) -> List[Solution]:
        """
        Stage 2: Genetic Algorithm for local refinement.

        Refines SA solutions through evolutionary optimization.

        Args:
            sa_solutions: Best solutions from SA phase (seed population)

        Returns:
            Best solutions from GA evolution (sorted by fitness)
        """
        logger.info("🧬 Starting GA Phase...")

        # Initialize population
        population = self._initialize_ga_population(sa_solutions)
        logger.info(f"  Initial population: {len(population)} individuals")

        # Evaluate initial population
        for solution in population:
            if solution.fitness is None:
                solution.fitness = self.evaluator.evaluate(solution)
                self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1

        # Track convergence
        best_fitness_history = []
        avg_fitness_history = []

        # Evolution loop
        generations = self.ga_config["generations"]

        for generation in range(generations):
            # 1. Selection
            parents = self._selection(population)

            # 2. Crossover
            offspring = self._crossover(parents)

            # 3. Mutation
            offspring = self._mutation(offspring)

            # 4. Evaluate offspring (only those with invalidated fitness)
            for solution in offspring:
                if solution.fitness is None:
                    solution.fitness = self.evaluator.evaluate(solution)
                    self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1

            # 5. Replacement (elitism)
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
                    f"Avg={avg_fitness:.4f}"
                )

        # Final generation stats
        fitnesses = [s.fitness for s in population if s.fitness is not None]
        if fitnesses:
            best = max(
                population,
                key=lambda s: s.fitness if s.fitness is not None else float("-inf"),
            )
        else:
            best = population[0]

        logger.info("✅ GA Phase complete.")
        best_fitness_val = best.fitness if best.fitness else 0.0
        logger.info(f"  Final best fitness: {best_fitness_val:.4f}")
        if len(best_fitness_history) > 1:
            improvement = best_fitness_history[-1] - best_fitness_history[0]
            logger.info(f"  Improvement: {improvement:+.4f}")

        # Store convergence history
        self.stats["ga_best_history"] = best_fitness_history
        self.stats["ga_avg_history"] = avg_fitness_history

        # Return top solutions (sorted)
        population.sort(
            key=lambda s: s.fitness if s.fitness is not None else float("-inf"),
            reverse=True,
        )
        return population[:10]  # Return top 10

    def evaluate_solution(self, solution: Solution) -> float:
        """
        Evaluate fitness of a solution (required by Optimizer ABC).

        Args:
            solution: Solution to evaluate

        Returns:
            Fitness score
        """
        if solution.fitness is None:
            solution.fitness = self.evaluator.evaluate(solution)
        return solution.fitness
