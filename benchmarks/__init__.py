"""
Performance Benchmarking Module
================================

This module provides tools for benchmarking and comparing optimization algorithms,
specifically NSGA-III and AdaptiveHSAGA.

Components:
    - BenchmarkRunner: Execute benchmark test cases
    - BenchmarkConfig: Configuration for benchmark parameters
    - BenchmarkReporter: Generate reports and visualizations
"""

from .benchmark_reporter import BenchmarkReporter
from .benchmark_runner import BenchmarkConfig, BenchmarkRunner
from .test_cases import BenchmarkTestCase, create_test_cases

__all__ = [
    "BenchmarkRunner",
    "BenchmarkConfig",
    "BenchmarkReporter",
    "BenchmarkTestCase",
    "create_test_cases",
]
