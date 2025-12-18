"""
Data Module
===========

Geospatial data structures and parsers for campus planning.

Modules:
    campus_data: Campus data structures
    parser: Data parsers (GeoJSON, Shapefile, dict)
    export: Result export utilities
"""

from .campus_data import CampusData
from .export import ResultExporter
from .parser import CampusDataParser

__all__ = ["CampusData", "CampusDataParser", "ResultExporter"]
