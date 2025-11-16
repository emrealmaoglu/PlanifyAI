"""
Unit tests for Turkish construction cost calculator
Target: 90%+ coverage
"""

import pytest
from backend.core.turkish_standards import (
    TurkishCostCalculator,
    ConstructionCost,
)


class TestTurkishCostCalculator:
    """Test suite for cost calculation"""

    @pytest.fixture
    def calculator(self):
        """Fixture: cost calculator instance"""
        return TurkishCostCalculator()

    def test_calculate_basic_cost(self, calculator):
        """Test basic cost calculation"""
        cost = calculator.calculate_total_cost("V-A", 5000, 4)
        assert isinstance(cost, ConstructionCost)
        assert cost.total_tl == 5000 * 2000  # area × base_cost
        assert cost.per_sqm_tl == 2000

    def test_calculate_cost_iii_a(self, calculator):
        """Test cost calculation for III-A class"""
        cost = calculator.calculate_total_cost("III-A", 3000, 3)
        assert cost.total_tl == 3000 * 1500
        assert cost.per_sqm_tl == 1500

    def test_calculate_cost_v_b(self, calculator):
        """Test cost calculation for V-B class"""
        cost = calculator.calculate_total_cost("V-B", 4000, 5)
        assert cost.total_tl == 4000 * 2500
        assert cost.per_sqm_tl == 2500

    def test_calculate_with_location_factor_istanbul(self, calculator):
        """Test cost calculation with Istanbul location"""
        cost_istanbul = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="istanbul"
        )
        cost_provincial = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="provincial"
        )

        assert cost_istanbul.total_tl > cost_provincial.total_tl
        assert cost_istanbul.location_factor == 1.3
        assert cost_provincial.location_factor == 1.0

    def test_calculate_with_location_factor_ankara(self, calculator):
        """Test cost calculation with Ankara location"""
        cost_ankara = calculator.calculate_total_cost("V-A", 5000, 4, location="ankara")
        cost_provincial = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="provincial"
        )

        assert cost_ankara.total_tl > cost_provincial.total_tl
        assert cost_ankara.location_factor == 1.2

    def test_calculate_with_location_factor_izmir(self, calculator):
        """Test cost calculation with Izmir location"""
        cost_izmir = calculator.calculate_total_cost("V-A", 5000, 4, location="izmir")
        assert cost_izmir.location_factor == 1.15

    def test_calculate_with_location_factor_rural(self, calculator):
        """Test cost calculation with rural location"""
        cost_rural = calculator.calculate_total_cost("V-A", 5000, 4, location="rural")
        cost_provincial = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="provincial"
        )

        assert cost_rural.total_tl < cost_provincial.total_tl
        assert cost_rural.location_factor == 0.9

    def test_calculate_with_quality_factor_luxury(self, calculator):
        """Test cost with luxury quality"""
        cost_luxury = calculator.calculate_total_cost("V-A", 5000, 4, quality="luxury")
        cost_standard = calculator.calculate_total_cost(
            "V-A", 5000, 4, quality="standard"
        )

        assert cost_luxury.total_tl > cost_standard.total_tl
        assert cost_luxury.quality_factor == 1.5

    def test_calculate_with_quality_factor_economy(self, calculator):
        """Test cost with economy quality"""
        cost_economy = calculator.calculate_total_cost(
            "V-A", 5000, 4, quality="economy"
        )
        cost_standard = calculator.calculate_total_cost(
            "V-A", 5000, 4, quality="standard"
        )

        assert cost_economy.total_tl < cost_standard.total_tl
        assert cost_economy.quality_factor == 0.8

    def test_calculate_with_both_factors(self, calculator):
        """Test cost with both location and quality factors"""
        cost = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="istanbul", quality="luxury"
        )
        assert cost.location_factor == 1.3
        assert cost.quality_factor == 1.5
        # Base: 2000 * 5000 = 10,000,000
        # With factors: 10,000,000 * 1.3 * 1.5 = 19,500,000
        assert cost.total_tl == 2000 * 5000 * 1.3 * 1.5

    def test_invalid_building_class(self, calculator):
        """Test error on invalid building class"""
        with pytest.raises(ValueError, match="Invalid building class"):
            calculator.calculate_total_cost("INVALID", 5000, 4)

    def test_invalid_location(self, calculator):
        """Test error on invalid location"""
        with pytest.raises(ValueError, match="Invalid location"):
            calculator.calculate_total_cost("V-A", 5000, 4, location="invalid")

    def test_invalid_quality(self, calculator):
        """Test error on invalid quality"""
        with pytest.raises(ValueError, match="Invalid quality"):
            calculator.calculate_total_cost("V-A", 5000, 4, quality="invalid")

    def test_zero_area(self, calculator):
        """Test error on zero area"""
        with pytest.raises(ValueError, match="Area must be positive"):
            calculator.calculate_total_cost("V-A", 0, 4)

    def test_negative_area(self, calculator):
        """Test error on negative area"""
        with pytest.raises(ValueError, match="Area must be positive"):
            calculator.calculate_total_cost("V-A", -100, 4)

    def test_zero_floors(self, calculator):
        """Test error on zero floors"""
        with pytest.raises(ValueError, match="Floors must be >= 1"):
            calculator.calculate_total_cost("V-A", 5000, 0)

    def test_negative_floors(self, calculator):
        """Test error on negative floors"""
        with pytest.raises(ValueError, match="Floors must be >= 1"):
            calculator.calculate_total_cost("V-A", 5000, -1)

    def test_get_base_cost(self, calculator):
        """Test getting base cost per m²"""
        cost = calculator.get_base_cost_per_sqm("V-A")
        assert cost == 2000.0

    def test_get_base_cost_iii_a(self, calculator):
        """Test getting base cost for III-A"""
        cost = calculator.get_base_cost_per_sqm("III-A")
        assert cost == 1500.0

    def test_get_base_cost_v_b(self, calculator):
        """Test getting base cost for V-B"""
        cost = calculator.get_base_cost_per_sqm("V-B")
        assert cost == 2500.0

    def test_get_base_cost_invalid(self, calculator):
        """Test error on invalid building class for base cost"""
        with pytest.raises(ValueError, match="Invalid building class"):
            calculator.get_base_cost_per_sqm("INVALID")

    def test_compare_costs(self, calculator):
        """Test cost comparison between classes"""
        comparison = calculator.compare_costs("III-A", "V-A", 5000)

        assert comparison["cost_a_tl"] < comparison["cost_b_tl"]
        assert comparison["cheaper"] == "III-A"
        assert comparison["difference_tl"] > 0
        assert comparison["class_a"] == "III-A"
        assert comparison["class_b"] == "V-A"

    def test_compare_costs_reverse(self, calculator):
        """Test cost comparison in reverse order"""
        comparison = calculator.compare_costs("V-A", "III-A", 5000)

        assert comparison["cost_a_tl"] > comparison["cost_b_tl"]
        assert comparison["cheaper"] == "III-A"

    def test_compare_costs_same_class(self, calculator):
        """Test cost comparison with same class"""
        comparison = calculator.compare_costs("V-A", "V-A", 5000)

        assert comparison["cost_a_tl"] == comparison["cost_b_tl"]
        assert comparison["difference_tl"] == 0

    def test_cost_breakdown(self, calculator):
        """Test cost breakdown structure"""
        cost = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="ankara", quality="luxury"
        )

        assert "base_cost_tl" in cost.breakdown
        assert "location_adjustment_tl" in cost.breakdown
        assert "quality_adjustment_tl" in cost.breakdown

    def test_cost_breakdown_values(self, calculator):
        """Test cost breakdown values are correct"""
        cost = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="ankara", quality="standard"
        )

        base_cost = 2000 * 5000
        assert cost.breakdown["base_cost_tl"] == base_cost
        # Location adjustment: base * (1.2 - 1) = base * 0.2
        assert abs(cost.breakdown["location_adjustment_tl"] - base_cost * 0.2) < 0.01
        # Quality adjustment: base * 1.2 * (1.0 - 1) = 0
        assert abs(cost.breakdown["quality_adjustment_tl"]) < 0.01

    def test_cost_str_representation(self, calculator):
        """Test string representation of ConstructionCost"""
        cost = calculator.calculate_total_cost("V-A", 5000, 4)
        cost_str = str(cost)
        assert "ConstructionCost" in cost_str
        assert "TL" in cost_str
        assert "V-A" in cost_str

    def test_cost_attributes(self, calculator):
        """Test all cost attributes are set correctly"""
        cost = calculator.calculate_total_cost(
            "V-A", 5000, 4, location="ankara", quality="luxury"
        )

        assert cost.building_class == "V-A"
        assert cost.area_sqm == 5000
        assert cost.floors == 4
        assert cost.location_factor == 1.2
        assert cost.quality_factor == 1.5
        assert cost.total_tl > 0
        assert cost.per_sqm_tl > 0

    @pytest.mark.parametrize(
        "building_class,expected_cost_per_sqm",
        [
            ("I-A", 800),
            ("II-B", 1200),
            ("III-A", 1500),
            ("III-B", 1800),
            ("IV-A", 2000),
            ("IV-B", 1800),
            ("V-A", 2000),
            ("V-B", 2500),
            ("V-C", 2200),
        ],
    )
    def test_base_costs_parametrized(
        self, calculator, building_class, expected_cost_per_sqm
    ):
        """Parametrized test for base costs"""
        cost = calculator.get_base_cost_per_sqm(building_class)
        assert cost == expected_cost_per_sqm

    @pytest.mark.parametrize(
        "location,expected_factor",
        [
            ("istanbul", 1.3),
            ("ankara", 1.2),
            ("izmir", 1.15),
            ("other_metropolitan", 1.1),
            ("provincial", 1.0),
            ("rural", 0.9),
        ],
    )
    def test_location_factors_parametrized(self, calculator, location, expected_factor):
        """Parametrized test for location factors"""
        cost = calculator.calculate_total_cost("V-A", 1000, 2, location=location)
        assert cost.location_factor == expected_factor

    @pytest.mark.parametrize(
        "quality,expected_factor",
        [
            ("luxury", 1.5),
            ("standard", 1.0),
            ("economy", 0.8),
        ],
    )
    def test_quality_factors_parametrized(self, calculator, quality, expected_factor):
        """Parametrized test for quality factors"""
        cost = calculator.calculate_total_cost("V-A", 1000, 2, quality=quality)
        assert cost.quality_factor == expected_factor

    def test_small_area(self, calculator):
        """Test cost calculation with small area"""
        cost = calculator.calculate_total_cost("V-A", 10, 1)
        assert cost.total_tl == 10 * 2000

    def test_large_area(self, calculator):
        """Test cost calculation with large area"""
        cost = calculator.calculate_total_cost("V-A", 100000, 10)
        assert cost.total_tl == 100000 * 2000

    def test_single_floor(self, calculator):
        """Test cost calculation with single floor"""
        cost = calculator.calculate_total_cost("V-A", 5000, 1)
        assert cost.floors == 1
        assert cost.total_tl > 0
