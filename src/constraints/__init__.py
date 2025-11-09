"""
Spatial Constraints Module
==========================

Spatial constraint system for campus planning.

Modules:
    spatial_constraints: Constraint classes and manager
"""

from .spatial_constraints import (
    ConstraintManager,
    CoverageRatioConstraint,
    FloorAreaRatioConstraint,
    GreenSpaceConstraint,
    SetbackConstraint,
    SpatialConstraint,
)

__all__ = [
    "SpatialConstraint",
    "SetbackConstraint",
    "CoverageRatioConstraint",
    "FloorAreaRatioConstraint",
    "GreenSpaceConstraint",
    "ConstraintManager",
]
