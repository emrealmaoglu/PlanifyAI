"""
Turkish Building Classification System

Implements Yapı Sınıfları (Building Classes I-A to V-C)
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

from .data import BUILDING_CLASSES, BUILDING_TYPE_TO_CLASS


class BuildingClass(Enum):
    """Official Turkish building classification categories"""

    CLASS_I_A = "I-A"
    CLASS_II_B = "II-B"
    CLASS_III_A = "III-A"
    CLASS_III_B = "III-B"
    CLASS_IV_A = "IV-A"
    CLASS_IV_B = "IV-B"
    CLASS_V_A = "V-A"
    CLASS_V_B = "V-B"
    CLASS_V_C = "V-C"


@dataclass
class BuildingClassInfo:
    """Detailed information about a building class"""

    building_class: BuildingClass
    name_tr: str
    name_en: str
    description: str
    examples: list[str]
    cost_per_sqm_tl: float
    max_floors: int
    max_height_m: float


class TurkishBuildingClassifier:
    """
    Classifies buildings according to Turkish Yapı Sınıfları standards.

    Usage:
        >>> classifier = TurkishBuildingClassifier()
        >>> building_class = classifier.classify("residential_low", 2000, 3)
        >>> print(building_class)
        BuildingClass.CLASS_III_A

        >>> info = classifier.get_class_info(building_class)
        >>> print(info.cost_per_sqm_tl)
        1500
    """

    def __init__(self):
        """Initialize classifier with Turkish building standards data"""
        self._classes = BUILDING_CLASSES
        self._type_mappings = BUILDING_TYPE_TO_CLASS

    def classify(
        self,
        building_type: str,
        area: float,
        floors: int,
    ) -> BuildingClass:
        """
        Classify a building into Turkish building class.

        Args:
            building_type: Building type identifier
                (e.g., "residential_low", "educational_university")
            area: Total building area in m²
            floors: Number of floors

        Returns:
            BuildingClass enum value

        Raises:
            ValueError: If building_type is not recognized

        Examples:
            >>> classifier = TurkishBuildingClassifier()
            >>> classifier.classify("educational_university", 5000, 4)
            BuildingClass.CLASS_V_A
        """
        if building_type not in self._type_mappings:
            raise ValueError(
                f"Unknown building type: {building_type}. "
                f"Valid types: {list(self._type_mappings.keys())}"
            )

        class_code = self._type_mappings[building_type]
        return BuildingClass(class_code)

    def get_class_info(self, building_class: BuildingClass) -> BuildingClassInfo:
        """
        Get detailed information about a building class.

        Args:
            building_class: BuildingClass enum value

        Returns:
            BuildingClassInfo with complete class details

        Examples:
            >>> classifier = TurkishBuildingClassifier()
            >>> info = classifier.get_class_info(BuildingClass.CLASS_V_A)
            >>> print(info.name_en)
            'Educational facilities (schools, universities)'
        """
        class_data = self._classes[building_class.value]

        return BuildingClassInfo(
            building_class=building_class,
            name_tr=class_data["name_tr"],
            name_en=class_data["name_en"],
            description=class_data["description"],
            examples=class_data["examples"],
            cost_per_sqm_tl=class_data["cost_per_sqm_tl"],
            max_floors=class_data["max_floors"],
            max_height_m=class_data["max_height_m"],
        )

    def get_available_types(self) -> list[str]:
        """
        Get list of all available building types.

        Returns:
            List of valid building type identifiers
        """
        return list(self._type_mappings.keys())

    def get_class_by_code(self, class_code: str) -> Optional[BuildingClass]:
        """
        Get BuildingClass enum from class code string.

        Args:
            class_code: Class code (e.g., "V-A", "III-B")

        Returns:
            BuildingClass if valid, None otherwise

        Examples:
            >>> classifier = TurkishBuildingClassifier()
            >>> classifier.get_class_by_code("V-A")
            BuildingClass.CLASS_V_A
        """
        try:
            return BuildingClass(class_code)
        except ValueError:
            return None
