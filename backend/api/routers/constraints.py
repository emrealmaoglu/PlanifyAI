from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.constraints.manual_constraints import (
    ManualConstraintManager, ManualConstraint, FixedBuilding,
    ConstraintType, create_exclusion_zone, create_fixed_building
)

router = APIRouter(prefix="/api/constraints", tags=["constraints"])

# In-memory storage (replace with database in production)
_constraint_managers: Dict[str, ManualConstraintManager] = {}


class ConstraintCreate(BaseModel):
    session_id: str
    constraint_type: str  # "exclusion", "preferred", "green_space", "parking", "utility"
    coordinates: List[List[float]]  # [[x1, y1], [x2, y2], ...]
    name: Optional[str] = None
    priority: int = 1
    properties: Dict[str, Any] = {}


class FixedBuildingCreate(BaseModel):
    session_id: str
    building_type: str
    x: float
    y: float
    width: float = 40
    depth: float = 30
    floors: int = 3
    orientation: float = 0
    name: Optional[str] = None


def get_manager(session_id: str) -> ManualConstraintManager:
    """Get or create constraint manager for session."""
    if session_id not in _constraint_managers:
        _constraint_managers[session_id] = ManualConstraintManager()
    return _constraint_managers[session_id]


@router.post("/add")
async def add_constraint(data: ConstraintCreate):
    """Add a new constraint zone."""
    try:
        manager = get_manager(data.session_id)
        
        coords = [(c[0], c[1]) for c in data.coordinates]
        constraint = create_exclusion_zone(
            coordinates=coords,
            zone_type=data.constraint_type,
            name=data.name
        )
        constraint.priority = data.priority
        constraint.properties.update(data.properties)
        
        manager.add_constraint(constraint)
        
        return {
            "status": "success",
            "constraint_id": constraint.id,
            "area": constraint.area
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/add-building")
async def add_fixed_building(data: FixedBuildingCreate):
    """Add a fixed building placement."""
    try:
        manager = get_manager(data.session_id)
        
        building = create_fixed_building(
            x=data.x,
            y=data.y,
            building_type=data.building_type,
            width=data.width,
            depth=data.depth,
            floors=data.floors,
            name=data.name
        )
        building.orientation = data.orientation
        
        manager.add_fixed_building(building)
        
        return {
            "status": "success",
            "building_id": building.id,
            "height": building.height
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/remove/{session_id}/{constraint_id}")
async def remove_constraint(session_id: str, constraint_id: str):
    """Remove a constraint by ID."""
    manager = get_manager(session_id)
    
    if manager.remove_constraint(constraint_id):
        return {"status": "success", "removed": constraint_id}
    elif manager.remove_fixed_building(constraint_id):
        return {"status": "success", "removed": constraint_id}
    else:
        raise HTTPException(status_code=404, detail="Constraint not found")


@router.get("/list/{session_id}")
async def list_constraints(session_id: str):
    """List all constraints for a session."""
    manager = get_manager(session_id)
    
    return {
        "constraints": [c.to_dict() for c in manager.constraints.values()],
        "fixed_buildings": [b.to_dict() for b in manager.fixed_buildings.values()],
        "exclusion_count": len(manager.exclusion_zones),
        "preferred_count": len(manager.preferred_zones)
    }


@router.get("/geojson/{session_id}")
async def get_geojson(session_id: str):
    """Get all constraints as GeoJSON for map display."""
    manager = get_manager(session_id)
    return manager.to_geojson()


@router.post("/import/{session_id}")
async def import_geojson(session_id: str, geojson: Dict[str, Any]):
    """Import constraints from GeoJSON."""
    try:
        manager = ManualConstraintManager.from_geojson(geojson)
        _constraint_managers[session_id] = manager
        
        return {
            "status": "success",
            "constraints_imported": len(manager.constraints),
            "fixed_buildings_imported": len(manager.fixed_buildings)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-violations/{session_id}")
async def check_violations(session_id: str, polygons: List[Dict[str, Any]]):
    """Check if building polygons violate any constraints."""
    from shapely.geometry import shape
    
    manager = get_manager(session_id)
    
    poly_list = [shape(p) for p in polygons]
    total_violation, details = manager.check_building_violations(poly_list)
    
    return {
        "total_violation_area": total_violation,
        "violation_count": len(details),
        "details": details,
        "all_valid": total_violation == 0
    }
