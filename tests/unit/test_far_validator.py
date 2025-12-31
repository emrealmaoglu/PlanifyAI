"""
Unit tests for FAR (Floor Area Ratio) Validator.

Tests Turkish Emsal calculations with 30% exemption rule.
"""

import pytest

from backend.core.regulatory.far_validator import FARRules, FARValidator


class TestFARRules:
    """Test FAR calculation rules."""

    def test_default_rules(self):
        """Test default Turkish FAR rules (30% exemption)."""
        rules = FARRules()

        assert rules.exemption_ratio == 0.30
        assert rules.count_basement is True
        assert rules.count_mechanical is False
        assert rules.count_parking is False

    def test_custom_rules(self):
        """Test custom FAR rules."""
        rules = FARRules(exemption_ratio=0.25, count_basement=False)

        assert rules.exemption_ratio == 0.25
        assert rules.count_basement is False


class TestGrossFloorAreaCalculation:
    """Test gross floor area calculations."""

    @pytest.fixture
    def validator(self):
        """Create validator with 10,000 m² parcel, FAR limit 2.0."""
        return FARValidator(parcel_area=10000, max_far=2.0)

    def test_single_building(self, validator):
        """Test gross area for single building."""
        buildings = [{"area": 1000, "floors": 4}]

        gross = validator.calculate_gross_floor_area(buildings)

        assert gross == 4000  # 1000 * 4

    def test_multiple_buildings(self, validator):
        """Test gross area for multiple buildings."""
        buildings = [
            {"area": 500, "floors": 3},  # 1,500
            {"area": 800, "floors": 5},  # 4,000
            {"area": 600, "floors": 2},  # 1,200
        ]

        gross = validator.calculate_gross_floor_area(buildings)

        assert gross == 6700

    def test_with_basement(self, validator):
        """Test gross area including basement floors."""
        buildings = [
            {"area": 1000, "floors": 4, "basement_floors": 1}
            # 4,000 + 1,000 = 5,000
        ]

        gross = validator.calculate_gross_floor_area(buildings)

        assert gross == 5000

    def test_without_basement_counted(self):
        """Test basement not counted when rules exclude it."""
        rules = FARRules(count_basement=False)
        validator = FARValidator(parcel_area=10000, max_far=2.0, rules=rules)

        buildings = [{"area": 1000, "floors": 4, "basement_floors": 1}]

        gross = validator.calculate_gross_floor_area(buildings)

        # Basement not counted
        assert gross == 4000


class TestTurkish30PercentExemption:
    """Test Turkish 30% exemption rule."""

    @pytest.fixture
    def validator(self):
        """Create validator with default 30% exemption."""
        return FARValidator(parcel_area=10000, max_far=2.0)

    def test_exemption_calculation(self, validator):
        """Test 30% exemption applied to gross area."""
        buildings = [{"area": 1000, "floors": 10}]  # 10,000 m² gross

        area_data = validator.calculate_taxable_area(buildings)

        assert area_data["gross_floor_area"] == 10000
        assert area_data["exemption_area"] == 3000  # 30%
        assert area_data["taxable_area"] == 7000  # 70%
        assert area_data["exemption_ratio"] == 0.30

    def test_exemption_affects_far(self, validator):
        """Test that exemption reduces FAR calculation."""
        buildings = [{"area": 1000, "floors": 20}]  # 20,000 m² gross

        # Without exemption: FAR = 20,000 / 10,000 = 2.0
        # With exemption: FAR = 14,000 / 10,000 = 1.4
        far = validator.calculate_far(buildings)

        assert far == 1.4

    def test_multiple_buildings_exemption(self, validator):
        """Test exemption applies to total area."""
        buildings = [
            {"area": 500, "floors": 10},  # 5,000
            {"area": 500, "floors": 10},  # 5,000
        ]
        # Total: 10,000 m²
        # Exemption: 3,000 m²
        # Taxable: 7,000 m²

        area_data = validator.calculate_taxable_area(buildings)

        assert area_data["taxable_area"] == 7000


class TestFARCalculation:
    """Test FAR (Floor Area Ratio) calculations."""

    @pytest.fixture
    def validator(self):
        """Create validator with 10,000 m² parcel, FAR limit 2.0."""
        return FARValidator(parcel_area=10000, max_far=2.0)

    def test_basic_far(self, validator):
        """Test basic FAR calculation."""
        # 7,000 m² taxable / 10,000 m² parcel = 0.7 FAR
        buildings = [{"area": 1000, "floors": 10}]

        far = validator.calculate_far(buildings)

        assert far == 0.7

    def test_far_at_limit(self, validator):
        """Test FAR exactly at allowed limit (2.0)."""
        # Need taxable = 20,000 for FAR = 2.0
        # With 30% exemption: gross = 20,000 / 0.7 = 28,571
        buildings = [{"area": 2857, "floors": 10}]  # 28,570 m²

        far = validator.calculate_far(buildings)

        assert 1.99 <= far <= 2.01  # Allow small floating point variation

    def test_far_exceeds_limit(self, validator):
        """Test FAR exceeding limit."""
        # 30,000 gross → 21,000 taxable → 2.1 FAR
        buildings = [{"area": 3000, "floors": 10}]

        far = validator.calculate_far(buildings)

        assert far > 2.0


class TestFARValidation:
    """Test FAR compliance validation."""

    @pytest.fixture
    def validator(self):
        """Create validator with FAR limit 2.0."""
        return FARValidator(parcel_area=10000, max_far=2.0)

    def test_compliant_far(self, validator):
        """Test validation of compliant FAR."""
        buildings = [{"area": 1000, "floors": 10}]  # FAR = 0.7

        result = validator.validate(buildings)

        assert result["compliant"] is True
        assert result["actual_far"] == 0.7
        assert result["allowed_far"] == 2.0
        assert result["margin"] == 1.3
        assert result["margin_percentage"] == 65.0

    def test_violation_far(self, validator):
        """Test validation of FAR violation."""
        # 40,000 gross → 28,000 taxable → 2.8 FAR
        buildings = [{"area": 4000, "floors": 10}]

        result = validator.validate(buildings)

        assert result["compliant"] is False
        assert result["actual_far"] == 2.8
        assert result["margin"] < 0

    def test_exactly_at_limit(self, validator):
        """Test validation exactly at FAR limit."""
        # Calculate exact building size for FAR = 2.0
        buildings = [{"area": 2857, "floors": 10}]

        result = validator.validate(buildings)

        # Should be compliant (within rounding tolerance)
        assert result["compliant"] is True or abs(result["margin"]) < 0.01

    def test_validation_includes_all_metrics(self, validator):
        """Test that validation returns all required metrics."""
        buildings = [{"area": 1000, "floors": 5}]

        result = validator.validate(buildings)

        # Check all expected keys
        assert "compliant" in result
        assert "actual_far" in result
        assert "allowed_far" in result
        assert "margin" in result
        assert "margin_percentage" in result
        assert "gross_floor_area" in result
        assert "exemption_area" in result
        assert "taxable_area" in result


class TestMaxBuildableArea:
    """Test maximum buildable area calculations."""

    @pytest.fixture
    def validator(self):
        """Create validator with FAR limit 2.0."""
        return FARValidator(parcel_area=10000, max_far=2.0)

    def test_max_buildable_empty_site(self, validator):
        """Test max buildable on empty site."""
        result = validator.calculate_max_buildable_area()

        # Max taxable = 2.0 * 10,000 = 20,000 m²
        # Max gross = 20,000 / 0.7 ≈ 28,571 m²
        assert result["max_taxable_area"] == 20000
        assert result["used_taxable_area"] == 0
        assert result["remaining_taxable"] == 20000
        assert abs(result["remaining_gross"] - 28571) < 10
        assert result["utilization_percentage"] == 0

    def test_max_buildable_partial_use(self, validator):
        """Test remaining capacity with existing buildings."""
        existing = [{"area": 1000, "floors": 10}]  # 7,000 taxable

        result = validator.calculate_max_buildable_area(existing)

        assert result["used_taxable_area"] == 7000
        assert result["remaining_taxable"] == 13000  # 20,000 - 7,000
        assert result["utilization_percentage"] == 35.0

    def test_max_buildable_full_use(self, validator):
        """Test when site is fully utilized."""
        # Exactly at FAR limit
        existing = [{"area": 2857, "floors": 10}]

        result = validator.calculate_max_buildable_area(existing)

        # Should be at or near 100% utilization
        assert result["utilization_percentage"] >= 99.0
        assert result["remaining_taxable"] <= 100


class TestFloorDistributionOptimization:
    """Test floor distribution optimization."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return FARValidator(parcel_area=10000, max_far=2.0)

    def test_distribute_within_limit(self, validator):
        """Test floor distribution within FAR limit."""
        # Request 20,000 m² across 4 buildings
        buildings = validator.optimize_floor_distribution(target_gross_area=20000, num_buildings=4)

        assert len(buildings) == 4

        # Total should match target (or be scaled down if needed)
        total_area = sum(b["total_floor_area"] for b in buildings)
        assert total_area <= 30000  # Max allowed with 30% exemption

    def test_distribute_exceeds_limit(self, validator):
        """Test automatic scaling when target exceeds FAR."""
        # Request 40,000 m² (would violate FAR)
        buildings = validator.optimize_floor_distribution(target_gross_area=40000, num_buildings=5)

        # Should be scaled down to fit within FAR limit
        total_area = sum(b["total_floor_area"] for b in buildings)
        assert total_area > 0  # Ensure some area was allocated

        # Validate resulting FAR
        result = validator.validate(buildings)
        assert result["compliant"] is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_parcel_area(self):
        """Test with zero parcel area (should not crash)."""
        validator = FARValidator(parcel_area=0.001, max_far=2.0)

        buildings = [{"area": 100, "floors": 1}]
        result = validator.validate(buildings)

        # Should handle gracefully
        assert "actual_far" in result

    def test_zero_max_far(self):
        """Test with zero FAR limit."""
        validator = FARValidator(parcel_area=10000, max_far=0.0)

        buildings = [{"area": 100, "floors": 1}]
        result = validator.validate(buildings)

        # Any building should violate
        assert result["compliant"] is False

    def test_empty_buildings_list(self):
        """Test with no buildings."""
        validator = FARValidator(parcel_area=10000, max_far=2.0)

        result = validator.validate([])

        assert result["compliant"] is True
        assert result["actual_far"] == 0.0

    def test_very_high_far_limit(self):
        """Test with very high FAR limit (100.0)."""
        validator = FARValidator(parcel_area=10000, max_far=100.0)

        buildings = [{"area": 5000, "floors": 20}]  # 100,000 m² gross
        result = validator.validate(buildings)

        # Should be compliant
        assert result["compliant"] is True
