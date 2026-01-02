"""
Benchmarking Infrastructure

Systematic performance testing for optimization algorithms.
Supports Sprint A1+ research validation and performance monitoring.

Example:
    >>> from backend.core.research import BenchmarkRunner, BenchmarkResult
    >>> runner = BenchmarkRunner()
    >>> result = runner.run_benchmark(
    ...     algorithm="NSGA-III",
    ...     problem_size=50,
    ...     runs=10
    ... )
    >>> print(f"Mean hypervolume: {result.mean_hypervolume:.3f}")
"""

import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """
    Benchmark configuration.

    Attributes:
        problem_name: Problem identifier (e.g., "campus_50_buildings")
        algorithm: Algorithm to benchmark
        num_runs: Number of independent runs
        max_evaluations: Budget for each run
        parameters: Algorithm-specific parameters
        metrics: Metrics to track (hypervolume, runtime, etc.)
    """

    problem_name: str
    algorithm: str
    num_runs: int = 10
    max_evaluations: int = 10000
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics: List[str] = field(default_factory=lambda: ["hypervolume", "runtime_s", "convergence"])


@dataclass
class BenchmarkResult:
    """
    Aggregated benchmark results across multiple runs.

    Attributes:
        config: Benchmark configuration
        mean_metrics: Mean values for each metric
        std_metrics: Standard deviation for each metric
        min_metrics: Minimum values
        max_metrics: Maximum values
        all_runs: Individual run results
    """

    config: BenchmarkConfig
    mean_metrics: Dict[str, float] = field(default_factory=dict)
    std_metrics: Dict[str, float] = field(default_factory=dict)
    min_metrics: Dict[str, float] = field(default_factory=dict)
    max_metrics: Dict[str, float] = field(default_factory=dict)
    all_runs: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def mean_hypervolume(self) -> float:
        """Convenience property for mean hypervolume."""
        return self.mean_metrics.get("hypervolume", 0.0)

    @property
    def mean_runtime(self) -> float:
        """Convenience property for mean runtime."""
        return self.mean_metrics.get("runtime_s", 0.0)

    def summary(self) -> str:
        """
        Generate human-readable summary.

        Returns:
            Summary string with key metrics
        """
        lines = [
            f"Benchmark: {self.config.algorithm} on {self.config.problem_name}",
            f"Runs: {self.config.num_runs}",
            "",
            "Results:",
        ]

        for metric in self.config.metrics:
            mean = self.mean_metrics.get(metric, 0.0)
            std = self.std_metrics.get(metric, 0.0)
            min_val = self.min_metrics.get(metric, 0.0)
            max_val = self.max_metrics.get(metric, 0.0)

            lines.append(
                f"  {metric}: {mean:.4f} ± {std:.4f} " f"(min: {min_val:.4f}, max: {max_val:.4f})"
            )

        return "\n".join(lines)


class BenchmarkRunner:
    """
    Runs systematic benchmarks for algorithm comparison.

    Usage:
        >>> runner = BenchmarkRunner(output_dir="data/benchmarks")
        >>> config = BenchmarkConfig(
        ...     problem_name="campus_50",
        ...     algorithm="NSGA-III",
        ...     num_runs=10
        ... )
        >>> result = runner.run(config, optimization_function)
        >>> print(result.summary())
    """

    def __init__(self, output_dir: str = "data/benchmarks"):
        """
        Initialize benchmark runner.

        Args:
            output_dir: Directory for benchmark results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, config: BenchmarkConfig, optimization_fn: Callable) -> BenchmarkResult:
        """
        Run benchmark with specified configuration.

        Args:
            config: Benchmark configuration
            optimization_fn: Function that runs optimization and returns metrics

        Returns:
            Aggregated benchmark results
        """
        logger.info(
            f"Starting benchmark: {config.algorithm} on {config.problem_name} "
            f"({config.num_runs} runs)"
        )

        all_runs = []

        for run_idx in range(config.num_runs):
            logger.info(f"  Run {run_idx + 1}/{config.num_runs}")

            start_time = time.time()

            try:
                # Run optimization
                run_metrics = optimization_fn(config.parameters)

                # Add runtime
                run_metrics["runtime_s"] = time.time() - start_time

                all_runs.append(run_metrics)

            except Exception as e:
                logger.error(f"Run {run_idx + 1} failed: {e}")
                # Add failed run with zero metrics
                all_runs.append({metric: 0.0 for metric in config.metrics})

        # Aggregate results
        result = self._aggregate_results(config, all_runs)

        # Save results
        self._save_result(result)

        logger.info(f"Benchmark complete:\n{result.summary()}")

        return result

    def _aggregate_results(
        self, config: BenchmarkConfig, all_runs: List[Dict[str, Any]]
    ) -> BenchmarkResult:
        """
        Aggregate individual run results.

        Args:
            config: Benchmark configuration
            all_runs: List of individual run metrics

        Returns:
            Aggregated benchmark result
        """
        result = BenchmarkResult(config=config, all_runs=all_runs)

        for metric in config.metrics:
            values = [run.get(metric, 0.0) for run in all_runs]

            result.mean_metrics[metric] = statistics.mean(values)
            result.std_metrics[metric] = statistics.stdev(values) if len(values) > 1 else 0.0
            result.min_metrics[metric] = min(values)
            result.max_metrics[metric] = max(values)

        return result

    def _save_result(self, result: BenchmarkResult):
        """
        Save benchmark result to JSON.

        Args:
            result: Benchmark result to save
        """
        # Create filename from config
        problem = result.config.problem_name
        algorithm = result.config.algorithm
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{problem}_{algorithm}_{timestamp}.json"

        filepath = self.output_dir / filename

        # Convert to dict
        data = {
            "config": {
                "problem_name": result.config.problem_name,
                "algorithm": result.config.algorithm,
                "num_runs": result.config.num_runs,
                "max_evaluations": result.config.max_evaluations,
                "parameters": result.config.parameters,
                "metrics": result.config.metrics,
            },
            "results": {
                "mean_metrics": result.mean_metrics,
                "std_metrics": result.std_metrics,
                "min_metrics": result.min_metrics,
                "max_metrics": result.max_metrics,
                "all_runs": result.all_runs,
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved benchmark result to {filepath}")

    def load_result(self, filepath: Path) -> BenchmarkResult:
        """
        Load benchmark result from JSON.

        Args:
            filepath: Path to result file

        Returns:
            Loaded benchmark result
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        config = BenchmarkConfig(**data["config"])

        result = BenchmarkResult(
            config=config,
            mean_metrics=data["results"]["mean_metrics"],
            std_metrics=data["results"]["std_metrics"],
            min_metrics=data["results"]["min_metrics"],
            max_metrics=data["results"]["max_metrics"],
            all_runs=data["results"]["all_runs"],
        )

        return result

    def compare_algorithms(
        self, results: List[BenchmarkResult], metric: str = "hypervolume"
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare multiple algorithms on a specific metric.

        Args:
            results: List of benchmark results
            metric: Metric to compare

        Returns:
            Dictionary mapping algorithm to {mean, std}
        """
        comparison = {}

        for result in results:
            algo = result.config.algorithm
            comparison[algo] = {
                "mean": result.mean_metrics.get(metric, 0.0),
                "std": result.std_metrics.get(metric, 0.0),
                "min": result.min_metrics.get(metric, 0.0),
                "max": result.max_metrics.get(metric, 0.0),
            }

        return comparison
