"""
Gateway Parser Utility

Parses gateway data from campus GeoJSON (from /api/campus/relocate endpoint).
"""

from typing import List, Dict, Any, Optional
import logging

from shapely.geometry import shape, Point

from backend.core.domain.models.campus import Gateway

logger = logging.getLogger(__name__)


def parse_gateways_from_geojson(campus_geojson: Optional[Dict[str, Any]]) -> List[Gateway]:
    """
    Extract gateways from campus GeoJSON.

    This function parses the GeoJSON output from /api/campus/relocate endpoint
    and extracts all gateway features.

    Args:
        campus_geojson: GeoJSON FeatureCollection containing gateway features

    Returns:
        List of Gateway objects

    Example:
        >>> campus_geojson = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "geometry": {"type": "Point", "coordinates": [33.78, 41.38]},
        ...             "properties": {
        ...                 "layer": "gateway",
        ...                 "id": "gateway_1",
        ...                 "bearing": -1.91,
        ...                 "type": "main",
        ...                 "name": "Main Entrance"
        ...             }
        ...         }
        ...     ]
        ... }
        >>> gateways = parse_gateways_from_geojson(campus_geojson)
        >>> len(gateways)
        1
        >>> gateways[0].id
        'gateway_1'
    """
    gateways = []

    if not campus_geojson:
        return gateways

    features = campus_geojson.get('features', [])

    for feature in features:
        props = feature.get('properties', {})
        layer = props.get('layer', '')

        if layer == 'gateway':
            try:
                geom = shape(feature['geometry'])

                # Ensure it's a Point
                if geom.geom_type != 'Point':
                    logger.warning(f"Gateway geometry is not a Point: {geom.geom_type}")
                    continue

                gateway = Gateway(
                    id=props.get('id', f'gateway_{len(gateways)}'),
                    location=geom,
                    bearing=float(props.get('bearing', 0.0)),
                    type=props.get('type', 'main'),
                    name=props.get('name')
                )
                gateways.append(gateway)

            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse gateway feature: {e}")
                continue

    logger.info(f"Parsed {len(gateways)} gateways from GeoJSON")
    return gateways


def parse_boundary_from_geojson(campus_geojson: Optional[Dict[str, Any]]):
    """
    Extract campus boundary from campus GeoJSON.

    Args:
        campus_geojson: GeoJSON FeatureCollection containing boundary feature

    Returns:
        Shapely Polygon representing campus boundary, or None if not found
    """
    if not campus_geojson:
        return None

    features = campus_geojson.get('features', [])

    for feature in features:
        props = feature.get('properties', {})
        layer = props.get('layer', '')

        if layer == 'boundary':
            try:
                geom = shape(feature['geometry'])
                if geom.geom_type == 'Polygon':
                    return geom
            except Exception as e:
                logger.warning(f"Failed to parse boundary: {e}")
                continue

    return None
