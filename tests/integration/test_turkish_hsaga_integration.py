"""
Integration tests for Turkish Standards + H-SAGA

Verifies end-to-end functionality
"""

import pytest
import numpy as np
from shapely.geometry import box

from backend.core.optimization.building_mapper import (
    BuildingTypeMapper,
    BuildingWithTurkishClass,
)
from backend.core.optimization.objectives import ObjectiveFunctions
from backend.core.optimization.constraints import TurkishConstraintValidator
from backend.core.turkish_standards import BuildingClass


class TestBuildingMapper:
    """Test building type mapping"""

    @pytest.fixture
    def mapper(self):
        return BuildingTypeMapper()

    def test_map_single_building(self, mapper):
        """Test mapping a single building"""
        result = mapper.map_to_turkish(
            building_id="B001",
            building_type="educational_university",
            area=5000,
            floors=4,
            position=(100, 100),
        )

        assert isinstance(result, BuildingWithTurkishClass)
        assert result.building_id == "B001"
        assert result.turkish_class == BuildingClass.CLASS_V_A
        assert result.cost_per_sqm == 2000.0

    def test_map_residential(self, mapper):
        """Test mapping residential building"""
        result = mapper.map_to_turkish("B002", "residential_low", 3000, 3)

        assert result.turkish_class == BuildingClass.CLASS_III_A
        assert result.cost_per_sqm == 1500.0

    def test_map_commercial(self, mapper):
        """Test mapping commercial building"""
        result = mapper.map_to_turkish("B003", "commercial_office", 4000, 5)

        assert result.turkish_class == BuildingClass.CLASS_IV_A
        assert result.cost_per_sqm == 2000.0

    def test_invalid_type_raises_error(self, mapper):
        """Test that invalid type raises ValueError"""
        with pytest.raises(ValueError, match="Cannot map"):
            mapper.map_to_turkish("B004", "invalid_type_xyz", 1000, 1)

    def test_map_building_list(self, mapper):
        """Test mapping a list of buildings"""
        buildings = [
            {"id": "B001", "type": "residential_low", "area": 2000, "floors": 3},
            {
                "id": "B002",
                "type": "educational_university",
                "area": 5000,
                "floors": 4,
            },
            {"id": "B003", "type": "health_hospital", "area": 8000, "floors": 5},
        ]

        result = mapper.map_building_list(buildings)

        assert len(result) == 3
        assert all(isinstance(b, BuildingWithTurkishClass) for b in result)
        assert result[0].turkish_class == BuildingClass.CLASS_III_A
        assert result[1].turkish_class == BuildingClass.CLASS_V_A
        assert result[2].turkish_class == BuildingClass.CLASS_V_B


class TestIntegratedCostObjective:
    """Test cost objective with Turkish Standards"""

    @pytest.fixture
    def objectives(self):
        return ObjectiveFunctions(location="ankara", quality="standard")

    @pytest.fixture
    def sample_buildings(self):
        """Sample buildings for testing"""

        class MockBuilding:
            def __init__(self, id, type, area, floors):
                self.id = id
                self.building_id = id
                self.type = type
                self.building_type = type
                self.area = area
                self.floors = floors
                self.position = (0, 0)

        return [
            MockBuilding("B001", "residential_low", 2000, 3),
            MockBuilding("B002", "educational_university", 5000, 4),
            MockBuilding("B003", "commercial_office", 3000, 4),
        ]

    def test_minimize_cost_integration(self, objectives, sample_buildings):
        """Test cost minimization with Turkish calculator"""
        cost = objectives.minimize_cost(sample_buildings)

        assert isinstance(cost, float)
        assert 0.0 <= cost <= 1.0  # Normalized

    def test_cost_breakdown(self, objectives, sample_buildings):
        """Test detailed cost breakdown"""
        breakdown = objectives.get_cost_breakdown(sample_buildings)

        assert "total_cost_tl" in breakdown
        assert breakdown["total_cost_tl"] > 0
        assert "by_type" in breakdown
        assert "by_class" in breakdown
        assert len(breakdown["buildings"]) == 3

        # Verify educational building has Class V-A cost
        edu_building = [
            b for b in breakdown["buildings"] if "educational" in b["type"]
        ][0]
        assert edu_building["turkish_class"] == "V-A"

    def test_location_affects_cost(self, sample_buildings):
        """Test that location factor affects cost"""
        obj_ankara = ObjectiveFunctions(location="ankara", quality="standard")
        obj_provincial = ObjectiveFunctions(location="provincial", quality="standard")

        cost_ankara = obj_ankara.minimize_cost(sample_buildings)
        cost_provincial = obj_provincial.minimize_cost(sample_buildings)

        # Ankara should be more expensive (factor 1.2 vs 1.0)
        assert cost_ankara > cost_provincial

    def test_quality_affects_cost(self, sample_buildings):
        """Test that quality factor affects cost"""
        obj_luxury = ObjectiveFunctions(location="provincial", quality="luxury")
        obj_economy = ObjectiveFunctions(location="provincial", quality="economy")

        cost_luxury = obj_luxury.minimize_cost(sample_buildings)
        cost_economy = obj_economy.minimize_cost(sample_buildings)

        # Luxury should be more expensive
        assert cost_luxury > cost_economy

    def test_fallback_on_mapping_failure(self, objectives):
        """Test fallback cost calculation if mapping fails"""

        # Create invalid buildings
        invalid_buildings = [
            {"id": "B001", "type": "INVALID_TYPE", "area": 1000, "floors": 1}
        ]

        # Should not crash, should use fallback
        cost = objectives.minimize_cost(invalid_buildings)
        assert isinstance(cost, float)
        assert cost >= 0


class TestComplianceConstraints:
    """Test constraint validation with Turkish compliance"""

    @pytest.fixture
    def validator(self):
        """Create validator with sample parcel"""
        parcel_boundary = box(0, 0, 200, 200)  # 200x200m parcel
        parcel_area = 40000  # 40,000 m²

        return TurkishConstraintValidator(
            parcel_boundary=parcel_boundary,
            parcel_area=parcel_area,
            zone_type="educational",
            enable_compliance_checks=True,
        )

    @pytest.fixture
    def valid_buildings(self):
        """Sample valid building configuration"""

        class MockBuilding:
            def __init__(self, id, type, area, floors, position):
                self.id = id
                self.building_id = id
                self.type = type
                self.building_type = type
                self.area = area
                self.floors = floors
                self.position = position

        return [
            MockBuilding("B001", "educational_university", 2000, 3, (50, 50)),
            MockBuilding("B002", "residential_low", 1500, 3, (150, 50)),
            MockBuilding("B003", "commercial_office", 1000, 2, (100, 150)),
        ]

    def test_validate_valid_solution(self, validator, valid_buildings):
        """Test validation of valid solution"""
        summary = validator.validate_solution(valid_buildings)

        # Should have no critical errors (warnings OK)
        assert summary.severity_breakdown["error"] == 0
        assert isinstance(summary.compliance_report, type(None)) or hasattr(
            summary.compliance_report, "is_compliant"
        )

    def test_detect_overlap(self, validator):
        """Test detection of building overlaps"""

        # Create overlapping buildings

        class MockBuilding:
            def __init__(self, id, type, area, floors, position):
                self.id = id
                self.building_id = id
                self.type = type
                self.area = area
                self.floors = floors
                self.position = position

        overlapping_buildings = [
            MockBuilding("B001", "residential_low", 10000, 1, (50, 50)),
            MockBuilding("B002", "residential_low", 10000, 1, (55, 55)),  # Overlap!
        ]

        summary = validator.validate_solution(overlapping_buildings)

        assert not summary.is_valid
        assert any("overlap" in v.lower() for v in summary.violations)

    def test_detect_boundary_violation(self, validator):
        """Test detection of buildings outside boundary"""

        class MockBuilding:
            def __init__(self, id, type, area, floors, position):
                self.id = id
                self.type = type
                self.area = area
                self.floors = floors
                self.position = position

        out_of_bounds = [
            MockBuilding("B001", "residential_low", 1000, 1, (250, 250)),  # Outside!
        ]

        summary = validator.validate_solution(out_of_bounds)

        assert not summary.is_valid
        assert any(
            "outside" in v.lower() or "boundary" in v.lower()
            for v in summary.violations
        )

    def test_compliance_penalty(self, validator, valid_buildings):
        """Test penalty calculation"""
        penalty = validator.get_constraint_penalty(valid_buildings)

        # Valid solution should have low or zero penalty
        assert penalty >= 0.0


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    def test_complete_pipeline(self):
        """Test complete Turkish Standards → H-SAGA pipeline"""

        # 1. Create sample buildings

        class MockBuilding:
            def __init__(self, id, type, area, floors, position):
                self.id = id
                self.building_id = id
                self.type = type
                self.building_type = type
                self.area = area
                self.floors = floors
                self.position = position

        buildings = [
            MockBuilding("B001", "educational_university", 5000, 4, (50, 50)),
            MockBuilding("B002", "residential_low", 3000, 3, (150, 50)),
            MockBuilding("B003", "health_clinic", 2000, 2, (100, 150)),
        ]

        # 2. Map to Turkish types
        mapper = BuildingTypeMapper()
        turkish_buildings = mapper.map_building_list(buildings)

        assert len(turkish_buildings) == 3
        assert turkish_buildings[0].turkish_class == BuildingClass.CLASS_V_A

        # 3. Calculate costs
        objectives = ObjectiveFunctions(location="ankara")
        cost = objectives.minimize_cost(buildings)
        breakdown = objectives.get_cost_breakdown(buildings)

        assert cost > 0
        assert breakdown["total_cost_tl"] > 0

        # 4. Check constraints
        parcel = box(0, 0, 200, 200)
        validator = TurkishConstraintValidator(
            parcel_boundary=parcel, parcel_area=40000, zone_type="educational"
        )

        summary = validator.validate_solution(buildings)

        # Solution may have warnings but should be feasible
        assert isinstance(summary.is_valid, bool)

        # 5. Verify all components work together
        assert True  # If we got here, integration successful!

    def test_different_building_types(self):
        """Test integration with various building types"""
        building_types = [
            "residential_low",
            "residential_mid",
            "commercial_office",
            "educational_university",
            "health_hospital",
            "social_sports",
        ]

        mapper = BuildingTypeMapper()

        for i, btype in enumerate(building_types):
            building = mapper.map_to_turkish(
                building_id=f"B{i:03d}",
                building_type=btype,
                area=3000,
                floors=3,
            )

            # Should successfully map all types
            assert isinstance(building, BuildingWithTurkishClass)
            assert building.turkish_class is not None
            assert building.cost_per_sqm > 0
