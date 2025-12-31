"""
Gateway Clearance Constraint

Gateway'lerin önünde yeterli boşluk olmasını sağlar.
"""

from typing import List, Tuple, Optional
from shapely.geometry import Point, Polygon

from backend.core.domain.models.campus import Gateway


class GatewayClearanceConstraint:
    """
    Gateway'lerin önünde minimum clearance (boşluk) zone'u oluşturur.

    Directional Clearance:
        - Gateway'nin bearing yönünde 2x radius uzunluğunda elliptical zone
        - Diğer yönlerde 1x radius (normal circular buffer)

    Bearing Convention:
        - Gateway bearing: Clockwise from North (0° = North, 90° = East)
        - Shapely rotate: Counter-clockwise from East (0° = East, 90° = North)
        - Conversion: shapely_angle = 90 - bearing

    Example:
        >>> gateways = [Gateway(id="g1", location=Point(0, 0), bearing=0, type="main")]
        >>> constraint = GatewayClearanceConstraint(gateways, clearance_radius=50.0)
        >>> buildings = [Polygon([...])]
        >>> is_valid = constraint.is_valid(buildings)
        >>> violation = constraint.get_violation_distance(buildings)
    """

    def __init__(
        self,
        gateways: List[Gateway],
        clearance_radius: float = 50.0,
        use_directional_clearance: bool = True
    ):
        """
        Initialize gateway clearance constraint.

        Args:
            gateways: Gateway listesi
            clearance_radius: Minimum clearance mesafesi (meters)
            use_directional_clearance: Directional (elliptical) zone kullan
                - True: Bearing yönünde 2x uzunlukta elliptical zone
                - False: Her yönde eşit circular buffer
        """
        self.gateways = gateways
        self.clearance_radius = clearance_radius
        self.use_directional_clearance = use_directional_clearance

        # Pre-calculate clearance zones
        self.clearance_zones = self._create_clearance_zones()

    def _create_clearance_zones(self) -> List[Polygon]:
        """
        Her gateway için clearance zone oluştur.

        Returns:
            List of Polygon clearance zones
        """
        zones = []
        for gateway in self.gateways:
            if self.use_directional_clearance:
                zone = self._create_directional_zone(gateway)
            else:
                zone = self._create_circular_zone(gateway)
            zones.append(zone)
        return zones

    def _create_circular_zone(self, gateway: Gateway) -> Polygon:
        """
        Circular (eşit yarıçaplı) clearance zone.

        Args:
            gateway: Gateway objesi

        Returns:
            Circular buffer Polygon
        """
        return gateway.location.buffer(self.clearance_radius)

    def _create_directional_zone(self, gateway: Gateway) -> Polygon:
        """
        Directional clearance zone using two circles (union).

        Gateway'nin bearing yönünde 2x radius uzunlukta, diğer yönlerde 1x radius.

        Algorithm:
            1. Create base circle at gateway location (radius r)
            2. Create forward circle offset by r in bearing direction (radius r)
            3. Union creates an elongated zone extending 2r in bearing direction

        This creates an asymmetric zone that extends MORE in the bearing direction.

        Args:
            gateway: Gateway objesi

        Returns:
            Union of two circles creating directional zone
        """
        import math

        # 1. Base circle at gateway location
        base_circle = gateway.location.buffer(self.clearance_radius)

        # 2. Calculate offset in bearing direction
        # bearing: 0° = North (+Y), 90° = East (+X), clockwise
        # Convert to radians for trig
        bearing_rad = math.radians(gateway.bearing)

        # Offset distance: shift by radius in bearing direction
        # This creates a "forward" circle that extends the zone
        offset_distance = self.clearance_radius

        # Calculate dx, dy from bearing
        # bearing=0° (North) → dx=0, dy=+offset
        # bearing=90° (East) → dx=+offset, dy=0
        # bearing=180° (South) → dx=0, dy=-offset
        # bearing=270° (West) → dx=-offset, dy=0
        dx = offset_distance * math.sin(bearing_rad)
        dy = offset_distance * math.cos(bearing_rad)

        # 3. Create forward circle
        forward_center = Point(gateway.location.x + dx, gateway.location.y + dy)
        forward_circle = forward_center.buffer(self.clearance_radius)

        # 4. Union creates elongated zone
        directional_zone = base_circle.union(forward_circle)

        return directional_zone

    def is_valid(self, buildings: List[Polygon]) -> bool:
        """
        Check if all buildings respect gateway clearance zones.

        Args:
            buildings: List of building Polygons

        Returns:
            True if NO buildings intersect clearance zones, False otherwise
        """
        if not buildings:
            return True  # No buildings = no violations

        for building in buildings:
            for zone in self.clearance_zones:
                if building.intersects(zone):
                    return False  # Violation found

        return True  # No violations

    def get_violation_distance(self, buildings: List[Polygon]) -> float:
        """
        Calculate total violation distance (sum of all intersections).

        Useful for penalty-based optimization where partial violations
        need to be quantified.

        Args:
            buildings: List of building Polygons

        Returns:
            Total violation area (m²) or 0.0 if no violations
        """
        if not buildings:
            return 0.0

        total_violation_area = 0.0

        for building in buildings:
            for zone in self.clearance_zones:
                if building.intersects(zone):
                    intersection = building.intersection(zone)
                    total_violation_area += intersection.area

        return total_violation_area

    def get_violations(self, buildings: List[Polygon]) -> List[Tuple[int, int, float]]:
        """
        Get detailed violation information.

        Args:
            buildings: List of building Polygons

        Returns:
            List of tuples: (building_idx, gateway_idx, intersection_area)
        """
        violations = []

        for building_idx, building in enumerate(buildings):
            for gateway_idx, zone in enumerate(self.clearance_zones):
                if building.intersects(zone):
                    intersection = building.intersection(zone)
                    violations.append((building_idx, gateway_idx, intersection.area))

        return violations

    def get_minimum_clearance_for_building(self, building: Polygon) -> Optional[float]:
        """
        Get minimum clearance distance from building to nearest gateway zone.

        Args:
            building: Building Polygon

        Returns:
            Minimum distance to clearance zone edge, or None if inside zone
        """
        min_distance = float('inf')

        for zone in self.clearance_zones:
            if building.intersects(zone):
                return None  # Building is inside zone (violation)

            distance = building.distance(zone)
            min_distance = min(min_distance, distance)

        return min_distance if min_distance != float('inf') else None

    def __repr__(self):
        return (f"GatewayClearanceConstraint("
                f"gateways={len(self.gateways)}, "
                f"radius={self.clearance_radius}m, "
                f"directional={self.use_directional_clearance})")
