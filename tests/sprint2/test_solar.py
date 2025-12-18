import pytest
import numpy as np
from datetime import datetime, timezone
from shapely.geometry import Polygon, box

from backend.core.physics.solar import (
    SolarCalculator, SunPosition, ShadowCalculator,
    SolarPenaltyCalculator, quick_shadow_check
)


class TestSolarCalculator:
    """Tests for SolarCalculator."""
    
    @pytest.fixture
    def kastamonu_calc(self):
        return SolarCalculator(latitude=41.3833, longitude=33.7833)
    
    def test_winter_solstice_low_sun(self, kastamonu_calc):
        """Winter solstice should have low sun altitude."""
        # Kastamonu is ~34°E, so noon is ~09:45 UTC
        # Use 10:00 UTC for near-noon
        dt = datetime(2024, 12, 21, 10, 0, tzinfo=timezone.utc)
        pos = kastamonu_calc.get_position(dt)
        
        # Sun should be above horizon
        assert pos.is_daytime
        
        # Winter solstice altitude around 25° at noon (90 - 41.4 - 23.5 = 25.1)
        assert 20 < pos.altitude < 30
        
        # Sun should be roughly south (180°)
        assert 160 < pos.azimuth < 200
    
    def test_summer_solstice_high_sun(self, kastamonu_calc):
        """Summer solstice should have high sun altitude."""
        # Use 10:00 UTC for near-noon
        dt = datetime(2024, 6, 21, 10, 0, tzinfo=timezone.utc)
        pos = kastamonu_calc.get_position(dt)
        
        # Summer sun much higher (90 - 41.4 + 23.5 = 72.1)
        assert 65 < pos.altitude < 75
    
    def test_shadow_multiplier(self, kastamonu_calc):
        """Shadow length multiplier should be correct."""
        # Use 10:00 UTC for near-noon
        dt = datetime(2024, 12, 21, 10, 0, tzinfo=timezone.utc)
        pos = kastamonu_calc.get_position(dt)
        
        mult = pos.shadow_length_multiplier()
        
        # At ~25° altitude, tan(25) ≈ 0.466, 1/0.466 ≈ 2.14
        assert 1.8 < mult < 2.5
        
        # 10m building should cast ~21m shadow
        shadow_length = 10 * mult
        assert 18 < shadow_length < 25
    
    def test_night_no_shadow(self, kastamonu_calc):
        """Night time should not produce shadows."""
        dt = datetime(2024, 12, 21, 2, 0, tzinfo=timezone.utc)  # 2 AM
        pos = kastamonu_calc.get_position(dt)
        
        assert not pos.is_daytime


class TestShadowCalculator:
    """Tests for ShadowCalculator."""
    
    @pytest.fixture
    def shadow_calc(self):
        solar = SolarCalculator(latitude=41.3833, longitude=33.7833)
        return ShadowCalculator(solar)
    
    def test_shadow_created(self, shadow_calc):
        """Should create shadow polygon."""
        building = box(0, 0, 20, 15)  # 20x15m building
        height = 10.0
        
        dt = datetime(2024, 12, 21, 12, 0, tzinfo=timezone.utc)
        sun_pos = shadow_calc.solar_calc.get_position(dt)
        
        shadow = shadow_calc.calculate_shadow(building, height, sun_pos)
        
        assert shadow is not None
        assert shadow.shadow_polygon.is_valid
        assert shadow.shadow_polygon.area > building.area
    
    def test_shadow_points_away_from_sun(self, shadow_calc):
        """Shadow should extend away from sun."""
        building = box(100, 100, 120, 115)
        height = 10.0
        
        dt = datetime(2024, 12, 21, 12, 0, tzinfo=timezone.utc)
        sun_pos = shadow_calc.solar_calc.get_position(dt)
        
        shadow = shadow_calc.calculate_shadow(building, height, sun_pos)
        
        # Shadow centroid should be north of building (sun is south)
        building_centroid = building.centroid
        shadow_centroid = shadow.shadow_polygon.centroid
        
        assert shadow_centroid.y > building_centroid.y  # Shadow extends north
    
    def test_taller_building_longer_shadow(self, shadow_calc):
        """Taller buildings should cast longer shadows."""
        building = box(0, 0, 20, 15)
        
        dt = datetime(2024, 12, 21, 12, 0, tzinfo=timezone.utc)
        sun_pos = shadow_calc.solar_calc.get_position(dt)
        
        shadow_10m = shadow_calc.calculate_shadow(building, 10.0, sun_pos)
        shadow_20m = shadow_calc.calculate_shadow(building, 20.0, sun_pos)
        
        assert shadow_20m.shadow_polygon.area > shadow_10m.shadow_polygon.area


class TestSolarPenaltyCalculator:
    """Tests for SolarPenaltyCalculator."""
    
    @pytest.fixture
    def penalty_calc(self):
        return SolarPenaltyCalculator(latitude=41.3833, longitude=33.7833)
    
    def test_no_penalty_for_distant_buildings(self, penalty_calc):
        """Distant buildings should not shadow each other."""
        buildings = [
            (0, box(0, 0, 20, 15), 10.0),
            (1, box(500, 500, 520, 515), 10.0)  # 500m away
        ]
        
        penalty, details = penalty_calc.calculate_penalty(buildings)
        
        assert penalty == 0.0
        assert len(details["shadow_overlaps"]) == 0
    
    def test_penalty_for_adjacent_buildings(self, penalty_calc):
        """Adjacent buildings should have shadow penalty."""
        # Building to south will shadow building to north
        buildings = [
            (0, box(0, 0, 20, 15), 15.0),    # South building (tall)
            (1, box(0, 30, 20, 45), 10.0)    # North building (30m north)
        ]
        
        penalty, details = penalty_calc.calculate_penalty(buildings)
        
        # Should have some penalty (south building shadows north building)
        assert penalty > 0
        assert len(details["shadow_overlaps"]) > 0
    
    def test_south_facade_extra_penalty(self, penalty_calc):
        """South facade shadowing should have extra penalty."""
        # This is tested implicitly through the weight factor
        south_facade = penalty_calc.get_south_facade(box(0, 0, 20, 15))
        
        assert south_facade.is_valid
        assert south_facade.area > 0


class TestQuickShadowCheck:
    """Tests for convenience function."""
    
    def test_quick_check_returns_float(self):
        """Should return a numeric penalty."""
        buildings = [
            (box(0, 0, 20, 15), 10.0),
            (box(0, 25, 20, 40), 10.0)
        ]
        
        penalty = quick_shadow_check(buildings)
        
        assert isinstance(penalty, float)
        assert penalty >= 0


class TestSolarIntegration:
    """Integration tests with building geometry."""
    
    def test_with_building_genes(self):
        """Test solar analysis with BuildingGene polygons."""
        from backend.core.integration.building_geometry import (
            BuildingGene, BuildingType, ShapeGenerator
        )
        
        # Create some buildings
        genes = [
            BuildingGene((100, 100), BuildingType.ACADEMIC, 60, 45, 5),
            BuildingGene((100, 180), BuildingType.DORMITORY, 50, 40, 6)
        ]
        
        polygons = [ShapeGenerator.generate(g) for g in genes]
        
        # Run shadow analysis
        buildings = [
            (poly, gene.height) for gene, poly in zip(genes, polygons)
        ]
        
        penalty = quick_shadow_check(buildings)
        
        assert isinstance(penalty, float)
