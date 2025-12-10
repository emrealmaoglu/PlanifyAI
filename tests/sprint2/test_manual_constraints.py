import pytest
import numpy as np
from shapely.geometry import Polygon, box

from backend.core.constraints.manual_constraints import (
    ManualConstraint, ConstraintType, FixedBuilding,
    ManualConstraintManager, create_exclusion_zone, create_fixed_building
)


class TestManualConstraint:
    """Tests for ManualConstraint."""
    
    def test_create_exclusion_zone(self):
        """Create an exclusion zone."""
        coords = [(0, 0), (100, 0), (100, 100), (0, 100)]
        constraint = create_exclusion_zone(coords, "exclusion", "parking_lot")
        
        assert constraint.constraint_type == ConstraintType.EXCLUSION
        assert constraint.area == 10000  # 100x100
        assert constraint.id == "parking_lot"
    
    def test_contains_point(self):
        """Check if point is inside constraint."""
        coords = [(0, 0), (100, 0), (100, 100), (0, 100)]
        constraint = create_exclusion_zone(coords)
        
        assert constraint.contains_point(50, 50)
        assert not constraint.contains_point(150, 50)
    
    def test_to_dict_roundtrip(self):
        """Serialize and deserialize constraint."""
        coords = [(0, 0), (50, 0), (50, 50), (0, 50)]
        original = create_exclusion_zone(coords, "green_space", "garden")
        
        data = original.to_dict()
        restored = ManualConstraint.from_dict(data)
        
        assert restored.id == original.id
        assert restored.constraint_type == original.constraint_type
        assert abs(restored.area - original.area) < 0.1


class TestFixedBuilding:
    """Tests for FixedBuilding."""
    
    def test_create_fixed_building(self):
        """Create a fixed building."""
        building = create_fixed_building(100, 100, "academic", 60, 40, 4)
        
        assert building.position == (100, 100)
        assert building.height == 14.0  # 4 * 3.5
        assert building.building_type == "academic"
    
    def test_polygon_generation(self):
        """Fixed building should generate valid polygon."""
        building = create_fixed_building(100, 100, "dormitory", 50, 30, 5)
        
        poly = building.polygon
        assert poly.is_valid
        assert poly.area == 1500  # 50 * 30
        
        # Centroid should be at position
        assert abs(poly.centroid.x - 100) < 1
        assert abs(poly.centroid.y - 100) < 1


class TestManualConstraintManager:
    """Tests for ManualConstraintManager."""
    
    @pytest.fixture
    def manager(self):
        return ManualConstraintManager()
    
    @pytest.fixture
    def sample_constraints(self, manager):
        """Add some sample constraints."""
        # Exclusion zone (parking)
        parking = create_exclusion_zone(
            [(0, 0), (100, 0), (100, 50), (0, 50)],
            "parking", "main_parking"
        )
        manager.add_constraint(parking)
        
        # Green space
        garden = create_exclusion_zone(
            [(200, 200), (300, 200), (300, 300), (200, 300)],
            "green_space", "central_garden"
        )
        manager.add_constraint(garden)
        
        # Preferred zone
        preferred = ManualConstraint(
            id="academic_zone",
            constraint_type=ConstraintType.PREFERRED,
            geometry=box(400, 400, 600, 600)
        )
        manager.add_constraint(preferred)
        
        return manager
    
    def test_add_remove_constraint(self, manager):
        """Add and remove constraints."""
        constraint = create_exclusion_zone([(0, 0), (10, 0), (10, 10), (0, 10)])
        manager.add_constraint(constraint)
        
        assert constraint.id in manager.constraints
        assert len(manager.constraints) == 1
        
        manager.remove_constraint(constraint.id)
        assert constraint.id not in manager.constraints
    
    def test_exclusion_zones(self, sample_constraints):
        """Get all exclusion-type zones."""
        zones = sample_constraints.exclusion_zones
        
        assert len(zones) == 2  # parking + green_space
    
    def test_is_position_allowed(self, sample_constraints):
        """Check if positions are in allowed areas."""
        # Inside parking (not allowed)
        assert not sample_constraints.is_position_allowed(50, 25)
        
        # Outside all exclusions (allowed)
        assert sample_constraints.is_position_allowed(150, 150)
        
        # Inside garden (not allowed)
        assert not sample_constraints.is_position_allowed(250, 250)
    
    def test_is_polygon_allowed(self, sample_constraints):
        """Check if polygon placements are allowed."""
        # Building overlapping parking
        bad_building = box(50, 25, 90, 75)  # Overlaps parking
        allowed, violation = sample_constraints.is_polygon_allowed(bad_building)
        assert not allowed
        assert violation > 0
        
        # Building in clear area
        good_building = box(150, 150, 180, 175)
        allowed, violation = sample_constraints.is_polygon_allowed(good_building)
        assert allowed
        assert violation == 0
    
    def test_preferred_bonus(self, sample_constraints):
        """Buildings in preferred zones get bonus."""
        # Building fully in preferred zone
        preferred_building = box(420, 420, 480, 480)
        bonus = sample_constraints.get_preferred_bonus(preferred_building)
        assert bonus == 1.0  # 100% in preferred zone
        
        # Building outside preferred zone
        outside_building = box(100, 100, 150, 150)
        bonus = sample_constraints.get_preferred_bonus(outside_building)
        assert bonus == 0.0
    
    def test_check_building_violations(self, sample_constraints):
        """Check multiple buildings for violations."""
        buildings = [
            box(50, 25, 90, 75),    # Overlaps parking
            box(150, 150, 180, 175), # Clear
            box(220, 220, 280, 280)  # Overlaps garden
        ]
        
        total, details = sample_constraints.check_building_violations(buildings)
        
        assert total > 0
        assert len(details) == 2  # Two buildings violate
    
    def test_fixed_building_overlap_detection(self, manager):
        """Detect overlap with fixed buildings."""
        # Add fixed building
        fixed = create_fixed_building(100, 100, "academic", 40, 30, 4)
        manager.add_fixed_building(fixed)
        
        # Building overlapping fixed
        overlapping = [box(90, 90, 130, 130)]
        total, details = manager.check_building_violations(overlapping)
        
        assert total > 0
        assert any(d.get("type") == "fixed_building_overlap" for d in details)
    
    def test_geojson_export_import(self, sample_constraints):
        """Export and import as GeoJSON."""
        # Export
        geojson = sample_constraints.to_geojson()
        
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 3
        
        # Import into new manager
        restored = ManualConstraintManager.from_geojson(geojson)
        
        assert len(restored.constraints) == 3


class TestIntegration:
    """Integration tests with optimizer."""
    
    def test_with_building_genes(self):
        """Test constraint checking with BuildingGene polygons."""
        from backend.core.integration.building_geometry import (
            BuildingGene, BuildingType, ShapeGenerator
        )
        
        # Create manager with exclusion zone
        manager = ManualConstraintManager()
        exclusion = create_exclusion_zone(
            [(0, 0), (200, 0), (200, 100), (0, 100)],
            "parking"
        )
        manager.add_constraint(exclusion)
        
        # Create buildings - one in exclusion, one outside
        genes = [
            BuildingGene((100, 50), BuildingType.ACADEMIC, 60, 40, 4),  # In exclusion
            BuildingGene((300, 200), BuildingType.DORMITORY, 50, 35, 5)  # Outside
        ]
        
        polygons = [ShapeGenerator.generate(g) for g in genes]
        
        total, details = manager.check_building_violations(polygons)
        
        assert total > 0
        assert len(details) == 1  # Only one violation
        assert details[0]["building_idx"] == 0
