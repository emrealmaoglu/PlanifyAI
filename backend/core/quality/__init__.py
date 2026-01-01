"""
Quality Metrics Module for Multi-Objective Optimization
========================================================

Provides advanced quality assessment tools for evaluating optimization results.

Key Components:
    - pareto_analyzer: Pareto front analysis and hypervolume metrics
    - robustness: Solution robustness and sensitivity analysis
    - convergence: Convergence diagnostics and stopping criteria

Purpose:
    Enable quantitative assessment of optimization quality, not just fitness.

References:
    - Deb et al. (2002): NSGA-II and Pareto dominance
    - Zitzler & Thiele (1999): Hypervolume indicator
    - Research: "Multi-Objective Campus Planning.docx"
"""

from .pareto_analyzer import ParetoFront, ParetoQualityMetrics, compute_hypervolume, is_dominated

__all__ = [
    # Pareto Analysis
    "ParetoFront",
    "ParetoQualityMetrics",
    "compute_hypervolume",
    "is_dominated",
]
