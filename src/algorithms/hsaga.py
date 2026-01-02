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

from .base import Optimizer
from .building import Building
from .fitness import FitnessEvaluator
from .solution import Solution

if TYPE_CHECKING:
    from ..constraints.spatial_constraints import ConstraintManager
    from ..data.campus_data import CampusData

logger = logging.getLogger(__name__)


# =============================================================================
# PARALLEL EVALUATION WORKERS (Module-level for picklability)
# =============================================================================


def _evaluate_solution_worker(
    solution: Solution,
    buildings: List[Building],
    bounds: Tuple[float, float, float, float],
) -> Tuple[Solution, float]:
    """
    Worker function for parallel fitness evaluation.

    Args:
        solution: Solution to evaluate
        buildings: List of buildings
        bounds: Site boundaries

    Returns:
        Tuple of (solution, fitness)
    """
    evaluator = FitnessEvaluator(buildings, bounds)
    fitness = evaluator.evaluate(solution)
    solution.fitness = fitness
    return solution, fitness


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
        # Print header
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

        # ========================================
        # PRINT FINAL RESULTS
        # ========================================
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
            # Calculate objectives if not stored
            objectives = {
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

        # ========================================
        # ROAD NETWORK GENERATION (Day 2)
        # ========================================
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
            road_time = 0.0

        # Prepare result dictionary
        result = {
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

        return result

    def _evaluate_population_parallel(
        self,
        solutions: List[Solution],
        max_workers: Optional[int] = None,
        parallel_threshold: int = 50,
    ) -> List[Solution]:
        """
        Evaluate multiple solutions with smart parallelization.

        Uses ThreadPoolExecutor for GA (shared memory) to avoid pickling overhead.
        Only parallelizes when batch size justifies overhead.

        Args:
            solutions: List of solutions to evaluate
            max_workers: Maximum parallel workers (None = auto)
            parallel_threshold: Minimum batch size for parallel (default 50)

        Returns:
            Solutions with fitness values updated
        """
        # Filter solutions that need evaluation
        to_evaluate = [s for s in solutions if s.fitness is None]

        if not to_evaluate:
            return solutions

        # Sequential for small batches (overhead not worth it)
        if len(to_evaluate) < parallel_threshold:
            for solution in to_evaluate:
                solution.fitness = self.evaluator.evaluate(solution)
                self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1
            return solutions

        # Parallel evaluation with ThreadPoolExecutor (no pickling!)
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            if max_workers is None:
                max_workers = min(len(to_evaluate) // 10, 4)  # Conservative

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit evaluation tasks
                future_to_solution = {
                    executor.submit(self.evaluator.evaluate, sol): sol for sol in to_evaluate
                }

                # Collect results
                for future in as_completed(future_to_solution):
                    solution = future_to_solution[future]
                    try:
                        fitness = future.result()
                        solution.fitness = fitness
                        self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1
                    except Exception as e:
                        # Fallback for this solution
                        logger.warning(f"Thread evaluation failed: {e}")
                        solution.fitness = self.evaluator.evaluate(solution)
                        self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1

        except Exception as e:
            # Complete fallback to sequential
            logger.warning(f"Parallel evaluation failed: {e}. Using sequential.")
            for solution in to_evaluate:
                solution.fitness = self.evaluator.evaluate(solution)
                self.stats["evaluations"] = self.stats.get("evaluations", 0) + 1

        return solutions

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
        Generate neighbor solution via temperature-adaptive perturbation.

        Applies one of three perturbation operators:
        - Gaussian move (80%): σ = T/10, single building position jitter
        - Swap buildings (15%): Exchange positions of two buildings
        - Random reset (5%): Completely randomize one building position

        Step size adapts to temperature: large moves when hot, fine-tuning when cold.

        Args:
            solution: Current solution
            temperature: Current SA temperature

        Returns:
            New Solution (neighbor)
        """
        # Create copy
        new_solution = solution.copy()
        new_positions = new_solution.positions.copy()

        # Select perturbation operator based on probability
        rand = np.random.random()

        if rand < 0.80:
            # Gaussian move (80%)
            building_id = np.random.choice(list(new_positions.keys()))
            x, y = new_positions[building_id]

            # Adaptive step size: σ = T/10
            sigma = max(temperature / 10.0, 0.1)  # Minimum 0.1m

            dx = np.random.normal(0, sigma)
            dy = np.random.normal(0, sigma)

            # Clip to bounds
            x_min, y_min, x_max, y_max = self.bounds
            building = next(b for b in self.buildings if b.id == building_id)
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
            x_min, y_min, x_max, y_max = self.bounds
            building = next(b for b in self.buildings if b.id == building_id)
            margin = building.radius + 5.0

            x = np.random.uniform(x_min + margin, x_max - margin)
            y = np.random.uniform(y_min + margin, y_max - margin)
            new_positions[building_id] = (x, y)

        new_solution.positions = new_positions
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

    def _tournament_selection(
        self, population: List[Solution], tournament_size: Optional[int] = None
    ) -> Solution:
        """
        Tournament selection operator.

        Randomly selects k individuals from population, returns the best.
        This creates selection pressure while maintaining diversity.

        Args:
            population: Current population
            tournament_size: Number of individuals in tournament
                            (default: self.ga_config['tournament_size'])

        Returns:
            Selected solution (deep copy to avoid reference issues)

        Raises:
            ValueError: If tournament_size > population size
        """
        if tournament_size is None:
            tournament_size = self.ga_config["tournament_size"]

        if tournament_size > len(population):
            raise ValueError(
                f"Tournament size ({tournament_size}) cannot exceed "
                f"population size ({len(population)})"
            )

        # Randomly select tournament candidates
        indices = np.random.choice(len(population), tournament_size, replace=False)
        candidates = [population[i] for i in indices]

        # Select best (highest fitness)
        # Filter out None fitness values
        valid_candidates = [s for s in candidates if s.fitness is not None]
        if not valid_candidates:
            # If all have None fitness, just return first
            winner = candidates[0]
        else:
            winner = max(valid_candidates, key=lambda s: s.fitness)

        # Return deep copy
        selected = Solution(positions={bid: pos for bid, pos in winner.positions.items()})
        selected.fitness = winner.fitness
        if hasattr(winner, "objectives"):
            selected.objectives = winner.objectives.copy()

        return selected

    def _selection(
        self, population: List[Solution], n_parents: Optional[int] = None
    ) -> List[Solution]:
        """
        Select parents for reproduction.

        Uses tournament selection to create parent pool.
        Default selects population_size // 2 parents.

        Args:
            population: Current population (must have fitness evaluated)
            n_parents: Number of parents to select
                       (default: len(population) // 2)

        Returns:
            List of selected parent solutions
        """
        if n_parents is None:
            n_parents = len(population) // 2

        parents = []
        for _ in range(n_parents):
            parent = self._tournament_selection(population)
            parents.append(parent)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Selected {len(parents)} parents via tournament selection")

        return parents

    def _uniform_crossover(self, parent1: Solution, parent2: Solution) -> Tuple[Solution, Solution]:
        """
        Uniform crossover operator.

        For each building, randomly select position from parent1 or parent2.
        This maintains diversity while combining parent traits.

        Args:
            parent1: First parent solution
            parent2: Second parent solution

        Returns:
            Tuple of two offspring solutions

        Note:
            Each gene (building position) has 50% chance from each parent.
        """
        child1_positions = {}
        child2_positions = {}

        for building_id in parent1.positions.keys():
            if np.random.random() < 0.5:
                # Child1 gets parent1's gene, child2 gets parent2's
                child1_positions[building_id] = parent1.positions[building_id]
                child2_positions[building_id] = parent2.positions[building_id]
            else:
                # Swap
                child1_positions[building_id] = parent2.positions[building_id]
                child2_positions[building_id] = parent1.positions[building_id]

        child1 = Solution(positions=child1_positions)
        child2 = Solution(positions=child2_positions)

        # Fitness needs re-evaluation
        child1.fitness = None
        child2.fitness = None

        return child1, child2

    def _crossover(self, parents: List[Solution]) -> List[Solution]:
        """
        Create offspring via crossover.

        Pairs up parents and applies crossover based on crossover_rate.
        If crossover doesn't occur, parents are copied to offspring.

        Args:
            parents: Selected parent solutions

        Returns:
            Offspring solutions (approximately same size as parents)
        """
        offspring = []
        crossover_rate = self.ga_config["crossover_rate"]

        # Pair up parents (iterate by 2)
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]

            if np.random.random() < crossover_rate:
                # Apply crossover
                child1, child2 = self._uniform_crossover(parent1, parent2)
                offspring.extend([child1, child2])
            else:
                # No crossover - copy parents
                child1 = Solution(positions={bid: pos for bid, pos in parent1.positions.items()})
                child2 = Solution(positions={bid: pos for bid, pos in parent2.positions.items()})
                child1.fitness = parent1.fitness
                child2.fitness = parent2.fitness

                if hasattr(parent1, "objectives"):
                    child1.objectives = parent1.objectives.copy()
                if hasattr(parent2, "objectives"):
                    child2.objectives = parent2.objectives.copy()

                offspring.extend([child1, child2])

        # Handle odd number of parents (last one just gets copied)
        if len(parents) % 2 == 1:
            last_parent = parents[-1]
            child = Solution(positions={bid: pos for bid, pos in last_parent.positions.items()})
            child.fitness = last_parent.fitness
            if hasattr(last_parent, "objectives"):
                child.objectives = last_parent.objectives.copy()
            offspring.append(child)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Crossover: Created {len(offspring)} offspring " f"from {len(parents)} parents"
            )

        return offspring

    def _gaussian_mutation(self, solution: Solution, sigma: Optional[float] = None) -> Solution:
        """
        Gaussian mutation: perturb one random building position.

        Uses Gaussian distribution for perturbation, providing local search.

        Args:
            solution: Solution to mutate (modified in-place)
            sigma: Standard deviation for Gaussian (default: 30.0 meters)

        Returns:
            Mutated solution (same object, modified)
        """
        if sigma is None:
            sigma = 30.0

        # Select random building
        building_id = np.random.choice(list(solution.positions.keys()))
        x, y = solution.positions[building_id]

        # Gaussian perturbation
        dx = np.random.normal(0, sigma)
        dy = np.random.normal(0, sigma)

        # Apply bounds
        x_min, y_min, x_max, y_max = self.bounds
        margin = 10  # Meters from edge
        new_x = np.clip(x + dx, x_min + margin, x_max - margin)
        new_y = np.clip(y + dy, y_min + margin, y_max - margin)

        # Update position
        solution.positions[building_id] = (new_x, new_y)

        return solution

    def _swap_mutation(self, solution: Solution) -> Solution:
        """
        Swap mutation: exchange positions of two random buildings.

        Provides large-scale exploration without leaving valid space.

        Args:
            solution: Solution to mutate (modified in-place)

        Returns:
            Mutated solution (same object, modified)
        """
        if len(solution.positions) < 2:
            return solution  # Can't swap with <2 buildings

        # Select two random buildings
        building_ids = list(solution.positions.keys())
        id1, id2 = np.random.choice(building_ids, 2, replace=False)

        # Swap positions
        solution.positions[id1], solution.positions[id2] = (
            solution.positions[id2],
            solution.positions[id1],
        )

        return solution

    def _random_reset_mutation(self, solution: Solution) -> Solution:
        """
        Random reset: completely randomize one building position.

        Provides escape from local optima.

        Args:
            solution: Solution to mutate (modified in-place)

        Returns:
            Mutated solution (same object, modified)
        """
        # Select random building
        building_id = np.random.choice(list(solution.positions.keys()))

        # Generate completely new random position
        x_min, y_min, x_max, y_max = self.bounds
        margin = 10
        new_x = np.random.uniform(x_min + margin, x_max - margin)
        new_y = np.random.uniform(y_min + margin, y_max - margin)

        solution.positions[building_id] = (new_x, new_y)

        return solution

    def _mutation(self, offspring: List[Solution]) -> List[Solution]:
        """
        Apply mutation to offspring population.

        Mutation distribution (research-based):
        - Gaussian: 70% (local search)
        - Swap: 20% (exploration)
        - Random reset: 10% (escape mechanism)

        Args:
            offspring: Offspring solutions to potentially mutate

        Returns:
            Mutated offspring (modified in-place, same list returned)
        """
        mutation_rate = self.ga_config["mutation_rate"]
        mutated_count = 0

        for solution in offspring:
            if np.random.random() < mutation_rate:
                # Select mutation type
                mut_type = np.random.choice(["gaussian", "swap", "reset"], p=[0.7, 0.2, 0.1])

                if mut_type == "gaussian":
                    solution = self._gaussian_mutation(solution)
                elif mut_type == "swap":
                    solution = self._swap_mutation(solution)
                else:  # reset
                    solution = self._random_reset_mutation(solution)

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

        # Evaluate initial population (parallel)
        population = self._evaluate_population_parallel(population)

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

            # 4. Evaluate offspring (parallel)
            offspring = self._evaluate_population_parallel(offspring)

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
