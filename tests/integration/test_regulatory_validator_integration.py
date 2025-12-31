"""
Integration tests for Regulatory Validator.

Tests integration between regulatory module and optimization pipeline.
"""

import pytest
from shapely.geometry import box

from backend.core.optimization.regulatory_validator import RegulatoryValidator
from backend.core.regulatory.paiy_compliance import ZoneType


class TestRegulatoryValidatorIntegration:
    """Test regulatory validator integration with optimization."""

    @pytest.fixture
    def educational_validator(self):
        """Create validator for educational zone (25 hectare campus)."""
        # Square parcel: 500m x 500m = 250,000 m²
        boundary = box(0, 0, 500, 500)

        return RegulatoryValidator(
            zone_type=ZoneType.EDUCATIONAL, parcel_area=250000, boundary=boundary
        )

    def test_compliant_layout(self, educational_validator):
        """Test validation of compliant layout."""
        # 4 educational buildings, well-spaced
        buildings = [
            {"area": 2000, "floors": 4, "height": 14.0, "type": "EDUCATIONAL"},
            {"area": 2000, "floors": 4, "height": 14.0, "type": "EDUCATIONAL"},
            {"area": 1500, "floors": 3, "height": 10.5, "type": "RESIDENTIAL"},
            {"area": 1500, "floors": 3, "height": 10.5, "type": "RESIDENTIAL"},
        ]

        # Buildings well within boundary (20m setback minimum)
        building_polygons = [
            box(50, 50, 100, 90),  # 2,000 m²
            box(150, 50, 200, 90),  # 2,000 m²
            box(50, 150, 88, 187.5),  # 1,500 m²
            box(150, 150, 188, 187.5),  # 1,500 m²
        ]

        result = educational_validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is True
        assert result["violation_count"] == 0
        assert result["metrics"]["far"]["compliant"] is True
        assert result["metrics"]["green_space"]["compliant"] is True
        assert result["metrics"]["setback_compliant"] is True
        assert result["metrics"]["separation_compliant"] is True

    def test_far_violation(self, educational_validator):
        """Test FAR violation detection."""
        # Too many large buildings → FAR violation
        # Educational zone FAR = 2.0, parcel = 250,000 m²
        # Max taxable = 500,000 m², max gross = 714,286 m² (with 30% exemption)
        # Build 800,000 m² gross → 560,000 m² taxable → FAR = 2.24 (VIOLATION)
        buildings = [
            {"area": 5000, "floors": 16, "type": "EDUCATIONAL"}
            for _ in range(10)  # 800,000 m² gross
        ]

        building_polygons = [
            box(i * 50, j * 50, i * 50 + 70, j * 50 + 70) for i in range(5) for j in range(2)
        ]

        result = educational_validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is False
        assert any(v["type"] == "FAR_VIOLATION" for v in result["violations"])
        assert result["metrics"]["far"]["compliant"] is False

    def test_green_space_violation(self, educational_validator):
        """Test green space violation detection."""
        # Large buildings covering >70% of site
        buildings = [
            {"area": 60000, "floors": 2, "type": "EDUCATIONAL"}
            for _ in range(3)  # 180,000 m² coverage
        ]

        building_polygons = [
            box(10, 10, 255, 245),  # ~60,000 m²
            box(260, 10, 490, 245),  # ~54,000 m²
            box(10, 260, 490, 490),  # ~110,000 m²
        ]

        result = educational_validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is False
        assert any(v["type"] == "GREEN_SPACE_VIOLATION" for v in result["violations"])
        assert result["metrics"]["green_space"]["compliant"] is False

    def test_height_violation(self, educational_validator):
        """Test height limit violation (educational zone: 21.5m max)."""
        # One building exceeds height limit
        buildings = [
            {"area": 2000, "floors": 4, "height": 14.0, "type": "EDUCATIONAL"},
            {"area": 2000, "floors": 8, "height": 28.0, "type": "EDUCATIONAL"},  # VIOLATION
        ]

        building_polygons = [box(50, 50, 100, 90), box(150, 50, 200, 90)]

        result = educational_validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is False
        assert any(v["type"] == "HEIGHT_VIOLATION" for v in result["violations"])
        assert result["metrics"]["height_limits"]["compliant"] is False

    def test_setback_violation(self, educational_validator):
        """Test setback violation (building too close to boundary)."""
        # Building only 2m from boundary (requires 5m minimum)
        buildings = [{"area": 1000, "floors": 4, "height": 14.0, "type": "EDUCATIONAL"}]

        building_polygons = [box(2, 2, 33, 32)]  # Only 2m from edge

        result = educational_validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is False
        assert any(v["type"] == "SETBACK_VIOLATION" for v in result["violations"])
        assert result["metrics"]["setback_compliant"] is False

    def test_building_separation_violation(self, educational_validator):
        """Test building separation violation (fire safety <10m)."""
        # Two buildings only 5m apart
        buildings = [
            {"area": 1000, "floors": 4, "height": 14.0, "type": "EDUCATIONAL"},
            {"area": 1000, "floors": 4, "height": 14.0, "type": "EDUCATIONAL"},
        ]

        building_polygons = [
            box(50, 50, 81, 81),  # Building 1
            box(86, 50, 117, 81),  # Building 2, only 5m away
        ]

        result = educational_validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is False
        assert any(v["type"] == "SEPARATION_VIOLATION" for v in result["violations"])
        assert result["metrics"]["separation_compliant"] is False

    def test_multiple_violations(self, educational_validator):
        """Test layout with multiple violation types."""
        # Violates FAR, green space, and setback
        # 5 × 10,000m² × 20 floors = 1,000,000 m² gross → 700,000 m² taxable → FAR = 2.8 (VIOLATION)
        buildings = [
            {"area": 10000, "floors": 20, "type": "EDUCATIONAL"}
            for _ in range(5)  # Massive overbuild
        ]

        building_polygons = [
            box(1, 1, 101, 101),  # Too close to boundary
            box(110, 1, 210, 101),
            box(220, 1, 320, 101),
            box(1, 110, 101, 210),
            box(110, 110, 210, 210),
        ]

        result = educational_validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is False
        assert result["violation_count"] >= 3
        violation_types = {v["type"] for v in result["violations"]}
        assert "FAR_VIOLATION" in violation_types
        assert "SETBACK_VIOLATION" in violation_types

    def test_construction_cost_calculation(self, educational_validator):
        """Test construction cost estimation."""
        buildings = [
            {"area": 2000, "floors": 4, "type": "EDUCATIONAL"},  # 8,000 m² × 2,000 TL/m²
            {"area": 1500, "floors": 3, "type": "RESIDENTIAL"},  # 4,500 m² × 1,500 TL/m²
        ]

        building_polygons = [box(50, 50, 100, 90), box(150, 50, 188, 80)]

        result = educational_validator.validate_layout(buildings, building_polygons)

        # Educational: 16,000,000 TL + Residential: 6,750,000 TL = 22,750,000 TL
        expected_cost = 22_750_000
        assert result["metrics"]["construction_cost_tl"] == expected_cost

    def test_max_buildable_area(self, educational_validator):
        """Test max buildable area calculation."""
        # Empty site
        result = educational_validator.get_max_buildable_area()

        # Educational zone FAR = 2.0
        # Max taxable = 2.0 × 250,000 = 500,000 m²
        assert result["max_taxable_area"] == 500000
        assert result["utilization_percentage"] == 0

    def test_max_buildable_with_existing(self, educational_validator):
        """Test max buildable area with existing buildings."""
        existing = [{"area": 5000, "floors": 10}]  # 50,000 m² gross → 35,000 m² taxable

        result = educational_validator.get_max_buildable_area(existing)

        assert result["used_taxable_area"] == 35000
        assert result["remaining_taxable"] == 465000  # 500,000 - 35,000
        assert result["utilization_percentage"] == pytest.approx(7.0)

    def test_floor_distribution_suggestion(self, educational_validator):
        """Test floor distribution optimization."""
        # Request 20,000 m² across 4 buildings
        suggestions = educational_validator.suggest_floor_distribution(
            target_gross_area=20000, num_buildings=4
        )

        assert len(suggestions) == 4
        total_area = sum(b["total_floor_area"] for b in suggestions)
        assert total_area <= 30000  # Should respect FAR limits


class TestDifferentZoneTypes:
    """Test validator with different Turkish zone types."""

    def test_residential_low_density(self):
        """Test low-density residential zone (FAR 0.8)."""
        boundary = box(0, 0, 100, 100)  # 10,000 m²
        validator = RegulatoryValidator(
            zone_type=ZoneType.RESIDENTIAL_LOW, parcel_area=10000, boundary=boundary
        )

        # Small buildings appropriate for low density
        buildings = [{"area": 500, "floors": 2, "type": "RESIDENTIAL"} for _ in range(3)]

        # Spread buildings 15m apart (need 10m min)
        building_polygons = [
            box(20, 20, 42, 42),  # 22x22m building
            box(57, 20, 79, 42),  # 15m gap
            box(20, 57, 42, 79),  # 15m gap
        ]

        result = validator.validate_layout(buildings, building_polygons)

        assert result["compliant"] is True
        assert result["metrics"]["far"]["allowed_far"] == 0.8

    def test_commercial_zone(self):
        """Test commercial zone (FAR 3.0, higher density allowed)."""
        boundary = box(0, 0, 100, 100)
        validator = RegulatoryValidator(
            zone_type=ZoneType.COMMERCIAL, parcel_area=10000, boundary=boundary
        )

        # Higher density buildings allowed in commercial zone
        buildings = [{"area": 800, "floors": 8, "type": "COMMERCIAL"} for _ in range(3)]

        building_polygons = [
            box(20, 20, 48, 48),
            box(55, 20, 83, 48),
            box(20, 55, 48, 83),
        ]

        result = validator.validate_layout(buildings, building_polygons)

        # Should be compliant with FAR 3.0
        assert result["metrics"]["far"]["allowed_far"] == 3.0


class TestTurkishExemptionRule:
    """Test Turkish 30% exemption rule integration."""

    @pytest.fixture
    def validator(self):
        boundary = box(0, 0, 100, 100)
        return RegulatoryValidator(
            zone_type=ZoneType.EDUCATIONAL, parcel_area=10000, boundary=boundary
        )

    def test_exemption_applied(self, validator):
        """Test that 30% exemption is applied correctly."""
        buildings = [{"area": 1000, "floors": 10, "type": "EDUCATIONAL"}]  # 10,000 m²
        building_polygons = [box(20, 20, 51, 51)]

        result = validator.validate_layout(buildings, building_polygons, apply_far_exemption=True)

        # With exemption: 10,000 × 0.7 = 7,000 m² taxable → FAR = 0.7
        assert result["metrics"]["far"]["exemption_area"] == 3000
        assert result["metrics"]["far"]["taxable_area"] == 7000
        assert result["metrics"]["far"]["actual_far"] == pytest.approx(0.7)

    def test_exemption_disabled(self, validator):
        """Test validation without exemption."""
        buildings = [{"area": 1000, "floors": 10, "type": "EDUCATIONAL"}]
        building_polygons = [box(20, 20, 51, 51)]

        result = validator.validate_layout(buildings, building_polygons, apply_far_exemption=False)

        # Without exemption: 10,000 m² taxable → FAR = 1.0
        assert result["metrics"]["far"]["exemption_area"] == 0
        assert result["metrics"]["far"]["taxable_area"] == 10000
        assert result["metrics"]["far"]["actual_far"] == pytest.approx(1.0)
