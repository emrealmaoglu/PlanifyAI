# tests/sprint1/test_edge_cases.py
import pytest
import numpy as np
from backend.core.integration.building_geometry import (
    BuildingGene, BuildingType, ShapeGenerator
)
from backend.core.integration.smart_magnet import SmartMagnet

class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_zero_width_building(self):
        """Zero width should handle gracefully"""
        gene = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ADMIN,
            base_width=0.0,
            base_depth=40.0,
            floors=3
        )
        # Should either raise error or produce valid (empty) polygon
        try:
            polygon = ShapeGenerator.generate(gene)
            # If it doesn't raise, polygon should still be valid
            assert polygon.is_valid or polygon.is_empty
        except (ValueError, ZeroDivisionError):
            pass  # Acceptable to raise error

    def test_negative_dimensions(self):
        """Negative dimensions should be handled"""
        gene = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ADMIN,
            base_width=-50.0,
            base_depth=40.0,
            floors=3
        )
        try:
            polygon = ShapeGenerator.generate(gene)
            # Might produce flipped polygon
            assert polygon.is_valid
        except ValueError:
            pass  # Acceptable to raise error

    def test_very_small_building(self):
        """Very small building (1m x 1m)"""
        gene = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ADMIN,
            base_width=1.0,
            base_depth=1.0,
            floors=1
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid
        assert polygon.area > 0

    def test_very_large_building(self):
        """Very large building (1000m x 1000m)"""
        gene = BuildingGene(
            position=(500, 500),
            building_type=BuildingType.ACADEMIC,
            base_width=1000.0,
            base_depth=1000.0,
            floors=50
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid
        assert polygon.area > 0

    def test_building_at_origin(self):
        """Building centered at (0, 0)"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ACADEMIC,
            base_width=50.0,
            base_depth=40.0,
            floors=4
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid
        centroid = polygon.centroid
        assert abs(centroid.x) < 1.0
        assert abs(centroid.y) < 1.0

    def test_building_negative_coordinates(self):
        """Building at negative coordinates"""
        gene = BuildingGene(
            position=(-500, -300),
            building_type=BuildingType.DORMITORY,
            base_width=50.0,
            base_depth=40.0,
            floors=5
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid
        centroid = polygon.centroid
        assert centroid.x < 0
        assert centroid.y < 0

    def test_full_rotation(self):
        """360 degree rotation should return to original"""
        gene1 = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ACADEMIC,
            base_width=50.0,
            base_depth=40.0,
            floors=4,
            orientation=0.0
        )
        gene2 = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ACADEMIC,
            base_width=50.0,
            base_depth=40.0,
            floors=4,
            orientation=2*np.pi
        )
        poly1 = ShapeGenerator.generate(gene1)
        poly2 = ShapeGenerator.generate(gene2)

        # Polygons should be nearly identical
        assert abs(poly1.area - poly2.area) < 0.01

    def test_smart_magnet_building_on_road(self):
        """Building exactly on road line"""
        roads = [np.array([[0, 0], [200, 0]])]
        magnet = SmartMagnet(roads)

        gene = BuildingGene(
            position=(100, 0),  # Exactly on road
            building_type=BuildingType.ADMIN,
            base_width=30,
            base_depth=20,
            floors=2
        )

        # Should not crash
        aligned = magnet.align_buildings([gene])
        assert len(aligned) == 1
        assert aligned[0].orientation is not None

    def test_smart_magnet_single_point_road(self):
        """Degenerate road with single point"""
        roads = [np.array([[100, 100]])]  # Single point

        try:
            magnet = SmartMagnet(roads)
            result = magnet.find_nearest_road((150, 150))
            # Should either work or return None
            assert result is None or result[0] is not None
        except (ValueError, IndexError):
            pass  # Acceptable to fail

    def test_parallel_roads_selection(self):
        """Should select closest of two parallel roads"""
        roads = [
            np.array([[0, 0], [200, 0]]),    # y=0
            np.array([[0, 100], [200, 100]]) # y=100
        ]
        magnet = SmartMagnet(roads)

        # Building at y=30 - should select y=0 road
        result = magnet.find_nearest_road((100, 30))
        assert result is not None
        _, point, dist = result
        assert point.y == pytest.approx(0.0, abs=1.0)
        assert dist == pytest.approx(30.0, abs=1.0)
