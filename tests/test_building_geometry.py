import pytest
import numpy as np
from backend.core.integration.building_geometry import BuildingGene, BuildingType, ShapeGenerator, ShapeType

def test_all_shapes_generate_valid_polygons():
    """Every ShapeType must produce a valid, non-empty Polygon."""
    for bt in BuildingType:
        gene = BuildingGene(
            position=(100.0, 100.0),
            building_type=bt,
            base_width=40.0,
            base_depth=30.0,
            floors=3
        )
        polygon = ShapeGenerator.generate(gene)
        assert polygon.is_valid, f"{bt.name} produced invalid polygon"
        assert polygon.area > 0, f"{bt.name} produced zero-area polygon"
        assert not polygon.is_empty, f"{bt.name} produced empty polygon"

def test_rotation_preserves_area():
    """Rotation must not change polygon area."""
    gene = BuildingGene(
        position=(0, 0),
        building_type=BuildingType.ACADEMIC,
        base_width=50.0,
        base_depth=40.0,
        floors=4,
        orientation=0.0
    )
    area_0 = ShapeGenerator.generate(gene).area
    
    gene.orientation = np.pi / 4  # 45 degrees
    area_45 = ShapeGenerator.generate(gene).area
    
    assert abs(area_0 - area_45) < 0.01, "Rotation changed area"

def test_translation_to_position():
    """Polygon centroid must match gene.position."""
    pos = (500.0, 300.0)
    gene = BuildingGene(
        position=pos,
        building_type=BuildingType.DORMITORY,
        base_width=60.0,
        base_depth=45.0,
        floors=5
    )
    polygon = ShapeGenerator.generate(gene)
    centroid = polygon.centroid
    
    assert abs(centroid.x - pos[0]) < 1.0, "X translation failed"
    assert abs(centroid.y - pos[1]) < 1.0, "Y translation failed"
