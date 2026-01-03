"""
Benchmark Runner
================

Executes benchmark test cases and collects performance metrics.

Metrics Collected:
    - Runtime (seconds)
    - Number of evaluations
    - Pareto front size
    - Hypervolume indicator
    - Convergence metrics
    - Memory usage
"""

import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np

from backend.core.optimization.adaptive_hsaga_runner import (
    AdaptiveHSAGARunner,
    AdaptiveHSAGARunnerConfig,
)
from backend.core.optimization.nsga3_runner import NSGA3Runner, NSGA3RunnerConfig
from src.algorithms.objective_profiles import ProfileType

from .test_cases import BenchmarkTestCase


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""

    # Algorithm configurations
    nsga3_population_size: int = 50
    nsga3_n_generations: int = 50
    nsga3_n_partitions: int = 12

    hsaga_population_size: int = 50
    hsaga_n_iterations: int = 50
    hsaga_initial_temp: float = 1000.0
    hsaga_final_temp: float = 0.01

    # Objective profile
    objective_profile: ProfileType = ProfileType.RESEARCH_ENHANCED

    # Number of runs for each test case (for statistical significance)
    n_runs: int = 5

    # Random seeds for reproducibility
    seeds: List[int] = field(default_factory=lambda: [42, 123, 456, 789, 1011])

    # Verbosity
    verbose: bool = False


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    algorithm: str  # "NSGA-III" or "AdaptiveHSAGA"
    test_case_name: str
    seed: int
    run_number: int

    # Performance metrics
    runtime: float
    evaluations: int
    pareto_size: int
    hypervolume: float
    memory_peak_mb: float

    # Solution quality
    best_objective_values: List[float]
    pareto_objectives: np.ndarray

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)


class BenchmarkRunner:
    """
    Execute benchmarks comparing NSGA-III and AdaptiveHSAGA.
    """

    def __init__(self, config: BenchmarkConfig):
        """
        Initialize benchmark runner.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        self.results: List[BenchmarkResult] = []

    def run_nsga3(
        self, test_case: BenchmarkTestCase, seed: int, run_number: int
    ) -> BenchmarkResult:
        """
        Run NSGA-III on a test case.

        Args:
            test_case: Test case to run
            seed: Random seed
            run_number: Run number (for multiple runs)

        Returns:
            Benchmark result
        """
        if self.config.verbose:
            print(f"  Running NSGA-III (seed={seed}, run={run_number})...")

        # Configure NSGA-III
        nsga3_config = NSGA3RunnerConfig(
            population_size=self.config.nsga3_population_size,
            n_generations=self.config.nsga3_n_generations,
            n_partitions=self.config.nsga3_n_partitions,
            objective_profile=self.config.objective_profile,
            seed=seed,
            verbose=False,
        )

        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()

        # Run optimization
        runner = NSGA3Runner(test_case.buildings, test_case.bounds, nsga3_config)
        result = runner.run()

        # Measure performance
        runtime = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memory_peak_mb = peak / 1024 / 1024

        # Extract metrics
        pareto_objectives = result["pareto_objectives"]
        best_compromise = result.get("best_compromise")
        best_obj = best_compromise["objectives"] if best_compromise else pareto_objectives[0]

        # Compute hypervolume (simplified)
        reference_point = np.max(pareto_objectives, axis=0) * 1.1
        hypervolume = self._compute_hypervolume(pareto_objectives, reference_point)

        return BenchmarkResult(
            algorithm="NSGA-III",
            test_case_name=test_case.name,
            seed=seed,
            run_number=run_number,
            runtime=runtime,
            evaluations=result["statistics"]["evaluations"],
            pareto_size=len(result["pareto_front"]),
            hypervolume=hypervolume,
            memory_peak_mb=memory_peak_mb,
            best_objective_values=best_obj.tolist(),
            pareto_objectives=pareto_objectives,
            metadata={
                "population_size": self.config.nsga3_population_size,
                "n_generations": self.config.nsga3_n_generations,
                "n_partitions": self.config.nsga3_n_partitions,
            },
        )

    def run_hsaga(
        self, test_case: BenchmarkTestCase, seed: int, run_number: int
    ) -> BenchmarkResult:
        """
        Run AdaptiveHSAGA on a test case.

        Args:
            test_case: Test case to run
            seed: Random seed
            run_number: Run number (for multiple runs)

        Returns:
            Benchmark result
        """
        if self.config.verbose:
            print(f"  Running AdaptiveHSAGA (seed={seed}, run={run_number})...")

        # Configure AdaptiveHSAGA
        hsaga_config = AdaptiveHSAGARunnerConfig(
            population_size=self.config.hsaga_population_size,
            n_iterations=self.config.hsaga_n_iterations,
            initial_temp=self.config.hsaga_initial_temp,
            final_temp=self.config.hsaga_final_temp,
            seed=seed,
            verbose=False,
        )

        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()

        # Run optimization
        runner = AdaptiveHSAGARunner(test_case.buildings, test_case.bounds, hsaga_config)
        result = runner.run()

        # Measure performance
        runtime = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memory_peak_mb = peak / 1024 / 1024

        # Extract metrics
        pareto_front = result["pareto_front"]
        pareto_objectives = np.array([sol.fitness for sol in pareto_front])

        best_solution = result.get("best_solution")
        best_obj = best_solution.fitness if best_solution else pareto_objectives[0]

        # Compute hypervolume
        reference_point = np.max(pareto_objectives, axis=0) * 1.1
        hypervolume = self._compute_hypervolume(pareto_objectives, reference_point)

        return BenchmarkResult(
            algorithm="AdaptiveHSAGA",
            test_case_name=test_case.name,
            seed=seed,
            run_number=run_number,
            runtime=runtime,
            evaluations=result["statistics"]["evaluations"],
            pareto_size=len(pareto_front),
            hypervolume=hypervolume,
            memory_peak_mb=memory_peak_mb,
            best_objective_values=best_obj.tolist() if hasattr(best_obj, "tolist") else best_obj,
            pareto_objectives=pareto_objectives,
            metadata={
                "population_size": self.config.hsaga_population_size,
                "n_iterations": self.config.hsaga_n_iterations,
                "initial_temp": self.config.hsaga_initial_temp,
            },
        )

    def run_benchmark(self, test_case: BenchmarkTestCase) -> List[BenchmarkResult]:
        """
        Run benchmark for a single test case.

        Args:
            test_case: Test case to benchmark

        Returns:
            List of benchmark results
        """
        print(f"\n{'=' * 70}")
        print(f"Benchmarking: {test_case.name}")
        print(f"Description: {test_case.description}")
        print(f"Category: {test_case.category} ({len(test_case.buildings)} buildings)")
        print(f"{'=' * 70}")

        results = []

        # Run NSGA-III
        print("\n[NSGA-III]")
        for i, seed in enumerate(self.config.seeds[: self.config.n_runs]):
            result = self.run_nsga3(test_case, seed, i + 1)
            results.append(result)
            if self.config.verbose:
                print(
                    f"  Run {i+1}: Runtime={result.runtime:.2f}s, "
                    f"Pareto={result.pareto_size}, HV={result.hypervolume:.2f}"
                )

        # Run AdaptiveHSAGA
        print("\n[AdaptiveHSAGA]")
        for i, seed in enumerate(self.config.seeds[: self.config.n_runs]):
            result = self.run_hsaga(test_case, seed, i + 1)
            results.append(result)
            if self.config.verbose:
                print(
                    f"  Run {i+1}: Runtime={result.runtime:.2f}s, "
                    f"Pareto={result.pareto_size}, HV={result.hypervolume:.2f}"
                )

        self.results.extend(results)
        return results

    def run_all_benchmarks(self, test_cases: List[BenchmarkTestCase]) -> List[BenchmarkResult]:
        """
        Run benchmarks for all test cases.

        Args:
            test_cases: List of test cases

        Returns:
            List of all benchmark results
        """
        print("\n" + "#" * 70)
        print("Starting Benchmark Suite")
        print("#" * 70)
        print(f"Total test cases: {len(test_cases)}")
        print(f"Runs per test case: {self.config.n_runs}")
        print(f"Total runs: {len(test_cases) * self.config.n_runs * 2}")  # 2 algorithms
        print(f"Objective profile: {self.config.objective_profile.value}")

        for test_case in test_cases:
            self.run_benchmark(test_case)

        print("\n" + "#" * 70)
        print("Benchmark Suite Complete!")
        print(f"Total results collected: {len(self.results)}")
        print("#" * 70)

        return self.results

    def _compute_hypervolume(self, objectives: np.ndarray, reference_point: np.ndarray) -> float:
        """
        Compute hypervolume indicator (simplified approximation).

        Args:
            objectives: Objective values (n_solutions x n_objectives)
            reference_point: Reference point for hypervolume

        Returns:
            Hypervolume value
        """
        if len(objectives) == 0:
            return 0.0

        # Ensure objectives is 2D
        if objectives.ndim == 1:
            objectives = objectives.reshape(1, -1)

        if objectives.shape[0] == 0:
            return 0.0

        # For 2D objectives, compute exact hypervolume
        if objectives.shape[1] == 2:
            # Sort by first objective
            sorted_idx = np.argsort(objectives[:, 0])
            sorted_obj = objectives[sorted_idx]

            hv = 0.0
            for i in range(len(sorted_obj)):
                width = reference_point[0] - sorted_obj[i, 0]
                height = reference_point[1] - sorted_obj[i, 1]
                if width > 0 and height > 0:
                    # Subtract overlapping area with previous solution
                    if i > 0:
                        prev_height = reference_point[1] - sorted_obj[i - 1, 1]
                        if prev_height > height:
                            height = prev_height
                    hv += width * height

            return hv

        # For higher dimensions, use simple approximation
        # (Product of ranges covered)
        min_vals = np.min(objectives, axis=0)
        ranges = reference_point - min_vals
        hv = np.prod(ranges) * len(objectives) / 1000.0  # Normalize
        return float(hv)

    def get_results_by_algorithm(self, algorithm: str) -> List[BenchmarkResult]:
        """
        Get all results for a specific algorithm.

        Args:
            algorithm: Algorithm name

        Returns:
            Filtered results
        """
        return [r for r in self.results if r.algorithm == algorithm]

    def get_results_by_test_case(self, test_case_name: str) -> List[BenchmarkResult]:
        """
        Get all results for a specific test case.

        Args:
            test_case_name: Test case name

        Returns:
            Filtered results
        """
        return [r for r in self.results if r.test_case_name == test_case_name]
