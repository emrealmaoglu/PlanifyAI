"""
Unit tests for PAİY (Turkish Planning and Zoning) Compliance Module.

Tests Turkish building code validation:
- Setback calculations
- FAR (Floor Area Ratio) validation
- Green space requirements
- Height limits
- Construction costs
"""

import pytest
from shapely.geometry import box

from backend.core.regulatory.paiy_compliance import PAIYCompliance, PAIYConstants, ZoneType


class TestPAIYConstants:
    """Test PAİY regulation constants."""

    def test_constants_initialization(self):
        """Test that constants initialize with correct defaults."""
        constants = PAIYConstants()

        assert constants.BASE_SETBACK == 5.0
        assert constants.SETBACK_PER_FLOOR_ABOVE_4 == 0.5
        assert constants.MAX_HEIGHT_SETBACK == 15.0
        assert constants.MIN_GREEN_SPACE_RATIO == 0.30

    def test_far_limits_by_zone(self):
        """Test FAR limits for different zone types."""
        constants = PAIYConstants()

        assert constants.FAR_LIMITS[ZoneType.RESIDENTIAL_LOW] == 0.80
        assert constants.FAR_LIMITS[ZoneType.RESIDENTIAL_MID] == 1.50
        assert constants.FAR_LIMITS[ZoneType.RESIDENTIAL_HIGH] == 2.50
        assert constants.FAR_LIMITS[ZoneType.EDUCATIONAL] == 2.00
        assert constants.FAR_LIMITS[ZoneType.COMMERCIAL] == 3.00

    def test_height_limits_by_zone(self):
        """Test height limits for different zone types."""
        constants = PAIYConstants()

        assert constants.HEIGHT_LIMITS[ZoneType.RESIDENTIAL_LOW] == 12.5
        assert constants.HEIGHT_LIMITS[ZoneType.RESIDENTIAL_MID] == 21.5
        assert constants.HEIGHT_LIMITS[ZoneType.EDUCATIONAL] == 21.5

    def test_construction_costs(self):
        """Test construction cost constants from research."""
        constants = PAIYConstants()

        assert constants.CONSTRUCTION_COSTS["RESIDENTIAL"] == 1500
        assert constants.CONSTRUCTION_COSTS["EDUCATIONAL"] == 2000
        assert constants.CONSTRUCTION_COSTS["HEALTH"] == 2500


class TestSetbackCalculation:
    """Test setback distance calculations."""

    @pytest.fixture
    def checker(self):
        """Create PAİY compliance checker for educational zone."""
        return PAIYCompliance(zone_type=ZoneType.EDUCATIONAL, parcel_area=250000)  # 25 hectares

    def test_base_setback_low_rise(self, checker):
        """Test base 5m setback for buildings ≤4 floors."""
        setback = checker.calculate_required_setback(floors=4, height=14.0)
        assert setback == 5.0

    def test_incremental_setback_mid_rise(self, checker):
        """Test incremental setback for 5-10 floors."""
        # 6 floors: 5m + (6-4)*0.5m = 6m
        setback = checker.calculate_required_setback(floors=6, height=21.0)
        assert setback == 6.0

        # 8 floors: 5m + (8-4)*0.5m = 7m
        setback = checker.calculate_required_setback(floors=8, height=28.0)
        assert setback == 7.0

    def test_max_setback_high_rise(self, checker):
        """Test 15m cap for very tall buildings (>60.5m)."""
        setback = checker.calculate_required_setback(floors=20, height=70.0)
        assert setback == 15.0

    def test_setback_exactly_at_threshold(self, checker):
        """Test setback at 60.5m threshold."""
        # Just under threshold
        setback_under = checker.calculate_required_setback(floors=17, height=60.0)
        assert setback_under < 15.0

        # Just over threshold
        setback_over = checker.calculate_required_setback(floors=18, height=61.0)
        assert setback_over == 15.0


class TestFARValidation:
    """Test Floor Area Ratio (FAR) validation."""

    @pytest.fixture
    def checker(self):
        """Create checker for educational zone (FAR limit: 2.0)."""
        return PAIYCompliance(zone_type=ZoneType.EDUCATIONAL, parcel_area=10000)

    def test_far_compliant_with_exemption(self, checker):
        """Test compliant FAR with 30% exemption."""
        buildings = [
            {"area": 1000, "floors": 2},  # 2,000 m²
            {"area": 1000, "floors": 2},  # 2,000 m²
            {"area": 1000, "floors": 2},  # 2,000 m²
        ]
        # Total: 6,000 m²
        # With 30% exemption: 4,200 m² taxable
        # FAR: 4,200 / 10,000 = 0.42

        result = checker.validate_far(buildings, apply_exemption=True)

        assert result["compliant"] is True
        assert result["total_floor_area"] == 6000
        assert result["exemption_area"] == 1800
        assert result["taxable_area"] == 4200
        assert result["actual_far"] == 0.42
        assert result["allowed_far"] == 2.0

    def test_far_violation_without_exemption(self, checker):
        """Test FAR violation when exemption not applied."""
        buildings = [{"area": 1500, "floors": 8}]  # 12,000 m²
        # Without exemption: FAR = 12,000 / 10,000 = 1.2

        result = checker.validate_far(buildings, apply_exemption=False)

        assert result["taxable_area"] == 12000
        assert result["actual_far"] == 1.2

    def test_far_exactly_at_limit(self, checker):
        """Test FAR exactly at allowed limit (2.0)."""
        # Need 20,000 m² total floor area for FAR = 2.0
        # With 30% exemption: taxable = 14,000 m²
        # FAR = 14,000 / 10,000 = 1.4 (compliant)
        # So we need: taxable = 20,000 for FAR = 2.0
        # Total = 20,000 / 0.7 = 28,571 m²

        buildings = [{"area": 2857, "floors": 10}]  # 28,570 m²

        result = checker.validate_far(buildings, apply_exemption=True)

        # Should be very close to limit
        assert 1.99 <= result["actual_far"] <= 2.01

    def test_turkish_exemption_rule(self, checker):
        """Test that Turkish 30% exemption is applied correctly."""
        buildings = [{"area": 1000, "floors": 10}]  # 10,000 m²

        result = checker.validate_far(buildings, apply_exemption=True)

        # Exemption should be exactly 30%
        assert result["exemption_area"] == 3000
        assert result["taxable_area"] == 7000


class TestGreenSpaceValidation:
    """Test green space requirement validation."""

    @pytest.fixture
    def checker(self):
        """Create checker with 10,000 m² parcel."""
        return PAIYCompliance(zone_type=ZoneType.EDUCATIONAL, parcel_area=10000)

    def test_green_space_compliant(self, checker):
        """Test compliant green space (≥30%)."""
        # Buildings cover 6,000 m², leaving 4,000 m² (40%)
        buildings = [
            box(0, 0, 50, 40),  # 2,000 m²
            box(100, 100, 150, 140),  # 2,000 m²
            box(200, 200, 250, 240),  # 2,000 m²
        ]

        result = checker.validate_green_space(buildings)

        assert result["compliant"] is True
        assert result["green_space_area"] == 4000
        assert result["green_space_ratio"] == pytest.approx(0.4)
        assert result["margin"] == pytest.approx(0.1)  # 40% - 30%

    def test_green_space_violation(self, checker):
        """Test green space violation (<30%)."""
        # Buildings cover 8,000 m², leaving only 2,000 m² (20%)
        buildings = [
            box(0, 0, 100, 80),  # 8,000 m²
        ]

        result = checker.validate_green_space(buildings)

        assert result["compliant"] is False
        assert result["green_space_ratio"] == pytest.approx(0.2)
        assert result["margin"] == pytest.approx(-0.1)  # 20% - 30%

    def test_green_space_exactly_at_limit(self, checker):
        """Test green space exactly at 30% minimum."""
        # Buildings cover 7,000 m², leaving 3,000 m² (30%)
        buildings = [box(0, 0, 70, 100)]  # 7,000 m²

        result = checker.validate_green_space(buildings)

        assert result["compliant"] is True
        assert abs(result["green_space_ratio"] - 0.30) < 0.01


class TestHeightLimitValidation:
    """Test building height limit validation."""

    @pytest.fixture
    def checker(self):
        """Create checker for educational zone (21.5m limit)."""
        return PAIYCompliance(zone_type=ZoneType.EDUCATIONAL, parcel_area=10000)

    def test_height_compliant(self, checker):
        """Test compliant building heights."""
        buildings = [
            {"height": 14.0, "floors": 4},
            {"height": 21.0, "floors": 6},
        ]

        result = checker.validate_height_limits(buildings)

        assert result["compliant"] is True
        assert result["max_allowed_height"] == 21.5
        assert len(result["violations"]) == 0

    def test_height_violation(self, checker):
        """Test height limit violation."""
        buildings = [
            {"height": 14.0, "floors": 4},
            {"height": 28.0, "floors": 8},  # Exceeds 21.5m
        ]

        result = checker.validate_height_limits(buildings)

        assert result["compliant"] is False
        assert len(result["violations"]) == 1
        assert result["violations"][0]["building_index"] == 1
        assert result["violations"][0]["excess"] == 6.5  # 28.0 - 21.5

    def test_height_estimated_from_floors(self, checker):
        """Test height estimation when not provided (3.5m per floor)."""
        buildings = [{"floors": 7}]  # Estimated: 24.5m (exceeds 21.5m)

        result = checker.validate_height_limits(buildings)

        assert result["compliant"] is False
        assert len(result["violations"]) == 1


class TestConstructionCost:
    """Test construction cost calculation."""

    @pytest.fixture
    def checker(self):
        """Create checker."""
        return PAIYCompliance(zone_type=ZoneType.EDUCATIONAL, parcel_area=10000)

    def test_cost_single_building(self, checker):
        """Test cost for single building."""
        buildings = [
            {"type": "RESIDENTIAL", "area": 1000, "floors": 4}
            # 1000 * 4 * 1500 = 6,000,000 TL
        ]

        cost = checker.calculate_construction_cost(buildings)

        assert cost == 6_000_000

    def test_cost_multiple_types(self, checker):
        """Test cost for mixed building types."""
        buildings = [
            {"type": "RESIDENTIAL", "area": 1000, "floors": 2},  # 3,000,000 TL
            {"type": "EDUCATIONAL", "area": 1000, "floors": 2},  # 4,000,000 TL
            {"type": "HEALTH", "area": 500, "floors": 2},  # 2,500,000 TL
        ]

        cost = checker.calculate_construction_cost(buildings)

        assert cost == 9_500_000

    def test_cost_default_type(self, checker):
        """Test default cost when type unknown."""
        buildings = [{"type": "UNKNOWN", "area": 1000, "floors": 1}]

        cost = checker.calculate_construction_cost(buildings)

        # Should default to residential (1,500 TL/m²)
        assert cost == 1_500_000

    def test_cost_from_research_constants(self, checker):
        """Test that costs match research constants."""
        # Test all 9 building types from research
        types_and_costs = [
            ("RESIDENTIAL", 1500),
            ("EDUCATIONAL", 2000),
            ("ADMINISTRATIVE", 1800),
            ("HEALTH", 2500),
            ("SOCIAL", 1600),
            ("COMMERCIAL", 2200),
            ("LIBRARY", 2300),
            ("SPORTS", 1900),
            ("DINING", 1700),
        ]

        for building_type, expected_cost_per_sqm in types_and_costs:
            buildings = [{"type": building_type, "area": 1000, "floors": 1}]

            cost = checker.calculate_construction_cost(buildings)

            assert cost == expected_cost_per_sqm * 1000


class TestZoneTypeFARLimits:
    """Test FAR limits for different zone types."""

    def test_residential_low_far(self):
        """Test low-density residential FAR (0.80)."""
        checker = PAIYCompliance(zone_type=ZoneType.RESIDENTIAL_LOW, parcel_area=10000)

        # Just under limit
        buildings = [{"area": 1000, "floors": 4}]  # FAR ≈ 0.28 (with exemption)
        result = checker.validate_far(buildings)
        assert result["compliant"] is True

    def test_residential_high_far(self):
        """Test high-density residential FAR (2.50)."""
        checker = PAIYCompliance(zone_type=ZoneType.RESIDENTIAL_HIGH, parcel_area=10000)

        # Higher building allowed
        buildings = [{"area": 2000, "floors": 6}]  # FAR ≈ 0.84 (with exemption)
        result = checker.validate_far(buildings)
        assert result["compliant"] is True

    def test_commercial_far(self):
        """Test commercial zone FAR (3.00)."""
        checker = PAIYCompliance(zone_type=ZoneType.COMMERCIAL, parcel_area=10000)

        # Very high density allowed
        buildings = [{"area": 2000, "floors": 10}]  # FAR ≈ 1.4 (with exemption)
        result = checker.validate_far(buildings)
        assert result["compliant"] is True
