"""
Campus Optimization Package (Phase 6+).

This package contains the core optimization logic for the PlanifyAI system,
including the spatial problem definition, H-SAGA runner, and physics objectives.

Note: Legacy files (problem.py, objectives.py, constraints.py, hsaga.py)
were deleted in Phase 10 cleanup - replaced by spatial_problem.py and hsaga_runner.py.
"""

from backend.core.optimization.spatial_problem import (
    SpatialOptimizationProblem,
    ConstraintCalculator,
    ObjectiveCalculator
)

from backend.core.optimization.hsaga_runner import (
    HSAGARunner,
    HSAGARunnerConfig,
    run_hsaga
)

from backend.core.optimization.encoding import (
    BuildingGene,
    SmartInitializer,
    decode_all_to_polygons,
    array_to_genome
)

__all__ = [
    # Problem
    "SpatialOptimizationProblem",
    "ConstraintCalculator",
    "ObjectiveCalculator",
    # Runner
    "HSAGARunner",
    "HSAGARunnerConfig",
    "run_hsaga",
    # Encoding
    "BuildingGene",
    "SmartInitializer",
    "decode_all_to_polygons",
    "array_to_genome"
]
