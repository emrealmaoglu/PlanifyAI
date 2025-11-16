"""
Turkish Construction Cost Calculator

Based on 2025 Ministry of Environment official rates
"""

from typing import Dict
from dataclasses import dataclass, field

from .data import BUILDING_CLASSES, COST_FACTORS


@dataclass
class ConstructionCost:
    """
    Detailed construction cost breakdown.

    Attributes:
        total_tl: Total construction cost in Turkish Lira
        per_sqm_tl: Cost per square meter
        building_class: Turkish building class code
        area_sqm: Total building area
        floors: Number of floors
        location_factor: Location cost multiplier
        quality_factor: Quality cost multiplier
        breakdown: Cost component breakdown
    """

    total_tl: float
    per_sqm_tl: float
    building_class: str
    area_sqm: float
    floors: int
    location_factor: float = 1.0
    quality_factor: float = 1.0
    breakdown: Dict[str, float] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"ConstructionCost("
            f"total={self.total_tl:,.0f} TL, "
            f"per_sqm={self.per_sqm_tl:,.0f} TL/m², "
            f"class={self.building_class})"
        )


class TurkishCostCalculator:
    """
    Calculates construction costs for Turkish buildings.
    Based on 2025 official Ministry rates (Yapı Yaklaşık Birim Maliyetleri).

    Usage:
        >>> calculator = TurkishCostCalculator()
        >>> cost = calculator.calculate_total_cost("V-A", 5000, 4)
        >>> print(f"Total: {cost.total_tl:,.0f} TL")
        Total: 10,000,000 TL
    """

    def __init__(self):
        """Initialize cost calculator with 2025 rates"""
        self._classes = BUILDING_CLASSES
        self._location_factors = COST_FACTORS["location"]
        self._quality_factors = COST_FACTORS["quality"]

    def calculate_total_cost(
        self,
        building_class: str,
        area: float,
        floors: int,
        location: str = "provincial",
        quality: str = "standard",
    ) -> ConstructionCost:
        """
        Calculate total construction cost.

        Args:
            building_class: Turkish building class (e.g., "V-A", "III-A")
            area: Total building area in m²
            floors: Number of floors
            location: Location type (istanbul, ankara, izmir, provincial, rural)
            quality: Quality level (luxury, standard, economy)

        Returns:
            ConstructionCost with complete breakdown

        Raises:
            ValueError: If building_class, location, or quality invalid

        Examples:
            >>> calculator = TurkishCostCalculator()
            >>> cost = calculator.calculate_total_cost(
            ...     "V-A", 5000, 4, "ankara", "standard"
            ... )
            >>> assert cost.total_tl > 10_000_000
        """
        # Validate inputs
        if building_class not in self._classes:
            raise ValueError(f"Invalid building class: {building_class}")

        if location not in self._location_factors:
            raise ValueError(
                f"Invalid location: {location}. "
                f"Valid: {list(self._location_factors.keys())}"
            )

        if quality not in self._quality_factors:
            raise ValueError(
                f"Invalid quality: {quality}. "
                f"Valid: {list(self._quality_factors.keys())}"
            )

        if area <= 0:
            raise ValueError(f"Area must be positive, got: {area}")

        if floors < 1:
            raise ValueError(f"Floors must be >= 1, got: {floors}")

        # Get base cost per m²
        base_cost_per_sqm = self._classes[building_class]["cost_per_sqm_tl"]

        # Apply location and quality factors
        location_factor = self._location_factors[location]
        quality_factor = self._quality_factors[quality]

        # Calculate adjusted cost per m²
        adjusted_cost_per_sqm = base_cost_per_sqm * location_factor * quality_factor

        # Calculate total cost
        total_cost = adjusted_cost_per_sqm * area

        # Calculate breakdown
        breakdown = {
            "base_cost_tl": base_cost_per_sqm * area,
            "location_adjustment_tl": base_cost_per_sqm * area * (location_factor - 1),
            "quality_adjustment_tl": base_cost_per_sqm
            * area
            * location_factor
            * (quality_factor - 1),
        }

        return ConstructionCost(
            total_tl=total_cost,
            per_sqm_tl=adjusted_cost_per_sqm,
            building_class=building_class,
            area_sqm=area,
            floors=floors,
            location_factor=location_factor,
            quality_factor=quality_factor,
            breakdown=breakdown,
        )

    def get_base_cost_per_sqm(self, building_class: str) -> float:
        """
        Get base construction cost per m² for a building class.

        Args:
            building_class: Building class code (e.g., "V-A")

        Returns:
            Base cost in TL/m² (2025 rates)

        Raises:
            ValueError: If building_class invalid

        Examples:
            >>> calculator = TurkishCostCalculator()
            >>> calculator.get_base_cost_per_sqm("V-A")
            2000.0
        """
        if building_class not in self._classes:
            raise ValueError(f"Invalid building class: {building_class}")

        return self._classes[building_class]["cost_per_sqm_tl"]

    def compare_costs(
        self,
        building_class_a: str,
        building_class_b: str,
        area: float,
    ) -> Dict[str, float]:
        """
        Compare costs between two building classes.

        Args:
            building_class_a: First building class
            building_class_b: Second building class
            area: Building area in m²

        Returns:
            Dictionary with cost comparison

        Examples:
            >>> calculator = TurkishCostCalculator()
            >>> comparison = calculator.compare_costs("III-A", "V-A", 5000)
            >>> assert comparison["difference_tl"] > 0
        """
        cost_a = self.calculate_total_cost(building_class_a, area, 1)
        cost_b = self.calculate_total_cost(building_class_b, area, 1)

        return {
            "class_a": building_class_a,
            "class_b": building_class_b,
            "cost_a_tl": cost_a.total_tl,
            "cost_b_tl": cost_b.total_tl,
            "difference_tl": abs(cost_a.total_tl - cost_b.total_tl),
            "cheaper": (
                building_class_a
                if cost_a.total_tl < cost_b.total_tl
                else building_class_b
            ),
        }
