"""Tests for streamline integration."""

import pytest
import numpy as np
from shapely.geometry import Polygon

from backend.core.spatial.basis_fields import GridField, RadialField
from backend.core.spatial.tensor_field import TensorField
from backend.core.spatial.streamline import StreamlineIntegrator, RoadNetworkGenerator


class TestStreamlineIntegrator:
    """Test streamline integration logic."""

    @pytest.fixture
    def simple_grid_field(self):
        """Simple grid tensor field for testing."""
        field = GridField((250, 250), 50, theta=0, decay_radius=300)
        tensor_field = TensorField([field])
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])

        integrator = StreamlineIntegrator(
            tensor_field=tensor_field, boundary_polygon=boundary
        )

        return integrator

    def test_trace_stops_at_boundary(self, simple_grid_field):
        """
        PRIORITY TEST 1 (Gemini):
        Streamline must terminate at boundary.
        """
        integrator = simple_grid_field

        # Seed near edge (will hit boundary quickly)
        seed = np.array([450, 250])

        streamline = integrator.trace(seed, max_length=200)

        # Last point should be near/at boundary
        last_point = streamline[-1]
        assert last_point[0] <= 500, "Did not stop at boundary"

    def test_trace_stops_at_junction(self):
        """
        PRIORITY TEST 2 (Gemini):
        Streamline must stop at low-anisotropy regions (junctions).
        """
        # Create junction with radial field
        radial = RadialField((250, 250), decay_radius=150)
        tensor_field = TensorField([radial])
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])

        integrator = StreamlineIntegrator(
            tensor_field=tensor_field, boundary_polygon=boundary
        )

        # Seed outside radial center, trace toward it
        seed = np.array([350, 250])

        streamline = integrator.trace(seed, max_length=200, min_anisotropy=0.2)

        # Should stop near center (junction)
        # Since tracing is bidirectional, one end goes to boundary, one to junction
        # We check if the minimum distance of any point to center is small
        distances = np.linalg.norm(streamline - np.array([250, 250]), axis=1)
        min_distance = np.min(distances)
        
        assert min_distance < 50, f"Did not reach junction. Min distance: {min_distance}"

    def test_bidirectional_tracing(self, simple_grid_field):
        """
        PRIORITY TEST 3 (Gemini):
        Ensure road extends in BOTH directions from seed.
        """
        integrator = simple_grid_field

        seed = np.array([250, 250])  # Center

        streamline = integrator.trace(seed, max_length=100)

        # Check that road extends in both +x and -x directions
        x_coords = streamline[:, 0]

        assert np.min(x_coords) < seed[0], "No backward trace"
        assert np.max(x_coords) > seed[0], "No forward trace"

    def test_streamline_smoothness(self, simple_grid_field):
        """Streamline should be smooth (no large jumps)."""
        integrator = simple_grid_field

        seed = np.array([100, 250])
        streamline = integrator.trace(seed, max_length=200)

        # Check segment lengths
        segments = np.diff(streamline, axis=0)
        segment_lengths = np.linalg.norm(segments, axis=1)

        # No segment should be > max_step
        assert np.all(segment_lengths <= integrator.max_step + 1e-6)


class TestRoadNetworkGenerator:
    """Test complete road network generation."""

    def test_seed_generation(self):
        """Test anisotropy-weighted seeding."""
        # Create 5-field campus layout
        fields = [
            GridField((250, 250), 50, theta=0, decay_radius=150),
            RadialField((400, 400), decay_radius=100),
        ]
        tensor_field = TensorField(fields)
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])

        integrator = StreamlineIntegrator(tensor_field, boundary)
        generator = RoadNetworkGenerator(integrator)

        # Generate seeds
        seeds = generator.generate_seed_points(
            bbox=(0, 0, 500, 500), grid_spacing=50, min_anisotropy=0.5
        )

        # Should have some seeds (not empty)
        assert len(seeds) > 0

        # Seeds should avoid junction center (400, 400)
        distances_to_junction = np.linalg.norm(seeds - np.array([400, 400]), axis=1)
        assert np.all(distances_to_junction > 30), "Seeds too close to junction"

    def test_network_generation(self):
        """Test complete network generation."""
        field = GridField((250, 250), 50, theta=0, decay_radius=300)
        tensor_field = TensorField([field])
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])

        integrator = StreamlineIntegrator(tensor_field, boundary)
        generator = RoadNetworkGenerator(integrator)

        # Manual seeds
        seeds = np.array(
            [
                [100, 250],
                [250, 100],
                [400, 250],
            ]
        )

        roads = generator.generate_network(seeds, min_road_length=20)

        # Should generate some roads
        assert len(roads) > 0

        # Each road should be an array
        for road in roads:
            assert isinstance(road, np.ndarray)
            assert road.shape[1] == 2  # (N, 2)

    def test_geojson_export(self, tmp_path):
        """Test GeoJSON export."""
        field = GridField((250, 250), 50, theta=0, decay_radius=300)
        tensor_field = TensorField([field])
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])

        integrator = StreamlineIntegrator(tensor_field, boundary)
        generator = RoadNetworkGenerator(integrator)

        # Generate simple network
        seeds = np.array([[250, 250]])
        roads = generator.generate_network(seeds)

        # Export
        filepath = tmp_path / "test_roads.geojson"
        generator.export_geojson(roads, str(filepath))

        # Verify file exists
        assert filepath.exists()

        # Verify valid JSON
        import json

        with open(filepath) as f:
            data = json.load(f)

        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
