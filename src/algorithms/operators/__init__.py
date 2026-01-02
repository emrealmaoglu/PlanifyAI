"""
Modular Optimization Operators
===============================

Plugin-based operator system for metaheuristic algorithms.

Created: 2026-01-02 (Week 4 Day 3)
"""

from .base import (
    CrossoverOperator,
    MutationOperator,
    OperatorRegistry,
    PerturbationOperator,
    SelectionOperator,
)
from .crossover import PartiallyMatchedCrossover, UniformCrossover
from .mutation import GaussianMutation, RandomResetMutation, SwapMutation
from .perturbation import GaussianPerturbation, RandomResetPerturbation, SwapPerturbation
from .registry import DEFAULT_REGISTRY, create_default_registry
from .selection import RouletteWheelSelection, TournamentSelection

__all__ = [
    # Base classes
    "CrossoverOperator",
    "MutationOperator",
    "PerturbationOperator",
    "SelectionOperator",
    "OperatorRegistry",
    # Crossover
    "UniformCrossover",
    "PartiallyMatchedCrossover",
    # Mutation
    "GaussianMutation",
    "SwapMutation",
    "RandomResetMutation",
    # Perturbation
    "GaussianPerturbation",
    "SwapPerturbation",
    "RandomResetPerturbation",
    # Selection
    "TournamentSelection",
    "RouletteWheelSelection",
    # Registry
    "DEFAULT_REGISTRY",
    "create_default_registry",
]
