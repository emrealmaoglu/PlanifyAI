"""
NSGA-III Optimization Runner
=============================

Pure NSGA-III runner using our custom implementation.
Provides clean multi-objective optimization without hybrid SA phase.

Created: 2026-01-03
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from src.algorithms import Building, ObjectiveProfile, ProfileType, get_profile
from src.algorithms.nsga3 import NSGA3

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class NSGA3RunnerConfig:
    """Configuration for NSGA-III runner."""

    # Population parameters
    population_size: int = 100
    n_generations: int = 100

    # Reference points
    n_partitions: int = 12
    use_two_layer: bool = False
    n_partitions_inner: Optional[int] = None
    reference_points: Optional[np.ndarray] = None

    # Genetic operators
    crossover_rate: float = 0.9
    mutation_rate: float = 0.15

    # Objective configuration
    objective_profile: Optional[Union[ObjectiveProfile, ProfileType, str]] = None

    # Performance
    seed: Optional[int] = 42
    verbose: bool = True


# =============================================================================
# NSGA-III RUNNER
# =============================================================================


class NSGA3Runner:
    """
    NSGA-III optimization runner for campus planning.

    Provides a clean interface to run NSGA-III optimization
    with building placement problems.

    Example:
        >>> buildings = [...]
        >>> bounds = (0, 0, 1000, 1000)
        >>> config = NSGA3RunnerConfig(population_size=50, n_generations=50)
        >>> runner = NSGA3Runner(buildings, bounds, config)
        >>> result = runner.run()
        >>> pareto_front = result["pareto_front"]
    """

    def __init__(
        self,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        config: Optional[NSGA3RunnerConfig] = None,
    ):
        """
        Initialize NSGA-III runner.

        Args:
            buildings: List of buildings to place
            bounds: Site boundaries (x_min, y_min, x_max, y_max)
            config: Optional configuration
        """
        self.buildings = buildings
        self.bounds = bounds
        self.config = config or NSGA3RunnerConfig()

        # Set random seed if provided
        if self.config.seed is not None:
            np.random.seed(self.config.seed)

        # Resolve objective profile
        self.objective_profile = self._resolve_objective_profile(self.config.objective_profile)

        # Create fitness evaluator with profile settings
        from src.algorithms.fitness import FitnessEvaluator

        evaluator = FitnessEvaluator(
            buildings=buildings,
            bounds=bounds,
            weights=self.objective_profile.weights,
            use_enhanced=self.objective_profile.use_enhanced,
            walking_speed_kmh=self.objective_profile.walking_speed_kmh,
        )

        # Initialize optimizer
        self.optimizer = NSGA3(
            buildings=buildings,
            bounds=bounds,
            population_size=self.config.population_size,
            n_generations=self.config.n_generations,
            n_partitions=self.config.n_partitions,
            use_two_layer=self.config.use_two_layer,
            n_partitions_inner=self.config.n_partitions_inner,
            reference_points=self.config.reference_points,
            crossover_rate=self.config.crossover_rate,
            mutation_rate=self.config.mutation_rate,
            evaluator=evaluator,
        )

        # Stats
        self.stats = {
            "evaluations": 0,
            "generations": 0,
            "runtime": 0,
            "pareto_size": 0,
        }

    def _resolve_objective_profile(
        self, profile: Optional[Union[ObjectiveProfile, ProfileType, str]]
    ) -> ObjectiveProfile:
        """
        Resolve objective profile from various input types.

        Args:
            profile: ObjectiveProfile, ProfileType enum, or profile name string

        Returns:
            Resolved ObjectiveProfile

        Raises:
            ValueError: If profile type is invalid
        """
        if profile is None:
            # Default to standard profile
            return get_profile(ProfileType.STANDARD)
        elif isinstance(profile, ObjectiveProfile):
            # Already an ObjectiveProfile
            return profile
        elif isinstance(profile, ProfileType):
            # ProfileType enum
            return get_profile(profile)
        elif isinstance(profile, str):
            # String profile name - try to match
            try:
                profile_type = ProfileType(profile.lower())
                return get_profile(profile_type)
            except ValueError:
                raise ValueError(
                    f"Invalid profile name: {profile}. "
                    f"Valid options: {[p.value for p in ProfileType if p != ProfileType.CUSTOM]}"
                )
        else:
            raise ValueError(f"Invalid profile type: {type(profile)}")

    def run(self) -> Dict[str, Any]:
        """
        Run NSGA-III optimization.

        Returns:
            Dict containing:
                - pareto_front: List of non-dominated solutions
                - pareto_objectives: Objective values for Pareto front
                - reference_points: Reference points used
                - statistics: Runtime statistics
                - convergence: Convergence history
                - best_compromise: Best compromise solution
        """
        if self.config.verbose:
            self._print_header()

        start_time = time.time()

        # Run optimization
        result = self.optimizer.optimize()

        runtime = time.time() - start_time

        # Update stats
        self.stats["evaluations"] = result["statistics"]["evaluations"]
        self.stats["generations"] = self.config.n_generations
        self.stats["runtime"] = runtime
        self.stats["pareto_size"] = len(result["pareto_front"])

        if self.config.verbose:
            self._print_results(result, runtime)

        # Add best compromise solution
        result["best_compromise"] = self._find_best_compromise(result)

        return result

    def _find_best_compromise(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find best compromise solution from Pareto front.

        Uses minimum sum of normalized objectives.

        Args:
            result: Optimization result

        Returns:
            Dict with best compromise solution
        """
        pareto_objectives = result["pareto_objectives"]

        if len(pareto_objectives) == 0:
            return None

        # Normalize objectives to [0, 1]
        obj_min = np.min(pareto_objectives, axis=0)
        obj_max = np.max(pareto_objectives, axis=0)

        # Avoid division by zero
        obj_range = obj_max - obj_min
        obj_range[obj_range == 0] = 1.0

        normalized = (pareto_objectives - obj_min) / obj_range

        # Find solution with minimum sum of normalized objectives
        sums = np.sum(normalized, axis=1)
        best_idx = np.argmin(sums)

        pareto_front = result["pareto_front"]
        best_solution = pareto_front[best_idx]

        return {
            "solution": best_solution,
            "objectives": pareto_objectives[best_idx],
            "normalized_objectives": normalized[best_idx],
            "index": int(best_idx),
        }

    def _print_header(self):
        """Print optimization header."""
        print("\n" + "=" * 70)
        print("🚀 NSGA-III MULTI-OBJECTIVE OPTIMIZATION")
        print("=" * 70)
        print(f"📍 Area: {self.bounds}")
        print(f"🏢 Buildings: {len(self.buildings)}")
        print("⚙️  Configuration:")
        print(f"   Population Size: {self.config.population_size}")
        print(f"   Generations: {self.config.n_generations}")
        print(f"   Reference Points: {len(self.optimizer.reference_points)}")
        print(f"   Crossover Rate: {self.config.crossover_rate}")
        print(f"   Mutation Rate: {self.config.mutation_rate}")
        print("=" * 70)
        print()

    def _print_results(self, result: Dict[str, Any], runtime: float):
        """Print optimization results."""
        print("\n" + "=" * 70)
        print("✅ NSGA-III OPTIMIZATION COMPLETE")
        print("=" * 70)
        print(f"⏱️  Runtime: {runtime:.2f}s")
        print("📊 Statistics:")
        print(f"   Evaluations: {result['statistics']['evaluations']:,}")
        print(f"   Generations: {self.config.n_generations}")
        print(f"   Pareto Front Size: {len(result['pareto_front'])}")
        print()

        # Print convergence summary
        if "convergence" in result:
            conv = result["convergence"]
            if "n_pareto_front" in conv and len(conv["n_pareto_front"]) > 0:
                final_size = conv["n_pareto_front"][-1]
                print("📈 Convergence:")
                print(f"   Initial Pareto Size: {conv['n_pareto_front'][0]}")
                print(f"   Final Pareto Size: {final_size}")

        print("=" * 70)
        print()


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


def run_nsga3(
    buildings: List[Building],
    bounds: Tuple[float, float, float, float],
    population_size: int = 100,
    n_generations: int = 100,
    n_partitions: int = 12,
    verbose: bool = True,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Convenience function to run NSGA-III optimization.

    Args:
        buildings: List of buildings to place
        bounds: Site boundaries (x_min, y_min, x_max, y_max)
        population_size: Population size
        n_generations: Number of generations
        n_partitions: Number of partitions for reference points
        verbose: Print progress
        seed: Random seed

    Returns:
        Result dictionary with Pareto front and statistics

    Example:
        >>> buildings = [
        ...     Building("Library", BuildingType.EDUCATIONAL, 2000, 3),
        ...     Building("Dorm", BuildingType.RESIDENTIAL, 3000, 5),
        ... ]
        >>> bounds = (0, 0, 1000, 1000)
        >>> result = run_nsga3(buildings, bounds, population_size=50)
        >>> print(f"Pareto front size: {len(result['pareto_front'])}")
    """
    config = NSGA3RunnerConfig(
        population_size=population_size,
        n_generations=n_generations,
        n_partitions=n_partitions,
        verbose=verbose,
        seed=seed,
    )

    runner = NSGA3Runner(buildings, bounds, config)
    return runner.run()
