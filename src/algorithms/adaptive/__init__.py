"""
Adaptive Operator Selection
============================

Self-tuning mechanisms for optimization operators.

Components:
- OperatorSelector: Adaptive operator selection based on performance
- ParameterTuner: Self-tuning operator parameters
- CreditAssignment: Track and reward operator performance

Created: 2026-01-02 (Week 4 Day 3)
"""

from .credit_assignment import CreditAssignment, OperatorCredit
from .operator_selector import AdaptiveOperatorSelector, SelectionStrategy
from .parameter_tuner import AdaptiveParameterTuner, ParameterSchedule

__all__ = [
    # Credit Assignment
    "CreditAssignment",
    "OperatorCredit",
    # Operator Selection
    "AdaptiveOperatorSelector",
    "SelectionStrategy",
    # Parameter Tuning
    "AdaptiveParameterTuner",
    "ParameterSchedule",
]
