"""
AdaptiveHSAGA Optimization Runner
==================================

Runner for AdaptiveHSAGA with ObjectiveProfile support.
Provides clean multi-objective optimization with hybrid SA+GA approach.

Created: 2026-01-03
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from src.algorithms import Building, ObjectiveProfile, ProfileType, get_profile
from src.algorithms.hsaga_adaptive import AdaptiveHSAGA
from src.algorithms.solution import Solution

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class AdaptiveHSAGARunnerConfig:
    """Configuration for AdaptiveHSAGA runner."""

    # Population parameters
    population_size: int = 50
    n_iterations: int = 50

    # SA parameters
    initial_temp: float = 1000.0
    final_temp: float = 0.1
    cooling_rate: float = 0.95
    num_chains: int = 4
    chain_iterations: int = 500
    cooling_schedule: str = "adaptive_specific_heat"  # or "exponential", "hybrid"
    adaptive_alpha: float = 0.95
    markov_base_length: int = 10
    use_adaptive_markov: bool = True

    # GA parameters
    generations: int = 50
    crossover_rate: float = 0.8
    mutation_rate: float = 0.15
    elite_size: int = 5
    tournament_size: int = 3

    # Adaptive operator selection
    enable_adaptive: bool = True
    selection_strategy: str = "adaptive_pursuit"  # or "ucb", "thompson", "epsilon_greedy"

    # Objective configuration
    objective_profile: Optional[Union[ObjectiveProfile, ProfileType, str]] = None

    # Performance
    seed: Optional[int] = 42
    verbose: bool = True


# =============================================================================
# ADAPTIVE HSAGA RUNNER
# =============================================================================


class AdaptiveHSAGARunner:
    """
    AdaptiveHSAGA optimization runner for campus planning.

    Provides a clean interface to run AdaptiveHSAGA optimization
    with building placement problems and configurable objective profiles.

    Example:
        >>> buildings = [...]
        >>> bounds = (0, 0, 1000, 1000)
        >>> config = AdaptiveHSAGARunnerConfig(
        ...     population_size=50,
        ...     generations=50,
        ...     objective_profile=ProfileType.RESEARCH_ENHANCED
        ... )
        >>> runner = AdaptiveHSAGARunner(buildings, bounds, config)
        >>> result = runner.run()
        >>> best_solution = result["best_solution"]
    """

    def __init__(
        self,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        config: Optional[AdaptiveHSAGARunnerConfig] = None,
    ):
        """
        Initialize AdaptiveHSAGA runner.

        Args:
            buildings: List of buildings to place
            bounds: Site boundaries (x_min, y_min, x_max, y_max)
            config: Optional configuration
        """
        self.buildings = buildings
        self.bounds = bounds
        self.config = config or AdaptiveHSAGARunnerConfig()

        # Set random seed if provided
        if self.config.seed is not None:
            np.random.seed(self.config.seed)

        # Resolve objective profile
        self.objective_profile = self._resolve_objective_profile(self.config.objective_profile)

        # Create fitness evaluator with profile settings
        from src.algorithms.fitness import FitnessEvaluator

        self.evaluator = FitnessEvaluator(
            buildings=buildings,
            bounds=bounds,
            weights=self.objective_profile.weights,
            use_enhanced=self.objective_profile.use_enhanced,
            walking_speed_kmh=self.objective_profile.walking_speed_kmh,
        )

        # Parse selection strategy
        from src.algorithms.adaptive import SelectionStrategy

        strategy_map = {
            "adaptive_pursuit": SelectionStrategy.ADAPTIVE_PURSUIT,
            "ucb": SelectionStrategy.UCB,
            "softmax": SelectionStrategy.SOFTMAX,
            "greedy": SelectionStrategy.GREEDY,
            "uniform": SelectionStrategy.UNIFORM,
        }
        strategy = strategy_map.get(
            self.config.selection_strategy, SelectionStrategy.ADAPTIVE_PURSUIT
        )

        # Prepare SA config
        sa_config = {
            "initial_temp": self.config.initial_temp,
            "final_temp": self.config.final_temp,
            "cooling_rate": self.config.cooling_rate,
            "num_chains": self.config.num_chains,
            "chain_iterations": self.config.chain_iterations,
            "cooling_schedule": self.config.cooling_schedule,
            "adaptive_alpha": self.config.adaptive_alpha,
            "markov_base_length": self.config.markov_base_length,
            "use_adaptive_markov": self.config.use_adaptive_markov,
        }

        # Prepare GA config
        ga_config = {
            "population_size": self.config.population_size,
            "generations": self.config.generations,
            "crossover_rate": self.config.crossover_rate,
            "mutation_rate": self.config.mutation_rate,
            "elite_size": self.config.elite_size,
            "tournament_size": self.config.tournament_size,
        }

        # Initialize optimizer with custom evaluator
        self.optimizer = AdaptiveHSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config,
            ga_config=ga_config,
            selection_strategy=strategy,
            enable_adaptive=self.config.enable_adaptive,
        )

        # Override evaluator with profile-configured one
        self.optimizer.evaluator = self.evaluator

        # Stats
        self.stats = {
            "evaluations": 0,
            "runtime": 0,
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
            return get_profile(ProfileType.STANDARD)

        if isinstance(profile, ObjectiveProfile):
            return profile

        if isinstance(profile, ProfileType):
            return get_profile(profile)

        if isinstance(profile, str):
            # Try to parse as ProfileType
            try:
                profile_type = ProfileType(profile.lower())
                return get_profile(profile_type)
            except ValueError:
                raise ValueError(
                    f"Invalid profile name: {profile}. "
                    f"Valid options: {[p.value for p in ProfileType]}"
                )

        raise ValueError(f"Invalid profile type: {type(profile)}")

    def run(self) -> Dict[str, Any]:
        """
        Run the full AdaptiveHSAGA optimization.

        Returns:
            Dict containing best solution, Pareto front, and statistics
        """
        start_time = time.time()

        if self.config.verbose:
            print("\n" + "=" * 70)
            print("ADAPTIVE H-SAGA OPTIMIZATION")
            print("=" * 70)
            print(f"Buildings: {len(self.buildings)}")
            print(f"Bounds: {self.bounds}")
            print(f"Objective Profile: {self.objective_profile.name}")
            print(f"  - Use Enhanced: {self.objective_profile.use_enhanced}")
            print(f"  - Weights: {self.objective_profile.weights}")
            print("SA Configuration:")
            print(f"  - Chains: {self.config.num_chains}")
            print(f"  - Iterations/Chain: {self.config.chain_iterations}")
            print(f"  - Cooling: {self.config.cooling_schedule}")
            print(f"  - Adaptive Markov: {self.config.use_adaptive_markov}")
            print("GA Configuration:")
            print(f"  - Population: {self.config.population_size}")
            print(f"  - Generations: {self.config.generations}")
            print(f"Adaptive Operators: {self.config.enable_adaptive}")
            if self.config.enable_adaptive:
                print(f"  - Strategy: {self.config.selection_strategy}")
            print("=" * 70)
            print()

        # Run optimization
        result = self.optimizer.optimize()

        runtime = time.time() - start_time
        self.stats["runtime"] = runtime
        self.stats["evaluations"] = result["statistics"].get("evaluations", 0)

        if self.config.verbose:
            print("\n" + "=" * 70)
            print("OPTIMIZATION COMPLETE")
            print("=" * 70)
            print(f"Total Runtime: {runtime:.2f}s")
            print(f"Total Evaluations: {self.stats['evaluations']}")
            print(f"Best Fitness: {result['fitness']:.4f}")
            print("=" * 70)
            print()

        # Build result in consistent format with NSGA3Runner
        return self._build_result(result)

    def _build_result(self, optimizer_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the final result dictionary in consistent format.

        Args:
            optimizer_result: Result from AdaptiveHSAGA.optimize()

        Returns:
            Standardized result dictionary
        """
        best_solution: Solution = optimizer_result["best_solution"]
        all_solutions: List[Solution] = optimizer_result.get("all_solutions", [])

        # Extract Pareto front (all non-dominated solutions)
        pareto_front = [sol for sol in all_solutions if sol.fitness is not None]
        pareto_front.sort(key=lambda s: s.fitness, reverse=True)

        # Get objectives for Pareto front
        # Ensure consistent number of objectives for all solutions
        pareto_objectives = []
        for sol in pareto_front:
            if hasattr(sol, "objectives") and sol.objectives:
                # Convert objectives dict to array
                obj_list = [
                    sol.objectives.get("cost", 0.0),
                    sol.objectives.get("walking", 0.0),
                    sol.objectives.get("adjacency", 0.0),
                ]
                # Always add diversity if profile uses enhanced objectives
                # (set to 0.0 if not present for consistency)
                if self.objective_profile.use_enhanced:
                    obj_list.append(sol.objectives.get("diversity", 0.0))
                pareto_objectives.append(obj_list)
            else:
                # Fallback: use fitness as single objective
                # Create consistent array based on profile
                if self.objective_profile.use_enhanced:
                    pareto_objectives.append([sol.fitness, 0.0, 0.0, 0.0])
                else:
                    pareto_objectives.append([sol.fitness, 0.0, 0.0])

        pareto_objectives = np.array(pareto_objectives) if pareto_objectives else np.array([[]])

        # Find best compromise (minimum sum of normalized objectives)
        best_compromise = None
        if len(pareto_objectives) > 0 and pareto_objectives.shape[1] > 1:
            # Normalize objectives
            obj_min = np.min(pareto_objectives, axis=0)
            obj_max = np.max(pareto_objectives, axis=0)
            obj_range = obj_max - obj_min
            obj_range[obj_range == 0] = 1  # Avoid division by zero

            normalized_objs = (pareto_objectives - obj_min) / obj_range

            # Find solution with minimum sum of normalized objectives
            sums = np.sum(normalized_objs, axis=1)
            best_idx = np.argmin(sums)

            best_compromise = {
                "index": int(best_idx),
                "solution": pareto_front[best_idx],
                "objectives": pareto_objectives[best_idx].tolist(),
                "normalized_objectives": normalized_objs[best_idx].tolist(),
                "buildings": [
                    {
                        "name": bid,
                        "building_type": self.buildings[i].type.name,
                        "x": pareto_front[best_idx].positions.get(bid, (0, 0))[0],
                        "y": pareto_front[best_idx].positions.get(bid, (0, 0))[1],
                    }
                    for i, bid in enumerate(pareto_front[best_idx].positions.keys())
                ],
            }

        result = {
            "success": True,
            "best_solution": best_solution,
            "pareto_front": pareto_front,
            "pareto_objectives": pareto_objectives,
            "pareto_size": len(pareto_front),
            "n_objectives": pareto_objectives.shape[1] if len(pareto_objectives) > 0 else 0,
            "best_compromise": best_compromise,
            "statistics": {
                "runtime": self.stats["runtime"],
                "evaluations": self.stats["evaluations"],
                "sa_time": optimizer_result["statistics"].get("sa_time", 0),
                "ga_time": optimizer_result["statistics"].get("ga_time", 0),
                "sa_chains": self.config.num_chains,
                "ga_generations": self.config.generations,
            },
            "convergence": optimizer_result.get("convergence", {}),
            "operator_stats": optimizer_result.get("operator_stats", {}),
            "selection_probabilities": optimizer_result.get("selection_probabilities", {}),
            "objective_profile": {
                "name": self.objective_profile.name,
                "description": self.objective_profile.description,
                "use_enhanced": self.objective_profile.use_enhanced,
                "weights": self.objective_profile.weights,
            },
        }

        return result


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


def run_adaptive_hsaga(
    buildings: List[Building],
    bounds: Tuple[float, float, float, float],
    population_size: int = 50,
    generations: int = 50,
    objective_profile: Optional[Union[ObjectiveProfile, ProfileType, str]] = None,
    verbose: bool = True,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Convenience function to run AdaptiveHSAGA optimization.

    Args:
        buildings: List of buildings to place
        bounds: Site boundaries
        population_size: GA population size
        generations: Number of GA generations
        objective_profile: Objective profile to use
        verbose: Print progress
        seed: Random seed

    Returns:
        Result dictionary with best solution and statistics
    """
    config = AdaptiveHSAGARunnerConfig(
        population_size=population_size,
        generations=generations,
        objective_profile=objective_profile,
        verbose=verbose,
        seed=seed,
    )

    runner = AdaptiveHSAGARunner(buildings, bounds, config)
    return runner.run()
