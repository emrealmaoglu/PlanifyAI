from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class BuildingResponse(BaseModel):
    """Single building in optimization result."""
    id: int
    building_type: str          # "academic", "dormitory", "social", "admin"
    shape_type: str             # "h_shape", "u_shape", "l_shape", "rectangular"
    floors: int
    height: float               # meters (floors * 3.5)
    area: float                 # m² (polygon area)
    centroid: Dict[str, float]  # {"x": ..., "y": ...}
    orientation: float          # radians
    # GeoJSON Polygon coordinates for frontend
    geometry: Dict[str, Any]    # {"type": "Polygon", "coordinates": [...]}


class RoadResponse(BaseModel):
    """Single road segment."""
    id: int
    width: float
    # GeoJSON LineString
    geometry: Dict[str, Any]    # {"type": "LineString", "coordinates": [...]}


class DrivewayResponse(BaseModel):
    """Building-to-road connection."""
    building_id: int
    geometry: Dict[str, Any]    # {"type": "LineString", "coordinates": [...]}


class SolutionResponse(BaseModel):
    """Complete optimization solution."""
    solution_id: str
    buildings: List[BuildingResponse]
    roads: List[RoadResponse]
    driveways: List[DrivewayResponse]
    objectives: Dict[str, float]
    constraints: Dict[str, float]
    rank: int
    crowding_distance: float
