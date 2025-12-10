from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.core.domain.geometry.osm_service import fetch_campus_context

router = APIRouter(prefix="/api/context", tags=["context"])


import math

def sanitize_for_json(obj):
    """Recursively replace NaN/Infinity with None for JSON serialization."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    return obj

@router.get("/fetch")
async def fetch_context(
    location: Optional[str] = Query(None, description="Place name"),
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    radius: float = Query(500, description="Radius in meters"),
    north: Optional[float] = Query(None),
    south: Optional[float] = Query(None),
    east: Optional[float] = Query(None),
    west: Optional[float] = Query(None)
):
    """
    Fetch real-world campus context from OpenStreetMap.
    
    Returns GeoJSON with existing buildings, roads, and buildable area.
    """
    try:
        bbox = None
        if all([north, south, east, west]):
            bbox = (north, south, east, west)
        
        context = fetch_campus_context(
            location=location,
            lat=lat,
            lon=lon,
            radius=radius,
            bbox=bbox
        )
        
        response_data = {
            "status": "success",
            "data": context.to_geojson_wgs84(),
            "summary": {
                "existing_buildings": len(context.existing_buildings),
                "existing_roads": len(context.existing_roads),
                "total_building_area_m2": context.total_existing_building_area,
                "buildable_area_m2": context.buildable_area.area,
                "center_latlon": context.center_latlon,
                "bounds_meters": context.bounds_meters
            }
        }
        
        return sanitize_for_json(response_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch context: {e}")
