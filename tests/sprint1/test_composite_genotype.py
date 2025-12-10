# tests/sprint1/test_composite_genotype.py
import pytest
import numpy as np
from backend.core.integration.composite_genotype import (
    CompositeGenotype, TensorFieldParams, BuildingLayoutV2
)
from backend.core.integration.building_geometry import BuildingType, EntranceSide

class TestBuildingLayoutV2:
    """Unit tests for BuildingLayoutV2."""

    @pytest.fixture
    def sample_layout(self):
        return BuildingLayoutV2(
            positions=np.array([[100, 100], [200, 200], [300, 300]]),
            building_types=np.array([0, 1, 2]),
            base_widths=np.array([50.0, 60.0, 40.0]),
            base_depths=np.array([40.0, 45.0, 30.0]),
            floors=np.array([4, 6, 2]),
            orientations=np.array([0.0, 0.5, 1.0]),
            entrance_sides=np.array([180, 90, 270])
        )

    def test_to_building_genes_count(self, sample_layout):
        """Should create correct number of genes"""
        genes = sample_layout.to_building_genes()
        assert len(genes) == 3

    def test_to_building_genes_types(self, sample_layout):
        """Should preserve building types"""
        genes = sample_layout.to_building_genes()
        assert genes[0].building_type == BuildingType.ACADEMIC
        assert genes[1].building_type == BuildingType.DORMITORY
        assert genes[2].building_type == BuildingType.SOCIAL

    def test_to_building_genes_positions(self, sample_layout):
        """Should preserve positions"""
        genes = sample_layout.to_building_genes()
        assert genes[0].position == (100, 100)
        assert genes[1].position == (200, 200)

    def test_to_polygons_valid(self, sample_layout):
        """Should create valid polygons"""
        polygons = sample_layout.to_polygons()
        assert len(polygons) == 3
        for poly in polygons:
            assert poly.is_valid
            assert poly.area > 0

    def test_from_genes_roundtrip(self, sample_layout):
        """from_genes should be inverse of to_building_genes"""
        genes = sample_layout.to_building_genes()
        restored = BuildingLayoutV2.from_genes(genes)

        np.testing.assert_array_almost_equal(
            restored.positions, sample_layout.positions
        )
        np.testing.assert_array_equal(
            restored.building_types, sample_layout.building_types
        )


class TestCompositeGenotype:
    """Unit tests for CompositeGenotype."""

    @pytest.fixture
    def sample_genotype(self):
        tensor_params = TensorFieldParams(
            grid_centers=np.array([[100, 100], [200, 200]]),
            grid_orientations=np.array([0.0, np.pi/4]),
            grid_decay_radii=np.array([50.0, 60.0]),
            radial_centers=np.array([[150, 150]]),
            radial_decay_radii=np.array([40.0])
        )
        building_layout = BuildingLayoutV2(
            positions=np.array([[50, 50], [100, 100], [150, 150]]),
            building_types=np.array([0, 1, 2]),
            base_widths=np.array([40.0, 50.0, 35.0]),
            base_depths=np.array([30.0, 40.0, 25.0]),
            floors=np.array([3, 5, 2]),
            orientations=np.array([0.0, 0.5, 1.0]),
            entrance_sides=np.array([180, 90, 270])
        )
        return CompositeGenotype(tensor_params, building_layout)

    def test_to_flat_array_is_1d(self, sample_genotype):
        """Flattened array should be 1D"""
        flat = sample_genotype.to_flat_array()
        assert flat.ndim == 1

    def test_to_flat_array_all_numeric(self, sample_genotype):
        """All values should be numeric (float)"""
        flat = sample_genotype.to_flat_array()
        assert flat.dtype in [np.float64, np.float32]

    def test_chromosome_size_calculation(self):
        """get_chromosome_size should match actual array length"""
        n_grids, n_radials, n_buildings = 2, 1, 3
        expected = CompositeGenotype.get_chromosome_size(n_grids, n_radials, n_buildings)

        # Create genotype with these dimensions
        tensor_params = TensorFieldParams(
            grid_centers=np.zeros((n_grids, 2)),
            grid_orientations=np.zeros(n_grids),
            grid_decay_radii=np.zeros(n_grids),
            radial_centers=np.zeros((n_radials, 2)),
            radial_decay_radii=np.zeros(n_radials)
        )
        building_layout = BuildingLayoutV2(
            positions=np.zeros((n_buildings, 2)),
            building_types=np.zeros(n_buildings),
            base_widths=np.zeros(n_buildings),
            base_depths=np.zeros(n_buildings),
            floors=np.zeros(n_buildings),
            orientations=np.zeros(n_buildings),
            entrance_sides=np.zeros(n_buildings)
        )
        genotype = CompositeGenotype(tensor_params, building_layout)
        actual = len(genotype.to_flat_array())

        assert actual == expected, f"Expected {expected}, got {actual}"

    def test_serialization_roundtrip(self, sample_genotype):
        """to_flat_array → from_flat_array should preserve data"""
        flat = sample_genotype.to_flat_array()
        restored = CompositeGenotype.from_flat_array(
            flat, n_grids=2, n_radials=1, n_buildings=3
        )

        # Check tensor params
        np.testing.assert_array_almost_equal(
            restored.tensor_params.grid_centers,
            sample_genotype.tensor_params.grid_centers
        )

        # Check building layout
        np.testing.assert_array_almost_equal(
            restored.building_layout.positions,
            sample_genotype.building_layout.positions
        )
        np.testing.assert_array_equal(
            restored.building_layout.floors,
            sample_genotype.building_layout.floors
        )

    def test_pymoo_compatibility(self, sample_genotype):
        """Array should be compatible with pymoo (all floats, no NaN)"""
        flat = sample_genotype.to_flat_array()
        assert not np.any(np.isnan(flat)), "Array contains NaN"
        assert not np.any(np.isinf(flat)), "Array contains Inf"
        assert flat.dtype == np.float64, "Array should be float64"


class TestLegacyRemoval:
    """Verify Boy Scout rule: old classes removed."""

    def test_old_building_layout_removed(self):
        """BuildingLayout class should not exist"""
        from backend.core.integration import composite_genotype
        assert not hasattr(composite_genotype, 'BuildingLayout'), \
            "BOY SCOUT VIOLATION: Old BuildingLayout still exists"

    def test_building_layout_v2_exists(self):
        """BuildingLayoutV2 should exist"""
        from backend.core.integration import composite_genotype
        assert hasattr(composite_genotype, 'BuildingLayoutV2')
