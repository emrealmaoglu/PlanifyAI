"""
Constraint Violation Reporter with Explainability
==================================================

Generates human-readable explanations for constraint violations,
helping users understand what went wrong and how to fix it.

Key Features:
    - Categorizes violations by severity (CRITICAL, HIGH, MEDIUM, LOW)
    - Provides actionable fix suggestions
    - Prioritizes violations for user attention
    - Exports reports in multiple formats (JSON, text, HTML)

References:
    - XAI principles: Interpretability, Actionability, Transparency
    - Research: "Explainable AI Campus Planning.docx"

Created: 2026-01-01
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class ViolationSeverity(Enum):
    """Severity levels for constraint violations."""

    CRITICAL = "critical"  # Blocks solution entirely (e.g., building outside boundary)
    HIGH = "high"  # Major issue (e.g., building overlap)
    MEDIUM = "medium"  # Moderate issue (e.g., excessive slope)
    LOW = "low"  # Minor issue (e.g., slightly over FAR limit)
    WARNING = "warning"  # Not a violation but suboptimal


@dataclass
class ConstraintViolation:
    """
    Detailed record of a single constraint violation.

    Attributes:
        constraint_name: Name of violated constraint
        severity: Violation severity level
        violation_amount: Quantitative measure of violation
        affected_buildings: Building IDs affected by this violation
        explanation: Human-readable explanation of what went wrong
        fix_suggestions: List of actionable suggestions to resolve
        location: (x, y) location of violation (if applicable)
        metadata: Additional context-specific information
    """

    constraint_name: str
    severity: ViolationSeverity
    violation_amount: float
    affected_buildings: List[str] = field(default_factory=list)
    explanation: str = ""
    fix_suggestions: List[str] = field(default_factory=list)
    location: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "constraint": self.constraint_name,
            "severity": self.severity.value,
            "violation_amount": float(self.violation_amount),
            "affected_buildings": self.affected_buildings,
            "explanation": self.explanation,
            "fix_suggestions": self.fix_suggestions,
            "location": self.location,
            "metadata": self.metadata,
        }

    @property
    def severity_score(self) -> int:
        """Numeric score for sorting (higher = more severe)."""
        scores = {
            ViolationSeverity.CRITICAL: 4,
            ViolationSeverity.HIGH: 3,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.LOW: 1,
            ViolationSeverity.WARNING: 0,
        }
        return scores[self.severity]


class ConstraintReporter:
    """
    Generates comprehensive constraint violation reports with explanations.

    Usage:
        >>> reporter = ConstraintReporter()
        >>> reporter.analyze_solution(solution, buildings, constraints)
        >>> report = reporter.generate_report()
        >>> print(report['summary'])
    """

    def __init__(self):
        self.violations: List[ConstraintViolation] = []

    def clear(self):
        """Clear all recorded violations."""
        self.violations = []

    def add_violation(self, violation: ConstraintViolation):
        """Add a violation to the report."""
        self.violations.append(violation)

    def analyze_boundary_violations(
        self,
        building_polygons: List,
        building_ids: List[str],
        boundary_polygon,
    ) -> None:
        """
        Analyze boundary constraint violations.

        Args:
            building_polygons: List of Shapely Polygon objects
            building_ids: Corresponding building IDs
            boundary_polygon: Campus boundary Polygon
        """
        for poly, bid in zip(building_polygons, building_ids):
            if not boundary_polygon.contains(poly):
                # Calculate how much is outside
                outside_area = poly.difference(boundary_polygon).area
                violation_percent = (outside_area / poly.area) * 100

                # Determine severity
                if violation_percent > 50:
                    severity = ViolationSeverity.CRITICAL
                elif violation_percent > 20:
                    severity = ViolationSeverity.HIGH
                elif violation_percent > 5:
                    severity = ViolationSeverity.MEDIUM
                else:
                    severity = ViolationSeverity.LOW

                # Get centroid for location
                centroid = poly.centroid
                location = (centroid.x, centroid.y)

                # Calculate distance to nearest boundary point
                nearest_point = boundary_polygon.exterior.interpolate(
                    boundary_polygon.exterior.project(centroid)
                )
                distance_to_boundary = centroid.distance(nearest_point)

                self.add_violation(
                    ConstraintViolation(
                        constraint_name="boundary_containment",
                        severity=severity,
                        violation_amount=outside_area,
                        affected_buildings=[bid],
                        explanation=(
                            f"Building '{bid}' extends {outside_area:.1f}m² "
                            f"({violation_percent:.1f}%) outside the campus boundary. "
                            f"The building center is {distance_to_boundary:.1f}m "
                            f"from the nearest valid position."
                        ),
                        fix_suggestions=[
                            f"Move building '{bid}' {distance_to_boundary:.1f}m "
                            f"toward campus center",
                            "Reduce building footprint to fit within boundary",
                            "Check if boundary polygon is correctly defined",
                        ],
                        location=location,
                        metadata={
                            "outside_area_m2": outside_area,
                            "violation_percent": violation_percent,
                            "distance_to_boundary": distance_to_boundary,
                        },
                    )
                )

    def analyze_overlap_violations(
        self,
        building_polygons: List,
        building_ids: List[str],
    ) -> None:
        """
        Analyze building overlap violations.

        Args:
            building_polygons: List of Shapely Polygon objects
            building_ids: Corresponding building IDs
        """
        from shapely.strtree import STRtree

        if len(building_polygons) < 2:
            return

        # Build spatial index
        tree = STRtree(building_polygons)

        # Check each pair
        checked_pairs = set()

        for i, poly_i in enumerate(building_polygons):
            bid_i = building_ids[i]

            # Query potential overlaps
            candidates = tree.query(poly_i)

            for j in candidates:
                if i >= j:  # Skip self and already checked pairs
                    continue

                pair_key = tuple(sorted([i, j]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                poly_j = building_polygons[j]
                bid_j = building_ids[j]

                if poly_i.intersects(poly_j):
                    overlap = poly_i.intersection(poly_j)
                    overlap_area = overlap.area

                    # Calculate violation severity
                    min_area = min(poly_i.area, poly_j.area)
                    overlap_percent = (overlap_area / min_area) * 100

                    if overlap_percent > 50:
                        severity = ViolationSeverity.CRITICAL
                    elif overlap_percent > 20:
                        severity = ViolationSeverity.HIGH
                    elif overlap_percent > 5:
                        severity = ViolationSeverity.MEDIUM
                    else:
                        severity = ViolationSeverity.LOW

                    # Get overlap centroid
                    centroid = overlap.centroid
                    location = (centroid.x, centroid.y)

                    # Calculate minimum separation needed
                    distance_between = poly_i.centroid.distance(poly_j.centroid)
                    min_separation_needed = np.sqrt(overlap_area) * 2

                    self.add_violation(
                        ConstraintViolation(
                            constraint_name="no_overlap",
                            severity=severity,
                            violation_amount=overlap_area,
                            affected_buildings=[bid_i, bid_j],
                            explanation=(
                                f"Buildings '{bid_i}' and '{bid_j}' overlap by "
                                f"{overlap_area:.1f}m² ({overlap_percent:.1f}% of smaller "
                                f"building). Current separation: {distance_between:.1f}m. "
                                f"Minimum required: {min_separation_needed:.1f}m."
                            ),
                            fix_suggestions=[
                                f"Move buildings {min_separation_needed:.1f}m apart",
                                f"Reduce size of '{bid_i}' or '{bid_j}'",
                                "Try rotating one building to reduce overlap",
                                "Consider merging into single building if functionally compatible",
                            ],
                            location=location,
                            metadata={
                                "overlap_area_m2": overlap_area,
                                "overlap_percent": overlap_percent,
                                "current_distance": distance_between,
                                "min_separation": min_separation_needed,
                            },
                        )
                    )

    def analyze_slope_violations(
        self,
        building_polygons: List,
        building_ids: List[str],
        slope_values: List[float],
        max_slope: float = 0.15,
    ) -> None:
        """
        Analyze slope constraint violations.

        Args:
            building_polygons: List of Shapely Polygon objects
            building_ids: Corresponding building IDs
            slope_values: Slope values for each building (0-1 range, 0.15 = 15%)
            max_slope: Maximum allowed slope (default: 0.15 = 15%)
        """
        for poly, bid, slope in zip(building_polygons, building_ids, slope_values):
            if slope > max_slope:
                violation_amount = slope - max_slope
                slope_percent = slope * 100
                max_slope_percent = max_slope * 100

                # Determine severity
                if slope > 0.25:  # > 25%
                    severity = ViolationSeverity.CRITICAL
                elif slope > 0.20:  # > 20%
                    severity = ViolationSeverity.HIGH
                elif slope > 0.17:  # > 17%
                    severity = ViolationSeverity.MEDIUM
                else:
                    severity = ViolationSeverity.LOW

                centroid = poly.centroid
                location = (centroid.x, centroid.y)

                self.add_violation(
                    ConstraintViolation(
                        constraint_name="max_slope",
                        severity=severity,
                        violation_amount=violation_amount,
                        affected_buildings=[bid],
                        explanation=(
                            f"Building '{bid}' is on terrain with {slope_percent:.1f}% slope, "
                            f"exceeding maximum of {max_slope_percent:.1f}%. Excess: "
                            f"{(violation_amount * 100):.1f}%."
                        ),
                        fix_suggestions=[
                            f"Relocate '{bid}' to flatter terrain",
                            "Consider terracing or grading at this location",
                            "Reduce building height to minimize foundation requirements",
                            "Use specialized foundation design for steep slopes",
                        ],
                        location=location,
                        metadata={
                            "slope_percent": slope_percent,
                            "max_allowed_percent": max_slope_percent,
                            "excess_percent": violation_amount * 100,
                        },
                    )
                )

    def analyze_fire_separation_violations(
        self,
        building_polygons: List,
        building_ids: List[str],
        building_heights: List[float],
        min_fire_separation: float = 6.0,
    ) -> None:
        """
        Analyze fire separation constraint violations.

        Args:
            building_polygons: List of Shapely Polygon objects
            building_ids: Corresponding building IDs
            building_heights: Building heights in meters
            min_fire_separation: Base minimum separation (default: 6m)
        """
        from shapely.strtree import STRtree

        if len(building_polygons) < 2:
            return

        tree = STRtree(building_polygons)
        checked_pairs = set()

        for i, poly_i in enumerate(building_polygons):
            bid_i = building_ids[i]
            height_i = building_heights[i]

            # Fire separation: max(6m, H/2) where H is taller building
            candidates = tree.query(poly_i)

            for j in candidates:
                if i >= j:
                    continue

                pair_key = tuple(sorted([i, j]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                poly_j = building_polygons[j]
                bid_j = building_ids[j]
                height_j = building_heights[j]

                # Required separation
                max_height = max(height_i, height_j)
                required_separation = max(min_fire_separation, max_height / 2.0)

                # Actual separation
                actual_separation = poly_i.distance(poly_j)

                if actual_separation < required_separation:
                    violation_amount = required_separation - actual_separation

                    # Severity based on how far below requirement
                    percent_deficit = (violation_amount / required_separation) * 100

                    if percent_deficit > 50:
                        severity = ViolationSeverity.CRITICAL
                    elif percent_deficit > 30:
                        severity = ViolationSeverity.HIGH
                    elif percent_deficit > 15:
                        severity = ViolationSeverity.MEDIUM
                    else:
                        severity = ViolationSeverity.LOW

                    # Midpoint between buildings
                    centroid_i = poly_i.centroid
                    centroid_j = poly_j.centroid
                    location = (
                        (centroid_i.x + centroid_j.x) / 2,
                        (centroid_i.y + centroid_j.y) / 2,
                    )

                    self.add_violation(
                        ConstraintViolation(
                            constraint_name="fire_separation",
                            severity=severity,
                            violation_amount=violation_amount,
                            affected_buildings=[bid_i, bid_j],
                            explanation=(
                                f"Buildings '{bid_i}' (H={height_i:.1f}m) and '{bid_j}' "
                                f"(H={height_j:.1f}m) are {actual_separation:.1f}m apart, "
                                f"below required {required_separation:.1f}m fire separation. "
                                f"Deficit: {violation_amount:.1f}m ({percent_deficit:.1f}%)."
                            ),
                            fix_suggestions=[
                                f"Increase separation to {required_separation:.1f}m",
                                f"Reduce height of taller building to {actual_separation * 2:.1f}m",
                                "Install fire-rated walls if reducing separation",
                                "Consider fire suppression systems for closer spacing",
                            ],
                            location=location,
                            metadata={
                                "actual_separation_m": actual_separation,
                                "required_separation_m": required_separation,
                                "deficit_m": violation_amount,
                                "deficit_percent": percent_deficit,
                                "taller_building_height": max_height,
                            },
                        )
                    )

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive violation report.

        Returns:
            Dictionary with summary, violations by severity, and recommendations
        """
        # Sort violations by severity
        sorted_violations = sorted(self.violations, key=lambda v: v.severity_score, reverse=True)

        # Group by severity
        by_severity = {severity: [] for severity in ViolationSeverity}
        for v in sorted_violations:
            by_severity[v.severity].append(v)

        # Count by constraint type
        by_constraint = {}
        for v in self.violations:
            if v.constraint_name not in by_constraint:
                by_constraint[v.constraint_name] = []
            by_constraint[v.constraint_name].append(v)

        # Generate summary
        n_critical = len(by_severity[ViolationSeverity.CRITICAL])
        n_high = len(by_severity[ViolationSeverity.HIGH])
        n_medium = len(by_severity[ViolationSeverity.MEDIUM])
        n_low = len(by_severity[ViolationSeverity.LOW])
        n_warnings = len(by_severity[ViolationSeverity.WARNING])

        total_violations = n_critical + n_high + n_medium + n_low

        # Overall health score (0-100)
        if total_violations == 0:
            health_score = 100.0
        else:
            # Weight violations by severity
            weighted_score = (
                n_critical * 10 + n_high * 5 + n_medium * 2 + n_low * 1
            ) / total_violations
            health_score = max(0.0, 100.0 - weighted_score * 10)

        # Top priority fixes
        top_priority = sorted_violations[:5]  # Top 5 most critical

        return {
            "summary": {
                "total_violations": total_violations,
                "critical": n_critical,
                "high": n_high,
                "medium": n_medium,
                "low": n_low,
                "warnings": n_warnings,
                "health_score": health_score,
                "status": self._get_status(n_critical, n_high),
            },
            "violations_by_severity": {
                severity.value: [v.to_dict() for v in violations]
                for severity, violations in by_severity.items()
            },
            "violations_by_constraint": {
                constraint: [v.to_dict() for v in violations]
                for constraint, violations in by_constraint.items()
            },
            "top_priority_fixes": [v.to_dict() for v in top_priority],
            "all_violations": [v.to_dict() for v in sorted_violations],
        }

    def _get_status(self, n_critical: int, n_high: int) -> str:
        """Determine overall solution status."""
        if n_critical > 0:
            return "FAILED - Critical violations present"
        elif n_high > 3:
            return "POOR - Multiple high-severity violations"
        elif n_high > 0:
            return "NEEDS IMPROVEMENT - High-severity violations present"
        else:
            return "ACCEPTABLE - No critical or high violations"

    def generate_text_report(self) -> str:
        """Generate human-readable text report."""
        report = self.generate_report()
        summary = report["summary"]

        lines = []
        lines.append("=" * 80)
        lines.append("CONSTRAINT VIOLATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Status: {summary['status']}")
        lines.append(f"Health Score: {summary['health_score']:.1f}/100")
        lines.append("")
        lines.append(f"Total Violations: {summary['total_violations']}")
        lines.append(f"  - Critical: {summary['critical']}")
        lines.append(f"  - High:     {summary['high']}")
        lines.append(f"  - Medium:   {summary['medium']}")
        lines.append(f"  - Low:      {summary['low']}")
        lines.append(f"  - Warnings: {summary['warnings']}")
        lines.append("")

        if summary["total_violations"] == 0:
            lines.append("✓ No violations found. Solution is valid.")
            lines.append("")
        else:
            lines.append("TOP PRIORITY FIXES:")
            lines.append("-" * 80)

            for i, v in enumerate(report["top_priority_fixes"], 1):
                lines.append(f"\n{i}. [{v['severity'].upper()}] {v['constraint']}")
                lines.append(f"   {v['explanation']}")
                lines.append("   Suggestions:")
                for suggestion in v["fix_suggestions"][:3]:  # Top 3 suggestions
                    lines.append(f"   • {suggestion}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)
