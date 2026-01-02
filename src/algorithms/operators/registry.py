"""
Default Operator Registry
==========================

Pre-configured operator registry with all standard operators.

Created: 2026-01-02 (Week 4 Day 3)
"""

from .base import OperatorRegistry
from .crossover import PartiallyMatchedCrossover, UniformCrossover
from .mutation import GaussianMutation, RandomResetMutation, SwapMutation
from .perturbation import GaussianPerturbation, RandomResetPerturbation, SwapPerturbation
from .selection import RouletteWheelSelection, TournamentSelection


def create_default_registry() -> OperatorRegistry:
    """
    Create default operator registry with all standard operators.

    Returns:
        OperatorRegistry with all operators registered

    Example:
        >>> registry = create_default_registry()
        >>> mutation = registry.get_mutation("gaussian", sigma=30.0)
        >>> crossover = registry.get_crossover("uniform")
    """
    registry = OperatorRegistry()

    # Register perturbation operators (SA)
    registry.register_perturbation("gaussian", GaussianPerturbation)
    registry.register_perturbation("swap", SwapPerturbation)
    registry.register_perturbation("reset", RandomResetPerturbation)

    # Register mutation operators (GA)
    registry.register_mutation("gaussian", GaussianMutation)
    registry.register_mutation("swap", SwapMutation)
    registry.register_mutation("reset", RandomResetMutation)

    # Register crossover operators (GA)
    registry.register_crossover("uniform", UniformCrossover)
    registry.register_crossover("pmx", PartiallyMatchedCrossover)

    # Register selection operators (GA)
    registry.register_selection("tournament", TournamentSelection)
    registry.register_selection("roulette", RouletteWheelSelection)

    return registry


# Global default registry instance
DEFAULT_REGISTRY = create_default_registry()
