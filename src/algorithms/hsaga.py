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
from typing import Dict, List, Optional, Tuple

import numpy as np

from .base import Optimizer
from .building import Building
from .fitness import FitnessEvaluator
from .solution import Solution

logger = logging.getLogger(__name__)


# Module-level function for multiprocessing (must be picklable)
def _run_sa_chain_worker(
    buildings: List[Building], bounds: Tuple[float, float, float, float], seed: int, config: Dict
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
            new_positions[id1], new_positions[id2] = (new_positions[id2], new_positions[id1])

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
        constraints: Optional[Dict] = None,
        sa_config: Optional[Dict] = None,
        ga_config: Optional[Dict] = None,
    ):
        """
        Initialize H-SAGA optimizer.

        Args:
            buildings: List of Building objects to place
            bounds: Site boundaries (x_min, y_min, x_max, y_max)
            constraints: Optional constraints dict (green_areas, obstacles, etc.)
            sa_config: Optional SA configuration override
            ga_config: Optional GA configuration (for Day 3)

        Raises:
            ValueError: If buildings empty, bounds invalid, or oversized footprints
        """
        # Validate buildings
        if not buildings:
            raise ValueError("buildings list cannot be empty")

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

        # Store constraints
        self.constraints = constraints or {}

        # SA configuration (Li et al. 2025 + research synthesis)
        self.sa_config = sa_config or {
            "initial_temp": 1000.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,  # Geometric schedule
            "max_iterations": 500,
            "num_chains": 4,  # M1: 4 performance cores
            "chain_iterations": 500,
        }

        # GA configuration (for Day 3, placeholder)
        self.ga_config = ga_config or {
            "population_size": 100,
            "generations": 100,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 10,
        }

    def optimize(self) -> Dict:
        """
        Run H-SAGA optimization (Day 2: SA phase only).

        Returns:
            Dict with:
                - best_solution: Solution object
                - fitness: Best fitness score
                - statistics: Algorithm stats
                - convergence: Convergence history
                - time: Execution time in seconds

        Raises:
            RuntimeError: If optimization fails
        """
        start_time = time.perf_counter()
        logger.info("Starting H-SAGA optimization (SA phase)")

        # Stage 1: SA Global Exploration
        logger.info("Stage 1: Simulated Annealing exploration...")
        sa_solutions = self._simulated_annealing()

        # Select best solution from SA chains
        best_solution = max(sa_solutions, key=lambda s: s.fitness)

        # Update statistics
        elapsed = time.perf_counter() - start_time
        self.stats["iterations"] = self.sa_config["max_iterations"]
        self.stats["best_fitness"] = best_solution.fitness

        logger.info(
            f"SA phase completed in {elapsed:.2f}s. " f"Best fitness: {best_solution.fitness:.4f}"
        )

        return {
            "best_solution": best_solution,
            "fitness": best_solution.fitness,
            "statistics": self.stats,
            "convergence": self.stats["convergence_history"],
            "time": elapsed,
        }

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
                        _run_sa_chain_worker, self.buildings, self.bounds, seed, self.sa_config
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
                new_positions[id1], new_positions[id2] = (new_positions[id2], new_positions[id1])

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
