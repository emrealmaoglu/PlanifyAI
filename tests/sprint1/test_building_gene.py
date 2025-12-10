# tests/sprint1/test_building_gene.py
import pytest
import numpy as np
from backend.core.integration.building_geometry import (
    BuildingGene, BuildingType, ShapeType, EntranceSide, ShapeGenerator
)

class TestBuildingGene:
    """Unit tests for BuildingGene dataclass."""

    def test_shape_type_mapping_academic(self):
        """ACADEMIC → H_SHAPE"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ACADEMIC,
            base_width=50, base_depth=40, floors=4
        )
        assert gene.shape_type == ShapeType.H_SHAPE

    def test_shape_type_mapping_dormitory(self):
        """DORMITORY → U_SHAPE"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.DORMITORY,
            base_width=50, base_depth=40, floors=5
        )
        assert gene.shape_type == ShapeType.U_SHAPE

    def test_shape_type_mapping_social(self):
        """SOCIAL → L_SHAPE"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.SOCIAL,
            base_width=35, base_depth=25, floors=2
        )
        assert gene.shape_type == ShapeType.L_SHAPE

    def test_shape_type_mapping_admin(self):
        """ADMIN → RECTANGULAR"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ADMIN,
            base_width=30, base_depth=20, floors=3
        )
        assert gene.shape_type == ShapeType.RECTANGULAR

    def test_height_calculation(self):
        """Height = floors * 3.5m"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ACADEMIC,
            base_width=50, base_depth=40, floors=6
        )
        assert gene.height == 21.0  # 6 * 3.5

    def test_height_single_floor(self):
        """Single floor building height"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.ADMIN,
            base_width=20, base_depth=15, floors=1
        )
        assert gene.height == 3.5

    def test_default_orientation(self):
        """Default orientation should be 0.0"""
        gene = BuildingGene(
            position=(100, 200),
            building_type=BuildingType.SOCIAL,
            base_width=30, base_depth=25, floors=2
        )
        assert gene.orientation == 0.0

    def test_default_entrance_side(self):
        """Default entrance should be SOUTH"""
        gene = BuildingGene(
            position=(100, 200),
            building_type=BuildingType.SOCIAL,
            base_width=30, base_depth=25, floors=2
        )
        assert gene.entrance_side == EntranceSide.SOUTH

    def test_custom_entrance_side(self):
        """Custom entrance side assignment"""
        gene = BuildingGene(
            position=(0, 0),
            building_type=BuildingType.DORMITORY,
            base_width=50, base_depth=40, floors=5,
            entrance_side=EntranceSide.EAST
        )
        assert gene.entrance_side == EntranceSide.EAST
        assert gene.entrance_side.value == 90
