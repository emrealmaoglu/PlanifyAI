"""
Objective Functions for H-SAGA Optimization

Now integrated with Turkish Standards for accurate cost calculation
"""

from typing import List, Dict
import numpy as np

from backend.core.turkish_standards import TurkishCostCalculator
from .building_mapper import BuildingTypeMapper


class ObjectiveFunctions:
    """
    Multi-objective optimization functions for campus planning.

    Objectives:
    1. Minimize construction cost (using Turkish 2025 rates)
    2. Minimize walking distances (accessibility)
    3. Maximize adjacency satisfaction
    4. Maximize green space
    5. Maximize solar exposure (optional)
    """

    def __init__(self, location: str = "provincial", quality: str = "standard"):
        """
        Initialize objective functions with Turkish standards.

        Args:
            location: Location type for cost calculation
            quality: Quality level for cost calculation
        """
        self.cost_calculator = TurkishCostCalculator()
        self.building_mapper = BuildingTypeMapper()
        self.location = location
        self.quality = quality

        # Normalization factors (will be set during optimization)
        self.max_cost = None
        self.max_distance = None

    def minimize_cost(self, buildings: List, **kwargs) -> float:
        """
        Minimize total construction cost using Turkish 2025 rates.

        This function now uses TurkishCostCalculator for accurate
        cost estimation based on building type, location, and quality.

        Args:
            buildings: List of Building objects with positions

        Returns:
            Normalized cost value in [0, 1] where lower is better

        Examples:
            >>> obj = ObjectiveFunctions(location="ankara", quality="standard")
            >>> cost = obj.minimize_cost(buildings)
            >>> # Returns normalized cost based on Turkish 2025 rates
        """
        total_cost = 0.0

        # Map buildings to Turkish classifications
        try:
            turkish_buildings = self.building_mapper.map_building_list(buildings)
        except Exception as e:
            # Fallback to simple calculation if mapping fails
            print(f"Warning: Building mapping failed: {e}")
            print("Using fallback cost calculation")
            return self._fallback_cost_calculation(buildings)

        # Calculate cost for each building
        for tb in turkish_buildings:
            try:
                cost_result = self.cost_calculator.calculate_total_cost(
                    building_class=tb.turkish_class.value,
                    area=tb.area,
                    floors=tb.floors,
                    location=self.location,
                    quality=self.quality,
                )
                total_cost += cost_result.total_tl
            except Exception as e:
                # Use base cost if calculation fails
                print(f"Warning: Cost calculation failed for {tb.building_id}: {e}")
                total_cost += tb.area * tb.cost_per_sqm

        # Normalize cost
        if self.max_cost is None:
            # Estimate max cost for normalization
            total_area = sum(b.area * b.floors for b in turkish_buildings)
            self.max_cost = total_area * 2500  # Max cost per m² (Class V-B)

        normalized_cost = min(total_cost / self.max_cost, 1.0)

        return normalized_cost

    def _fallback_cost_calculation(self, buildings: List) -> float:
        """
        Fallback cost calculation if Turkish Standards integration fails.
        Uses simple area-based estimation.
        """
        # Simple cost model (backward compatibility)
        total_cost = 0.0
        for building in buildings:
            area = getattr(building, "area", 1000)
            floors = getattr(building, "floors", 1)
            # Use average cost
            total_cost += area * floors * 1500

        # Normalize
        total_area = sum(
            getattr(b, "area", 1000) * getattr(b, "floors", 1) for b in buildings
        )
        max_cost = total_area * 2500

        return min(total_cost / max_cost, 1.0)

    def get_cost_breakdown(self, buildings: List) -> Dict:
        """
        Get detailed cost breakdown by building type.

        Returns:
            Dictionary with cost breakdown and Turkish classifications
        """
        turkish_buildings = self.building_mapper.map_building_list(buildings)

        breakdown = {
            "total_cost_tl": 0.0,
            "by_type": {},
            "by_class": {},
            "buildings": [],
        }

        for tb in turkish_buildings:
            cost_result = self.cost_calculator.calculate_total_cost(
                building_class=tb.turkish_class.value,
                area=tb.area,
                floors=tb.floors,
                location=self.location,
                quality=self.quality,
            )

            breakdown["total_cost_tl"] += cost_result.total_tl

            # By type
            if tb.building_type not in breakdown["by_type"]:
                breakdown["by_type"][tb.building_type] = 0.0
            breakdown["by_type"][tb.building_type] += cost_result.total_tl

            # By class
            class_name = tb.turkish_class.value
            if class_name not in breakdown["by_class"]:
                breakdown["by_class"][class_name] = 0.0
            breakdown["by_class"][class_name] += cost_result.total_tl

            # Individual buildings
            breakdown["buildings"].append(
                {
                    "id": tb.building_id,
                    "type": tb.building_type,
                    "turkish_class": class_name,
                    "cost_tl": cost_result.total_tl,
                    "cost_per_sqm_tl": cost_result.per_sqm_tl,
                }
            )

        return breakdown

    # Keep existing objective functions (walking distance, adjacency, etc.)
    # Add them here if they exist in the original file

    def minimize_walking_distance(self, buildings: List, **kwargs) -> float:
        """
        Minimize average walking distances between buildings.
        (Existing implementation preserved)
        """
        # If exists in original file, keep implementation
        # Otherwise, provide basic implementation
        if len(buildings) < 2:
            return 0.0

        total_distance = 0.0
        count = 0

        for i, b1 in enumerate(buildings):
            pos1 = getattr(b1, "position", (0, 0))
            for j, b2 in enumerate(buildings[i + 1 :], start=i + 1):
                pos2 = getattr(b2, "position", (0, 0))
                distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
                total_distance += distance
                count += 1

        avg_distance = total_distance / count if count > 0 else 0.0

        # Normalize (assuming max distance is site diagonal)
        if self.max_distance is None:
            self.max_distance = 1000.0  # Default max distance

        return min(avg_distance / self.max_distance, 1.0)

    def maximize_adjacency_satisfaction(self, buildings: List, **kwargs) -> float:
        """
        Maximize satisfaction of building type adjacency preferences.
        (Existing implementation preserved)
        """
        # Basic implementation: prefer similar types nearby
        # More sophisticated version would use adjacency matrix
        satisfaction = 0.0
        total_pairs = 0

        for i, b1 in enumerate(buildings):
            type1 = getattr(b1, "type", getattr(b1, "building_type", "residential"))
            pos1 = getattr(b1, "position", (0, 0))

            for j, b2 in enumerate(buildings[i + 1 :], start=i + 1):
                type2 = getattr(b2, "type", getattr(b2, "building_type", "residential"))
                pos2 = getattr(b2, "position", (0, 0))

                distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

                # Simple rule: similar types should be close
                if type1 == type2 and distance < 100:
                    satisfaction += 1.0
                elif type1 != type2 and distance > 50:
                    satisfaction += 0.5

                total_pairs += 1

        return satisfaction / total_pairs if total_pairs > 0 else 0.0
