"""
Campus Detection and Management API

Kampüs tespit, analiz ve yönetim endpoint'leri.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from pydantic import BaseModel
import logging

from backend.core.domain.geometry.geocoding_service import UniversityCampusLocator
from backend.core.domain.geometry.osm_service import fetch_campus_context
from backend.core.domain.models.campus import CampusContext, Gateway
from backend.core.domain.geometry.relocation_service import CampusRelocator, relocate_campus_to_coordinates
from shapely.geometry import Point, shape

router = APIRouter(prefix="/api/campus", tags=["campus"])
logger = logging.getLogger(__name__)


class RelocationRequest(BaseModel):
    """Request model for campus relocation."""
    campus_geojson: dict
    target_lat: float = 0.0
    target_lon: float = 0.0
    preserve_topology: bool = True
    clear_existing_buildings: bool = True


@router.get("/detect")
async def detect_campus(
    university_name: str = Query(..., description="Üniversite adı (örn: Kastamonu Üniversitesi)"),
    country: str = Query("Turkey", description="Ülke"),
    auto_radius: bool = Query(True, description="Otomatik radius tespiti")
):
    """
    Üniversite kampüsünü otomatik tespit eder.

    Workflow:
    1. University name → Geocode → Coordinates
    2. Coordinates → OSM Query → Campus boundary
    3. Boundary → Extract gateways, buildings, roads

    Example:
        GET /api/campus/detect?university_name=Kastamonu Üniversitesi

    Returns:
        {
            "status": "success",
            "university": {
                "name": "Kastamonu Üniversitesi",
                "location": {"lat": 41.424274, "lon": 33.777434}
            },
            "campus": {
                "boundary": {...},  # GeoJSON
                "gateways": [...],
                "area_m2": 1542289,
                "center": {"lat": ..., "lon": ...}
            },
            "summary": {
                "existing_buildings": 2,
                "gateways": 3,
                "roads": 24
            }
        }
    """
    try:
        # 1. Find university coordinates
        locator = UniversityCampusLocator()
        coords = locator.find_university(university_name, country)

        if not coords:
            raise HTTPException(
                status_code=404,
                detail=f"University not found: {university_name}"
            )

        lat, lon = coords
        logger.info(f"Found university at: lat={lat}, lon={lon}")

        # 2. Determine optimal radius
        if auto_radius:
            radius = locator.auto_detect_optimal_radius(lat, lon)
        else:
            radius = 1500  # default 1.5km

        logger.info(f"Using radius: {radius}m")

        # 3. Fetch campus context from OSM
        context = fetch_campus_context(
            lat=lat,
            lon=lon,
            radius=radius
        )

        # 4. Convert to CampusContext model
        # (osm_service already returns CampusContext-like data)

        # 5. Prepare response
        university_info = locator.get_university_info(university_name)

        # Sanitize function for NaN/Inf values
        import math
        import json

        def sanitize_value(value):
            """Replace NaN/Inf with None for JSON compliance."""
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    return None
                return value
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                return [sanitize_value(item) for item in value]
            return value

        # Get GeoJSON and sanitize
        try:
            campus_geojson = context.to_geojson_wgs84()
            campus_geojson = sanitize_value(campus_geojson)
        except Exception as e:
            logger.error(f"Error converting to GeoJSON: {e}", exc_info=True)
            # Fallback to minimal response
            campus_geojson = {
                "type": "FeatureCollection",
                "features": []
            }

        response = {
            "status": "success",
            "university": {
                "name": university_info.get('name', university_name) if university_info else university_name,
                "location": {
                    "lat": lat,
                    "lon": lon
                },
                "city": university_info.get('city') if university_info else None
            },
            "campus": {
                "boundary": campus_geojson,  # Sanitized GeoJSON
                "area_m2": sanitize_value(context.buildable_area.area if hasattr(context, 'buildable_area') else None),
                "center": {
                    "lat": sanitize_value(context.center_latlon[0] if hasattr(context, 'center_latlon') else lat),
                    "lon": sanitize_value(context.center_latlon[1] if hasattr(context, 'center_latlon') else lon)
                }
            },
            "summary": {
                "existing_buildings": len(context.existing_buildings) if hasattr(context, 'existing_buildings') else 0,
                "existing_roads": len(context.existing_roads) if hasattr(context, 'existing_roads') else 0,
                "total_building_area_m2": sanitize_value(context.total_existing_building_area if hasattr(context, 'total_existing_building_area') else 0),
                "buildable_area_m2": sanitize_value(context.buildable_area.area if hasattr(context, 'buildable_area') else 0),
                "bounds_meters": sanitize_value(context.bounds_meters if hasattr(context, 'bounds_meters') else None)
            },
            "metadata": {
                "radius_used": radius,
                "auto_radius": auto_radius,
                "data_source": "OpenStreetMap"
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting campus: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect campus: {str(e)}"
        )


@router.get("/list")
async def list_known_universities():
    """
    Bilinen üniversiteleri listeler.

    Returns:
        {
            "status": "success",
            "universities": [
                {"name": "Kastamonu Üniversitesi", "city": "Kastamonu"},
                ...
            ],
            "total": 7
        }
    """
    locator = UniversityCampusLocator()
    universities = []

    for key, info in locator.KNOWN_UNIVERSITIES.items():
        # Duplicate'leri engelle
        if not any(u['name'] == info['name'] for u in universities):
            universities.append({
                "name": info['name'],
                "city": info['city'],
                "country": info['country']
            })

    return {
        "status": "success",
        "universities": universities,
        "total": len(universities)
    }


@router.post("/relocate")
async def relocate_campus(request: RelocationRequest):
    """
    Kampüsü yeni koordinatlara taşır.

    Workflow:
    1. Parse GeoJSON → CampusContext
    2. Convert to local coordinates (WGS84 → metric)
    3. Relocate to target center using CampusRelocator
    4. Verify gateway topology preservation
    5. Return relocated campus as GeoJSON

    Args:
        campus_geojson: Orijinal kampüs GeoJSON (from /detect endpoint)
        target_lat: Hedef latitude (default: 0.0 for empty space)
        target_lon: Hedef longitude (default: 0.0 for empty space)
        preserve_topology: Gateway topology'sini doğrula (default: True)
        clear_existing_buildings: Mevcut binaları temizle (default: True for empty space)

    Returns:
        {
            "status": "success",
            "relocated_campus": {...},  # GeoJSON
            "topology_preserved": true,
            "distance_error": 0.0,
            "translation_vector": {"dx": 100, "dy": 200},
            "metadata": {...}
        }

    Example:
        POST /api/campus/relocate
        {
            "campus_geojson": {...},
            "target_lat": 0.0,
            "target_lon": 0.0
        }
    """
    try:
        # 1. Parse GeoJSON to CampusContext
        # Expected format: output from /detect endpoint
        from shapely.geometry import shape as geojson_to_shape

        # Extract features by layer
        features = request.campus_geojson.get('features', [])
        print(f"DEBUG: Received {len(features)} features in GeoJSON")

        boundary = None
        gateways = []
        existing_buildings = []
        roads = []
        green_areas = []

        for feature in features:
            props = feature.get('properties', {})
            layer = props.get('layer', '')
            print(f"DEBUG: Processing feature with layer: '{layer}'")

            try:
                geom = geojson_to_shape(feature['geometry'])
            except Exception as e:
                logger.warning(f"Failed to parse geometry for layer {layer}: {e}")
                continue

            if layer == 'boundary':
                boundary = geom
                print(f"DEBUG: Found boundary: {type(boundary)}, area={boundary.area if hasattr(boundary, 'area') else 'N/A'}")
            elif layer == 'gateway':
                gateways.append(Gateway(
                    id=props['id'],
                    location=geom,
                    bearing=props['bearing'],
                    type=props.get('type', 'main'),
                    name=props.get('name')
                ))
            elif layer == 'existing_building':
                from backend.core.domain.models.campus import ExistingBuilding
                existing_buildings.append(ExistingBuilding(
                    id=props['id'],
                    geometry=geom,
                    building_type=props.get('building_type', 'Unknown'),
                    height=props.get('height', 15.0),
                    name=props.get('name'),
                    floors=props.get('floors')
                ))
            elif layer == 'existing_road':
                roads.append(geom)
            elif layer == 'green_area':
                green_areas.append(geom)

        if not boundary:
            raise HTTPException(
                status_code=400,
                detail="Campus GeoJSON must contain a boundary feature"
            )

        # Create CampusContext
        campus_wgs84 = CampusContext(
            boundary=boundary,
            gateways=gateways,
            existing_buildings=existing_buildings,
            roads=roads,
            green_areas=green_areas
        )

        logger.info(f"Parsed campus with {len(gateways)} gateways, {len(existing_buildings)} buildings")

        # 2. Use relocation service
        relocator = CampusRelocator(preserve_topology=request.preserve_topology)

        # Convert to local coordinates and relocate
        target_center = Point(request.target_lon, request.target_lat)  # Note: Point(x, y) = Point(lon, lat)

        # First convert WGS84 to local metric coordinates
        campus_local = campus_wgs84.to_local_coordinates(target_center=Point(0, 0))

        # Then relocate to final target
        result = relocator.relocate_to_empty_space(
            campus=campus_local,
            target_center=target_center,
            clear_existing_buildings=request.clear_existing_buildings
        )

        logger.info(f"Relocation complete: topology_preserved={result.topology_preserved}, error={result.distance_error:.2%}")

        # 3. Convert back to GeoJSON
        relocated_geojson = result.relocated_campus.to_geojson()

        # 4. Prepare response
        import math
        # Handle NaN/Inf values for JSON serialization
        distance_error = float(result.distance_error)
        if not math.isfinite(distance_error):
            distance_error = 0.0

        response = {
            "status": "success",
            "relocated_campus": relocated_geojson,
            "topology_preserved": bool(result.topology_preserved),
            "distance_error": distance_error,
            "translation_vector": {
                "dx": float(result.translation_vector[0]),
                "dy": float(result.translation_vector[1])
            },
            "metadata": {
                "original_gateways": len(campus_wgs84.gateways),
                "relocated_gateways": len(result.relocated_campus.gateways),
                "original_buildings": len(campus_wgs84.existing_buildings),
                "relocated_buildings": len(result.relocated_campus.existing_buildings),
                "buildings_cleared": request.clear_existing_buildings,
                "target_center": {
                    "lat": request.target_lat,
                    "lon": request.target_lon
                }
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error relocating campus: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to relocate campus: {str(e)}"
        )


@router.get("/health")
async def campus_health():
    """Campus router health check."""
    return {
        "status": "healthy",
        "router": "campus",
        "features": {
            "detect": "operational",
            "list": "operational",
            "relocate": "operational"
        }
    }
