"""
Context module for real-world campus data.
"""

from backend.core.domain.geometry.osm_service import (
    CampusContext,
    ExistingBuilding,
    ExistingRoad,
    OSMContextFetcher,
    fetch_campus_context
)

__all__ = [
    'CampusContext',
    'ExistingBuilding',
    'ExistingRoad',
    'OSMContextFetcher',
    'fetch_campus_context'
]
