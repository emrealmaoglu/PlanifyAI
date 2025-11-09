"""
Campus Data Structure
=====================

Data structures for representing campus geospatial data.

Created: 2025-11-08
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from shapely.geometry import Point, Polygon

from src.algorithms.building import Building


@dataclass
class CampusData:
    """
    Campus geospatial data container.

    Represents a campus with boundary, existing buildings, constraints, and metadata.

    Attributes:
        name: Campus name (e.g., "Boğaziçi University")
        location: Location string (e.g., "Istanbul, Turkey")
        boundary: Campus boundary polygon (shapely.Polygon)
        buildings: List of existing buildings
        constraints: Spatial constraints dictionary
        metadata: Additional metadata dictionary

    Example:
        >>> from shapely.geometry import Polygon
        >>> boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        >>> campus = CampusData(
        ...     name="Test Campus",
        ...     location="Istanbul, Turkey",
        ...     boundary=boundary,
        ...     buildings=[],
        ...     constraints={"setback": 10.0},
        ...     metadata={"area": 1000000}
        ... )
        >>> bounds = campus.get_bounds()
        >>> print(bounds)
        (0.0, 0.0, 1000.0, 1000.0)
    """

    name: str
    location: str
    boundary: Polygon
    buildings: List[Building] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate campus data."""
        if not isinstance(self.boundary, Polygon):
            raise ValueError(f"boundary must be a shapely.Polygon, got {type(self.boundary)}")

        if not self.boundary.is_valid:
            raise ValueError("boundary polygon is not valid")

        if not isinstance(self.buildings, list):
            raise ValueError(f"buildings must be a list, got {type(self.buildings)}")

        # Validate all buildings have positions
        for building in self.buildings:
            if building.position is None:
                raise ValueError(f"Building {building.id} must have a position set")

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Return bounding box of campus boundary.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) in meters
        """
        bounds = self.boundary.bounds
        return (bounds[0], bounds[1], bounds[2], bounds[3])

    def is_valid_position(self, point: Point) -> bool:
        """
        Check if position is within campus boundary.

        Args:
            point: Point to check (shapely.Point or (x, y) tuple)

        Returns:
            True if point is within boundary, False otherwise
        """
        if isinstance(point, (tuple, list)):
            point = Point(point[0], point[1])
        elif not isinstance(point, Point):
            raise ValueError(f"point must be Point or (x, y) tuple, got {type(point)}")

        return self.boundary.contains(point) or self.boundary.touches(point)

    def get_total_area(self) -> float:
        """
        Get total campus area in square meters.

        Returns:
            Area in square meters
        """
        return self.boundary.area

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize campus data to dictionary.

        Returns:
            Dictionary representation of campus data
        """
        # Convert boundary to GeoJSON format
        boundary_coords = list(self.boundary.exterior.coords)

        # Convert buildings to dictionaries
        buildings_data = []
        for building in self.buildings:
            buildings_data.append(
                {
                    "id": building.id,
                    "type": building.type.value,
                    "position": list(building.position) if building.position else None,
                    "area": building.area,
                    "floors": building.floors,
                }
            )

        return {
            "name": self.name,
            "location": self.location,
            "boundary": {
                "type": "Polygon",
                "coordinates": [boundary_coords],
            },
            "existing_buildings": buildings_data,
            "constraints": self.constraints,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampusData":
        """
        Deserialize campus data from dictionary.

        Args:
            data: Dictionary containing campus data

        Returns:
            CampusData instance

        Raises:
            ValueError: If data is invalid
        """
        # Parse boundary
        if "boundary" in data:
            boundary_data = data["boundary"]
            if isinstance(boundary_data, dict):
                # GeoJSON format
                coords = boundary_data["coordinates"][0]
                boundary = Polygon(coords)
            else:
                # Assume it's already a Polygon
                boundary = boundary_data
        else:
            raise ValueError("boundary is required in campus data")

        # Parse buildings
        buildings = []
        if "existing_buildings" in data:
            from src.algorithms.building import BuildingType

            for bdata in data["existing_buildings"]:
                building = Building(
                    id=bdata["id"],
                    type=BuildingType(bdata["type"]),
                    area=bdata["area"],
                    floors=bdata["floors"],
                    position=tuple(bdata["position"]) if bdata.get("position") else None,
                )
                buildings.append(building)

        return cls(
            name=data.get("name", "Unknown Campus"),
            location=data.get("location", "Unknown Location"),
            boundary=boundary,
            buildings=buildings,
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CampusData(name='{self.name}', location='{self.location}', "
            f"buildings={len(self.buildings)}, area={self.get_total_area():.0f}m²)"
        )
