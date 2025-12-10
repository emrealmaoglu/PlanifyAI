# tests/sprint1/test_shape_generator.py
import pytest
import numpy as np
from shapely.geometry import Polygon
from shapely.validation import make_valid
from backend.core.integration.building_geometry import (
    BuildingGene, BuildingType, ShapeGenerator
)

class TestShapeGenerator:
    """Unit tests for ShapeGenerator polygon factory."""

    @pytest.fixture
    def standard_dimensions(self):
        return {"base_width": 50.0, "base_depth": 40.0}

    def test_rectangular_is_valid_polygon(self, standard_dimensions):
        """Rectangular shape produces valid polygon"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ADMIN,
            floors=3,
            **standard_dimensions
        )
        polygon = ShapeGenerator.generate(gene)
        assert isinstance(polygon, Polygon)
        assert polygon.is_valid
        assert not polygon.is_empty

    def test_l_shape_is_valid_polygon(self, standard_dimensions):
        """L-shape produces valid polygon"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.SOCIAL,
            floors=2,
            **standard_dimensions
        )
        polygon = ShapeGenerator.generate(gene)
        assert isinstance(polygon, Polygon)
        assert polygon.is_valid
        assert not polygon.is_empty

    def test_u_shape_is_valid_polygon(self, standard_dimensions):
        """U-shape produces valid polygon"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.DORMITORY,
            floors=5,
            **standard_dimensions
        )
        polygon = ShapeGenerator.generate(gene)
        assert isinstance(polygon, Polygon)
        assert polygon.is_valid
        assert not polygon.is_empty

    def test_h_shape_is_valid_polygon(self, standard_dimensions):
        """H-shape produces valid polygon"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ACADEMIC,
            floors=4,
            **standard_dimensions
        )
        polygon = ShapeGenerator.generate(gene)
        assert isinstance(polygon, Polygon)
        assert polygon.is_valid
        assert not polygon.is_empty

    def test_u_shape_has_courtyard(self, standard_dimensions):
        """U-shape area < rectangular area (has courtyard)"""
        rect_gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ADMIN,
            floors=3,
            **standard_dimensions
        )
        u_gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.DORMITORY,
            floors=3,
            **standard_dimensions
        )
        rect_area = ShapeGenerator.generate(rect_gene).area
        u_area = ShapeGenerator.generate(u_gene).area
        assert u_area < rect_area, "U-shape should have smaller area due to courtyard"

    def test_h_shape_has_notches(self, standard_dimensions):
        """H-shape area < rectangular area (has notches)"""
        rect_gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ADMIN,
            floors=3,
            **standard_dimensions
        )
        h_gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ACADEMIC,
            floors=3,
            **standard_dimensions
        )
        rect_area = ShapeGenerator.generate(rect_gene).area
        h_area = ShapeGenerator.generate(h_gene).area
        assert h_area < rect_area, "H-shape should have smaller area due to notches"

    def test_rotation_preserves_area(self, standard_dimensions):
        """Rotation should not change polygon area"""
        gene1 = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ACADEMIC,
            floors=4,
            orientation=0.0,
            **standard_dimensions
        )
        gene2 = BuildingGene(
            position=(100, 100),
            building_type=BuildingType.ACADEMIC,
            floors=4,
            orientation=np.pi/4,  # 45 degrees
            **standard_dimensions
        )
        area1 = ShapeGenerator.generate(gene1).area
        area2 = ShapeGenerator.generate(gene2).area
        assert abs(area1 - area2) < 0.1, "Rotation changed area"

    def test_translation_to_position(self, standard_dimensions):
        """Polygon centroid should match gene position"""
        pos = (500.0, 300.0)
        gene = BuildingGene(
            position=pos,
            building_type=BuildingType.DORMITORY,
            floors=5,
            **standard_dimensions
        )
        polygon = ShapeGenerator.generate(gene)
        centroid = polygon.centroid
        assert abs(centroid.x - pos[0]) < 1.0, "X translation incorrect"
        assert abs(centroid.y - pos[1]) < 1.0, "Y translation incorrect"

    def test_small_dimensions(self):
        """Small buildings should still produce valid polygons"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ADMIN,
            base_width=10.0,
            base_depth=8.0,
            floors=1
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid
        assert polygon.area > 0

    def test_large_dimensions(self):
        """Large buildings should produce valid polygons"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ACADEMIC,
            base_width=200.0,
            base_depth=150.0,
            floors=10
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid
        assert polygon.area > 0

    def test_extreme_aspect_ratio(self):
        """Extreme aspect ratios should still work"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.DORMITORY,
            base_width=100.0,
            base_depth=20.0,  # Very narrow
            floors=3
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid

    def test_all_rotation_angles(self):
        """Test various rotation angles"""
        angles = [0, np.pi/6, np.pi/4, np.pi/3, np.pi/2, np.pi, 3*np.pi/2]
        for angle in angles:
            gene = BuildingGene(
                position=(100, 100),
                building_type=BuildingType.SOCIAL,
                base_width=40,
                base_depth=30,
                floors=2,
                orientation=angle
            )
            polygon = ShapeGenerator.generate(gene)
            assert polygon.is_valid, f"Invalid polygon at angle {angle}"
