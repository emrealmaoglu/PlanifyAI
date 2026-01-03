"""
Optimization Algorithms Module
==============================

Core classes for spatial planning optimization.

Classes:
    BuildingType: Building type enumeration
    Building: Building entity
    Solution: Spatial planning solution
    Optimizer: Base class for optimizers

Week 1: Core data structures implemented
"""

from .base import Optimizer
from .building import Building, BuildingType, create_sample_campus
from .fitness import FitnessEvaluator
from .hsaga import HybridSAGA
from .hsaga_adaptive import AdaptiveHSAGA
from .objective_profiles import (
    ObjectiveProfile,
    ProfileType,
    create_custom_profile,
    get_profile,
    list_available_profiles,
)
from .solution import Solution

__all__ = [
    "Building",
    "BuildingType",
    "Solution",
    "Optimizer",
    "create_sample_campus",
    "FitnessEvaluator",
    "HybridSAGA",
    "AdaptiveHSAGA",
    "ObjectiveProfile",
    "ProfileType",
    "get_profile",
    "create_custom_profile",
    "list_available_profiles",
]

__version__ = "0.1.0"
