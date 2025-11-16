"""
End-to-end integration tests for complete road generation pipeline.

Tests full workflow:
Building layout → Tensor field → Roads → Visualization
"""

import numpy as np
import pytest

try:
    from src.algorithms.building import Building, BuildingType

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

from src.spatial.road_network import RoadNetworkConfig, RoadNetworkGenerator


@pytest.mark.skipif(not WEEK1_AVAILABLE, reason="Week 1 code required")
class TestEndToEndRoadGeneration:
    """Test complete pipeline."""

    def test_simple_campus_road_generation(self):
        """Test generating roads for small campus."""
        # Create simple campus layout
        buildings = [
            Building("ADM-01", BuildingType.ADMINISTRATIVE, 1200, 3, position=(500, 500)),
            Building("LIB-01", BuildingType.LIBRARY, 1500, 2, position=(700, 300)),
            Building("RES-01", BuildingType.RESIDENTIAL, 800, 5, position=(300, 700)),
            Building("EDU-01", BuildingType.EDUCATIONAL, 1000, 3, position=(300, 300)),
        ]

        # Generate roads
        generator = RoadNetworkGenerator(bounds=(0, 0, 1000, 1000))
        major_roads, minor_roads = generator.generate(buildings)

        # Verify output
        assert len(major_roads) > 0, "Should generate major roads"
        assert len(minor_roads) > 0, "Should generate minor roads"

        # All roads should be (N, 2) arrays
        for road in major_roads + minor_roads:
            assert road.shape[1] == 2
            assert len(road) > 2

    def test_road_generation_performance(self):
        """Test generation completes in reasonable time."""
        import time

        # Create 10 buildings
        buildings = [
            Building(
                f"BLD-{i}",
                BuildingType.RESIDENTIAL,
                800,
                4,
                position=(100 + i * 80, 100 + (i % 3) * 250),
            )
            for i in range(10)
        ]

        generator = RoadNetworkGenerator(bounds=(0, 0, 1000, 1000))

        start = time.time()
        major, minor = generator.generate(buildings)
        elapsed = time.time() - start

        print(f"\n⏱️  Road generation (10 buildings): {elapsed:.2f}s")

        # Should complete in <5s (target from spec)
        assert elapsed < 5.0, f"Too slow: {elapsed:.2f}s"

    def test_road_network_config_override(self):
        """Test custom config parameters."""
        buildings = [Building("A", BuildingType.ADMINISTRATIVE, 1000, 3, position=(500, 500))]

        # Custom config
        config = RoadNetworkConfig(n_major_roads=2, n_agents_per_building=1)  # Fewer roads

        generator = RoadNetworkGenerator((0, 0, 1000, 1000))
        major, minor = generator.generate(buildings, config)

        # Should respect config
        assert len(major) <= 2

    def test_empty_building_list(self):
        """Test handling of empty building list."""
        buildings = []

        generator = RoadNetworkGenerator((0, 0, 1000, 1000))
        major, minor = generator.generate(buildings)

        # Should not crash
        # May have major roads (from perimeter seeds) but no minor
        assert isinstance(major, list)
        assert isinstance(minor, list)

    def test_statistics_generation(self):
        """Test road network statistics."""
        buildings = [
            Building("A", BuildingType.ADMINISTRATIVE, 1000, 3, position=(500, 500)),
            Building("B", BuildingType.RESIDENTIAL, 800, 5, position=(300, 300)),
        ]

        generator = RoadNetworkGenerator((0, 0, 1000, 1000))
        generator.generate(buildings)

        stats = generator.get_stats()

        assert "n_major_roads" in stats
        assert "n_minor_roads" in stats
        assert "total_length_m" in stats

        assert stats["n_major_roads"] >= 0
        assert stats["total_length_m"] >= 0


@pytest.mark.skipif(not WEEK1_AVAILABLE, reason="Week 1 code required")
def test_optimizer_integration():
    """Test road generation integrates with H-SAGA optimizer."""
    # This would test the full optimize() → roads pipeline
    # Requires full Week 1 optimizer code

    # Placeholder for now
    pass


def test_visualization_data_format():
    """Test roads are in correct format for Folium."""
    # Mock road
    road = np.array([[100, 200], [110, 210], [120, 220]])

    # Convert to Folium format (lat, lon)
    coords = [(p[1], p[0]) for p in road]

    assert len(coords) == 3
    assert coords[0] == (200, 100)  # (lat, lon)
