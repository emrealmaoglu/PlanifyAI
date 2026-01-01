"""
Explainability Module for Campus Planning Optimization
=======================================================

Provides transparency and interpretability for optimization decisions.

Key Components:
    - constraint_reporter: Human-readable constraint violation reports
    - decision_logger: Logs algorithm decisions and reasoning
    - pareto_analyzer: Multi-objective trade-off analysis

Purpose:
    Enable users to understand WHY the optimizer made specific decisions,
    WHAT constraints were violated, and HOW to fix issues.

References:
    - XAI (Explainable AI) principles
    - LIME/SHAP for model interpretability
    - Research: "Explainable AI Campus Planning.docx"
"""

from .constraint_reporter import ConstraintReporter, ConstraintViolation, ViolationSeverity
from .decision_logger import DecisionLogger, DecisionType, OptimizerDecision

__all__ = [
    # Constraint Reporting
    "ConstraintReporter",
    "ConstraintViolation",
    "ViolationSeverity",
    # Decision Logging
    "DecisionLogger",
    "DecisionType",
    "OptimizerDecision",
]
