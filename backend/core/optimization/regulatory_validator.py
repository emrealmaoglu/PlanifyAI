"""
Regulatory Validator for Turkish Building Codes

Integrates PAİY compliance with optimization pipeline:
- Validates layouts against Turkish setback rules
- Enforces FAR (Floor Area Ratio) limits
- Checks green space requirements
- Validates height limits by zone
- Provides cost estimates

This bridges between the optimization layer and regulatory module.
"""

from typing import Dict, List, Optional

from shapely.geometry import Polygon

from backend.core.regulatory.far_validator import FARRules, FARValidator
from backend.core.regulatory.paiy_compliance import PAIYCompliance, PAIYConstants, ZoneType
from backend.core.regulatory.setback_calculator import SetbackCalculator, SetbackRules


class RegulatoryValidator:
    """
    Validates building layouts against Turkish PAİY regulations.

    Integrates with optimization pipeline to ensure all generated
    solutions comply with Turkish building codes.

    Example:
        >>> validator = RegulatoryValidator(
        ...     zone_type=ZoneType.EDUCATIONAL,
        ...     parcel_area=250000,
        ...     boundary=parcel_boundary
        ... )
        >>> result = validator.validate_layout(buildings, building_polygons)
        >>> if not result["compliant"]:
        ...     violations = result["violations"]
    """

    def __init__(
        self,
        zone_type: ZoneType,
        parcel_area: float,
        boundary: Polygon,
        constants: Optional[PAIYConstants] = None,
        far_rules: Optional[FARRules] = None,
        setback_rules: Optional[SetbackRules] = None,
    ):
        """
        Initialize regulatory validator.

        Args:
            zone_type: Turkish urban zone classification
            parcel_area: Total parcel area (m²)
            boundary: Parcel boundary polygon
            constants: PAİY constants (uses defaults if None)
            far_rules: FAR calculation rules (uses defaults if None)
            setback_rules: Setback calculation rules (uses defaults if None)
        """
        self.zone_type = zone_type
        self.parcel_area = parcel_area
        self.boundary = boundary

        # Initialize regulatory modules
        self.constants = constants or PAIYConstants()
        self.paiy = PAIYCompliance(zone_type, parcel_area, self.constants)

        # Get FAR limit for this zone
        max_far = self.constants.FAR_LIMITS.get(zone_type, 2.0)
        self.far_validator = FARValidator(parcel_area, max_far, far_rules)

        self.setback_calc = SetbackCalculator(setback_rules)

    def validate_layout(
        self,
        buildings: List[Dict],
        building_polygons: List[Polygon],
        apply_far_exemption: bool = True,
    ) -> Dict:
        """
        Comprehensive layout validation.

        Args:
            buildings: List of building data dictionaries with:
                - area: Footprint area (m²)
                - floors: Number of floors
                - height: Building height (m), optional
                - type: Building type (RESIDENTIAL, EDUCATIONAL, etc.)
            building_polygons: List of building geometry polygons
            apply_far_exemption: Apply Turkish 30% exemption rule

        Returns:
            Dictionary with compliance status and detailed violations
        """
        violations = []
        metrics = {}

        # 1. FAR Validation
        far_result = self.paiy.validate_far(buildings, apply_far_exemption)
        metrics["far"] = far_result
        if not far_result["compliant"]:
            violations.append(
                {
                    "type": "FAR_VIOLATION",
                    "severity": "CRITICAL",
                    "actual": far_result["actual_far"],
                    "allowed": far_result["allowed_far"],
                    "excess": far_result["actual_far"] - far_result["allowed_far"],
                }
            )

        # 2. Green Space Validation
        green_result = self.paiy.validate_green_space(building_polygons)
        metrics["green_space"] = green_result
        if not green_result["compliant"]:
            violations.append(
                {
                    "type": "GREEN_SPACE_VIOLATION",
                    "severity": "HIGH",
                    "actual_ratio": green_result["green_space_ratio"],
                    "required_ratio": green_result["required_ratio"],
                    "deficit": abs(green_result["margin"]),
                }
            )

        # 3. Height Limit Validation
        height_result = self.paiy.validate_height_limits(buildings)
        metrics["height_limits"] = height_result
        if not height_result["compliant"]:
            for violation in height_result["violations"]:
                violations.append(
                    {
                        "type": "HEIGHT_VIOLATION",
                        "severity": "HIGH",
                        "building_index": violation["building_index"],
                        "actual_height": violation["height"],
                        "max_allowed": violation["max_allowed"],
                        "excess": violation["excess"],
                    }
                )

        # 4. Setback Validation
        setback_violations = self._validate_setbacks(buildings, building_polygons)
        if setback_violations:
            violations.extend(setback_violations)
            metrics["setback_compliant"] = False
        else:
            metrics["setback_compliant"] = True

        # 5. Building Separation (Fire Safety)
        separation_violations = self._validate_building_separation(building_polygons)
        if separation_violations:
            violations.extend(separation_violations)
            metrics["separation_compliant"] = False
        else:
            metrics["separation_compliant"] = True

        # 6. Construction Cost Estimate
        total_cost = self.paiy.calculate_construction_cost(buildings)
        metrics["construction_cost_tl"] = total_cost

        # Overall compliance
        compliant = len(violations) == 0

        return {
            "compliant": compliant,
            "violations": violations,
            "violation_count": len(violations),
            "metrics": metrics,
            "summary": self._generate_summary(metrics, violations),
        }

    def _validate_setbacks(
        self, buildings: List[Dict], building_polygons: List[Polygon]
    ) -> List[Dict]:
        """Validate setback requirements for all buildings."""
        violations = []

        for i, (building_data, polygon) in enumerate(zip(buildings, building_polygons)):
            # Calculate required setback for this building
            floors = building_data.get("floors", 1)
            height = building_data.get("height")
            required_setback = self.paiy.calculate_required_setback(floors, height)

            # Check actual setback from boundary
            result = self.setback_calc.calculate_from_boundary(polygon, self.boundary)

            if result["min_distance"] < required_setback:
                violations.append(
                    {
                        "type": "SETBACK_VIOLATION",
                        "severity": "HIGH",
                        "building_index": i,
                        "required_setback": required_setback,
                        "actual_setback": result["min_distance"],
                        "deficit": required_setback - result["min_distance"],
                    }
                )

        return violations

    def _validate_building_separation(self, building_polygons: List[Polygon]) -> List[Dict]:
        """Validate minimum 10m separation between buildings."""
        violations = []
        min_separation = 10.0  # Turkish fire safety standard

        # Check all pairs
        for i, building1 in enumerate(building_polygons):
            for j, building2 in enumerate(building_polygons[i + 1 :], start=i + 1):
                result = self.setback_calc.calculate_separation(
                    building1, building2, min_separation
                )

                if not result["compliant"]:
                    violations.append(
                        {
                            "type": "SEPARATION_VIOLATION",
                            "severity": "CRITICAL",
                            "building_pair": (i, j),
                            "actual_distance": result["distance"],
                            "min_required": min_separation,
                            "deficit": min_separation - result["distance"],
                        }
                    )

        return violations

    def _generate_summary(self, metrics: Dict, violations: List[Dict]) -> str:
        """Generate human-readable summary."""
        if not violations:
            return "Layout compliant with all Turkish PAİY regulations"

        violation_types = {}
        for v in violations:
            vtype = v["type"]
            violation_types[vtype] = violation_types.get(vtype, 0) + 1

        summary_parts = []
        if "FAR_VIOLATION" in violation_types:
            far = metrics["far"]
            summary_parts.append(
                f"FAR exceeded: {far['actual_far']:.2f} > {far['allowed_far']:.2f}"
            )

        if "GREEN_SPACE_VIOLATION" in violation_types:
            gs = metrics["green_space"]
            actual_pct = gs["green_space_ratio"] * 100
            required_pct = gs["required_ratio"] * 100
            summary_parts.append(
                f"Insufficient green space: {actual_pct:.1f}% < {required_pct:.1f}%"
            )

        if "HEIGHT_VIOLATION" in violation_types:
            count = violation_types["HEIGHT_VIOLATION"]
            summary_parts.append(f"{count} building(s) exceed height limit")

        if "SETBACK_VIOLATION" in violation_types:
            count = violation_types["SETBACK_VIOLATION"]
            summary_parts.append(f"{count} building(s) violate setback requirements")

        if "SEPARATION_VIOLATION" in violation_types:
            count = violation_types["SEPARATION_VIOLATION"]
            summary_parts.append(f"{count} building pair(s) too close (fire safety)")

        return "; ".join(summary_parts)

    def get_max_buildable_area(self, existing_buildings: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate remaining buildable area capacity.

        Useful for optimization: guides how much more we can build.

        Args:
            existing_buildings: Already placed buildings (optional)

        Returns:
            Dictionary with remaining FAR capacity
        """
        return self.far_validator.calculate_max_buildable_area(existing_buildings)

    def suggest_floor_distribution(
        self, target_gross_area: float, num_buildings: int
    ) -> List[Dict]:
        """
        Suggest optimal floor distribution across buildings.

        Args:
            target_gross_area: Target total gross floor area
            num_buildings: Number of buildings

        Returns:
            List of building configurations
        """
        return self.far_validator.optimize_floor_distribution(target_gross_area, num_buildings)
