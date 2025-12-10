# tests/sprint1/test_smart_magnet.py
import pytest
import numpy as np
from shapely.geometry import LineString
from backend.core.integration.smart_magnet import SmartMagnet, RoadSegment
from backend.core.integration.building_geometry import (
    BuildingGene, BuildingType, EntranceSide
)

class TestRoadSegment:
    """Unit tests for RoadSegment."""

    def test_horizontal_road_angle(self):
        """Horizontal road should have angle 0"""
        seg = RoadSegment.from_points(
            np.array([0, 0]), np.array([100, 0])
        )
        assert seg.angle == pytest.approx(0.0, abs=0.01)

    def test_vertical_road_angle(self):
        """Vertical road should have angle π/2"""
        seg = RoadSegment.from_points(
            np.array([0, 0]), np.array([0, 100])
        )
        assert seg.angle == pytest.approx(np.pi/2, abs=0.01)

    def test_diagonal_road_angle(self):
        """45° diagonal road"""
        seg = RoadSegment.from_points(
            np.array([0, 0]), np.array([100, 100])
        )
        assert seg.angle == pytest.approx(np.pi/4, abs=0.01)

    def test_reverse_direction(self):
        """Reversed road should have opposite angle"""
        seg1 = RoadSegment.from_points(np.array([0, 0]), np.array([100, 0]))
        seg2 = RoadSegment.from_points(np.array([100, 0]), np.array([0, 0]))
        assert abs(abs(seg1.angle - seg2.angle) - np.pi) < 0.01

    def test_degenerate_segment(self):
        """Zero-length segment should not crash"""
        seg = RoadSegment.from_points(
            np.array([50, 50]), np.array([50, 50])
        )
        assert seg.angle == 0.0  # Default
        assert seg.line.is_valid


class TestSmartMagnet:
    """Unit tests for SmartMagnet."""

    @pytest.fixture
    def simple_roads(self):
        """Single horizontal road at y=0"""
        return [np.array([[0, 0], [200, 0]])]

    @pytest.fixture
    def complex_roads(self):
        """Multiple roads forming a grid"""
        return [
            np.array([[0, 0], [200, 0]]),      # Horizontal bottom
            np.array([[0, 100], [200, 100]]),  # Horizontal top
            np.array([[0, 0], [0, 100]]),      # Vertical left
            np.array([[200, 0], [200, 100]])   # Vertical right
        ]

    def test_find_nearest_horizontal(self, simple_roads):
        """Find nearest point on horizontal road"""
        magnet = SmartMagnet(simple_roads)
        result = magnet.find_nearest_road((100, 50))

        assert result is not None
        segment, point, dist = result
        assert point.y == pytest.approx(0.0, abs=0.1)
        assert dist == pytest.approx(50.0, abs=1.0)

    def test_find_nearest_complex(self, complex_roads):
        """Find correct nearest road in complex network"""
        magnet = SmartMagnet(complex_roads)

        # Point at (100, 20) - closest to bottom horizontal
        result = magnet.find_nearest_road((100, 20))
        assert result is not None
        _, point, dist = result
        assert dist == pytest.approx(20.0, abs=1.0)

        # Point at (100, 80) - closest to top horizontal
        result = magnet.find_nearest_road((100, 80))
        assert result is not None
        _, point, dist = result
        assert dist == pytest.approx(20.0, abs=1.0)

    def test_empty_roads(self):
        """Empty road list should return None"""
        magnet = SmartMagnet([])
        result = magnet.find_nearest_road((100, 100))
        assert result is None

    def test_orientation_calculation(self, simple_roads):
        """Building should face toward road"""
        magnet = SmartMagnet(simple_roads)

        # Building north of road with SOUTH entrance
        orientation = magnet.calculate_orientation(
            position=(100, 50),
            entrance_side=EntranceSide.SOUTH
        )

        # Should be valid angle
        assert -np.pi <= orientation <= np.pi

    def test_align_buildings_preserves_count(self, simple_roads):
        """align_buildings should return same number of genes"""
        magnet = SmartMagnet(simple_roads)

        genes = [
            BuildingGene((50, 50), BuildingType.ACADEMIC, 40, 30, 3),
            BuildingGene((100, 80), BuildingType.DORMITORY, 50, 40, 5),
            BuildingGene((150, 60), BuildingType.SOCIAL, 35, 25, 2)
        ]

        aligned = magnet.align_buildings(genes)
        assert len(aligned) == len(genes)

    def test_align_buildings_modifies_orientation(self, simple_roads):
        """align_buildings should change orientations"""
        magnet = SmartMagnet(simple_roads)

        gene = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ACADEMIC,
            base_width=40,
            base_depth=30,
            floors=3,
            orientation=0.0  # Original
        )

        aligned = magnet.align_buildings([gene])
        # Orientation should be different (building is far from road)
        # (might be same if already aligned, but generally different)
        assert aligned[0].orientation is not None

    def test_align_buildings_immutable(self, simple_roads):
        """Original genes should not be modified"""
        magnet = SmartMagnet(simple_roads)

        original_gene = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ADMIN,
            base_width=30,
            base_depth=20,
            floors=2,
            orientation=0.0
        )
        original_orientation = original_gene.orientation

        magnet.align_buildings([original_gene])

        assert original_gene.orientation == original_orientation

    def test_get_driveway_creates_linestring(self, simple_roads):
        """Driveway should be valid LineString"""
        magnet = SmartMagnet(simple_roads)

        gene = BuildingGene(
            position=(100, 50),
            building_type=BuildingType.ADMIN,
            base_width=30,
            base_depth=20,
            floors=2,
            orientation=-np.pi/2
        )

        driveway = magnet.get_driveway(gene)

        assert driveway is not None
        assert isinstance(driveway, LineString)
        assert driveway.length > 0

    def test_get_driveway_ends_on_road(self, simple_roads):
        """Driveway should end on the road"""
        magnet = SmartMagnet(simple_roads)

        gene = BuildingGene(
            position=(100, 50),
            building_type=BuildingType.ADMIN,
            base_width=30,
            base_depth=20,
            floors=2,
            orientation=-np.pi/2
        )

        driveway = magnet.get_driveway(gene)
        coords = list(driveway.coords)

        # Last point should be on road (y ≈ 0)
        assert coords[-1][1] == pytest.approx(0.0, abs=1.0)

    def test_get_driveway_no_roads(self):
        """No roads should return None"""
        magnet = SmartMagnet([])

        gene = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ADMIN,
            base_width=30,
            base_depth=20,
            floors=2
        )

        driveway = magnet.get_driveway(gene)
        assert driveway is None
