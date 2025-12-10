# tests/sprint1/test_integration.py
import pytest
import numpy as np
from shapely.geometry import Polygon, box

from backend.core.integration.building_geometry import (
    BuildingGene, BuildingType, ShapeGenerator
)
from backend.core.integration.composite_genotype import (
    CompositeGenotype, TensorFieldParams, BuildingLayoutV2
)
from backend.core.integration.smart_magnet import SmartMagnet


class TestEndToEndPipeline:
    """Integration tests for complete Sprint 1 pipeline."""

    @pytest.fixture
    def campus_boundary(self):
        """500x400m campus boundary"""
        return box(0, 0, 500, 400)

    @pytest.fixture
    def sample_roads(self):
        """Sample road network"""
        return [
            np.array([[50, 200], [450, 200]]),   # Main horizontal
            np.array([[250, 50], [250, 350]]),   # Main vertical
            np.array([[50, 50], [200, 50]]),     # Secondary
        ]

    @pytest.fixture
    def sample_genes(self):
        """Sample building genes"""
        return [
            BuildingGene((100, 100), BuildingType.ACADEMIC, 60, 45, 4),
            BuildingGene((100, 300), BuildingType.DORMITORY, 50, 40, 6),
            BuildingGene((350, 100), BuildingType.SOCIAL, 40, 30, 2),
            BuildingGene((350, 300), BuildingType.ADMIN, 35, 25, 3),
            BuildingGene((200, 200), BuildingType.ACADEMIC, 70, 50, 5),
        ]

    def test_full_pipeline_no_overlap(self, sample_genes, sample_roads):
        """Complete pipeline should not crash"""
        # 1. Generate polygons
        polygons = [ShapeGenerator.generate(gene) for gene in sample_genes]

        # 2. Align to roads
        magnet = SmartMagnet(sample_roads)
        aligned_genes = magnet.align_buildings(sample_genes)

        # 3. Regenerate polygons with new orientations
        aligned_polygons = [ShapeGenerator.generate(gene) for gene in aligned_genes]

        # 4. Verify all polygons are valid
        for poly in aligned_polygons:
            assert poly.is_valid
            assert poly.area > 0

    def test_genotype_to_polygons(self, sample_genes):
        """BuildingLayoutV2 should produce valid polygons"""
        layout = BuildingLayoutV2.from_genes(sample_genes)
        polygons = layout.to_polygons()

        assert len(polygons) == len(sample_genes)
        for poly in polygons:
            assert poly.is_valid

    def test_serialization_preserves_geometry(self, sample_genes):
        """Serialization roundtrip should preserve polygon geometry"""
        # Create layout
        layout = BuildingLayoutV2.from_genes(sample_genes)
        original_polygons = layout.to_polygons()
        original_areas = [p.area for p in original_polygons]

        # Create genotype
        tensor_params = TensorFieldParams(
            grid_centers=np.array([[100, 100]]),
            grid_orientations=np.array([0.0]),
            grid_decay_radii=np.array([50.0]),
            radial_centers=np.array([[200, 200]]),
            radial_decay_radii=np.array([40.0])
        )
        genotype = CompositeGenotype(tensor_params, layout)

        # Serialize and deserialize
        flat = genotype.to_flat_array()
        restored = CompositeGenotype.from_flat_array(
            flat, n_grids=1, n_radials=1, n_buildings=5
        )

        # Check polygons
        restored_polygons = restored.building_layout.to_polygons()
        restored_areas = [p.area for p in restored_polygons]

        for orig, rest in zip(original_areas, restored_areas):
            assert abs(orig - rest) < 0.1, "Area changed after serialization"

    def test_smart_magnet_integration(self, sample_genes, sample_roads):
        """SmartMagnet should work with ShapeGenerator"""
        magnet = SmartMagnet(sample_roads)
        aligned = magnet.align_buildings(sample_genes)

        for gene in aligned:
            polygon = ShapeGenerator.generate(gene)
            driveway = magnet.get_driveway(gene)

            assert polygon.is_valid
            if driveway is not None:
                assert driveway.is_valid


class TestCollisionDetection:
    """Test building overlap detection."""

    def test_no_self_intersection(self):
        """Generated polygons should not self-intersect"""
        for building_type in BuildingType:
            gene = BuildingGene(
                position=(100, 100),
                building_type=building_type,
                base_width=50,
                base_depth=40,
                floors=3
            )
            polygon = ShapeGenerator.generate(gene)
            assert polygon.is_valid
            assert polygon.is_simple  # No self-intersection

    def test_detect_overlap(self):
        """Two overlapping buildings should be detected"""
        gene1 = BuildingGene((100, 100), BuildingType.ACADEMIC, 50, 40, 3)
        gene2 = BuildingGene((120, 110), BuildingType.DORMITORY, 50, 40, 5)

        poly1 = ShapeGenerator.generate(gene1)
        poly2 = ShapeGenerator.generate(gene2)

        # These should overlap
        assert poly1.intersects(poly2)

    def test_no_overlap(self):
        """Distant buildings should not overlap"""
        gene1 = BuildingGene((100, 100), BuildingType.ACADEMIC, 50, 40, 3)
        gene2 = BuildingGene((300, 300), BuildingType.DORMITORY, 50, 40, 5)

        poly1 = ShapeGenerator.generate(gene1)
        poly2 = ShapeGenerator.generate(gene2)

        assert not poly1.intersects(poly2)
