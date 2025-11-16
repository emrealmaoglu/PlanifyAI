"""
Building Type Mapper

Maps H-SAGA Building types to Turkish Building Classifications
"""

from dataclasses import dataclass

from backend.core.turkish_standards import (
    TurkishBuildingClassifier,
    BuildingClass,
)

# H-SAGA Building Types (if using enum)
# If using strings, adjust accordingly
HSAGA_TO_TURKISH_TYPE_MAP = {
    # Residential types
    "RESIDENTIAL": "residential_low",
    "residential": "residential_low",
    "residential_low": "residential_low",
    "residential_mid": "residential_mid",
    "residential_high": "residential_high",
    # Commercial types
    "COMMERCIAL": "commercial_office",
    "commercial": "commercial_office",
    "commercial_retail": "commercial_retail",
    "commercial_mall": "commercial_mall",
    "commercial_office": "commercial_office",
    # Educational types
    "EDUCATIONAL": "educational_university",
    "educational": "educational_university",
    "educational_school": "educational_school",
    "educational_university": "educational_university",
    # Healthcare types
    "HEALTH": "health_clinic",
    "health": "health_clinic",
    "health_clinic": "health_clinic",
    "health_hospital": "health_hospital",
    # Social types
    "SOCIAL": "social_cultural",
    "social": "social_cultural",
    "social_sports": "social_sports",
    "social_cultural": "social_cultural",
    # Administrative
    "administrative": "administrative_office",
}


@dataclass
class BuildingWithTurkishClass:
    """
    Extended building information with Turkish classification.

    This wrapper adds Turkish building class information to
    any H-SAGA Building object.
    """

    building_id: str
    building_type: str
    area: float
    floors: int
    position: tuple
    turkish_type: str
    turkish_class: BuildingClass
    cost_per_sqm: float


class BuildingTypeMapper:
    """
    Maps H-SAGA building types to Turkish classifications.

    Usage:
        >>> mapper = BuildingTypeMapper()
        >>> turkish_info = mapper.map_to_turkish(building)
        >>> print(turkish_info.turkish_class)
        BuildingClass.CLASS_V_A
    """

    def __init__(self):
        self.classifier = TurkishBuildingClassifier()
        self.type_map = HSAGA_TO_TURKISH_TYPE_MAP

    def get_turkish_type(self, hsaga_type: str) -> str:
        """
        Convert H-SAGA building type to Turkish Standards type.

        Args:
            hsaga_type: H-SAGA building type string

        Returns:
            Turkish Standards type identifier

        Raises:
            ValueError: If type cannot be mapped
        """
        # Normalize type string
        hsaga_type_normalized = hsaga_type.lower().strip()

        if hsaga_type_normalized in self.type_map:
            return self.type_map[hsaga_type_normalized]

        # Try to find partial match
        for key, value in self.type_map.items():
            if hsaga_type_normalized in key or key in hsaga_type_normalized:
                return value

        raise ValueError(
            f"Cannot map H-SAGA type '{hsaga_type}' to Turkish type. "
            f"Valid types: {list(self.type_map.keys())}"
        )

    def map_to_turkish(
        self,
        building_id: str,
        building_type: str,
        area: float,
        floors: int,
        position: tuple = (0, 0),
    ) -> BuildingWithTurkishClass:
        """
        Map an H-SAGA building to Turkish classification.

        Args:
            building_id: Unique building identifier
            building_type: H-SAGA building type
            area: Building area in m²
            floors: Number of floors
            position: (x, y) position

        Returns:
            BuildingWithTurkishClass with complete Turkish info

        Examples:
            >>> mapper = BuildingTypeMapper()
            >>> building = mapper.map_to_turkish(
            ...     "B001",
            ...     "educational_university",
            ...     5000,
            ...     4
            ... )
            >>> print(building.turkish_class)
            BuildingClass.CLASS_V_A
            >>> print(building.cost_per_sqm)
            2000.0
        """
        # Get Turkish type
        turkish_type = self.get_turkish_type(building_type)

        # Classify
        turkish_class = self.classifier.classify(turkish_type, area, floors)

        # Get cost information
        class_info = self.classifier.get_class_info(turkish_class)

        return BuildingWithTurkishClass(
            building_id=building_id,
            building_type=building_type,
            area=area,
            floors=floors,
            position=position,
            turkish_type=turkish_type,
            turkish_class=turkish_class,
            cost_per_sqm=class_info.cost_per_sqm_tl,
        )

    def map_building_list(self, buildings: list) -> list[BuildingWithTurkishClass]:
        """
        Map a list of H-SAGA buildings to Turkish classifications.

        Args:
            buildings: List of H-SAGA Building objects or dicts

        Returns:
            List of BuildingWithTurkishClass objects
        """
        mapped = []

        for building in buildings:
            # Handle both object and dict formats
            if hasattr(building, "__dict__"):
                # Object format
                b_id = getattr(
                    building, "id", getattr(building, "building_id", "unknown")
                )
                b_type = getattr(
                    building,
                    "type",
                    getattr(building, "building_type", "residential"),
                )
                b_area = getattr(building, "area", 1000)
                b_floors = getattr(building, "floors", 1)
                b_pos = getattr(building, "position", (0, 0))
            else:
                # Dict format
                b_id = building.get("id", building.get("building_id", "unknown"))
                b_type = building.get(
                    "type", building.get("building_type", "residential")
                )
                b_area = building.get("area", 1000)
                b_floors = building.get("floors", 1)
                b_pos = building.get("position", (0, 0))

            mapped_building = self.map_to_turkish(
                building_id=b_id,
                building_type=b_type,
                area=b_area,
                floors=b_floors,
                position=b_pos,
            )
            mapped.append(mapped_building)

        return mapped
