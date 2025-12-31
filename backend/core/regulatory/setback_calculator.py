"""
Dynamic Setback Calculator for Turkish Building Codes

Implements adaptive setback calculations based on:
- Building height and floor count
- Zone type and density
- Adjacent building relationships
- Fire safety requirements

Research source: Turkish Urban Planning Standards Research.docx
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from shapely.geometry import Point, Polygon


@dataclass
class SetbackRules:
    """
    Setback calculation rules for Turkish regulations.

    Attributes:
        base_setback: Minimum setback for all buildings (default: 5m)
        height_multiplier: Additional setback per meter of height
        floor_increment: Additional setback per floor above threshold
        floor_threshold: Floor count threshold for incremental setback
        max_setback: Maximum setback distance cap
    """

    base_setback: float = 5.0
    height_multiplier: float = 0.0  # Not used in basic Turkish rules
    floor_increment: float = 0.5  # 0.5m per floor above 4
    floor_threshold: int = 4  # Start increment after 4 floors
    max_setback: float = 15.0  # Cap for very tall buildings


class SetbackCalculator:
    """
    Calculate dynamic setbacks for building placement.

    Ensures compliance with Turkish PAİY regulations:
    - Base 5m setback for all buildings
    - +0.5m per floor above 4 floors
    - 15m for buildings > 60.5m height

    Example:
        >>> calc = SetbackCalculator(rules=SetbackRules())
        >>> setback = calc.calculate(floors=6, height=21.0)
        >>> print(f"Required setback: {setback}m")
        Required setback: 6.0m
    """

    def __init__(self, rules: Optional[SetbackRules] = None):
        """
        Initialize setback calculator.

        Args:
            rules: Setback rules (uses defaults if None)
        """
        self.rules = rules or SetbackRules()

    def calculate(
        self,
        floors: int,
        height: Optional[float] = None,
        zone_density: str = "medium",
    ) -> float:
        """
        Calculate required setback distance.

        Args:
            floors: Number of floors
            height: Building height in meters (estimated if None)
            zone_density: Zone density classification

        Returns:
            Required setback distance (meters)
        """
        # Estimate height if not provided (3.5m per floor)
        if height is None:
            height = floors * 3.5

        # Special case: Very tall buildings (> 60.5m)
        if height > 60.5:
            return self.rules.max_setback

        # Base setback
        setback = self.rules.base_setback

        # Add incremental setback for floors above threshold
        if floors > self.rules.floor_threshold:
            excess_floors = floors - self.rules.floor_threshold
            additional = excess_floors * self.rules.floor_increment
            setback += additional

        # Cap at maximum
        return min(setback, self.rules.max_setback)

    def calculate_from_boundary(self, building: Polygon, boundary: Polygon) -> Dict[str, float]:
        """
        Calculate setback violations from parcel boundary.

        Args:
            building: Building polygon
            boundary: Parcel boundary polygon

        Returns:
            Dictionary with min/max/avg distances and violation status
        """
        # Get minimum distance from building to boundary
        min_distance = building.distance(boundary)

        # Sample multiple points on building perimeter for detailed analysis
        exterior_coords = list(building.exterior.coords)
        distances = []

        for coord in exterior_coords:
            point = Point(coord)
            dist = point.distance(boundary)
            distances.append(dist)

        return {
            "min_distance": min_distance,
            "max_distance": max(distances),
            "avg_distance": sum(distances) / len(distances),
            "compliant": min_distance >= 0,  # Will be checked against required setback
        }

    def calculate_separation(
        self, building1: Polygon, building2: Polygon, min_separation: float = 10.0
    ) -> Dict:
        """
        Calculate building-to-building separation.

        Turkish regulation: Minimum 10m between buildings for fire safety.

        Args:
            building1: First building polygon
            building2: Second building polygon
            min_separation: Minimum required separation (default: 10m)

        Returns:
            Dictionary with separation metrics and compliance
        """
        distance = building1.distance(building2)
        compliant = distance >= min_separation

        return {
            "distance": distance,
            "min_required": min_separation,
            "compliant": compliant,
            "margin": distance - min_separation,
        }

    def calculate_adaptive_setback(self, building_data: Dict, context: Dict) -> float:
        """
        Calculate adaptive setback based on building and context.

        Considers:
        - Building characteristics (height, floors)
        - Surrounding density
        - Adjacent building heights
        - Fire safety requirements

        Args:
            building_data: Building properties (floors, height, type)
            context: Contextual data (zone, neighbors, etc.)

        Returns:
            Adaptive setback distance (meters)
        """
        # Base calculation
        floors = building_data.get("floors", 1)
        height = building_data.get("height")
        base_setback = self.calculate(floors, height)

        # Adjust for context
        adjacent_heights = context.get("adjacent_heights", [])

        # If surrounded by taller buildings, may allow reduced setback
        # If surrounded by shorter buildings, may require increased setback
        if adjacent_heights:
            avg_adjacent = sum(adjacent_heights) / len(adjacent_heights)
            building_height = height or (floors * 3.5)

            # Height differential factor (±20% adjustment)
            if building_height > avg_adjacent * 1.5:
                # Taller than neighbors: increase setback by 20%
                base_setback *= 1.2
            elif building_height < avg_adjacent * 0.7:
                # Shorter than neighbors: may reduce setback by 10%
                base_setback *= 0.9

        return min(base_setback, self.rules.max_setback)

    def validate_all_setbacks(
        self, buildings: List[Polygon], boundary: Polygon, required_setback: float
    ) -> Dict:
        """
        Validate setback compliance for all buildings.

        Args:
            buildings: List of building polygons
            boundary: Parcel boundary
            required_setback: Required setback distance

        Returns:
            Dictionary with violations and summary
        """
        violations = []

        for i, building in enumerate(buildings):
            result = self.calculate_from_boundary(building, boundary)

            if result["min_distance"] < required_setback:
                violations.append(
                    {
                        "building_index": i,
                        "min_distance": result["min_distance"],
                        "required": required_setback,
                        "deficit": required_setback - result["min_distance"],
                    }
                )

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "total_buildings": len(buildings),
            "violation_count": len(violations),
        }
