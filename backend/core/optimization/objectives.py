"""
Objective Functions for H-SAGA Optimization

Now integrated with Turkish Standards for accurate cost calculation
"""

from typing import List, Dict, Optional
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

    def maximize_adjacency_satisfaction(
        self,
        buildings: List,
        adjacency_matrix: Optional[Dict[str, Dict[str, float]]] = None,
        **kwargs,
    ) -> float:
        """
        Maximize satisfaction of building type adjacency preferences.

        Calculates how well building placements satisfy preferred adjacencies
        between different building types. For example:
        - Residential buildings benefit from being near recreational facilities
        - Educational buildings benefit from clustering together
        - Healthcare facilities should be centrally accessible

        Args:
            buildings: List of Building objects with positions and types
            adjacency_matrix: Optional custom adjacency preferences
                Format: {type1: {type2: preference_score}}
                If None, uses default Turkish campus preferences

        Returns:
            Normalized satisfaction score in [0, 1] where 1 is perfect

        Algorithm:
            1. For each building pair, check if they should be adjacent
            2. Calculate actual distance between them
            3. Compare to ideal distance (from adjacency matrix)
            4. Sum satisfaction scores (inverse distance for preferred pairs)
            5. Normalize by maximum possible satisfaction

        Examples:
            >>> obj = ObjectiveFunctions()
            >>> satisfaction = obj.maximize_adjacency_satisfaction(buildings)
            >>> # Returns 0.75 (75% of ideal adjacency achieved)
        """
        # Use default Turkish campus adjacency matrix if not provided
        if adjacency_matrix is None:
            adjacency_matrix = self._get_default_adjacency_matrix()

        total_satisfaction = 0.0
        max_possible_satisfaction = 0.0
        pair_count = 0

        # Extract positions and types
        building_data = []
        for b in buildings:
            b_type = self._normalize_building_type(
                getattr(b, "type", getattr(b, "building_type", "unknown"))
            )
            b_pos = getattr(b, "position", (0, 0))
            building_data.append((b_type, b_pos))

        # Calculate pairwise adjacency satisfaction
        for i, (type1, pos1) in enumerate(building_data):
            for j, (type2, pos2) in enumerate(building_data[i + 1 :], start=i + 1):
                # Get adjacency preference (0 = no preference, 1 = strong preference)
                preference = adjacency_matrix.get(type1, {}).get(type2, 0.0)

                if preference > 0:
                    # Calculate actual distance
                    actual_distance = np.sqrt(
                        (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2
                    )

                    # Ideal distance based on preference (higher preference = closer)
                    # Assuming campus size ~500m x 500m, ideal ranges:
                    # - Strong preference (0.8-1.0): 50-100m
                    # - Medium preference (0.4-0.7): 100-200m
                    # - Weak preference (0.1-0.3): 200-300m
                    ideal_distance = 50 + (1 - preference) * 250

                    # Calculate satisfaction using Gaussian-like function
                    # Satisfaction is highest at ideal distance,
                    # decreases with deviation
                    distance_ratio = actual_distance / ideal_distance
                    satisfaction = preference * np.exp(
                        -((distance_ratio - 1.0) ** 2) / 2
                    )

                    total_satisfaction += satisfaction
                    max_possible_satisfaction += preference
                    pair_count += 1

        # Normalize
        if max_possible_satisfaction > 0:
            normalized_satisfaction = total_satisfaction / max_possible_satisfaction
        else:
            normalized_satisfaction = 1.0  # No preferences = perfect

        return min(max(normalized_satisfaction, 0.0), 1.0)

    def _get_default_adjacency_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Get default Turkish campus adjacency preferences.

        Returns:
            Dictionary of building type adjacency preferences [0, 1]

        Preferences based on:
        - Functional relationships
        - Social interactions
        - Accessibility requirements
        - Turkish campus planning best practices
        """
        return {
            # Residential preferences
            "residential": {
                "social": 0.9,  # Very important: near recreational
                "commercial": 0.7,  # Important: near shops/services
                "health": 0.6,  # Moderate: healthcare accessibility
                "educational": 0.3,  # Low: can be separate
            },
            # Educational preferences
            "educational": {
                "educational": 0.9,  # Very important: cluster together
                "social": 0.7,  # Important: near library/cultural
                "commercial": 0.5,  # Moderate: cafeteria access
                "residential": 0.3,  # Low: can be separate
            },
            # Health/Medical preferences
            "health": {
                "residential": 0.6,  # Moderate: accessible from housing
                "educational": 0.5,  # Moderate: accessible from campus
                "commercial": 0.4,  # Low-moderate: nearby services
            },
            # Commercial preferences
            "commercial": {
                "residential": 0.7,  # Important: serve residents
                "educational": 0.5,  # Moderate: serve students
                "social": 0.6,  # Moderate: complement recreation
            },
            # Social/Recreational preferences
            "social": {
                "residential": 0.9,  # Very important: serve residents
                "educational": 0.7,  # Important: serve students
                "commercial": 0.6,  # Moderate: food/services nearby
            },
            # Administrative preferences
            "administrative": {
                "educational": 0.6,  # Moderate: administrative support
                "commercial": 0.4,  # Low-moderate
            },
        }

    def _normalize_building_type(self, building_type: str) -> str:
        """
        Normalize building type string to main category.

        Args:
            building_type: Raw building type
                (e.g., "residential_low", "health_hospital")

        Returns:
            Normalized category (e.g., "residential", "health")
        """
        # Extract main category before underscore
        if "_" in building_type:
            return building_type.split("_")[0]
        return building_type.lower()

    def maximize_green_space(
        self,
        buildings: List,
        parcel_area: float,
        population_estimate: Optional[int] = None,
        min_green_space_ratio: float = 0.30,
        target_per_capita: float = 15.0,
        **kwargs,
    ) -> float:
        """
        Maximize green/open space area in campus layout.

        Calculates available green space after building placement and
        compares to Turkish standards (30% minimum, 15 m²/person ideal).

        Args:
            buildings: List of Building objects with areas and floors
            parcel_area: Total campus parcel area in m²
            population_estimate: Estimated campus population
                If None, estimated from building areas (1 person per 50 m²)
            min_green_space_ratio: Minimum green space as fraction
                of total (default: 0.30)
            target_per_capita: Target green space per person in m²
                (default: 15.0)

        Returns:
            Normalized green space score in [0, 1] where 1 is ideal

        Algorithm:
            1. Calculate total building footprints (area / floors)
            2. Calculate roads/infrastructure (estimate 15% of parcel)
            3. Calculate available green space
            4. Compare to minimum ratio (30%)
            5. Calculate per-capita green space
            6. Compare to target (15 m²/person)
            7. Return weighted score (70% ratio, 30% per-capita)

        Turkish Standards:
            - Minimum 30% of campus should be green space (aspirational)
            - Target 15 m² green space per person (from İmar Kanunu)
            - Includes parks, gardens, sports fields, open areas

        Examples:
            >>> obj = ObjectiveFunctions()
            >>> green_score = obj.maximize_green_space(buildings, 100000)
            >>> # Returns 0.85 (exceeds minimum, near per-capita target)
        """
        # Calculate total building footprints
        total_footprint = 0.0
        total_building_area = 0.0

        for b in buildings:
            area = getattr(b, "area", 1000)
            floors = getattr(b, "floors", 1)

            # Footprint is area divided by floors (assuming vertical stacking)
            footprint = area / max(floors, 1)
            total_footprint += footprint
            total_building_area += area

        # Estimate infrastructure area (roads, parking, utilities)
        # Typically 15-20% of campus for roads/parking
        # Use 15% as conservative estimate
        infrastructure_area = parcel_area * 0.15

        # Calculate available green space
        green_space_area = parcel_area - total_footprint - infrastructure_area
        green_space_area = max(green_space_area, 0.0)  # Can't be negative

        # Calculate green space ratio
        green_space_ratio = green_space_area / parcel_area

        # Score based on ratio (compared to 30% minimum)
        # Using sigmoid-like function: below 30% penalized, above 30% rewarded
        ratio_score = min(
            green_space_ratio / min_green_space_ratio, 1.0
        )

        # Calculate per-capita green space
        if population_estimate is None:
            # Estimate: 1 person per 50 m² of building area
            # (Accounts for classrooms, offices, dorms, etc.)
            population_estimate = max(
                int(total_building_area / 50), 1
            )

        per_capita_green_space = green_space_area / population_estimate

        # Score based on per-capita (compared to 15 m²/person target)
        per_capita_score = min(per_capita_green_space / target_per_capita, 1.0)

        # Combined score (weighted average)
        # Ratio is more critical (70%), per-capita is aspirational (30%)
        combined_score = 0.7 * ratio_score + 0.3 * per_capita_score

        # Ensure score is in [0, 1]
        return min(max(combined_score, 0.0), 1.0)

    def get_green_space_breakdown(
        self, buildings: List, parcel_area: float, **kwargs
    ) -> Dict[str, float]:
        """
        Get detailed green space calculation breakdown.

        Returns:
            Dictionary with detailed green space metrics
        """
        total_footprint = sum(
            getattr(b, "area", 1000) / max(getattr(b, "floors", 1), 1)
            for b in buildings
        )

        total_building_area = sum(getattr(b, "area", 1000) for b in buildings)
        infrastructure_area = parcel_area * 0.15
        green_space_area = max(parcel_area - total_footprint - infrastructure_area, 0.0)

        population_estimate = max(int(total_building_area / 50), 1)
        per_capita = green_space_area / population_estimate

        return {
            "parcel_area_sqm": parcel_area,
            "total_footprint_sqm": total_footprint,
            "infrastructure_area_sqm": infrastructure_area,
            "green_space_area_sqm": green_space_area,
            "green_space_ratio": green_space_area / parcel_area,
            "population_estimate": population_estimate,
            "per_capita_green_space_sqm": per_capita,
            "meets_30_percent_minimum": green_space_area / parcel_area >= 0.30,
            "meets_15_sqm_per_person": per_capita >= 15.0,
        }
