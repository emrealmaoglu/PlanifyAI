"""
Integration module for co-optimizing roads and buildings.

This module bridges the spatial (tensor fields) and optimization
(H-SAGA) subsystems into a unified generative planning framework.
"""

from .composite_genotype import CompositeGenotype, TensorFieldParams, BuildingLayout
from .problem import IntegratedCampusProblem
from .visualization import visualize_integrated_layout
from .optimizer import AdvancedOptimizer
from .adaptive_field import AdaptiveTensorFieldGenerator

__all__ = [
    'CompositeGenotype',
    'TensorFieldParams',
    'BuildingLayout',
    'IntegratedCampusProblem',
    'visualize_integrated_layout',
    'AdvancedOptimizer',
    'AdaptiveTensorFieldGenerator'
]
