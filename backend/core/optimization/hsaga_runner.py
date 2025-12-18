"""
Phase 6: H-SAGA Runner - Hybrid Optimization Pipeline.

This module provides a simplified H-SAGA runner that:
1. Runs Simulated Annealing for exploration (30% of budget)
2. Injects SA survivors into NSGA-III population
3. Runs NSGA-III for refinement (70% of budget)
4. Returns the best solution from the Pareto front

Designed to work with the new SpatialOptimizationProblem.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.termination import get_termination
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions

from backend.core.optimization.spatial_problem import SpatialOptimizationProblem
from backend.core.optimization.encoding import (
    SmartInitializer, GENES_PER_BUILDING, array_to_genome, decode_all_to_polygons
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class HSAGARunnerConfig:
    """Configuration for the H-SAGA runner."""
    
    # Budget allocation
    total_evaluations: int = 5000
    sa_fraction: float = 0.30          # 30% for SA exploration
    
    # SA parameters
    initial_temperature: float = 1000.0
    final_temperature: float = 1.0
    cooling_schedule: str = "exponential"  # 'exponential' or 'linear'
    sa_chains: int = 8                     # Parallel SA chains
    
    # GA parameters
    population_size: int = 100
    crossover_prob: float = 0.9
    crossover_eta: float = 15.0
    mutation_prob: float = 0.2
    mutation_eta: float = 20.0
    
    # NSGA-III specific
    n_partitions: int = 12
    
    # Constraint handling
    constraint_penalty: float = 1e6
    
    # Performance
    seed: Optional[int] = 42
    verbose: bool = True
    parallel_sa: bool = True  # Enable parallel SA chains (ProcessPoolExecutor)


# =============================================================================
# WORKER FUNCTION (Top-Level for Multiprocessing Pickling)
# =============================================================================

def run_sa_chain_worker(
    problem: SpatialOptimizationProblem,
    config: HSAGARunnerConfig,
    chain_idx: int,
    iterations: int,
    seed_offset: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Worker function for parallel SA execution.
    Must be top-level to be pickleable for ProcessPoolExecutor.
    """
    # Create thread-local (process-local) RNG for reproducibility
    # We use a distinct seed for each chain
    base_seed = config.seed if config.seed is not None else int(time.time())
    local_rng = np.random.default_rng(base_seed + seed_offset)
    
    # Initialize random solution within bounds
    x = local_rng.uniform(problem.xl, problem.xu)
    
    # Evaluate initial solution
    # Note: We must replicate the _evaluate and _scalarize logic here 
    # since we don't have access to the SAExplorer instance methods easily
    
    out = {}
    problem._evaluate(x, out)
    F, G = out["F"], out["G"]
    
    # Scalarize
    obj_sum = np.sum(F)
    constraint_violation = np.sum(np.maximum(0, G))
    penalty = config.constraint_penalty * constraint_violation
    cost = obj_sum + penalty
    
    best_x = x.copy()
    best_F = F.copy()
    best_G = G.copy()
    best_cost = cost
    
    temperature = config.initial_temperature
    
    for iteration in range(iterations):
        # Generate neighbor
        # Step size decreases with temperature
        t_ratio = temperature / config.initial_temperature
        step_params = 0.1 * t_ratio + 0.01
        
        # Random perturbation
        delta = local_rng.normal(0, step_params, size=x.shape)
        y = x + delta
        y = np.clip(y, problem.xl, problem.xu)
        
        # Evaluate neighbor
        out_new = {}
        problem._evaluate(y, out_new)
        F_new, G_new = out_new["F"], out_new["G"]
        
        # Scalarize neighbor
        obj_sum_new = np.sum(F_new)
        viol_new = np.sum(np.maximum(0, G_new))
        penalty_new = config.constraint_penalty * viol_new
        cost_new = obj_sum_new + penalty_new
        
        # Metropolis acceptance
        if cost_new < cost:
            accepted = True
        else:
            delta_cost = cost_new - cost
            # Avoid overflow in exp
            prob = np.exp(-delta_cost / max(temperature, 1e-10))
            accepted = local_rng.random() < prob
            
        if accepted:
            x = y
            F = F_new
            G = G_new
            cost = cost_new
            
            if cost < best_cost:
                best_x = x.copy()
                best_F = F.copy()
                best_G = G.copy()
                best_cost = cost
        
        # Cool down
        progress = iteration / iterations
        if config.cooling_schedule == "linear":
            temperature = config.initial_temperature * (1 - progress) + config.final_temperature * progress
        else:
            ratio = config.final_temperature / config.initial_temperature
            temperature = config.initial_temperature * (ratio ** progress)
    
    return (best_x, best_F, best_G, best_cost)


# =============================================================================
# SIMULATED ANNEALING ENGINE
# =============================================================================

class SAExplorer:
    """
    Simulated Annealing phase for global exploration.
    
    Runs multiple parallel chains to find diverse basins of attraction
    before handing off to NSGA-III.
    """
    
    def __init__(
        self,
        problem: SpatialOptimizationProblem,
        config: HSAGARunnerConfig
    ):
        self.problem = problem
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        
        # Track evaluations
        self.n_evals = 0
        self.best_solutions = []
    
    def _evaluate(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Evaluate a single solution."""
        out = {}
        self.problem._evaluate(x, out)
        self.n_evals += 1
        return out["F"], out["G"]
    
    def _scalarize(self, F: np.ndarray, G: np.ndarray) -> float:
        """
        Convert multi-objective to scalar for SA acceptance.
        Uses weighted sum with constraint penalty.
        """
        # Sum objectives
        obj_sum = np.sum(F)
        
        # Add constraint penalty
        constraint_violation = np.sum(np.maximum(0, G))
        penalty = self.config.constraint_penalty * constraint_violation
        
        return obj_sum + penalty
    
    def _acceptance_probability(
        self,
        current_cost: float,
        new_cost: float,
        temperature: float
    ) -> float:
        """Metropolis acceptance probability."""
        if new_cost < current_cost:
            return 1.0
        
        delta = new_cost - current_cost
        return np.exp(-delta / max(temperature, 1e-10))
    
    def _neighbor(self, x: np.ndarray, temperature: float) -> np.ndarray:
        """
        Generate a neighbor solution.
        Uses adaptive step size based on temperature.
        """
        # Step size decreases with temperature
        t_ratio = temperature / self.config.initial_temperature
        step_size = 0.1 * t_ratio + 0.01  # 0.01 to 0.11
        
        # Random perturbation
        delta = self.rng.normal(0, step_size, size=x.shape)
        y = x + delta
        
        # Clip to bounds
        y = np.clip(y, self.problem.xl, self.problem.xu)
        
        return y
    
    def _update_temperature(
        self,
        iteration: int,
        max_iterations: int
    ) -> float:
        """Update temperature based on cooling schedule."""
        progress = iteration / max_iterations
        
        if self.config.cooling_schedule == "linear":
            return self.config.initial_temperature * (1 - progress) + self.config.final_temperature * progress
        else:  # Exponential
            ratio = self.config.final_temperature / self.config.initial_temperature
            return self.config.initial_temperature * (ratio ** progress)
    
    def run(self, max_evaluations: int) -> List[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Run SA exploration phase.
        
        Uses ProcessPoolExecutor for TRUE PARALLEL execution when parallel_sa=True.
        """
        n_chains = self.config.sa_chains
        evals_per_chain = max_evaluations // n_chains
        
        if self.config.verbose:
            parallel_str = "parallel (ProcessPool)" if self.config.parallel_sa else "sequential"
            print(f"[SA] Starting {n_chains} chains ({parallel_str}) with {max_evaluations} total evaluations...")
        
        if self.config.parallel_sa:
            # Parallel execution with ProcessPoolExecutor (Bypasses GIL)
            # Uses 'spawn' start method on macOS for safety with some libraries, 
            # though 'fork' is default on Unix. Python 3.8+ on macOS defaults to 'spawn'.
            
            chain_results = []
            
            # We must pass the problem and config to workers.
            # SpatialOptimizationProblem is now pickle-safe via __getstate__.
            
            with ProcessPoolExecutor(max_workers=n_chains) as executor:
                futures = {
                    executor.submit(
                        run_sa_chain_worker, 
                        self.problem, 
                        self.config, 
                        i, 
                        evals_per_chain, 
                        i
                    ): i
                    for i in range(n_chains)
                }
                
                for future in as_completed(futures):
                    chain_idx = futures[future]
                    try:
                        best_x, best_F, best_G, best_cost = future.result()
                        chain_results.append((best_x, best_F, best_G, best_cost, chain_idx))
                    except Exception as e:
                        print(f"[SA] ❌ Chain {chain_idx} failed: {e}")
                        # Don't crash the whole run, just lose this chain
            
            # Sort by chain index for consistent ordering
            chain_results.sort(key=lambda x: x[4])
            
            # Sum up evaluations (approximation, as each worker ran evals_per_chain)
            self.n_evals += n_chains * evals_per_chain
            
            if self.config.verbose:
                for best_x, best_F, best_G, best_cost, chain_idx in chain_results:
                    feasible = np.all(best_G <= 0)
                    status = "✓" if feasible else "✗"
                    print(f"  Chain {chain_idx + 1}: Cost={best_cost:.4f} [{status}]")
            
            # Extract results without chain_idx
            results = [(x, F, G) for x, F, G, _, _ in chain_results]
            
        else:
            # Sequential execution for debugging
            results = []
            for chain_idx in range(n_chains):
                # We can reuse the worker logic locally
                best_x, best_F, best_G, best_cost = run_sa_chain_worker(
                    self.problem,
                    self.config,
                    chain_idx,
                    evals_per_chain,
                    chain_idx
                )
                
                self.n_evals += evals_per_chain
                results.append((best_x, best_F, best_G))
                
                if self.config.verbose:
                    feasible = np.all(best_G <= 0)
                    status = "✓" if feasible else "✗"
                    print(f"  Chain {chain_idx + 1}: Cost={best_cost:.4f} [{status}]")
        
        self.best_solutions = results
        return results


# =============================================================================
# H-SAGA RUNNER
# =============================================================================

class HSAGARunner:
    """
    Hybrid Simulated Annealing to Genetic Algorithm runner.
    
    Orchestrates the two-phase optimization:
    1. SA for basin exploration
    2. NSGA-III for Pareto refinement
    """
    
    def __init__(
        self,
        problem: SpatialOptimizationProblem,
        config: HSAGARunnerConfig = None
    ):
        self.problem = problem
        self.config = config or HSAGARunnerConfig()
        self.rng = np.random.default_rng(self.config.seed)
        
        # State
        self.sa_results = None
        self.ga_result = None
        self.stats = {
            "sa_evaluations": 0,
            "ga_evaluations": 0,
            "total_time": 0,
            "sa_time": 0,
            "ga_time": 0
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Run the full H-SAGA optimization.
        
        Returns:
            Dict containing best solution, Pareto front, and statistics
        """
        start_time = time.time()
        
        # Calculate evaluation budget
        sa_budget = int(self.config.total_evaluations * self.config.sa_fraction)
        ga_budget = self.config.total_evaluations - sa_budget
        ga_generations = ga_budget // self.config.population_size
        
        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f"H-SAGA OPTIMIZATION")
            print(f"{'='*60}")
            print(f"Total Budget: {self.config.total_evaluations} evaluations")
            print(f"SA Phase: {sa_budget} ({self.config.sa_fraction*100:.0f}%)")
            print(f"GA Phase: {ga_budget} ({(1-self.config.sa_fraction)*100:.0f}%)")
            print(f"Buildings: {self.problem.num_buildings}")
            print(f"{'='*60}\n")
        
        # Phase 1: Simulated Annealing
        if self.config.verbose:
            print("[PHASE 1] SIMULATED ANNEALING (Exploration)")
        
        sa_start = time.time()
        sa_explorer = SAExplorer(self.problem, self.config)
        self.sa_results = sa_explorer.run(sa_budget)
        self.stats["sa_evaluations"] = sa_explorer.n_evals
        self.stats["sa_time"] = time.time() - sa_start
        
        # Phase 2: NSGA-III
        if self.config.verbose:
            print(f"\n[PHASE 2] NSGA-III (Refinement)")
        
        ga_start = time.time()
        
        # Create initial population from SA results
        initial_pop = self._create_initial_population()
        
        # Setup NSGA-III
        ref_dirs = get_reference_directions(
            "das-dennis",
            self.problem.n_obj,
            n_partitions=self.config.n_partitions
        )
        
        algorithm = NSGA3(
            ref_dirs=ref_dirs,
            pop_size=self.config.population_size,
            sampling=initial_pop,
            crossover=SBX(
                prob=self.config.crossover_prob,
                eta=self.config.crossover_eta
            ),
            mutation=PM(
                prob=self.config.mutation_prob,
                eta=self.config.mutation_eta
            )
        )
        
        if ga_generations < 1:
             ga_generations = 1
        
        termination = get_termination("n_gen", ga_generations)
        
        # Run optimization
        self.ga_result = minimize(
            self.problem,
            algorithm,
            termination,
            seed=self.config.seed,
            verbose=self.config.verbose
        )
        
        self.stats["ga_evaluations"] = self.ga_result.algorithm.evaluator.n_eval
        self.stats["ga_time"] = time.time() - ga_start
        self.stats["total_time"] = time.time() - start_time
        
        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f"OPTIMIZATION COMPLETE")
            print(f"{'='*60}")
            print(f"Total Evaluations: {self.stats['sa_evaluations'] + self.stats['ga_evaluations']}")
            print(f"Total Time: {self.stats['total_time']:.2f}s")
            print(f"Pareto Front Size: {len(self.ga_result.F) if self.ga_result.F is not None else 0}")
            print(f"{'='*60}\n")
        
        return self._build_result()
    
    def _create_initial_population(self) -> np.ndarray:
        """Create initial GA population from SA results."""
        pop_size = self.config.population_size
        n_vars = self.problem.n_var
        
        population = np.zeros((pop_size, n_vars))
        
        # Inject SA survivors
        n_sa = len(self.sa_results)
        for i, (x, F, G) in enumerate(self.sa_results):
            population[i] = x
        
        # Fill rest with random or perturbed SA solutions
        for i in range(n_sa, pop_size):
            # Pick random SA solution and perturb
            parent_idx = i % n_sa
            parent = self.sa_results[parent_idx][0]
            
            delta = self.rng.normal(0, 0.05, size=n_vars)
            child = parent + delta
            child = np.clip(child, self.problem.xl, self.problem.xu)
            
            population[i] = child
        
        return population
    
    def _build_result(self) -> Dict[str, Any]:
        """Build the final result dictionary."""
        result = {
            "success": self.ga_result.F is not None,
            "stats": self.stats
        }
        
        if self.ga_result.F is not None and len(self.ga_result.F) > 0:
            # Get best compromise solution (minimum sum of objectives)
            best_idx = np.argmin(np.sum(self.ga_result.F, axis=1))
            
            best_x = self.ga_result.X[best_idx]
            best_F = self.ga_result.F[best_idx]
            
            # Decode for visualization
            genes, polygons = self.problem.decode_solution(best_x)
            
            result["best_solution"] = {
                "x": best_x,
                "F": best_F,
                "genes": genes,
                "polygons": polygons
            }
            
            result["pareto_front"] = {
                "X": self.ga_result.X,
                "F": self.ga_result.F
            }
        
        return result
    
    def get_best_solution(self) -> Optional[Dict[str, Any]]:
        """Get the best solution found."""
        if self.ga_result is None or self.ga_result.F is None:
            return None
        
        best_idx = np.argmin(np.sum(self.ga_result.F, axis=1))
        best_x = self.ga_result.X[best_idx]
        genes, polygons = self.problem.decode_solution(best_x)
        
        return {
            "x": best_x,
            "F": self.ga_result.F[best_idx],
            "genes": genes,
            "polygons": polygons
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def run_hsaga(
    problem: SpatialOptimizationProblem,
    total_evaluations: int = 5000,
    sa_fraction: float = 0.30,
    verbose: bool = True,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Convenience function to run H-SAGA optimization.
    
    Args:
        problem: Configured SpatialOptimizationProblem
        total_evaluations: Total evaluation budget
        sa_fraction: Fraction of budget for SA phase
        verbose: Print progress
        seed: Random seed
    
    Returns:
        Result dictionary with best solution and statistics
    """
    config = HSAGARunnerConfig(
        total_evaluations=total_evaluations,
        sa_fraction=sa_fraction,
        verbose=verbose,
        seed=seed
    )
    
    runner = HSAGARunner(problem, config)
    return runner.run()
