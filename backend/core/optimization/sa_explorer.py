"""
Simulated Annealing Explorer
==============================

Phase 1 of H-SAGA: Global exploration via parallel SA chains.

Extracted from hsaga.py to follow Single Responsibility Principle.
This module handles all SA-specific logic including:
- Parallel chain execution
- Temperature cooling schedules
- Solution perturbation
- Metropolis acceptance criterion

References:
    - Li et al. (2025): Reverse hybrid approach (SA for exploration)
    - Kirkpatrick et al. (1983): Original SA algorithm
    - Adaptive cooling schedules (Lundy & Mees, 1986)

Created: 2026-01-01
"""

import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Optional, Tuple

import numpy as np

from .building import Building
from .fitness import FitnessEvaluator
from .solution import Solution

logger = logging.getLogger(__name__)


class SAConfig:
    """Configuration for Simulated Annealing phase."""

    def __init__(
        self,
        num_chains: int = 8,
        chain_iterations: int = 300,
        initial_temp: float = 1000.0,
        cooling_rate: float = 0.95,
        random_seed: Optional[int] = None,
    ):
        """
        Initialize SA configuration.

        Args:
            num_chains: Number of parallel SA chains (default: 8 for M1 cores)
            chain_iterations: Iterations per chain (default: 300)
            initial_temp: Starting temperature (default: 1000.0)
            cooling_rate: Cooling factor α (default: 0.95, slow cooling)
            random_seed: Seed for reproducibility (default: None)
        """
        self.num_chains = num_chains
        self.chain_iterations = chain_iterations
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.random_seed = random_seed


class SAExplorer:
    """
    Simulated Annealing Explorer for global search.

    Runs parallel SA chains to explore the solution space broadly,
    providing diverse seed solutions for GA refinement.
    """

    def __init__(
        self,
        config: SAConfig,
        evaluator: FitnessEvaluator,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
    ):
        """
        Initialize SA Explorer.

        Args:
            config: SA configuration parameters
            evaluator: Fitness evaluation function
            buildings: List of buildings to place
            bounds: Spatial bounds (x_min, y_min, x_max, y_max)
        """
        self.config = config
        self.evaluator = evaluator
        self.buildings = buildings
        self.bounds = bounds

        # Statistics
        self.stats = {"iterations": 0, "evaluations": 0}

        # Random state
        self._random_state = np.random.RandomState(config.random_seed)

    def explore(self) -> List[Solution]:
        """
        Run parallel SA chains for global exploration.

        Uses multiprocessing for M1's 4 performance cores.
        Falls back to sequential if num_chains=1 (debugging mode).

        Returns:
            List of best solutions from each SA chain
        """
        logger.info(f"🔥 Starting SA exploration ({self.config.num_chains} chains)...")
        start_time = time.perf_counter()

        if self.config.num_chains == 1:
            # Sequential mode (debugging)
            logger.info("Running single chain (sequential mode)")
            chain_result = self._run_sa_chain(chain_id=0)
            all_solutions = [chain_result]
        else:
            # Parallel mode
            all_solutions = self._run_parallel_chains()

        elapsed = time.perf_counter() - start_time

        # Log results
        best_fitness = max(sol.fitness for sol in all_solutions if sol.fitness is not None)
        logger.info(f"✅ SA exploration complete in {elapsed:.2f}s")
        logger.info(f"   Best fitness: {best_fitness:.4f}")
        logger.info(f"   Total iterations: {self.stats['iterations']:,}")

        return all_solutions

    def _run_parallel_chains(self) -> List[Solution]:
        """
        Run SA chains in parallel using ProcessPoolExecutor.

        Returns:
            List of best solutions from each chain
        """
        all_solutions = []

        with ProcessPoolExecutor(max_workers=self.config.num_chains) as executor:
            # Submit all chains
            futures = {
                executor.submit(self._run_sa_chain, chain_id): chain_id
                for chain_id in range(self.config.num_chains)
            }

            # Collect results as they complete
            for future in as_completed(futures):
                chain_id = futures[future]
                try:
                    solution = future.result()
                    all_solutions.append(solution)
                    logger.info(f"  Chain {chain_id} complete: fitness={solution.fitness:.4f}")
                except Exception as e:
                    logger.error(f"  Chain {chain_id} failed: {e}")

        return all_solutions

    def _run_sa_chain(self, chain_id: int) -> Solution:
        """
        Run a single SA chain with Metropolis acceptance.

        Args:
            chain_id: Chain identifier (for seeding)

        Returns:
            Best solution found in this chain
        """
        # Chain-specific random state
        chain_random = np.random.RandomState(
            self.config.random_seed + chain_id if self.config.random_seed else None
        )

        # Initialize with random solution
        current = self._generate_random_solution(chain_random)
        current.fitness = self.evaluator.evaluate(current)
        self.stats["evaluations"] += 1

        # Track best
        best = current.copy()
        best_fitness = current.fitness

        # SA parameters
        temperature = self.config.initial_temp
        iterations = self.config.chain_iterations

        # Main SA loop
        for iteration in range(iterations):
            # Generate neighbor
            candidate = self._perturb_solution(current, temperature, chain_random)
            candidate.fitness = self.evaluator.evaluate(candidate)
            self.stats["evaluations"] += 1

            # Metropolis acceptance criterion
            delta_E = candidate.fitness - current.fitness

            if delta_E > 0:
                # Always accept improvement
                accept = True
            else:
                # Accept worse solution with probability exp(ΔE/T)
                acceptance_prob = np.exp(delta_E / temperature)
                accept = chain_random.random() < acceptance_prob

            if accept:
                current = candidate

                # Update best if better
                if current.fitness > best_fitness:
                    best = current.copy()
                    best_fitness = current.fitness

            # Cool down (geometric schedule)
            temperature *= self.config.cooling_rate

            # Track iterations
            self.stats["iterations"] += 1

            # Log progress (every 50 iterations)
            if iteration % 50 == 0 and iteration > 0:
                logger.debug(
                    f"  Chain {chain_id} iter {iteration}: "
                    f"T={temperature:.2f}, best={best_fitness:.4f}"
                )

        return best

    def _generate_random_solution(self, random_state: np.random.RandomState) -> Solution:
        """
        Generate random solution within bounds.

        Args:
            random_state: Random number generator

        Returns:
            Random solution
        """
        x_min, y_min, x_max, y_max = self.bounds
        margin = 10.0  # Safety margin from boundary

        positions = {}
        for building in self.buildings:
            x = random_state.uniform(x_min + margin, x_max - margin)
            y = random_state.uniform(y_min + margin, y_max - margin)
            positions[building.id] = (x, y)

        return Solution(positions=positions)

    def _perturb_solution(
        self,
        solution: Solution,
        temperature: float,
        random_state: np.random.RandomState,
    ) -> Solution:
        """
        Generate neighbor via temperature-adaptive perturbation.

        Uses composite mutation strategy:
        - Gaussian move (80%): σ = T/10, temperature-adaptive
        - Swap buildings (15%): Exchange positions
        - Random reset (5%): Completely randomize position

        Step size adapts to temperature: large moves when hot, fine-tuning when cold.

        Args:
            solution: Current solution
            temperature: Current SA temperature
            random_state: Random number generator

        Returns:
            New Solution (neighbor)
        """
        new_solution = solution.copy()
        rand = random_state.random()

        if rand < 0.80:
            # Gaussian move with temperature-adaptive sigma
            self._gaussian_perturbation(new_solution, temperature, random_state)

        elif rand < 0.95:
            # Swap mutation
            self._swap_perturbation(new_solution, random_state)

        else:
            # Random reset
            self._reset_perturbation(new_solution, random_state)

        return new_solution

    def _gaussian_perturbation(
        self,
        solution: Solution,
        temperature: float,
        random_state: np.random.RandomState,
    ) -> None:
        """
        Perturb one building position with Gaussian noise.

        Args:
            solution: Solution to modify (in-place)
            temperature: Current temperature (controls step size)
            random_state: Random number generator
        """
        # Select random building
        building_ids = list(solution.positions.keys())
        if not building_ids:
            return

        building_id = random_state.choice(building_ids)
        x, y = solution.positions[building_id]

        # Temperature-adaptive step size (larger when hot)
        sigma = max(temperature / 10.0, 0.1)

        # Gaussian perturbation
        dx = random_state.normal(0, sigma)
        dy = random_state.normal(0, sigma)

        # Apply bounds with margin
        x_min, y_min, x_max, y_max = self.bounds
        margin = 5.0
        new_x = np.clip(x + dx, x_min + margin, x_max - margin)
        new_y = np.clip(y + dy, y_min + margin, y_max - margin)

        # Update position
        solution.positions[building_id] = (new_x, new_y)

    def _swap_perturbation(self, solution: Solution, random_state: np.random.RandomState) -> None:
        """
        Swap positions of two random buildings.

        Args:
            solution: Solution to modify (in-place)
            random_state: Random number generator
        """
        building_ids = list(solution.positions.keys())

        # Need at least 2 buildings to swap
        if len(building_ids) < 2:
            return

        # Select two random buildings
        id1, id2 = random_state.choice(building_ids, 2, replace=False)

        # Swap positions
        solution.positions[id1], solution.positions[id2] = (
            solution.positions[id2],
            solution.positions[id1],
        )

    def _reset_perturbation(self, solution: Solution, random_state: np.random.RandomState) -> None:
        """
        Completely randomize one building position.

        Args:
            solution: Solution to modify (in-place)
            random_state: Random number generator
        """
        # Select random building
        building_ids = list(solution.positions.keys())
        if not building_ids:
            return

        building_id = random_state.choice(building_ids)

        # Generate completely new random position
        x_min, y_min, x_max, y_max = self.bounds
        margin = 5.0
        new_x = random_state.uniform(x_min + margin, x_max - margin)
        new_y = random_state.uniform(y_min + margin, y_max - margin)

        solution.positions[building_id] = (new_x, new_y)
