import numpy as np
import pytest
from shapely.geometry import Polygon, box

from backend.core.integration.composite_genotype import (
    CompositeGenotype, TensorFieldParams, BuildingLayoutV2
)
from backend.core.integration.building_geometry import BuildingType, EntranceSide


def test_roundtrip_serialization():
    """to_flat_array → from_flat_array must preserve all data."""
    n_grids, n_radials, n_buildings = 2, 1, 5
    
    # Create test data
    tensor_params = TensorFieldParams(
        grid_centers=np.array([[100, 100], [200, 200]]),
        grid_orientations=np.array([0.0, np.pi/4]),
        grid_decay_radii=np.array([50.0, 60.0]),
        radial_centers=np.array([[150, 150]]),
        radial_decay_radii=np.array([40.0])
    )
    
    building_layout = BuildingLayoutV2(
        positions=np.array([[50, 50], [100, 100], [150, 150], [200, 200], [250, 250]]),
        building_types=np.array([0, 1, 2, 3, 0]),  # ACADEMIC, DORMITORY, SOCIAL, ADMIN, ACADEMIC
        base_widths=np.array([40.0, 50.0, 35.0, 30.0, 45.0]),
        base_depths=np.array([30.0, 40.0, 25.0, 20.0, 35.0]),
        floors=np.array([3, 5, 2, 4, 6]),
        orientations=np.array([0.0, 0.5, 1.0, 1.5, 2.0]),
        entrance_sides=np.array([0, 90, 180, 270, 0])
    )
    
    original = CompositeGenotype(tensor_params, building_layout)
    
    # Serialize
    flat = original.to_flat_array()
    
    # Verify chromosome size
    expected_size = CompositeGenotype.get_chromosome_size(n_grids, n_radials, n_buildings)
    assert len(flat) == expected_size, f"Expected {expected_size}, got {len(flat)}"
    
    # Deserialize
    restored = CompositeGenotype.from_flat_array(flat, n_grids, n_radials, n_buildings)
    
    # Verify building layout
    np.testing.assert_array_almost_equal(
        restored.building_layout.positions, 
        original.building_layout.positions
    )
    np.testing.assert_array_equal(
        restored.building_layout.building_types,
        original.building_layout.building_types
    )
    np.testing.assert_array_almost_equal(
        restored.building_layout.base_widths,
        original.building_layout.base_widths
    )
    np.testing.assert_array_equal(
        restored.building_layout.floors,
        original.building_layout.floors
    )


def test_to_building_genes_creates_valid_genes():
    """BuildingLayoutV2.to_building_genes must create valid BuildingGene objects."""
    layout = BuildingLayoutV2(
        positions=np.array([[100, 100], [200, 200]]),
        building_types=np.array([1, 2]),  # DORMITORY, SOCIAL
        base_widths=np.array([50.0, 40.0]),
        base_depths=np.array([40.0, 30.0]),
        floors=np.array([5, 3]),
        orientations=np.array([0.0, np.pi/2]),
        entrance_sides=np.array([180, 270])
    )
    
    genes = layout.to_building_genes()
    
    assert len(genes) == 2
    assert genes[0].building_type == BuildingType.DORMITORY
    assert genes[1].building_type == BuildingType.SOCIAL
    assert genes[0].floors == 5
    assert genes[1].orientation == pytest.approx(np.pi/2)


def test_to_polygons_generates_valid_shapes():
    """BuildingLayoutV2.to_polygons must create valid Shapely Polygons."""
    layout = BuildingLayoutV2(
        positions=np.array([[100, 100], [300, 300]]),
        building_types=np.array([0, 1]),  # ACADEMIC (H), DORMITORY (U)
        base_widths=np.array([60.0, 50.0]),
        base_depths=np.array([45.0, 40.0]),
        floors=np.array([4, 6]),
        orientations=np.array([0.0, 0.0]),
        entrance_sides=np.array([180, 180])
    )
    
    polygons = layout.to_polygons()
    
    assert len(polygons) == 2
    for poly in polygons:
        assert poly.is_valid, "Polygon is not valid"
        assert poly.area > 0, "Polygon has zero area"
        assert not poly.is_empty, "Polygon is empty"


def test_old_building_layout_class_deleted():
    """Verify Boy Scout rule: old BuildingLayout class must not exist."""
    from backend.core.integration import composite_genotype
    
    assert not hasattr(composite_genotype, 'BuildingLayout'), \
        "BOY SCOUT VIOLATION: Old BuildingLayout class still exists!"
