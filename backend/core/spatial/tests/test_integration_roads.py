"""End-to-end test: Generate complete road network."""

import numpy as np
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

from backend.core.spatial.basis_fields import GridField, RadialField
from backend.core.spatial.tensor_field import TensorField
from backend.core.spatial.streamline import StreamlineIntegrator, RoadNetworkGenerator


def test_complete_campus_road_network():
    """
    Generate and visualize complete road network for 5-field campus.

    This is the ultimate integration test for Phase 2.
    """
    # 1. Create 5-field campus layout (800×800m)
    fields = [
        GridField((250, 250), 50, theta=0, decay_radius=200),  # Main E-W
        GridField((400, 400), 50, theta=np.pi / 2, decay_radius=150),  # Main N-S
        RadialField((100, 100), decay_radius=120),  # Junction SW
        RadialField((700, 700), decay_radius=120),  # Junction NE
        GridField((500, 300), 50, theta=np.pi / 4, decay_radius=100),  # Diagonal
    ]

    tensor_field = TensorField(fields)
    boundary = Polygon([(0, 0), (800, 0), (800, 800), (0, 800)])

    # 2. Create integrator and generator
    integrator = StreamlineIntegrator(
        tensor_field=tensor_field,
        boundary_polygon=boundary,
        max_step=5.0,  # Tight curves
    )

    generator = RoadNetworkGenerator(integrator)

    # 3. Generate seed points (anisotropy-weighted)
    seeds = generator.generate_seed_points(
        bbox=(0, 0, 800, 800),
        grid_spacing=80,
        min_anisotropy=0.6,  # Only strong directional regions
    )

    print(f"Generated {len(seeds)} seed points")

    # 4. Generate road network
    roads = generator.generate_network(
        seed_points=seeds, field_type="major", min_road_length=30
    )

    print(f"Generated {len(roads)} roads")

    # 5. Compute metrics
    total_length = sum(
        np.sum(np.linalg.norm(np.diff(road, axis=0), axis=1)) for road in roads
    )
    print(f"Total road length: {total_length:.1f} meters")

    # 6. Visualize (overlay on tensor field)
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Left panel: Tensor field streamplot
    ax1 = axes[0]
    tensor_field.visualize(
        bbox=(0, 0, 800, 800),
        resolution=40,
        show_anisotropy=False,
        show_streamplot=True,
    )
    ax1.set_title("Tensor Field (Streamplot)")

    # Right panel: Generated road network
    ax2 = axes[1]

    # Plot roads
    for road in roads:
        ax2.plot(road[:, 0], road[:, 1], "r-", linewidth=2, alpha=0.7)

    # Plot seed points
    ax2.scatter(seeds[:, 0], seeds[:, 1], c="blue", s=20, alpha=0.5, label="Seeds")

    ax2.set_xlim(0, 800)
    ax2.set_ylim(0, 800)
    ax2.set_aspect("equal")
    ax2.set_title(f"Generated Road Network ({len(roads)} roads)")
    ax2.set_xlabel("X (meters)")
    ax2.set_ylabel("Y (meters)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save for thesis
    fig.savefig("/tmp/phase2_complete_road_network.png", dpi=150)
    print("✅ Visualization saved to /tmp/phase2_complete_road_network.png")

    # 7. Export GeoJSON
    generator.export_geojson(roads, "/tmp/campus_roads.geojson")

    # 8. Assertions
    assert len(roads) > 5, "Should generate multiple roads"
    assert total_length > 500, "Total network length should be substantial"

    print("✅ Phase 2 Complete! Road network generated successfully.")
