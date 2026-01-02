"""
FAR (Floor Area Ratio) Validator for Turkish Building Codes

Implements Turkish Emsal (FAR) calculations with 30% exemption rule.

Key Concepts:
- FAR (Emsal): Total floor area / Parcel area
- Turkish exemption: 30% exemption for basement, mechanical, parking
- Dynamic limits based on zone type

Research source: Construction_Cost_and_NPV_Optimization_Guide.docx
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

# Polygon import removed - not used in this module


@dataclass
class FARRules:
    """
    FAR calculation rules for Turkish regulations.

    Attributes:
        exemption_ratio: Exemption ratio for ancillary spaces (default: 0.30)
        count_basement: Include basement in floor area calculation
        count_mechanical: Include mechanical rooms in calculation
        count_parking: Include parking in calculation
    """

    exemption_ratio: float = 0.30  # Turkish 30% rule
    count_basement: bool = True  # Basement counts toward FAR
    count_mechanical: bool = False  # Mechanical exempt
    count_parking: bool = False  # Parking exempt


class FARValidator:
    """
    Validate Floor Area Ratio (FAR/Emsal) compliance.

    Turkish regulation allows 30% exemption for:
    - Basement parking
    - Mechanical/utility rooms
    - Building services

    Example:
        >>> validator = FARValidator(
        ...     parcel_area=10000,
        ...     max_far=2.0,
        ...     rules=FARRules()
        ... )
        >>> result = validator.validate(buildings)
        >>> if result["compliant"]:
        ...     print(f"FAR: {result['actual_far']:.2f} (allowed: {result['allowed_far']:.2f})")
    """

    def __init__(
        self,
        parcel_area: float,
        max_far: float,
        rules: Optional[FARRules] = None,
    ):
        """
        Initialize FAR validator.

        Args:
            parcel_area: Total parcel area (m²)
            max_far: Maximum allowed FAR for zone
            rules: FAR calculation rules (uses defaults if None)
        """
        self.parcel_area = parcel_area
        self.max_far = max_far
        self.rules = rules or FARRules()

    def calculate_gross_floor_area(self, buildings: List[Dict]) -> float:
        """
        Calculate total gross floor area.

        Args:
            buildings: List of building dictionaries with area, floors, basement

        Returns:
            Total gross floor area (m²)
        """
        total_area = 0.0

        for building in buildings:
            area = building.get("area", 0)
            floors = building.get("floors", 1)

            # Main building floors
            total_area += area * floors

            # Basement (if counted)
            if self.rules.count_basement:
                basement_floors = building.get("basement_floors", 0)
                total_area += area * basement_floors

        return total_area

    def calculate_exemption_area(self, buildings: List[Dict]) -> float:
        """
        Calculate area eligible for 30% exemption.

        Turkish regulation exempts:
        - Basement parking
        - Mechanical rooms
        - Building services

        Args:
            buildings: List of building dictionaries

        Returns:
            Total exemption-eligible area (m²)
        """
        exemption_area = 0.0

        for building in buildings:
            area = building.get("area", 0)

            # Basement parking (if not counted in rules)
            if not self.rules.count_parking:
                basement_parking = building.get("basement_parking_floors", 0)
                exemption_area += area * basement_parking

            # Mechanical/utility spaces (if not counted)
            if not self.rules.count_mechanical:
                mechanical_ratio = building.get("mechanical_ratio", 0.05)  # 5% default
                exemption_area += area * building.get("floors", 1) * mechanical_ratio

        return exemption_area

    def calculate_taxable_area(self, buildings: List[Dict]) -> Dict:
        """
        Calculate taxable floor area after exemptions.

        Applies Turkish 30% exemption rule.

        Args:
            buildings: List of building dictionaries

        Returns:
            Dictionary with gross, exemption, and taxable areas
        """
        gross_area = self.calculate_gross_floor_area(buildings)

        # Apply 30% blanket exemption (Turkish standard)
        exemption_area = gross_area * self.rules.exemption_ratio

        # Or use detailed exemption calculation
        # exemption_area = self.calculate_exemption_area(buildings)

        taxable_area = gross_area - exemption_area

        return {
            "gross_floor_area": gross_area,
            "exemption_area": exemption_area,
            "taxable_area": taxable_area,
            "exemption_ratio": exemption_area / gross_area if gross_area > 0 else 0,
        }

    def calculate_far(self, buildings: List[Dict]) -> float:
        """
        Calculate actual FAR (Emsal).

        FAR = Taxable Floor Area / Parcel Area

        Args:
            buildings: List of building dictionaries

        Returns:
            Calculated FAR value
        """
        area_data = self.calculate_taxable_area(buildings)
        taxable_area = area_data["taxable_area"]

        return taxable_area / self.parcel_area

    def validate(self, buildings: List[Dict]) -> Dict:
        """
        Validate FAR compliance.

        Args:
            buildings: List of building dictionaries

        Returns:
            Dictionary with compliance status and detailed metrics
        """
        area_data = self.calculate_taxable_area(buildings)
        actual_far = self.calculate_far(buildings)

        compliant = actual_far <= self.max_far
        margin = self.max_far - actual_far

        return {
            "compliant": compliant,
            "actual_far": actual_far,
            "allowed_far": self.max_far,
            "margin": margin,
            "margin_percentage": (margin / self.max_far * 100) if self.max_far > 0 else 0,
            **area_data,
        }

    def calculate_max_buildable_area(self, existing_buildings: List[Dict] = None) -> Dict:
        """
        Calculate maximum remaining buildable area.

        Useful for optimization: how much more can we build?

        Args:
            existing_buildings: Already placed buildings (optional)

        Returns:
            Dictionary with remaining capacity
        """
        if existing_buildings:
            area_data = self.calculate_taxable_area(existing_buildings)
            used_taxable = area_data["taxable_area"]
        else:
            used_taxable = 0.0

        # Maximum taxable area allowed
        max_taxable = self.max_far * self.parcel_area

        # Remaining capacity
        remaining_taxable = max_taxable - used_taxable

        # Convert back to gross (accounting for 30% exemption)
        # If taxable = gross * 0.7, then gross = taxable / 0.7
        remaining_gross = remaining_taxable / (1 - self.rules.exemption_ratio)

        return {
            "max_taxable_area": max_taxable,
            "used_taxable_area": used_taxable,
            "remaining_taxable": remaining_taxable,
            "remaining_gross": remaining_gross,
            "utilization_percentage": (used_taxable / max_taxable * 100) if max_taxable > 0 else 0,
        }

    def optimize_floor_distribution(
        self, target_gross_area: float, num_buildings: int
    ) -> List[Dict]:
        """
        Optimize floor distribution to maximize FAR utilization.

        Args:
            target_gross_area: Target total gross floor area
            num_buildings: Number of buildings to distribute across

        Returns:
            List of building configurations with floor counts
        """
        # Calculate what FAR this would achieve
        area_per_building = target_gross_area / num_buildings

        # Account for exemption
        taxable_total = target_gross_area * (1 - self.rules.exemption_ratio)
        target_far = taxable_total / self.parcel_area

        # Check if feasible
        if target_far > self.max_far:
            # Scale down to fit
            scale_factor = self.max_far / target_far
            target_gross_area *= scale_factor
            area_per_building *= scale_factor

        # Distribute evenly
        # Assume 3.5m floor height, 50m² average footprint
        avg_footprint = 500  # m²
        floors_per_building = max(1, int(area_per_building / avg_footprint))

        buildings = []
        for i in range(num_buildings):
            buildings.append(
                {
                    "area": avg_footprint,
                    "floors": floors_per_building,
                    "total_floor_area": avg_footprint * floors_per_building,
                }
            )

        return buildings
