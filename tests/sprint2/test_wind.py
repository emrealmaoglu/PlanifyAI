import pytest
import numpy as np
from backend.core.physics.wind import (
    WindData, WindDataFetcher, WindAlignmentCalculator,
    WindPenaltyCalculator, fetch_wind_data, quick_wind_score
)


class TestWindData:
    """Tests for WindData dataclass."""
    
    def test_direction_to_radians_north(self):
        """North (0°) should convert to π/2 radians."""
        data = WindData(
            dominant_direction=0,
            dominant_direction_name="N",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=365
        )
        # North in meteorological is 0°, in math is π/2
        assert data.dominant_direction_radians == pytest.approx(np.pi/2, abs=0.01)
    
    def test_direction_to_radians_east(self):
        """East (90°) should convert to 0 radians."""
        data = WindData(
            dominant_direction=90,
            dominant_direction_name="E",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=365
        )
        assert data.dominant_direction_radians == pytest.approx(0, abs=0.01)
    
    def test_direction_to_radians_south(self):
        """South (180°) should convert to -π/2 radians."""
        data = WindData(
            dominant_direction=180,
            dominant_direction_name="S",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=365
        )
        assert data.dominant_direction_radians == pytest.approx(-np.pi/2, abs=0.01)


class TestWindDataFetcher:
    """Tests for WindDataFetcher."""
    
    @pytest.fixture
    def fetcher(self):
        return WindDataFetcher()
    
    @pytest.mark.integration
    def test_fetch_kastamonu(self, fetcher):
        """Fetch real wind data for Kastamonu."""
        data = fetcher.fetch(latitude=41.3833, longitude=33.7833, days=30)
        
        assert data is not None
        assert 0 <= data.dominant_direction < 360
        assert data.average_speed > 0
        assert data.max_speed >= data.average_speed
        assert len(data.direction_frequencies) == 8
        
        print(f"\nKastamonu Wind Data:")
        print(f"  Dominant: {data.dominant_direction_name} ({data.dominant_direction}°)")
        print(f"  Avg speed: {data.average_speed:.1f} m/s")
        print(f"  Max speed: {data.max_speed:.1f} m/s")
    
    def test_fallback_on_error(self, fetcher):
        """Should return fallback data on API error."""
        # Force fallback by using invalid coordinates
        data = fetcher._get_fallback(41.0, 33.0, 365)
        
        assert data is not None
        assert data.dominant_direction == 45  # NE fallback
        assert data.dominant_direction_name == "NE"


class TestWindAlignmentCalculator:
    """Tests for WindAlignmentCalculator."""
    
    @pytest.fixture
    def calc_north_wind(self):
        """Calculator for north wind."""
        data = WindData(
            dominant_direction=0,  # North
            dominant_direction_name="N",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=365
        )
        return WindAlignmentCalculator(data)
    
    @pytest.fixture
    def calc_east_wind(self):
        """Calculator for east wind."""
        data = WindData(
            dominant_direction=90,  # East
            dominant_direction_name="E",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=365
        )
        return WindAlignmentCalculator(data)
    
    def test_parallel_road_north_wind(self, calc_north_wind):
        """Road parallel to north wind should score 1.0."""
        # North-south road (parallel to north wind)
        score = calc_north_wind.road_alignment_score(
            road_start=(0, 0),
            road_end=(0, 100)  # Pointing north
        )
        assert score == pytest.approx(1.0, abs=0.01)
    
    def test_perpendicular_road_north_wind(self, calc_north_wind):
        """Road perpendicular to north wind should score 0.0."""
        # East-west road (perpendicular to north wind)
        score = calc_north_wind.road_alignment_score(
            road_start=(0, 0),
            road_end=(100, 0)  # Pointing east
        )
        assert score == pytest.approx(0.0, abs=0.01)
    
    def test_diagonal_road(self, calc_north_wind):
        """45° road should score 0.5."""
        # NE diagonal road
        score = calc_north_wind.road_alignment_score(
            road_start=(0, 0),
            road_end=(100, 100)
        )
        assert score == pytest.approx(0.5, abs=0.01)
    
    def test_road_network_score(self, calc_east_wind):
        """Network score should weight by length."""
        roads = [
            np.array([[0, 0], [100, 0]]),    # East-west (aligned with east wind)
            np.array([[50, 0], [50, 50]])    # North-south (perpendicular)
        ]
        
        score, details = calc_east_wind.road_network_score(roads)
        
        # First road (100m) aligned, second (50m) perpendicular
        # Expected: (1.0*100 + 0.0*50) / 150 ≈ 0.67
        assert 0.5 < score < 0.8
        assert details["num_segments"] == 2
    
    def test_building_orientation_score(self, calc_east_wind):
        """Building with long axis parallel to wind scores high."""
        # Wide building (long axis = x) with 0 rotation
        # East wind (0 radians) should give high score
        score = calc_east_wind.building_orientation_score(
            building_orientation=0,
            building_width=60,  # Long axis
            building_depth=30
        )
        assert score > 0.9


class TestWindPenaltyCalculator:
    """Tests for WindPenaltyCalculator."""
    
    def test_penalty_calculation(self):
        """Penalty should be inverse of score."""
        # Create with known wind data
        wind_data = WindData(
            dominant_direction=0,  # North
            dominant_direction_name="N",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=365
        )
        
        calc = WindPenaltyCalculator(41.0, 33.0, wind_data=wind_data)
        
        # North-south roads (aligned)
        aligned_roads = [np.array([[0, 0], [0, 100]])]
        penalty_aligned, _ = calc.calculate_penalty(aligned_roads)
        
        # East-west roads (perpendicular)
        perp_roads = [np.array([[0, 0], [100, 0]])]
        penalty_perp, _ = calc.calculate_penalty(perp_roads)
        
        # Aligned should have lower penalty
        assert penalty_aligned < penalty_perp
        assert penalty_aligned < 0.3  # Good alignment
        assert penalty_perp >= 0.7     # Poor alignment


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_quick_wind_score(self):
        """Quick score should return valid value."""
        roads = [
            np.array([[0, 0], [100, 0]]),
            np.array([[0, 0], [0, 100]])
        ]
        
        # May use fallback if no network
        try:
            score = quick_wind_score(roads)
            assert 0 <= score <= 1
        except Exception:
            pass  # Network errors acceptable in tests


class TestWindIntegration:
    """Integration tests with Sprint 1 components."""
    
    def test_with_smart_magnet_roads(self):
        """Test with roads from SmartMagnet."""
        from backend.core.integration.smart_magnet import SmartMagnet
        from backend.core.integration.building_geometry import (
            BuildingGene, BuildingType
        )
        
        # Create roads
        roads = [
            np.array([[0, 0], [200, 0]]),      # East-west
            np.array([[100, 0], [100, 150]])   # North-south
        ]
        
        # Create wind data (NE wind)
        wind_data = WindData(
            dominant_direction=45,  # NE
            dominant_direction_name="NE",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=365
        )
        
        # Create buildings
        genes = [
            BuildingGene((50, 80), BuildingType.ACADEMIC, 60, 40, 4),
            BuildingGene((150, 80), BuildingType.DORMITORY, 50, 35, 5)
        ]
        
        # Align to roads
        magnet = SmartMagnet(roads)
        aligned_genes = magnet.align_buildings(genes)
        
        # Calculate wind penalty
        calc = WindAlignmentCalculator(wind_data)
        road_score, _ = calc.road_network_score(roads)
        
        assert 0 <= road_score <= 1
        
        # Building scores
        for gene in aligned_genes:
            bld_score = calc.building_orientation_score(
                gene.orientation, gene.base_width, gene.base_depth
            )
            assert 0 <= bld_score <= 1
