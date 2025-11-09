"""
Campus Data Parser
==================

Parser for loading campus data from various formats.

Classes:
    CampusDataParser: Parse campus data from GeoJSON, Shapefile, or dict

Created: 2025-11-09
"""

import json
from pathlib import Path
from typing import Any, Dict

import geopandas as gpd
from shapely.geometry import Polygon

from .campus_data import CampusData


class CampusDataParser:
    """
    Parser for campus data from various formats.

    Supports:
    - GeoJSON files
    - Shapefiles
    - Dictionary objects

    Example:
        >>> parser = CampusDataParser()
        >>> campus = parser.from_geojson('data/campuses/bogazici_university.json')
        >>> print(campus.name)
        'Boğaziçi University'
    """

    @staticmethod
    def from_geojson(filepath: str) -> CampusData:
        """
        Parse GeoJSON file to CampusData.

        Args:
            filepath: Path to GeoJSON file

        Returns:
            CampusData instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or missing required fields

        Example:
            >>> campus = CampusDataParser.from_geojson('data/campuses/bogazici.json')
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Read JSON file
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse using from_dict
        return CampusDataParser.from_dict(data)

    @staticmethod
    def from_shapefile(filepath: str) -> CampusData:
        """
        Parse Shapefile to CampusData.

        Note: Shapefile should contain polygon features with attributes.

        Args:
            filepath: Path to Shapefile (.shp) or directory containing .shp file

        Returns:
            CampusData instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or missing required fields

        Example:
            >>> campus = CampusDataParser.from_shapefile('data/campuses/campus.shp')
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Read shapefile using geopandas
        try:
            gdf = gpd.read_file(filepath)
        except Exception as e:
            raise ValueError(f"Failed to read shapefile: {e}") from e

        if len(gdf) == 0:
            raise ValueError("Shapefile contains no features")

        # Get first feature (assuming single campus per file)
        feature = gdf.iloc[0]
        geometry = feature.geometry

        if not isinstance(geometry, Polygon):
            raise ValueError(f"Expected Polygon geometry, got {type(geometry)}")

        # Extract attributes
        name = feature.get("name", "Unknown Campus")
        location = feature.get("location", "Unknown Location")

        # Extract constraints from attributes
        constraints = {
            "setback_from_boundary": feature.get("setback", 10.0),
            "coverage_ratio_max": feature.get("coverage_max", 0.3),
            "far_max": feature.get("far_max", 2.0),
            "min_green_space_ratio": feature.get("green_min", 0.4),
        }

        # Extract metadata
        metadata = {
            "total_area_m2": feature.get("area_m2", geometry.area),
            "student_count": feature.get("students", 0),
            "established": feature.get("established", 0),
        }

        # Note: Shapefile doesn't contain existing buildings in this implementation
        # They would need to be in a separate layer or file
        buildings = []

        return CampusData(
            name=str(name),
            location=str(location),
            boundary=geometry,
            buildings=buildings,
            constraints=constraints,
            metadata=metadata,
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> CampusData:
        """
        Parse dictionary to CampusData.

        Args:
            data: Dictionary representation of campus data

        Returns:
            CampusData instance

        Raises:
            ValueError: If data is invalid or missing required fields

        Example:
            >>> data = {
            ...     "name": "Test Campus",
            ...     "location": "Istanbul, Turkey",
            ...     "boundary": {
            ...         "type": "Polygon",
            ...         "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]]
            ...     },
            ... }
            >>> campus = CampusDataParser.from_dict(data)
        """
        # Validate required fields
        if "name" not in data:
            raise ValueError("Missing required field: 'name'")
        if "location" not in data:
            raise ValueError("Missing required field: 'location'")
        if "boundary" not in data:
            raise ValueError("Missing required field: 'boundary'")

        # Use CampusData.from_dict for parsing
        return CampusData.from_dict(data)

    @staticmethod
    def validate_data(data: CampusData) -> bool:
        """
        Validate campus data integrity.

        Checks:
        - Boundary is valid polygon
        - Buildings are within boundary
        - Constraints are valid
        - Metadata is present

        Args:
            data: CampusData instance to validate

        Returns:
            True if valid, raises ValueError if invalid

        Raises:
            ValueError: If data is invalid

        Example:
            >>> campus = CampusDataParser.from_geojson('data/campuses/bogazici.json')
            >>> CampusDataParser.validate_data(campus)
            True
        """
        # Validate boundary
        if not data.boundary.is_valid:
            raise ValueError("Boundary polygon is not valid")

        if not data.boundary.is_simple:
            raise ValueError("Boundary polygon is not simple (self-intersecting)")

        # Validate buildings are within boundary
        for building in data.buildings:
            if building.position:
                from shapely.geometry import Point

                point = Point(building.position[0], building.position[1])
                if not data.boundary.contains(point):
                    raise ValueError(f"Building {building.id} is outside campus boundary")

        # Validate constraints
        if "setback_from_boundary" in data.constraints:
            setback = data.constraints["setback_from_boundary"]
            if setback < 0:
                raise ValueError("setback_from_boundary must be >= 0")

        if "coverage_ratio_max" in data.constraints:
            coverage = data.constraints["coverage_ratio_max"]
            if not 0 < coverage <= 1.0:
                raise ValueError("coverage_ratio_max must be between 0 and 1")

        if "far_max" in data.constraints:
            far = data.constraints["far_max"]
            if far <= 0:
                raise ValueError("far_max must be > 0")

        if "min_green_space_ratio" in data.constraints:
            green = data.constraints["min_green_space_ratio"]
            if not 0 <= green <= 1.0:
                raise ValueError("min_green_space_ratio must be between 0 and 1")

        return True
