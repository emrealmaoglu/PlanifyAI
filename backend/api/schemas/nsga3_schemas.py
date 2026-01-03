"""
NSGA-III API Request/Response Schemas
======================================

Pydantic models for NSGA-III multi-objective optimization endpoints.

Created: 2026-01-03
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ObjectiveProfileType(str, Enum):
    """Predefined objective profile types."""

    STANDARD = "standard"
    RESEARCH_ENHANCED = "research_enhanced"
    FIFTEEN_MINUTE_CITY = "15_minute_city"
    CAMPUS_PLANNING = "campus_planning"
    CUSTOM = "custom"


class BuildingInput(BaseModel):
    """Building specification for optimization."""

    name: str = Field(..., description="Building name")
    building_type: str = Field(..., description="Building type (e.g., RESIDENTIAL, EDUCATIONAL)")
    area: float = Field(..., description="Floor area in square meters", gt=0)
    floors: int = Field(..., description="Number of floors", ge=1)

    class Config:
        schema_extra = {
            "example": {
                "name": "Library",
                "building_type": "EDUCATIONAL",
                "area": 2000,
                "floors": 3,
            }
        }


class CustomObjectiveProfile(BaseModel):
    """Custom objective profile configuration."""

    name: str = Field(..., description="Profile name")
    use_enhanced: bool = Field(..., description="Use research-based enhanced objectives")
    weights: Dict[str, float] = Field(..., description="Objective weights (must sum to 1.0)")
    walking_speed_kmh: float = Field(
        default=5.0, description="Walking speed in km/h", ge=0.5, le=10.0
    )
    description: str = Field(default="", description="Profile description")

    class Config:
        schema_extra = {
            "example": {
                "name": "Custom Balanced",
                "use_enhanced": True,
                "weights": {"cost": 0.25, "walking": 0.25, "adjacency": 0.25, "diversity": 0.25},
                "walking_speed_kmh": 4.5,
                "description": "Custom balanced profile",
            }
        }


class NSGA3Request(BaseModel):
    """Request schema for NSGA-III optimization."""

    # Buildings to optimize
    buildings: List[BuildingInput] = Field(..., description="Buildings to place", min_items=1)

    # Site boundaries (x_min, y_min, x_max, y_max)
    bounds: List[float] = Field(
        ..., description="Site boundaries [x_min, y_min, x_max, y_max]", min_items=4, max_items=4
    )

    # Population parameters
    population_size: int = Field(default=100, description="Population size", ge=10, le=500)
    n_generations: int = Field(default=100, description="Number of generations", ge=10, le=1000)

    # Reference points
    n_partitions: int = Field(
        default=12, description="Number of partitions for reference points", ge=3, le=20
    )
    use_two_layer: bool = Field(default=False, description="Use two-layer reference points")
    n_partitions_inner: Optional[int] = Field(
        default=None, description="Inner partitions for two-layer", ge=2, le=10
    )

    # Genetic operators
    crossover_rate: float = Field(default=0.9, description="Crossover probability", ge=0.0, le=1.0)
    mutation_rate: float = Field(default=0.15, description="Mutation probability", ge=0.0, le=1.0)

    # Objective profile
    objective_profile: Union[ObjectiveProfileType, CustomObjectiveProfile] = Field(
        default=ObjectiveProfileType.STANDARD,
        description="Objective profile (predefined type or custom profile)",
    )

    # Performance
    seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")
    verbose: bool = Field(default=False, description="Print progress messages")

    class Config:
        schema_extra = {
            "example": {
                "buildings": [
                    {"name": "Library", "building_type": "EDUCATIONAL", "area": 2000, "floors": 3},
                    {"name": "Dorm", "building_type": "RESIDENTIAL", "area": 3000, "floors": 5},
                    {"name": "Cafe", "building_type": "COMMERCIAL", "area": 1500, "floors": 2},
                ],
                "bounds": [0, 0, 500, 500],
                "population_size": 50,
                "n_generations": 50,
                "n_partitions": 12,
                "objective_profile": "research_enhanced",
                "seed": 42,
            }
        }


class SolutionResponse(BaseModel):
    """Single solution from Pareto front."""

    index: int = Field(..., description="Index in Pareto front")
    buildings: List[Dict[str, Any]] = Field(..., description="Building placements")
    objectives: List[float] = Field(..., description="Objective values")
    normalized_objectives: List[float] = Field(..., description="Normalized objective values")


class NSGA3Response(BaseModel):
    """Response schema for NSGA-III optimization."""

    success: bool = Field(..., description="Whether optimization succeeded")
    message: str = Field(..., description="Status message")

    # Results
    pareto_size: int = Field(..., description="Number of solutions in Pareto front")
    n_objectives: int = Field(..., description="Number of objectives")
    best_compromise: Optional[SolutionResponse] = Field(
        default=None, description="Best compromise solution"
    )

    # Statistics
    evaluations: int = Field(..., description="Total fitness evaluations")
    generations: int = Field(..., description="Number of generations")
    runtime: float = Field(..., description="Runtime in seconds")

    # Full Pareto front (optional, can be large)
    pareto_front: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="All solutions in Pareto front"
    )
    pareto_objectives: Optional[List[List[float]]] = Field(
        default=None, description="Objective values for all Pareto solutions"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Optimization complete",
                "pareto_size": 15,
                "n_objectives": 4,
                "evaluations": 5000,
                "generations": 50,
                "runtime": 12.5,
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""

    success: bool = Field(default=False, description="Always False for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
