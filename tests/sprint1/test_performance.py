# tests/sprint1/test_performance.py
import pytest
import numpy as np
import time
from backend.core.integration.building_geometry import (
    BuildingGene, BuildingType, ShapeGenerator
)
from backend.core.integration.composite_genotype import (
    CompositeGenotype, TensorFieldParams, BuildingLayoutV2
)
from backend.core.integration.smart_magnet import SmartMagnet


class TestPerformance:
    """Performance benchmarks for Sprint 1 components."""

    def generate_random_genes(self, n: int) -> list:
        """Generate n random building genes."""
        types = list(BuildingType)
        genes = []
        for i in range(n):
            gene = BuildingGene(
                position=(np.random.uniform(0, 1000), np.random.uniform(0, 1000)),
                building_type=np.random.choice(types),
                base_width=np.random.uniform(30, 80),
                base_depth=np.random.uniform(20, 60),
                floors=np.random.randint(1, 10)
            )
            genes.append(gene)
        return genes

    def generate_random_roads(self, n: int) -> list:
        """Generate n random road segments."""
        roads = []
        for _ in range(n):
            start = np.array([np.random.uniform(0, 1000), np.random.uniform(0, 1000)])
            end = start + np.array([np.random.uniform(-200, 200), np.random.uniform(-200, 200)])
            roads.append(np.array([start, end]))
        return roads

    @pytest.mark.benchmark
    def test_shape_generation_10(self):
        """Benchmark: Generate 10 polygons"""
        genes = self.generate_random_genes(10)

        start = time.perf_counter()
        polygons = [ShapeGenerator.generate(g) for g in genes]
        elapsed = time.perf_counter() - start

        assert elapsed < 0.1, f"10 polygons took {elapsed*1000:.2f}ms (should be <100ms)"
        print(f"\n  10 polygons: {elapsed*1000:.2f}ms")

    @pytest.mark.benchmark
    def test_shape_generation_50(self):
        """Benchmark: Generate 50 polygons"""
        genes = self.generate_random_genes(50)

        start = time.perf_counter()
        polygons = [ShapeGenerator.generate(g) for g in genes]
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"50 polygons took {elapsed*1000:.2f}ms (should be <500ms)"
        print(f"\n  50 polygons: {elapsed*1000:.2f}ms")

    @pytest.mark.benchmark
    def test_shape_generation_100(self):
        """Benchmark: Generate 100 polygons"""
        genes = self.generate_random_genes(100)

        start = time.perf_counter()
        polygons = [ShapeGenerator.generate(g) for g in genes]
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"100 polygons took {elapsed*1000:.2f}ms (should be <1000ms)"
        print(f"\n  100 polygons: {elapsed*1000:.2f}ms")

    @pytest.mark.benchmark
    def test_smart_magnet_alignment_50(self):
        """Benchmark: Align 50 buildings to 20 roads"""
        genes = self.generate_random_genes(50)
        roads = self.generate_random_roads(20)
        magnet = SmartMagnet(roads)

        start = time.perf_counter()
        aligned = magnet.align_buildings(genes)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.05, f"50 alignments took {elapsed*1000:.2f}ms (should be <50ms)"
        print(f"\n  50 buildings / 20 roads: {elapsed*1000:.2f}ms")

    @pytest.mark.benchmark
    def test_smart_magnet_alignment_100(self):
        """Benchmark: Align 100 buildings to 50 roads"""
        genes = self.generate_random_genes(100)
        roads = self.generate_random_roads(50)
        magnet = SmartMagnet(roads)

        start = time.perf_counter()
        aligned = magnet.align_buildings(genes)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.1, f"100 alignments took {elapsed*1000:.2f}ms (should be <100ms)"
        print(f"\n  100 buildings / 50 roads: {elapsed*1000:.2f}ms")

    @pytest.mark.benchmark
    def test_serialization_roundtrip(self):
        """Benchmark: Serialize and deserialize genotype"""
        genes = self.generate_random_genes(50)
        layout = BuildingLayoutV2.from_genes(genes)

        tensor_params = TensorFieldParams(
            grid_centers=np.random.rand(5, 2) * 1000,
            grid_orientations=np.random.rand(5) * np.pi,
            grid_decay_radii=np.random.rand(5) * 100,
            radial_centers=np.random.rand(3, 2) * 1000,
            radial_decay_radii=np.random.rand(3) * 100
        )
        genotype = CompositeGenotype(tensor_params, layout)

        # Benchmark serialization
        start = time.perf_counter()
        for _ in range(100):
            flat = genotype.to_flat_array()
        serialize_time = (time.perf_counter() - start) / 100

        # Benchmark deserialization
        start = time.perf_counter()
        for _ in range(100):
            restored = CompositeGenotype.from_flat_array(
                flat, n_grids=5, n_radials=3, n_buildings=50
            )
        deserialize_time = (time.perf_counter() - start) / 100

        print(f"\n  Serialize (50 buildings): {serialize_time*1000:.3f}ms")
        print(f"  Deserialize (50 buildings): {deserialize_time*1000:.3f}ms")

        assert serialize_time < 0.001, "Serialization too slow"
        assert deserialize_time < 0.001, "Deserialization too slow"

    @pytest.mark.benchmark
    def test_full_pipeline_50_buildings(self):
        """Benchmark: Full pipeline with 50 buildings"""
        genes = self.generate_random_genes(50)
        roads = self.generate_random_roads(20)

        start = time.perf_counter()

        # Step 1: Create layout
        layout = BuildingLayoutV2.from_genes(genes)

        # Step 2: Align to roads
        magnet = SmartMagnet(roads)
        aligned_genes = magnet.align_buildings(genes)

        # Step 3: Generate all polygons
        polygons = [ShapeGenerator.generate(g) for g in aligned_genes]

        # Step 4: Generate driveways
        driveways = [magnet.get_driveway(g) for g in aligned_genes]

        elapsed = time.perf_counter() - start

        print(f"\n  Full pipeline (50 buildings, 20 roads): {elapsed*1000:.2f}ms")

        assert elapsed < 0.5, f"Full pipeline took {elapsed*1000:.2f}ms (should be <500ms)"
