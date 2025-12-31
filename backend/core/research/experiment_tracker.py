"""
Experiment Tracking Infrastructure

Tracks optimization experiments for research integration (Sprint A1+).
Enables systematic comparison of algorithms, parameters, and objectives.

Example:
    >>> from backend.core.research import ExperimentTracker, ExperimentConfig
    >>> config = ExperimentConfig(
    ...     name="nsga3_vs_hsaga",
    ...     algorithm="NSGA-III",
    ...     parameters={"pop_size": 100, "n_gen": 50}
    ... )
    >>> tracker = ExperimentTracker(experiment_dir="data/experiments")
    >>> with tracker.track(config) as exp:
    ...     result = run_optimization()
    ...     exp.log_metrics({"hypervolume": 0.85, "runtime_s": 120})
    ...     exp.log_solution(result)
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """
    Experiment configuration for reproducibility.

    Attributes:
        name: Experiment name (e.g., "sprint_a1_turkish_codes")
        algorithm: Algorithm identifier (e.g., "NSGA-III", "H-SAGA")
        parameters: Algorithm hyperparameters
        objectives: List of objective functions
        constraints: List of constraint functions
        metadata: Additional context (sprint, research paper ref, etc.)
    """

    name: str
    algorithm: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    objectives: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """
    Experiment results for analysis.

    Attributes:
        config: Experiment configuration
        metrics: Performance metrics (hypervolume, runtime, etc.)
        solution: Best solution found
        history: Optimization history (convergence data)
        timestamp: Experiment start time
        duration_s: Total duration in seconds
    """

    config: ExperimentConfig
    metrics: Dict[str, float]
    solution: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None
    timestamp: str = ""
    duration_s: float = 0.0


class ExperimentTracker:
    """
    Tracks optimization experiments with structured logging.

    Usage:
        >>> tracker = ExperimentTracker(experiment_dir="data/experiments")
        >>> config = ExperimentConfig(name="test", algorithm="NSGA-III")
        >>> with tracker.track(config) as exp:
        ...     exp.log_metrics({"hypervolume": 0.85})
        ...     exp.log_solution({"buildings": [...]})
    """

    def __init__(self, experiment_dir: str = "data/experiments"):
        """
        Initialize experiment tracker.

        Args:
            experiment_dir: Root directory for experiment data
        """
        self.experiment_dir = Path(experiment_dir)
        self.experiment_dir.mkdir(parents=True, exist_ok=True)

        self.current_experiment: Optional[ExperimentContext] = None

    def track(self, config: ExperimentConfig) -> "ExperimentContext":
        """
        Start tracking an experiment.

        Args:
            config: Experiment configuration

        Returns:
            ExperimentContext for logging metrics and results
        """
        return ExperimentContext(self, config)

    def save_result(self, result: ExperimentResult) -> Path:
        """
        Save experiment result to JSON.

        Args:
            result: Experiment result to save

        Returns:
            Path to saved result file
        """
        # Create experiment subdirectory
        exp_name = result.config.name
        exp_timestamp = datetime.fromisoformat(result.timestamp).strftime("%Y%m%d_%H%M%S")
        exp_subdir = self.experiment_dir / exp_name / exp_timestamp
        exp_subdir.mkdir(parents=True, exist_ok=True)

        # Save result as JSON
        result_path = exp_subdir / "result.json"

        result_dict = {
            "config": asdict(result.config),
            "metrics": result.metrics,
            "solution": result.solution,
            "history": result.history,
            "timestamp": result.timestamp,
            "duration_s": result.duration_s,
        }

        with open(result_path, "w") as f:
            json.dump(result_dict, f, indent=2)

        logger.info(f"Saved experiment result to {result_path}")
        return result_path

    def load_results(self, experiment_name: str) -> List[ExperimentResult]:
        """
        Load all results for an experiment.

        Args:
            experiment_name: Name of experiment

        Returns:
            List of experiment results
        """
        exp_dir = self.experiment_dir / experiment_name
        if not exp_dir.exists():
            return []

        results = []
        for run_dir in sorted(exp_dir.iterdir()):
            result_path = run_dir / "result.json"
            if result_path.exists():
                with open(result_path, "r") as f:
                    data = json.load(f)

                config = ExperimentConfig(**data["config"])
                result = ExperimentResult(
                    config=config,
                    metrics=data["metrics"],
                    solution=data.get("solution"),
                    history=data.get("history"),
                    timestamp=data["timestamp"],
                    duration_s=data["duration_s"],
                )
                results.append(result)

        return results

    def compare_experiments(
        self, experiment_names: List[str], metric: str = "hypervolume"
    ) -> Dict[str, float]:
        """
        Compare experiments by a specific metric.

        Args:
            experiment_names: List of experiment names
            metric: Metric to compare (default: hypervolume)

        Returns:
            Dictionary mapping experiment name to best metric value
        """
        comparison = {}

        for exp_name in experiment_names:
            results = self.load_results(exp_name)
            if results:
                # Get best result by metric
                best_result = max(results, key=lambda r: r.metrics.get(metric, 0.0))
                comparison[exp_name] = best_result.metrics.get(metric, 0.0)
            else:
                comparison[exp_name] = 0.0

        return comparison


class ExperimentContext:
    """
    Context manager for experiment tracking.

    Automatically records start/end times and saves results.
    """

    def __init__(self, tracker: ExperimentTracker, config: ExperimentConfig):
        """
        Initialize experiment context.

        Args:
            tracker: Parent experiment tracker
            config: Experiment configuration
        """
        self.tracker = tracker
        self.config = config

        self.start_time = 0.0
        self.metrics: Dict[str, float] = {}
        self.solution: Optional[Dict[str, Any]] = None
        self.history: List[Dict[str, Any]] = []

    def __enter__(self) -> "ExperimentContext":
        """Start experiment tracking."""
        self.start_time = time.time()
        self.tracker.current_experiment = self
        logger.info(f"Started experiment: {self.config.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End experiment tracking and save results."""
        duration = time.time() - self.start_time

        # Create result
        result = ExperimentResult(
            config=self.config,
            metrics=self.metrics,
            solution=self.solution,
            history=self.history,
            timestamp=datetime.now().isoformat(),
            duration_s=duration,
        )

        # Save result
        self.tracker.save_result(result)

        logger.info(
            f"Completed experiment: {self.config.name} "
            f"(duration: {duration:.2f}s, metrics: {self.metrics})"
        )

        self.tracker.current_experiment = None

    def log_metrics(self, metrics: Dict[str, float]):
        """
        Log performance metrics.

        Args:
            metrics: Dictionary of metric names to values
        """
        self.metrics.update(metrics)

    def log_solution(self, solution: Dict[str, Any]):
        """
        Log the best solution found.

        Args:
            solution: Solution data (buildings, layout, etc.)
        """
        self.solution = solution

    def log_history(self, generation: int, data: Dict[str, Any]):
        """
        Log optimization history for a generation.

        Args:
            generation: Generation number
            data: Generation data (fitness, diversity, etc.)
        """
        self.history.append({"generation": generation, **data})
