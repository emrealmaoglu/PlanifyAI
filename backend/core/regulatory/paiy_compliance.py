"""
PAİY (Plan ve İmar Yönetmeliği) Compliance Module

Implements Turkish Planning and Zoning Regulation compliance checks.

Based on research from:
- Turkish Urban Planning Standards Research.docx
- objectives_constants.md (construction costs)

Reference: Official Gazette No. 3194 (İmar Kanunu)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from shapely.geometry import Polygon


class ZoneType(Enum):
    """Turkish urban zoning classifications (PAİY)."""

    RESIDENTIAL_LOW = "konut_az_yogun"  # E<1.0
    RESIDENTIAL_MID = "konut_orta_yogun"  # E=1.0-2.0
    RESIDENTIAL_HIGH = "konut_yogun"  # E>2.0
    COMMERCIAL = "ticaret"
    INDUSTRIAL_LIGHT = "sanayi_hafif"
    INDUSTRIAL_HEAVY = "sanayi_agir"
    EDUCATIONAL = "egitim"  # University campus zone
    HEALTH = "saglik"
    GREEN_SPACE = "yesil_alan"
    MIXED_USE = "karma_kullanim"


@dataclass
class PAIYConstants:
    """
    PAİY regulation constants for Turkish building codes.

    Constants extracted from research and official PAİY documentation.
    """

    # Minimum setbacks (m) by building height
    BASE_SETBACK: float = 5.0  # Minimum for all buildings
    SETBACK_PER_FLOOR_ABOVE_4: float = 0.5  # Additional per floor > 4
    MAX_HEIGHT_SETBACK: float = 15.0  # For buildings > 60.5m

    # FAR (Floor Area Ratio) limits by zone
    FAR_LIMITS: Dict[ZoneType, float] = None

    # Height limits (m) by zone
    HEIGHT_LIMITS: Dict[ZoneType, float] = None

    # Minimum green space ratios
    MIN_GREEN_SPACE_RATIO: float = 0.30  # 30% of total area

    # Construction costs (TL/m²) from research
    CONSTRUCTION_COSTS: Dict[str, float] = None

    # Fire access requirements
    MIN_FIRE_ROAD_WIDTH: float = 6.0  # meters
    MAX_FIRE_ACCESS_DISTANCE: float = 45.0  # meters from any building

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.FAR_LIMITS is None:
            self.FAR_LIMITS = {
                ZoneType.RESIDENTIAL_LOW: 0.80,
                ZoneType.RESIDENTIAL_MID: 1.50,
                ZoneType.RESIDENTIAL_HIGH: 2.50,
                ZoneType.COMMERCIAL: 3.00,
                ZoneType.EDUCATIONAL: 2.00,  # University campus
                ZoneType.HEALTH: 2.00,
                ZoneType.MIXED_USE: 2.00,
                ZoneType.GREEN_SPACE: 0.10,
            }

        if self.HEIGHT_LIMITS is None:
            self.HEIGHT_LIMITS = {
                ZoneType.RESIDENTIAL_LOW: 12.5,  # ~4 floors
                ZoneType.RESIDENTIAL_MID: 21.5,  # ~7 floors
                ZoneType.RESIDENTIAL_HIGH: 30.5,  # ~10 floors
                ZoneType.COMMERCIAL: 30.5,
                ZoneType.EDUCATIONAL: 21.5,
                ZoneType.HEALTH: 30.5,
                ZoneType.MIXED_USE: 21.5,
            }

        if self.CONSTRUCTION_COSTS is None:
            # From objectives_constants.md research
            self.CONSTRUCTION_COSTS = {
                "RESIDENTIAL": 1500,  # TL/m²
                "EDUCATIONAL": 2000,
                "ADMINISTRATIVE": 1800,
                "HEALTH": 2500,
                "SOCIAL": 1600,
                "COMMERCIAL": 2200,
                "LIBRARY": 2300,
                "SPORTS": 1900,
                "DINING": 1700,
            }


class PAIYCompliance:
    """
    Turkish PAİY regulation compliance checker.

    Validates building layouts against Turkish planning regulations:
    - Setback requirements
    - FAR (Floor Area Ratio) limits
    - Height restrictions
    - Green space minimums
    - Fire access requirements

    Example:
        >>> constants = PAIYConstants()
        >>> checker = PAIYCompliance(
        ...     zone_type=ZoneType.EDUCATIONAL,
        ...     parcel_area=250000,
        ...     constants=constants
        ... )
        >>> result = checker.validate_layout(buildings)
        >>> if not result.compliant:
        ...     print(f"Violations: {result.violations}")
    """

    def __init__(
        self,
        zone_type: ZoneType,
        parcel_area: float,
        constants: Optional[PAIYConstants] = None,
    ):
        """
        Initialize PAİY compliance checker.

        Args:
            zone_type: Urban zone classification
            parcel_area: Total parcel area (m²)
            constants: PAİY constants (uses defaults if None)
        """
        self.zone_type = zone_type
        self.parcel_area = parcel_area
        self.constants = constants or PAIYConstants()

    def calculate_required_setback(self, floors: int, height: float) -> float:
        """
        Calculate required setback distance based on building height.

        Turkish regulation: Base 5m + 0.5m per floor above 4 floors.
        Special case: Buildings > 60.5m require 15m setback.

        Args:
            floors: Number of floors
            height: Building height (meters)

        Returns:
            Required setback distance (meters)
        """
        if height > 60.5:
            return self.constants.MAX_HEIGHT_SETBACK

        base = self.constants.BASE_SETBACK

        if floors > 4:
            additional = (floors - 4) * self.constants.SETBACK_PER_FLOOR_ABOVE_4
            return base + additional

        return base

    def validate_far(self, buildings: List[Dict], apply_exemption: bool = True) -> Dict:
        """
        Validate Floor Area Ratio (FAR) compliance.

        Turkish regulation: 30% exemption for ancillary spaces
        (basement parking, mechanical rooms, etc.)

        Args:
            buildings: List of building dictionaries with 'area' and 'floors'
            apply_exemption: Apply 30% exemption rule (default: True)

        Returns:
            Dictionary with compliance status and metrics
        """
        total_floor_area = sum(b.get("area", 0) * b.get("floors", 1) for b in buildings)

        # Apply Turkish 30% exemption rule
        if apply_exemption:
            exemption_area = total_floor_area * 0.30
            taxable_area = total_floor_area - exemption_area
        else:
            taxable_area = total_floor_area

        actual_far = taxable_area / self.parcel_area
        allowed_far = self.constants.FAR_LIMITS.get(self.zone_type, 2.0)

        compliant = actual_far <= allowed_far
        margin = allowed_far - actual_far

        return {
            "compliant": compliant,
            "actual_far": actual_far,
            "allowed_far": allowed_far,
            "margin": margin,
            "total_floor_area": total_floor_area,
            "exemption_area": exemption_area if apply_exemption else 0.0,
            "taxable_area": taxable_area,
        }

    def validate_green_space(self, buildings: List[Polygon]) -> Dict:
        """
        Validate minimum green space requirement (30%).

        Args:
            buildings: List of building polygons

        Returns:
            Dictionary with compliance status and metrics
        """
        total_building_area = sum(b.area for b in buildings)
        green_space_area = self.parcel_area - total_building_area
        green_space_ratio = green_space_area / self.parcel_area

        required_ratio = self.constants.MIN_GREEN_SPACE_RATIO
        compliant = green_space_ratio >= required_ratio

        return {
            "compliant": compliant,
            "green_space_area": green_space_area,
            "green_space_ratio": green_space_ratio,
            "required_ratio": required_ratio,
            "margin": green_space_ratio - required_ratio,
        }

    def validate_height_limits(self, buildings: List[Dict]) -> Dict:
        """
        Validate building height limits for zone.

        Args:
            buildings: List of building dictionaries with 'height' or 'floors'

        Returns:
            Dictionary with compliance status and violations
        """
        max_allowed = self.constants.HEIGHT_LIMITS.get(self.zone_type, 21.5)
        violations = []

        for i, building in enumerate(buildings):
            height = building.get("height")

            # If height not provided, estimate from floors (3.5m per floor)
            if height is None:
                floors = building.get("floors", 1)
                height = floors * 3.5

            if height > max_allowed:
                violations.append(
                    {
                        "building_index": i,
                        "height": height,
                        "max_allowed": max_allowed,
                        "excess": height - max_allowed,
                    }
                )

        return {
            "compliant": len(violations) == 0,
            "max_allowed_height": max_allowed,
            "violations": violations,
        }

    def validate_fire_access(self, buildings: List[Polygon], roads: Optional[List] = None) -> Dict:
        """
        Validate fire access requirements.

        Turkish regulation:
        - Fire roads must be min 6m wide
        - All buildings must be within 45m of fire road

        Args:
            buildings: List of building polygons
            roads: List of road geometries (optional)

        Returns:
            Dictionary with compliance status
        """
        # Simplified check: verify road width and accessibility
        # Full implementation requires road network topology

        if roads is None:
            return {
                "compliant": False,
                "message": "No road network provided for fire access validation",
            }

        # TODO: Implement full fire access validation
        # - Check road widths >= 6m
        # - Verify all buildings within 45m of fire road
        # - Check turning radius for fire trucks

        return {
            "compliant": True,
            "message": "Fire access validation not fully implemented",
        }

    def calculate_construction_cost(self, buildings: List[Dict]) -> float:
        """
        Calculate total construction cost using Turkish standards.

        Uses construction costs from research (objectives_constants.md).

        Args:
            buildings: List of building dictionaries with 'type', 'area', 'floors'

        Returns:
            Total construction cost (TL)
        """
        total_cost = 0.0

        for building in buildings:
            building_type = building.get("type", "RESIDENTIAL").upper()
            area = building.get("area", 0)
            floors = building.get("floors", 1)

            # Get cost per m² for building type
            cost_per_sqm = self.constants.CONSTRUCTION_COSTS.get(
                building_type, 1500  # Default to residential cost
            )

            total_floor_area = area * floors
            building_cost = total_floor_area * cost_per_sqm

            total_cost += building_cost

        return total_cost
