"""
Unit tests for Setback Calculator.

Tests dynamic setback calculations for Turkish building codes.
"""

import pytest
from shapely.geometry import box

from backend.core.regulatory.setback_calculator import SetbackCalculator, SetbackRules


class TestSetbackRules:
    """Test setback rule configuration."""

    def test_default_rules(self):
        """Test default Turkish setback rules."""
        rules = SetbackRules()

        assert rules.base_setback == 5.0
        assert rules.floor_increment == 0.5
        assert rules.floor_threshold == 4
        assert rules.max_setback == 15.0

    def test_custom_rules(self):
        """Test custom setback rules."""
        rules = SetbackRules(
            base_setback=10.0, floor_increment=1.0, floor_threshold=3, max_setback=20.0
        )

        assert rules.base_setback == 10.0
        assert rules.floor_increment == 1.0


class TestBasicSetbackCalculation:
    """Test basic setback calculations."""

    @pytest.fixture
    def calc(self):
        """Create calculator with default Turkish rules."""
        return SetbackCalculator()

    def test_base_setback_low_rise(self, calc):
        """Test base 5m setback for ≤4 floors."""
        assert calc.calculate(floors=1) == 5.0
        assert calc.calculate(floors=2) == 5.0
        assert calc.calculate(floors=3) == 5.0
        assert calc.calculate(floors=4) == 5.0

    def test_incremental_setback(self, calc):
        """Test +0.5m per floor above 4."""
        # 5 floors: 5.0 + (5-4)*0.5 = 5.5m
        assert calc.calculate(floors=5) == 5.5

        # 6 floors: 5.0 + (6-4)*0.5 = 6.0m
        assert calc.calculate(floors=6) == 6.0

        # 10 floors: 5.0 + (10-4)*0.5 = 8.0m
        assert calc.calculate(floors=10) == 8.0

    def test_max_setback_cap(self, calc):
        """Test 15m maximum setback cap."""
        # 30 floors would normally be: 5.0 + (30-4)*0.5 = 18.0m
        # But capped at 15.0m
        assert calc.calculate(floors=30) == 15.0
        assert calc.calculate(floors=50) == 15.0

    def test_height_based_max_setback(self, calc):
        """Test 15m setback for buildings >60.5m."""
        # Any building over 60.5m gets 15m setback
        assert calc.calculate(floors=18, height=61.0) == 15.0
        assert calc.calculate(floors=20, height=70.0) == 15.0
        assert calc.calculate(floors=25, height=87.5) == 15.0

    def test_height_estimation(self, calc):
        """Test height estimation when not provided (3.5m per floor)."""
        # 6 floors → estimated 21m height → normal incremental setback
        setback = calc.calculate(floors=6)  # height estimated as 21m
        assert setback == 6.0

        # 18 floors → estimated 63m > 60.5m → max setback
        setback = calc.calculate(floors=18)  # height estimated as 63m
        assert setback == 15.0


class TestBoundaryCalculations:
    """Test setback from parcel boundary."""

    @pytest.fixture
    def calc(self):
        """Create setback calculator."""
        return SetbackCalculator()

    def test_calculate_from_boundary(self, calc):
        """Test distance calculation from boundary."""
        # Building at (10, 10) to (30, 30) - 20x20m
        building = box(10, 10, 30, 30)

        # Boundary at (0, 0) to (100, 100)
        boundary = box(0, 0, 100, 100)

        result = calc.calculate_from_boundary(building, boundary)

        # Minimum distance should be 10m (building is 10m from left edge)
        assert result["min_distance"] == 10.0
        assert result["compliant"] is True

    def test_building_touching_boundary(self, calc):
        """Test building exactly on boundary."""
        building = box(0, 0, 20, 20)
        boundary = box(0, 0, 100, 100)

        result = calc.calculate_from_boundary(building, boundary)

        # Distance should be 0 (touching)
        assert result["min_distance"] == 0.0

    def test_centered_building(self, calc):
        """Test centered building (equal distances)."""
        # Building centered at (50, 50), size 20x20
        building = box(40, 40, 60, 60)
        boundary = box(0, 0, 100, 100)

        result = calc.calculate_from_boundary(building, boundary)

        # All edges should be 40m from boundary
        assert result["min_distance"] == 40.0
        assert result["max_distance"] == 40.0
        assert result["avg_distance"] == 40.0


class TestBuildingSeparation:
    """Test building-to-building separation."""

    @pytest.fixture
    def calc(self):
        """Create setback calculator."""
        return SetbackCalculator()

    def test_sufficient_separation(self, calc):
        """Test buildings with sufficient separation (≥10m)."""
        building1 = box(0, 0, 20, 20)
        building2 = box(30, 30, 50, 50)  # 10√2 ≈ 14.14m apart

        result = calc.calculate_separation(building1, building2, min_separation=10.0)

        assert result["compliant"] is True
        assert result["distance"] > 10.0

    def test_insufficient_separation(self, calc):
        """Test buildings too close (<10m)."""
        building1 = box(0, 0, 20, 20)
        building2 = box(25, 25, 45, 45)  # 5√2 ≈ 7.07m apart

        result = calc.calculate_separation(building1, building2, min_separation=10.0)

        assert result["compliant"] is False
        assert result["distance"] < 10.0
        assert result["margin"] < 0

    def test_buildings_touching(self, calc):
        """Test adjacent buildings (distance = 0)."""
        building1 = box(0, 0, 20, 20)
        building2 = box(20, 0, 40, 20)  # Sharing edge

        result = calc.calculate_separation(building1, building2, min_separation=10.0)

        assert result["distance"] == 0.0
        assert result["compliant"] is False


class TestAdaptiveSetback:
    """Test context-aware adaptive setback calculations."""

    @pytest.fixture
    def calc(self):
        """Create setback calculator."""
        return SetbackCalculator()

    def test_adaptive_taller_than_neighbors(self, calc):
        """Test increased setback when taller than neighbors."""
        building_data = {"floors": 10, "height": 35.0}
        context = {"adjacent_heights": [14.0, 17.5, 21.0]}  # Avg: 17.5m

        # Building is 2x taller (35 vs 17.5) → +20% setback
        adaptive = calc.calculate_adaptive_setback(building_data, context)
        base = calc.calculate(floors=10, height=35.0)

        assert adaptive > base
        assert adaptive == base * 1.2

    def test_adaptive_shorter_than_neighbors(self, calc):
        """Test reduced setback when shorter than neighbors."""
        building_data = {"floors": 4, "height": 14.0}
        context = {"adjacent_heights": [28.0, 35.0, 42.0]}  # Avg: 35m

        # Building is much shorter (14 vs 35) → -10% setback
        adaptive = calc.calculate_adaptive_setback(building_data, context)
        base = calc.calculate(floors=4, height=14.0)

        assert adaptive < base
        assert adaptive == base * 0.9

    def test_adaptive_similar_height(self, calc):
        """Test no adjustment when similar to neighbors."""
        building_data = {"floors": 6, "height": 21.0}
        context = {"adjacent_heights": [19.5, 21.0, 22.5]}  # Similar heights

        adaptive = calc.calculate_adaptive_setback(building_data, context)
        base = calc.calculate(floors=6, height=21.0)

        # Should be close to base (within adjustment threshold)
        assert adaptive == base

    def test_adaptive_no_neighbors(self, calc):
        """Test adaptive setback with no neighbor context."""
        building_data = {"floors": 6}
        context = {"adjacent_heights": []}

        adaptive = calc.calculate_adaptive_setback(building_data, context)
        base = calc.calculate(floors=6)

        # Should equal base when no neighbors
        assert adaptive == base

    def test_adaptive_respects_max_cap(self, calc):
        """Test that adaptive setback still respects 15m cap."""
        building_data = {"floors": 20, "height": 70.0}
        context = {"adjacent_heights": [14.0]}  # Much shorter neighbors

        adaptive = calc.calculate_adaptive_setback(building_data, context)

        # Even with +20% adjustment, should cap at 15m
        assert adaptive == 15.0


class TestSetbackValidation:
    """Test setback validation for multiple buildings."""

    @pytest.fixture
    def calc(self):
        """Create setback calculator."""
        return SetbackCalculator()

    def test_all_buildings_compliant(self, calc):
        """Test validation when all buildings meet setback."""
        buildings = [
            box(10, 10, 30, 30),  # 10m from boundary
            box(40, 40, 60, 60),  # 40m from boundary
            box(70, 70, 85, 85),  # 15m from boundary
        ]
        boundary = box(0, 0, 100, 100)

        result = calc.validate_all_setbacks(buildings, boundary, required_setback=5.0)

        assert result["compliant"] is True
        assert result["violation_count"] == 0
        assert len(result["violations"]) == 0

    def test_some_buildings_violate(self, calc):
        """Test validation with some violations."""
        buildings = [
            box(10, 10, 30, 30),  # 10m - OK
            box(2, 2, 20, 20),  # 2m - VIOLATION
            box(40, 40, 60, 60),  # 40m - OK
        ]
        boundary = box(0, 0, 100, 100)

        result = calc.validate_all_setbacks(buildings, boundary, required_setback=5.0)

        assert result["compliant"] is False
        assert result["violation_count"] == 1
        assert result["violations"][0]["building_index"] == 1
        assert result["violations"][0]["min_distance"] == 2.0
        assert result["violations"][0]["deficit"] == 3.0  # 5.0 - 2.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def calc(self):
        """Create setback calculator."""
        return SetbackCalculator()

    def test_single_floor_building(self, calc):
        """Test minimum case (1 floor)."""
        setback = calc.calculate(floors=1)
        assert setback == 5.0

    def test_exactly_at_threshold(self, calc):
        """Test building exactly at 4-floor threshold."""
        setback_at_4 = calc.calculate(floors=4)
        setback_at_5 = calc.calculate(floors=5)

        assert setback_at_4 == 5.0
        assert setback_at_5 == 5.5

    def test_height_exactly_at_threshold(self, calc):
        """Test height exactly at 60.5m threshold."""
        setback_under = calc.calculate(floors=17, height=60.5)
        setback_over = calc.calculate(floors=18, height=60.6)

        assert setback_under < 15.0
        assert setback_over == 15.0

    def test_zero_floor_building(self, calc):
        """Test edge case with 0 floors (should use default 1)."""
        # This shouldn't happen in practice, but test defensiveness
        setback = calc.calculate(floors=0)
        # Implementation may vary, but should not crash
        assert setback >= 0
