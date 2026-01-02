"""
H-SAGA (Hybrid Simulated Annealing - Genetic Algorithm) Orchestrator
=====================================================================

Two-phase hybrid optimizer combining SA (exploration) + GA (refinement).

This module is a lean orchestrator that delegates to specialized modules:
- SAExplorer: Phase 1 (global exploration)
- GARefiner: Phase 2 (local refinement)

Architecture:
    Phase 1 (30% budget): Parallel SA chains → diverse seed solutions
    Phase 2 (70% budget): GA evolution → Pareto-optimal front

References:
    - Li et al. (2025): Reverse hybrid approach
    - Deb & Goyal (1996): Combined genetic adaptive search

Created: 2025-11-03
Refactored: 2026-01-01 (extracted SA/GA modules)
"""

import logging
import time
from typing import Dict, List, Optional, Tuple

from .base import Optimizer
from .building import Building
from .fitness import FitnessEvaluator
from .ga_refiner import GAConfig, GARefiner
from .sa_explorer import SAConfig, SAExplorer
from .solution import Solution

logger = logging.getLogger(__name__)


class HSAGAOptimizer(Optimizer):
    """
    H-SAGA Orchestrator: Coordinates SA exploration + GA refinement.

    Simplified to ~100 lines by delegating implementation to:
    - SAExplorer (backend/core/optimization/sa_explorer.py)
    - GARefiner (backend/core/optimization/ga_refiner.py)
    """

    def __init__(
        self,
        buildings: List[Building],
        evaluator: FitnessEvaluator,
        bounds: Tuple[float, float, float, float],
        constraint_manager=None,
        campus_data=None,
        sa_config: Optional[Dict] = None,
        ga_config: Optional[Dict] = None,
    ):
        """
        Initialize H-SAGA optimizer.

        Args:
            buildings: List of buildings to place
            evaluator: Fitness evaluation function
            bounds: Spatial bounds (x_min, y_min, x_max, y_max)
            constraint_manager: Optional constraint checker
            campus_data: Optional campus context data
            sa_config: SA configuration overrides
            ga_config: GA configuration overrides
        """
        super().__init__(buildings, evaluator, bounds)

        self.constraint_manager = constraint_manager
        self.campus_data = campus_data
        self.stats = {}

        # Create SA and GA configurations
        sa_params = sa_config or {}
        ga_params = ga_config or {}

        self.sa_config = SAConfig(
            num_chains=sa_params.get("num_chains", 8),
            chain_iterations=sa_params.get("chain_iterations", 300),
            initial_temp=sa_params.get("initial_temp", 1000.0),
            cooling_rate=sa_params.get("cooling_rate", 0.95),
        )

        self.ga_config = GAConfig(
            population_size=ga_params.get("population_size", 50),
            generations=ga_params.get("generations", 50),
            crossover_rate=ga_params.get("crossover_rate", 0.8),
            mutation_rate=ga_params.get("mutation_rate", 0.15),
            elite_size=ga_params.get("elite_size", 5),
            tournament_size=ga_params.get("tournament_size", 3),
        )

        # Initialize phase modules
        self.sa_explorer = SAExplorer(self.sa_config, evaluator, buildings, bounds)
        self.ga_refiner = GARefiner(self.ga_config, evaluator, buildings, bounds)

    def optimize(self) -> Dict:
        """
        Run H-SAGA optimization: SA → GA.

        Returns:
            Dict with best_solution, fitness, objectives, statistics
        """
        print("\n" + "=" * 70)
        print("🚀 H-SAGA OPTIMIZATION START")
        print("=" * 70)
        print(f"📍 Area: {self.bounds}")
        print(f"🏢 Buildings: {len(self.buildings)}")
        print(f"⚙️  SA Chains: {self.sa_config.num_chains}")
        print(f"⚙️  GA Population: {self.ga_config.population_size}")
        print("=" * 70)
        print()

        start_time = time.perf_counter()

        # ========================================
        # PHASE 1: SA EXPLORATION
        # ========================================
        print("🔥 PHASE 1: SIMULATED ANNEALING")
        print("-" * 70)
        sa_start = time.perf_counter()

        sa_solutions = self.sa_explorer.explore()

        sa_time = time.perf_counter() - sa_start
        sa_best_fitness = max(sol.fitness for sol in sa_solutions if sol.fitness)

        print(f"✅ SA Phase complete in {sa_time:.2f}s")
        print(f"   Best fitness: {sa_best_fitness:.4f}")
        print()

        # ========================================
        # PHASE 2: GA REFINEMENT
        # ========================================
        print("🧬 PHASE 2: GENETIC ALGORITHM")
        print("-" * 70)
        ga_start = time.perf_counter()

        ga_solutions = self.ga_refiner.refine(sa_solutions)

        ga_time = time.perf_counter() - ga_start
        ga_best_fitness = max(sol.fitness for sol in ga_solutions if sol.fitness)

        print(f"✅ GA Phase complete in {ga_time:.2f}s")
        print(f"   Best fitness: {ga_best_fitness:.4f}")
        print(f"   Improvement: {ga_best_fitness - sa_best_fitness:+.4f}")
        print()

        # ========================================
        # SELECT BEST & PREPARE RESULTS
        # ========================================
        all_solutions = sa_solutions + ga_solutions
        best_solution = max(all_solutions, key=lambda s: s.fitness or float("-inf"))

        total_time = time.perf_counter() - start_time

        # Print summary
        print("=" * 70)
        print("✅ H-SAGA OPTIMIZATION COMPLETE")
        print("=" * 70)
        print(f"🏆 Best fitness: {best_solution.fitness:.4f}")
        print(f"⏱️  Total runtime: {total_time:.2f}s")
        print(f"   └─ SA: {sa_time:.2f}s ({sa_time/total_time*100:.1f}%)")
        print(f"   └─ GA: {ga_time:.2f}s ({ga_time/total_time*100:.1f}%)")
        print("=" * 70)
        print()

        # Aggregate statistics
        self.stats = {
            "evaluations": (
                self.sa_explorer.stats["evaluations"] + self.ga_refiner.stats["evaluations"]
            ),
            "iterations": self.sa_explorer.stats["iterations"],
            "sa_best_history": [],  # Could be added if needed
            "sa_avg_history": [],
            "ga_best_history": self.ga_refiner.stats["best_history"],
            "ga_avg_history": self.ga_refiner.stats["avg_history"],
        }

        # Generate road network (if generator exists)
        major_roads, minor_roads, road_stats = self._generate_road_network(best_solution)

        return {
            "best_solution": best_solution,
            "fitness": best_solution.fitness,
            "objectives": getattr(best_solution, "objectives", {}),
            "constraints": self._get_constraint_info(best_solution),
            "statistics": {
                "runtime": total_time,
                "sa_time": sa_time,
                "ga_time": ga_time,
                "evaluations": self.stats["evaluations"],
                "iterations": self.stats["iterations"],
                "sa_best_history": self.stats["sa_best_history"],
                "sa_avg_history": self.stats["sa_avg_history"],
                "ga_best_history": self.stats["ga_best_history"],
                "ga_avg_history": self.stats["ga_avg_history"],
            },
            "all_solutions": all_solutions,
            "major_roads": major_roads,
            "minor_roads": minor_roads,
            "road_stats": road_stats,
        }

    def _get_constraint_info(self, solution: Solution) -> Dict:
        """Get constraint information if constraint manager is available."""
        if self.constraint_manager is None or self.campus_data is None:
            return {}

        return {
            "satisfied": self.constraint_manager.check_all(
                solution, self.campus_data, self.buildings
            ),
            "violations": self.constraint_manager.violations(
                solution, self.campus_data, self.buildings
            ),
            "penalty": self.constraint_manager.total_penalty(
                solution, self.campus_data, self.buildings
            ),
        }

    def _generate_road_network(self, best_solution: Solution) -> Tuple[List, List, Dict]:
        """
        Generate road network from optimized building positions using tensor fields.

        Returns:
            Tuple of (major_roads, minor_roads, road_stats)
        """
        try:
            from backend.core.geospatial.road_network_generator import RoadNetworkGenerator

            # Create generator
            generator = RoadNetworkGenerator(bounds=self.bounds)

            # Generate network
            major_roads, minor_roads, stats = generator.generate(self.buildings)

            return major_roads, minor_roads, stats

        except Exception as e:
            # Fallback if road generation fails
            import logging

            logging.warning(f"Road network generation failed: {e}. Using empty network.")
            return [], [], {"n_major_roads": 0, "n_minor_roads": 0, "total_length_m": 0}

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
