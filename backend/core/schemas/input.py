from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List

class OptimizationGoal(str, Enum):
    """
    Spatial Optimization Objectives.
    Derived from 'Multi-Objective Spatial Planning Research'.
    """
    COMPACTNESS = "COMPACTNESS"
    SOLAR_GAIN = "SOLAR_GAIN"
    WIND_COMFORT = "WIND_COMFORT"
    ADJACENCY = "ADJACENCY"

class SiteParameters(BaseModel):
    """
    Physical constraints derived from Turkish Zoning Laws (Planlı Alanlar İmar Yönetmeliği).
    """
    setback_front: float = Field(default=5.0, description="Front yard setback (meters)")
    setback_side: float = Field(default=3.0, description="Side yard setback (meters)")
    setback_rear: float = Field(default=3.0, description="Rear yard setback (meters)")

class OptimizationRequest(BaseModel):
    """
    The Contract: Defines all inputs required for a simulation run.
    Refined for Phase 5: Pure Spatial Optimization.
    """
    
    # 1. Project Info
    project_name: str = Field(default="Untitled Project", description="Name of the scenario")
    description: Optional[str] = Field(default=None, description="User notes")
    
    # 2. Geo Context (Where are we?)
    latitude: float = Field(..., description="Center latitude")
    longitude: float = Field(..., description="Center longitude")
    radius: float = Field(default=500.0, description="Analysis radius in meters")
    
    # 3. Design Constraints (What do we want?)
    building_counts: Dict[str, int] = Field(
        default_factory=dict, 
        description="Map of BuildingType ID to Count (e.g., {'Rectory': 1})"
    )
    
    # GeoJSON FeatureCollection for Red/Blue zones
    constraints: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="GeoJSON containing Exclusion (Red) and Preservation (Blue) zones"
    )

    # Custom Boundary (User Drawn)
    boundary_geojson: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User-drawn boundary polygon to override automatic detection"
    )
    
    # Clear All Existing (Greenfield Mode)
    clear_all_existing: bool = Field(
        default=False,
        description="If True, ignore all existing buildings and roads (Greenfield)"
    )

    # Kept Buildings (Exceptions to Clear All)
    kept_building_ids: List[str] = Field(
        default_factory=list,
        description="List of OSM IDs to preserve even if clear_all_existing is True"
    )
    
    # 4. Site Configuration (Zoning Rules)
    site_parameters: SiteParameters = Field(
        default_factory=SiteParameters,
        description="Legal setbacks and zoning constraints"
    )
    
    # 5. Optimization Goals (Weights 0.0 - 1.0)
    optimization_goals: Dict[OptimizationGoal, float] = Field(
        default={
            OptimizationGoal.COMPACTNESS: 0.5,
            OptimizationGoal.SOLAR_GAIN: 0.0,
            OptimizationGoal.WIND_COMFORT: 0.0,
            OptimizationGoal.ADJACENCY: 0.5
        },
        description="Weights for multi-objective optimization"
    )
    
    # 6. Analysis Flags (Physical Only)
    enable_solar: bool = Field(default=False, description="Calculate PV potential")
    enable_wind: bool = Field(default=False, description="Analyze wind corridors")
    enable_walkability: bool = Field(default=False, description="Generate walkability heatmap")
    
    class Config:
        extra = "forbid"
        schema_extra = {
            "example": {
                "project_name": "Kastamonu Spatial Plan",
                "latitude": 41.3833,
                "longitude": 33.7833,
                "building_counts": {"Rectory": 1, "Faculty": 2},
                "site_parameters": {
                    "setback_front": 5.0,
                    "setback_side": 3.0
                },
                "optimization_goals": {
                    "COMPACTNESS": 0.8,
                    "SOLAR_GAIN": 0.5
                }
            }
        }
