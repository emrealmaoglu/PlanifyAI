"""
Turkish Urban Planning Compliance Checker

İmar Kanunu (Zoning Law) and regulations implementation
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

try:
    from shapely.geometry import Polygon, Point
except ImportError:
    # Fallback if shapely not available
    Polygon = None
    Point = None

from .data import ZONING_RULES


@dataclass
class ComplianceViolation:
    """Represents a planning regulation violation"""

    rule: str
    severity: str  # "error" or "warning"
    message_tr: str
    message_en: str
    current_value: float
    required_value: float
    difference: float = 0.0

    def __post_init__(self):
        self.difference = abs(self.current_value - self.required_value)


@dataclass
class ComplianceReport:
    """Complete compliance assessment report"""

    is_compliant: bool
    errors: List[ComplianceViolation] = field(default_factory=list)
    warnings: List[ComplianceViolation] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def total_violations(self) -> int:
        return len(self.errors) + len(self.warnings)


class TurkishComplianceChecker:
    """
    Checks compliance with Turkish urban planning regulations.

    Implements:
    - FAR (Emsal) limits
    - Setback requirements (İnşaat yaklaşma mesafeleri)
    - Parking ratios
    - Green space standards
    """

    def __init__(self):
        self._rules = ZONING_RULES

    def check_far(
        self,
        building_area: float,
        floors: int,
        parcel_area: float,
        zone_type: str,
    ) -> Optional[ComplianceViolation]:
        """
        Check Floor Area Ratio (Emsal) compliance.

        Formula: FAR = (building_area × floors) / parcel_area

        Args:
            building_area: Building footprint area in m²
            floors: Number of floors
            parcel_area: Total parcel area in m²
            zone_type: Zone type (residential, commercial, educational, etc.)

        Returns:
            ComplianceViolation if FAR exceeds limit, None if compliant

        Examples:
            >>> checker = TurkishComplianceChecker()
            >>> violation = checker.check_far(1000, 5, 3000, "residential")
            >>> assert violation is not None  # FAR = 1.67 > 1.5 limit
        """
        if parcel_area <= 0:
            raise ValueError(f"Parcel area must be positive, got: {parcel_area}")

        if building_area <= 0:
            raise ValueError(f"Building area must be positive, got: {building_area}")

        if floors < 1:
            raise ValueError(f"Floors must be >= 1, got: {floors}")

        # Get FAR limit for zone type
        far_limits = self._rules["far_limits"]
        if zone_type not in far_limits:
            # Default to residential if unknown
            zone_type = "residential"

        far_limit = far_limits[zone_type]

        # Calculate actual FAR
        total_building_area = building_area * floors
        actual_far = total_building_area / parcel_area

        # Check compliance
        if actual_far > far_limit:
            return ComplianceViolation(
                rule="far",
                severity="error",
                message_tr=f"Emsal (FAR) aşıldı: {actual_far:.2f} > {far_limit:.2f}",
                message_en=f"FAR exceeded: {actual_far:.2f} > {far_limit:.2f}",
                current_value=actual_far,
                required_value=far_limit,
            )

        return None

    def check_setback(
        self,
        building_polygon: Polygon,
        parcel_boundary: Polygon,
    ) -> List[ComplianceViolation]:
        """
        Check setback distances from boundaries.

        Args:
            building_polygon: Shapely Polygon of building footprint
            parcel_boundary: Shapely Polygon of parcel boundary

        Returns:
            List of ComplianceViolation objects for any violations

        Examples:
            >>> from shapely.geometry import box
            >>> checker = TurkishComplianceChecker()
            >>> building = box(10, 10, 40, 40)
            >>> parcel = box(0, 0, 50, 50)
            >>> violations = checker.check_setback(building, parcel)
            >>> assert len(violations) == 0  # 10m setbacks, compliant
        """
        if Polygon is None:
            raise ImportError("Shapely is required for setback checking")

        violations = []
        setbacks = self._rules["setbacks_m"]

        # Validate inputs
        if not isinstance(building_polygon, Polygon):
            raise TypeError("building_polygon must be a Shapely Polygon")

        if not isinstance(parcel_boundary, Polygon):
            raise TypeError("parcel_boundary must be a Shapely Polygon")

        # Check if building is within parcel
        if not parcel_boundary.contains(building_polygon):
            violations.append(
                ComplianceViolation(
                    rule="setback_building_outside",
                    severity="error",
                    message_tr="Bina parsel sınırları dışında",
                    message_en="Building is outside parcel boundaries",
                    current_value=0.0,
                    required_value=0.0,
                )
            )
            return violations

        # Get parcel boundary as LineString
        parcel_exterior = parcel_boundary.exterior

        # Calculate minimum distance from building to each side
        # Approximate by checking distance to boundary segments
        building_exterior = building_polygon.exterior

        # Calculate distances from building corners to parcel boundary
        min_distance = float("inf")
        for point in building_exterior.coords:
            point_geom = Point(point)
            distance = parcel_exterior.distance(point_geom)
            min_distance = min(min_distance, distance)

        # Check front setback (assume front is minimum distance)
        front_required = setbacks["front"]
        if min_distance < front_required:
            violations.append(
                ComplianceViolation(
                    rule="setback_front",
                    severity="error",
                    message_tr=(
                        f"Ön yaklaşma mesafesi yetersiz: "
                        f"{min_distance:.2f}m < {front_required:.2f}m"
                    ),
                    message_en=(
                        f"Front setback insufficient: "
                        f"{min_distance:.2f}m < {front_required:.2f}m"
                    ),
                    current_value=min_distance,
                    required_value=front_required,
                )
            )

        # Check side setback
        side_required = setbacks["side"]
        if min_distance < side_required:
            violations.append(
                ComplianceViolation(
                    rule="setback_side",
                    severity="error",
                    message_tr=(
                        f"Yan yaklaşma mesafesi yetersiz: "
                        f"{min_distance:.2f}m < {side_required:.2f}m"
                    ),
                    message_en=(
                        f"Side setback insufficient: "
                        f"{min_distance:.2f}m < {side_required:.2f}m"
                    ),
                    current_value=min_distance,
                    required_value=side_required,
                )
            )

        # Check rear setback
        rear_required = setbacks["rear"]
        if min_distance < rear_required:
            violations.append(
                ComplianceViolation(
                    rule="setback_rear",
                    severity="error",
                    message_tr=(
                        f"Arka yaklaşma mesafesi yetersiz: "
                        f"{min_distance:.2f}m < {rear_required:.2f}m"
                    ),
                    message_en=(
                        f"Rear setback insufficient: "
                        f"{min_distance:.2f}m < {rear_required:.2f}m"
                    ),
                    current_value=min_distance,
                    required_value=rear_required,
                )
            )

        return violations

    def check_parking(
        self,
        building_area: float,
        building_type: str,
        parking_spaces_provided: int,
    ) -> Optional[ComplianceViolation]:
        """
        Check parking space requirements.

        Args:
            building_area: Total building area in m²
            building_type: Building type (residential, commercial, etc.)
            parking_spaces_provided: Number of parking spaces provided

        Returns:
            ComplianceViolation if parking insufficient, None if compliant

        Examples:
            >>> checker = TurkishComplianceChecker()
            >>> violation = checker.check_parking(5000, "residential", 40)
            >>> assert violation is not None  # 50 spaces required, only 40 provided
        """
        parking_ratios = self._rules["parking_ratio"]

        # Map building types to parking ratio keys
        type_mapping = {
            "residential": "residential",
            "commercial": "commercial",
            "office": "office",
            "educational": "educational",
            "health": "health",
            "health_hospital": "health",
            "health_clinic": "health",
        }

        parking_type = type_mapping.get(building_type, "residential")
        if parking_type not in parking_ratios:
            parking_type = "residential"

        required_ratio = parking_ratios[parking_type]
        required_spaces = int((building_area / 100.0) * required_ratio)

        if parking_spaces_provided < required_spaces:
            return ComplianceViolation(
                rule="parking",
                severity="error",
                message_tr=(
                    f"Otopark yetersiz: {parking_spaces_provided} < "
                    f"{required_spaces} (gerekli)"
                ),
                message_en=(
                    f"Insufficient parking: {parking_spaces_provided} < "
                    f"{required_spaces} (required)"
                ),
                current_value=float(parking_spaces_provided),
                required_value=float(required_spaces),
            )

        return None

    def check_green_space(
        self,
        green_area: float,
        total_population: int,
    ) -> Optional[ComplianceViolation]:
        """
        Check green space per person (15 m²/person standard).

        Args:
            green_area: Total green space area in m²
            total_population: Total population served

        Returns:
            ComplianceViolation if green space insufficient, None if compliant

        Examples:
            >>> checker = TurkishComplianceChecker()
            >>> violation = checker.check_green_space(10000, 1000)
            >>> assert violation is not None  # 10 m²/person < 15 m²/person required
        """
        if total_population <= 0:
            raise ValueError(f"Population must be positive, got: {total_population}")

        min_per_person = self._rules["green_space"]["min_per_person_sqm"]
        actual_per_person = green_area / total_population

        if actual_per_person < min_per_person:
            return ComplianceViolation(
                rule="green_space",
                severity="warning",  # Warning, not error (aspirational standard)
                message_tr=(
                    f"Yeşil alan yetersiz: {actual_per_person:.2f} m²/kişi < "
                    f"{min_per_person:.2f} m²/kişi"
                ),
                message_en=(
                    f"Insufficient green space: {actual_per_person:.2f} m²/person < "
                    f"{min_per_person:.2f} m²/person"
                ),
                current_value=actual_per_person,
                required_value=min_per_person,
            )

        return None

    def full_compliance_check(
        self,
        building_data: Dict,
        parcel_data: Dict,
    ) -> ComplianceReport:
        """
        Run all compliance checks and generate comprehensive report.

        Args:
            building_data: Dictionary with keys:
                - area: Building area in m²
                - floors: Number of floors
                - type: Building type
                - geometry: Shapely Polygon (optional, for setback check)
                - parking_spaces: Number of parking spaces (optional)
            parcel_data: Dictionary with keys:
                - area: Parcel area in m²
                - zone_type: Zone type
                - geometry: Shapely Polygon (optional, for setback check)
                - population: Total population (optional, for green space check)
                - green_area: Green space area in m² (optional)

        Returns:
            ComplianceReport with all violations

        Examples:
            >>> from shapely.geometry import box
            >>> checker = TurkishComplianceChecker()
            >>> building_data = {
            ...     "area": 1000,
            ...     "floors": 3,
            ...     "type": "residential",
            ...     "geometry": box(10, 10, 40, 40),
            ... }
            >>> parcel_data = {
            ...     "area": 3000,
            ...     "zone_type": "residential",
            ...     "geometry": box(0, 0, 50, 50),
            ... }
            >>> report = checker.full_compliance_check(building_data, parcel_data)
            >>> assert isinstance(report, ComplianceReport)
        """
        errors = []
        warnings = []
        metrics = {}

        # Extract data with defaults
        building_area = building_data.get("area", 0.0)
        floors = building_data.get("floors", 1)
        building_type = building_data.get("type", "residential")
        building_geometry = building_data.get("geometry", None)
        parking_spaces = building_data.get("parking_spaces", None)

        parcel_area = parcel_data.get("area", 0.0)
        zone_type = parcel_data.get("zone_type", "residential")
        parcel_geometry = parcel_data.get("geometry", None)
        population = parcel_data.get("population", None)
        green_area = parcel_data.get("green_area", None)

        # Check FAR
        far_violation = self.check_far(building_area, floors, parcel_area, zone_type)
        if far_violation:
            errors.append(far_violation)

        # Calculate and store FAR metric
        if parcel_area > 0:
            actual_far = (building_area * floors) / parcel_area
            metrics["far"] = actual_far
            metrics["far_limit"] = self._rules["far_limits"].get(zone_type, 1.5)

        # Check setbacks (if geometries provided)
        if building_geometry is not None and parcel_geometry is not None:
            try:
                setback_violations = self.check_setback(
                    building_geometry, parcel_geometry
                )
                errors.extend(setback_violations)
            except ImportError:
                # Shapely not available, skip setback check
                pass

        # Check parking (if data provided)
        if parking_spaces is not None:
            parking_violation = self.check_parking(
                building_area, building_type, parking_spaces
            )
            if parking_violation:
                errors.append(parking_violation)

            # Calculate and store parking metric
            parking_ratios = self._rules["parking_ratio"]
            type_mapping = {
                "residential": "residential",
                "commercial": "commercial",
                "office": "office",
                "educational": "educational",
                "health": "health",
            }
            parking_type = type_mapping.get(building_type, "residential")
            required_ratio = parking_ratios.get(parking_type, 1.0)
            required_spaces = int((building_area / 100.0) * required_ratio)
            metrics["parking_required"] = float(required_spaces)
            metrics["parking_provided"] = float(parking_spaces)

        # Check green space (if data provided)
        if green_area is not None and population is not None and population > 0:
            green_violation = self.check_green_space(green_area, population)
            if green_violation:
                warnings.append(green_violation)

            # Calculate and store green space metric
            metrics["green_space_per_person"] = green_area / population
            metrics["green_space_required_per_person"] = self._rules["green_space"][
                "min_per_person_sqm"
            ]

        # Determine overall compliance
        is_compliant = len(errors) == 0

        return ComplianceReport(
            is_compliant=is_compliant,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )
