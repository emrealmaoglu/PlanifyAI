"""
Constraint Validation for H-SAGA Optimization

Includes Turkish İmar Kanunu compliance checking
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from shapely.geometry import Polygon, Point, box

from backend.core.turkish_standards import (
    TurkishComplianceChecker,
    ComplianceReport,
)
from .building_mapper import BuildingTypeMapper


@dataclass
class ConstraintViolationSummary:
    """Summary of constraint violations"""

    is_valid: bool
    violation_count: int
    severity_breakdown: Dict[str, int]
    violations: List[str]
    compliance_report: Optional[ComplianceReport] = None


class TurkishConstraintValidator:
    """
    Validates campus layouts against Turkish urban planning regulations.

    Checks:
    - İmar Kanunu compliance (FAR, setbacks, parking, green space)
    - Physical constraints (overlaps, boundaries)
    - Accessibility requirements
    """

    def __init__(
        self,
        parcel_boundary: Polygon,
        parcel_area: float,
        zone_type: str = "educational",
        enable_compliance_checks: bool = True,
    ):
        """
        Initialize constraint validator.

        Args:
            parcel_boundary: Campus boundary polygon
            parcel_area: Total parcel area in m²
            zone_type: Zoning type (residential, commercial, educational, etc.)
            enable_compliance_checks: Enable Turkish compliance checking
        """
        self.parcel_boundary = parcel_boundary
        self.parcel_area = parcel_area
        self.zone_type = zone_type
        self.enable_compliance = enable_compliance_checks

        if enable_compliance_checks:
            self.compliance_checker = TurkishComplianceChecker()
            self.building_mapper = BuildingTypeMapper()

    def validate_solution(
        self, buildings: List, **kwargs
    ) -> ConstraintViolationSummary:
        """
        Validate a complete solution against all constraints.

        Args:
            buildings: List of Building objects with positions

        Returns:
            ConstraintViolationSummary with all violations
        """
        violations = []
        severity_breakdown = {"error": 0, "warning": 0}
        compliance_report = None

        # 1. Check physical constraints
        overlap_violations = self._check_overlaps(buildings)
        violations.extend(overlap_violations)
        severity_breakdown["error"] += len(overlap_violations)

        # 2. Check boundary constraints
        boundary_violations = self._check_boundaries(buildings)
        violations.extend(boundary_violations)
        severity_breakdown["error"] += len(boundary_violations)

        # 3. Check Turkish compliance (if enabled)
        if self.enable_compliance:
            try:
                compliance_report = self._check_turkish_compliance(buildings)

                # Add compliance violations
                for error in compliance_report.errors:
                    violations.append(f"İmar Kanunu violation: {error.message_en}")
                    severity_breakdown["error"] += 1

                for warning in compliance_report.warnings:
                    violations.append(f"Compliance warning: {warning.message_en}")
                    severity_breakdown["warning"] += 1

            except Exception as e:
                violations.append(f"Compliance check failed: {str(e)}")
                severity_breakdown["warning"] += 1

        is_valid = severity_breakdown["error"] == 0

        return ConstraintViolationSummary(
            is_valid=is_valid,
            violation_count=len(violations),
            severity_breakdown=severity_breakdown,
            violations=violations,
            compliance_report=compliance_report,
        )

    def _check_overlaps(self, buildings: List) -> List[str]:
        """Check for building overlaps"""
        violations = []

        # Create polygons for each building
        polygons = []
        for b in buildings:
            try:
                pos = getattr(b, "position", (0, 0))
                area = getattr(b, "area", 1000)
                floors = getattr(b, "floors", 1)

                # Estimate footprint (assuming square building)
                footprint = area / floors
                side_length = footprint**0.5

                # Create bounding box centered at position
                x, y = pos
                half_side = side_length / 2
                polygon = box(
                    x - half_side, y - half_side, x + half_side, y + half_side
                )
                polygons.append((b, polygon))

            except Exception as e:
                violations.append(f"Failed to create polygon for building: {e}")

        # Check all pairs for overlap
        for i, (b1, p1) in enumerate(polygons):
            for j, (b2, p2) in enumerate(polygons[i + 1 :], start=i + 1):
                if p1.intersects(p2) and not p1.touches(p2):
                    b1_id = getattr(b1, "id", getattr(b1, "building_id", f"B{i}"))
                    b2_id = getattr(b2, "id", getattr(b2, "building_id", f"B{j}"))
                    violations.append(f"Buildings {b1_id} and {b2_id} overlap")

        return violations

    def _check_boundaries(self, buildings: List) -> List[str]:
        """Check buildings are within parcel boundary"""
        violations = []

        for b in buildings:
            try:
                pos = getattr(b, "position", (0, 0))
                point = Point(pos)

                if not self.parcel_boundary.contains(point):
                    b_id = getattr(b, "id", getattr(b, "building_id", "unknown"))
                    violations.append(f"Building {b_id} is outside parcel boundary")

            except Exception as e:
                violations.append(f"Boundary check failed: {e}")

        return violations

    def _check_turkish_compliance(self, buildings: List) -> ComplianceReport:
        """
        Check Turkish İmar Kanunu compliance.

        Returns:
            ComplianceReport with detailed violations
        """
        # Map buildings to Turkish types
        turkish_buildings = self.building_mapper.map_building_list(buildings)

        # Aggregate data for compliance checking
        total_building_area = sum(tb.area for tb in turkish_buildings)
        total_floors = sum(tb.floors for tb in turkish_buildings)

        # Prepare compliance check data
        building_data = {
            "area": total_building_area / len(turkish_buildings),  # Avg
            "floors": total_floors // len(turkish_buildings),  # Avg
            "type": self.zone_type,
        }

        parcel_data = {
            "area": self.parcel_area,
            "geometry": self.parcel_boundary,
            "zone_type": self.zone_type,
        }

        # Run full compliance check
        compliance_report = self.compliance_checker.full_compliance_check(
            building_data, parcel_data
        )

        return compliance_report

    def get_constraint_penalty(self, buildings: List, **kwargs) -> float:
        """
        Calculate penalty value for constraint violations.

        Returns:
            Penalty value in [0, inf) where 0 = no violations
        """
        summary = self.validate_solution(buildings, **kwargs)

        if summary.is_valid:
            return 0.0

        # Penalty increases with number and severity of violations
        error_penalty = summary.severity_breakdown["error"] * 100.0
        warning_penalty = summary.severity_breakdown["warning"] * 10.0

        return error_penalty + warning_penalty
