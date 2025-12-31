"""
Research Integration Module

Experiment tracking, benchmarking, and research-to-production pipeline.
Supports Sprint A1+ research integration efforts.
"""

from .benchmark import BenchmarkResult, BenchmarkRunner
from .experiment_tracker import ExperimentConfig, ExperimentTracker

__all__ = [
    "ExperimentTracker",
    "ExperimentConfig",
    "BenchmarkRunner",
    "BenchmarkResult",
]
