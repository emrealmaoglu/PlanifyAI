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

from .building import Building, BuildingType, create_sample_campus
from .solution import Solution
from .base import Optimizer

__all__ = ["Building", "BuildingType", "Solution", "Optimizer", "create_sample_campus"]

__version__ = "0.1.0"
