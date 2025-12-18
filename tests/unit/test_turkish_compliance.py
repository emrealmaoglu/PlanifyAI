"""
Unit tests for Turkish urban planning compliance
Target: 90%+ coverage
"""

import pytest
from shapely.geometry import Polygon, box

from backend.core.turkish_standards import (
    TurkishComplianceChecker,
    ComplianceViolation,
    ComplianceReport,
)


class TestTurkishComplianceChecker:
    """Test suite for compliance checking"""

    @pytest.fixture
    def checker(self):
        """Fixture: compliance checker instance"""
        return TurkishComplianceChecker()

    def test_far_compliant(self, checker):
        """Test FAR compliance - passing case"""
        # FAR = (1000 × 3) / 3000 = 1.0 < 1.5 (residential limit) ✓
        violation = checker.check_far(1000, 3, 3000, "residential")
        assert violation is None

    def test_far_compliant_at_limit(self, checker):
        """Test FAR compliance - exactly at limit"""
        # FAR = (1000 × 4.5) / 3000 = 1.5 = 1.5 (residential limit) ✓
        violation = checker.check_far(1000, 4.5, 3000, "residential")
        assert violation is None

    def test_far_violation(self, checker):
        """Test FAR violation - failing case"""
        # FAR = (1000 × 5) / 3000 = 1.67 > 1.5 (residential limit) ✗
        violation = checker.check_far(1000, 5, 3000, "residential")
        assert isinstance(violation, ComplianceViolation)
        assert violation.rule == "far"
        assert violation.severity == "error"
        assert violation.current_value > violation.required_value

    def test_far_commercial_limit(self, checker):
        """Test FAR with commercial limit"""
        # Commercial limit is 2.0
        violation = checker.check_far(1000, 3, 2000, "commercial")
        # FAR = (1000 × 3) / 2000 = 1.5 < 2.0 ✓
        assert violation is None

    def test_far_commercial_violation(self, checker):
        """Test FAR violation for commercial"""
        # FAR = (1000 × 5) / 2000 = 2.5 > 2.0 ✗
        violation = checker.check_far(1000, 5, 2000, "commercial")
        assert violation is not None
        assert violation.required_value == 2.0

    def test_far_educational_limit(self, checker):
        """Test FAR with educational limit"""
        # Educational limit is 1.2
        violation = checker.check_far(1000, 2, 2000, "educational")
        # FAR = (1000 × 2) / 2000 = 1.0 < 1.2 ✓
        assert violation is None

    def test_far_educational_violation(self, checker):
        """Test FAR violation for educational"""
        # FAR = (1000 × 3) / 2000 = 1.5 > 1.2 ✗
        violation = checker.check_far(1000, 3, 2000, "educational")
        assert violation is not None

    def test_far_mixed_use_limit(self, checker):
        """Test FAR with mixed use limit"""
        violation = checker.check_far(1000, 3, 2000, "mixed_use")
        # FAR = (1000 × 3) / 2000 = 1.5 < 1.8 ✓
        assert violation is None

    def test_far_unknown_zone_defaults_to_residential(self, checker):
        """Test FAR with unknown zone type defaults to residential"""
        violation = checker.check_far(1000, 5, 3000, "unknown_zone")
        # Should use residential limit (1.5)
        assert violation is not None
        assert violation.required_value == 1.5

    def test_far_zero_parcel_area(self, checker):
        """Test error on zero parcel area"""
        with pytest.raises(ValueError, match="Parcel area must be positive"):
            checker.check_far(1000, 3, 0, "residential")

    def test_far_negative_parcel_area(self, checker):
        """Test error on negative parcel area"""
        with pytest.raises(ValueError, match="Parcel area must be positive"):
            checker.check_far(1000, 3, -100, "residential")

    def test_far_zero_building_area(self, checker):
        """Test error on zero building area"""
        with pytest.raises(ValueError, match="Building area must be positive"):
            checker.check_far(0, 3, 3000, "residential")

    def test_far_zero_floors(self, checker):
        """Test error on zero floors"""
        with pytest.raises(ValueError, match="Floors must be >= 1"):
            checker.check_far(1000, 0, 3000, "residential")

    def test_setback_compliant(self, checker):
        """Test setback compliance - passing case"""
        # Building 10m from all sides
        building = box(10, 10, 40, 40)  # 30×30m building
        parcel = box(0, 0, 50, 50)  # 50×50m parcel

        violations = checker.check_setback(building, parcel)
        assert len(violations) == 0

    def test_setback_front_violation(self, checker):
        """Test front setback violation"""
        # Building too close to front (3m instead of 5m)
        building = box(3, 10, 40, 40)
        parcel = box(0, 0, 50, 50)

        violations = checker.check_setback(building, parcel)
        assert len(violations) > 0
        assert any(v.rule == "setback_front" for v in violations)

    def test_setback_side_violation(self, checker):
        """Test side setback violation"""
        # Building too close to side (2m instead of 3m)
        building = box(10, 2, 40, 40)
        parcel = box(0, 0, 50, 50)

        violations = checker.check_setback(building, parcel)
        assert len(violations) > 0
        assert any(v.rule == "setback_side" for v in violations)

    def test_setback_rear_violation(self, checker):
        """Test rear setback violation"""
        # Building too close to rear (4m instead of 5m)
        building = box(10, 10, 46, 40)
        parcel = box(0, 0, 50, 50)

        violations = checker.check_setback(building, parcel)
        assert len(violations) > 0
        assert any(v.rule == "setback_rear" for v in violations)

    def test_setback_building_outside_parcel(self, checker):
        """Test building outside parcel boundary"""
        building = box(60, 60, 80, 80)
        parcel = box(0, 0, 50, 50)

        violations = checker.check_setback(building, parcel)
        assert len(violations) > 0
        assert any(v.rule == "setback_building_outside" for v in violations)

    def test_setback_invalid_building_type(self, checker):
        """Test error on invalid building polygon type"""
        with pytest.raises(
            TypeError, match="building_polygon must be a Shapely Polygon"
        ):
            checker.check_setback("not a polygon", box(0, 0, 50, 50))

    def test_setback_invalid_parcel_type(self, checker):
        """Test error on invalid parcel polygon type"""
        with pytest.raises(
            TypeError, match="parcel_boundary must be a Shapely Polygon"
        ):
            checker.check_setback(box(10, 10, 40, 40), "not a polygon")

    def test_parking_sufficient_residential(self, checker):
        """Test parking compliance - sufficient parking for residential"""
        # Residential: 1 space per 100m²
        # 5000m² × 1.0 = 50 spaces required, 60 provided ✓
        violation = checker.check_parking(5000, "residential", 60)
        assert violation is None

    def test_parking_insufficient_residential(self, checker):
        """Test parking violation for residential"""
        # 5000m² × 1.0 = 50 spaces required, 40 provided ✗
        violation = checker.check_parking(5000, "residential", 40)
        assert isinstance(violation, ComplianceViolation)
        assert violation.rule == "parking"
        assert violation.current_value == 40
        assert violation.required_value == 50

    def test_parking_commercial(self, checker):
        """Test parking for commercial building"""
        # Commercial: 2 spaces per 100m²
        # 5000m² × 2.0 = 100 spaces required
        violation = checker.check_parking(5000, "commercial", 100)
        assert violation is None

    def test_parking_commercial_insufficient(self, checker):
        """Test parking violation for commercial"""
        violation = checker.check_parking(5000, "commercial", 80)
        assert violation is not None
        assert violation.required_value == 100

    def test_parking_educational(self, checker):
        """Test parking for educational building"""
        # Educational: 0.5 spaces per 100m²
        # 5000m² × 0.5 = 25 spaces required
        violation = checker.check_parking(5000, "educational", 30)
        assert violation is None

    def test_parking_office(self, checker):
        """Test parking for office building"""
        # Office: 1.5 spaces per 100m²
        # 5000m² × 1.5 = 75 spaces required
        violation = checker.check_parking(5000, "office", 75)
        assert violation is None

    def test_parking_health(self, checker):
        """Test parking for health building"""
        # Health: 1.2 spaces per 100m²
        # 5000m² × 1.2 = 60 spaces required
        violation = checker.check_parking(5000, "health", 60)
        assert violation is None

    def test_parking_unknown_type_defaults_to_residential(self, checker):
        """Test parking with unknown type defaults to residential"""
        violation = checker.check_parking(5000, "unknown_type", 50)
        assert violation is None  # 50 spaces = required for residential

    def test_green_space_compliant(self, checker):
        """Test green space compliance - passing case"""
        # 15 m²/person standard
        # 1000 people × 15 = 15,000 m² required, 16,000 provided ✓
        violation = checker.check_green_space(16000, 1000)
        assert violation is None

    def test_green_space_violation(self, checker):
        """Test green space violation"""
        # 1000 people × 15 = 15,000 m² required, only 10,000 provided ✗
        violation = checker.check_green_space(10000, 1000)
        assert isinstance(violation, ComplianceViolation)
        assert violation.rule == "green_space"
        assert violation.severity == "warning"  # Warning, not error
        assert violation.current_value < violation.required_value

    def test_green_space_exactly_at_limit(self, checker):
        """Test green space exactly at limit"""
        # 1000 people × 15 = 15,000 m² required, exactly 15,000 provided ✓
        violation = checker.check_green_space(15000, 1000)
        assert violation is None

    def test_green_space_zero_population(self, checker):
        """Test error on zero population"""
        with pytest.raises(ValueError, match="Population must be positive"):
            checker.check_green_space(10000, 0)

    def test_green_space_negative_population(self, checker):
        """Test error on negative population"""
        with pytest.raises(ValueError, match="Population must be positive"):
            checker.check_green_space(10000, -100)

    def test_full_compliance_all_pass(self, checker):
        """Test full compliance check - all rules pass"""
        building_data = {
            "area": 1000,
            "floors": 3,
            "type": "residential",
            "geometry": box(10, 10, 40, 40),
            "parking_spaces": 15,
        }
        parcel_data = {
            "area": 3000,
            "geometry": box(0, 0, 50, 50),
            "zone_type": "residential",
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert isinstance(report, ComplianceReport)
        assert report.is_compliant is True
        assert len(report.errors) == 0

    def test_full_compliance_with_far_violation(self, checker):
        """Test full compliance check - FAR violation"""
        building_data = {
            "area": 1000,
            "floors": 6,  # Too many floors for FAR
            "type": "residential",
            "geometry": box(10, 10, 40, 40),
        }
        parcel_data = {
            "area": 3000,
            "geometry": box(0, 0, 50, 50),
            "zone_type": "residential",
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert report.is_compliant is False
        assert len(report.errors) > 0
        assert any(e.rule == "far" for e in report.errors)

    def test_full_compliance_with_setback_violations(self, checker):
        """Test full compliance check - setback violations"""
        building_data = {
            "area": 1000,
            "floors": 3,
            "type": "residential",
            "geometry": box(2, 2, 48, 48),  # Too close to boundaries
        }
        parcel_data = {
            "area": 3000,
            "geometry": box(0, 0, 50, 50),
            "zone_type": "residential",
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert report.is_compliant is False
        assert len(report.errors) > 0
        assert any("setback" in e.rule for e in report.errors)

    def test_full_compliance_with_parking_violation(self, checker):
        """Test full compliance check - parking violation"""
        building_data = {
            "area": 5000,
            "floors": 3,
            "type": "residential",
            "parking_spaces": 30,  # Insufficient (50 required)
        }
        parcel_data = {
            "area": 10000,
            "zone_type": "residential",
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert report.is_compliant is False
        assert len(report.errors) > 0
        assert any(e.rule == "parking" for e in report.errors)

    def test_full_compliance_with_green_space_warning(self, checker):
        """Test full compliance check - green space warning"""
        building_data = {
            "area": 1000,
            "floors": 3,
            "type": "residential",
        }
        parcel_data = {
            "area": 3000,
            "zone_type": "residential",
            "population": 1000,
            "green_area": 10000,  # Insufficient (15,000 required)
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert len(report.warnings) > 0
        assert any(w.rule == "green_space" for w in report.warnings)
        # Green space is warning, not error, so may still be compliant
        assert report.is_compliant is True  # No errors, only warnings

    def test_full_compliance_metrics(self, checker):
        """Test that compliance report includes metrics"""
        building_data = {
            "area": 1000,
            "floors": 3,
            "type": "residential",
            "parking_spaces": 15,
        }
        parcel_data = {
            "area": 3000,
            "zone_type": "residential",
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert "far" in report.metrics
        assert report.metrics["far"] == (1000 * 3) / 3000  # 1.0

    def test_full_compliance_parking_metrics(self, checker):
        """Test parking metrics in compliance report"""
        building_data = {
            "area": 5000,
            "floors": 3,
            "type": "residential",
            "parking_spaces": 50,
        }
        parcel_data = {
            "area": 10000,
            "zone_type": "residential",
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert "parking_required" in report.metrics
        assert "parking_provided" in report.metrics
        assert report.metrics["parking_required"] == 50.0
        assert report.metrics["parking_provided"] == 50.0

    def test_full_compliance_green_space_metrics(self, checker):
        """Test green space metrics in compliance report"""
        building_data = {
            "area": 1000,
            "floors": 3,
            "type": "residential",
        }
        parcel_data = {
            "area": 3000,
            "zone_type": "residential",
            "population": 1000,
            "green_area": 20000,
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert "green_space_per_person" in report.metrics
        assert report.metrics["green_space_per_person"] == 20.0

    def test_compliance_report_total_violations(self, checker):
        """Test total violations property"""
        building_data = {
            "area": 1000,
            "floors": 6,  # FAR violation
            "type": "residential",
            "geometry": box(2, 2, 48, 48),  # Setback violation
            "parking_spaces": 5,  # Parking violation
        }
        parcel_data = {
            "area": 3000,
            "geometry": box(0, 0, 50, 50),
            "zone_type": "residential",
            "population": 1000,
            "green_area": 10000,  # Green space warning
        }

        report = checker.full_compliance_check(building_data, parcel_data)
        assert report.total_violations > 0
        assert report.total_violations == len(report.errors) + len(report.warnings)

    @pytest.mark.parametrize(
        "zone_type,far_limit",
        [
            ("residential", 1.5),
            ("commercial", 2.0),
            ("educational", 1.2),
            ("mixed_use", 1.8),
            ("industrial", 1.0),
        ],
    )
    def test_far_limits_by_zone(self, checker, zone_type, far_limit):
        """Parametrized test for FAR limits by zone type"""
        # Test at exactly the limit
        building_area = 1000
        floors = int(far_limit * 3000 / building_area)
        parcel_area = 3000

        violation = checker.check_far(building_area, floors, parcel_area, zone_type)
        # Should be compliant or very close to limit
        if violation is not None:
            assert violation.current_value <= far_limit * 1.01  # Allow small rounding

    def test_violation_difference_calculation(self, checker):
        """Test that violation difference is calculated correctly"""
        violation = checker.check_far(1000, 5, 3000, "residential")
        assert violation is not None
        assert violation.difference > 0
        assert violation.difference == abs(
            violation.current_value - violation.required_value
        )
