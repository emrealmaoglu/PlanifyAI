"""
Visual quality check for generated road networks.

Generates example layouts and saves visualizations for manual inspection.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

try:
    from src.algorithms.building import Building, BuildingType

    BUILDINGS_AVAILABLE = True
except ImportError:
    BUILDINGS_AVAILABLE = False

    # Create mock Building class
    class BuildingType:
        ADMIN = "administrative"
        RESIDENTIAL = "residential"
        EDUCATIONAL = "educational"

    class Building:
        def __init__(self, id, type, position, area, floors):
            self.id = id
            self.type = type
            self.position = position
            self.area = area
            self.floors = floors

        @property
        def footprint(self):
            return self.area / self.floors


from src.spatial.road_network import RoadNetworkGenerator


def visualize_road_network(buildings, major_roads, minor_roads, bounds, save_path=None):
    """
    Create comprehensive visualization of road network.
    """
    fig, ax = plt.subplots(figsize=(12, 12))

    xmin, ymin, xmax, ymax = bounds

    # Plot buildings
    for building in buildings:
        x, y = building.position
        radius = np.sqrt(building.footprint / np.pi)

        color = {
            "administrative": "#E74C3C",
            "residential": "#3498DB",
            "educational": "#2ECC71",
            "library": "#F39C12",
        }.get(
            building.type.value if hasattr(building.type, "value") else building.type,
            "#95A5A6",
        )

        circle = Circle((x, y), radius, color=color, alpha=0.3, ec="black", lw=2)
        ax.add_patch(circle)

        ax.text(x, y, building.id, ha="center", va="center", fontsize=8)

    # Plot major roads
    for i, road in enumerate(major_roads):
        ax.plot(
            road[:, 0],
            road[:, 1],
            "r-",
            linewidth=3,
            alpha=0.8,
            label="Major" if i == 0 else "",
        )

    # Plot minor roads
    for i, road in enumerate(minor_roads):
        ax.plot(
            road[:, 0],
            road[:, 1],
            "b-",
            linewidth=1.5,
            alpha=0.6,
            label="Minor" if i == 0 else "",
        )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title("Generated Road Network", fontsize=14, fontweight="bold")
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ Saved visualization to {save_path}")
    else:
        plt.show()


def main():
    """Generate test visualizations."""

    # Test Case 1: Simple 4-building campus
    print("Test Case 1: Simple campus (4 buildings)")
    buildings1 = [
        Building("ADM", "administrative", [500, 500], 1200, 3),
        Building("LIB", "library", [700, 300], 1500, 2),
        Building("RES", "residential", [300, 700], 800, 5),
        Building("EDU", "educational", [300, 300], 1000, 3),
    ]

    # Convert to Building objects if needed
    if BUILDINGS_AVAILABLE:
        buildings1 = [
            Building("ADM", BuildingType.ADMINISTRATIVE, (500, 500), 1200, 3),
            Building("LIB", BuildingType.LIBRARY, (700, 300), 1500, 2),
            Building("RES", BuildingType.RESIDENTIAL, (300, 700), 800, 5),
            Building("EDU", BuildingType.EDUCATIONAL, (300, 300), 1000, 3),
        ]

    gen1 = RoadNetworkGenerator((0, 0, 1000, 1000))
    major1, minor1 = gen1.generate(buildings1)

    visualize_road_network(
        buildings1, major1, minor1, (0, 0, 1000, 1000), save_path="outputs/day2_simple_campus.png"
    )

    print(gen1.get_stats())

    # Test Case 2: Larger campus (10 buildings)
    print("\nTest Case 2: Larger campus (10 buildings)")
    np.random.seed(42)
    buildings2 = []
    for i in range(10):
        pos = [100 + i * 80, 100 + (i % 3) * 250]
        area = np.random.uniform(600, 1500)
        if BUILDINGS_AVAILABLE:
            buildings2.append(
                Building(
                    f"B{i}",
                    BuildingType.RESIDENTIAL,
                    tuple(pos),
                    area,
                    np.random.randint(2, 6),
                )
            )
        else:
            buildings2.append(Building(f"B{i}", "residential", pos, area, np.random.randint(2, 6)))

    gen2 = RoadNetworkGenerator((0, 0, 1000, 1000))
    major2, minor2 = gen2.generate(buildings2)

    visualize_road_network(
        buildings2, major2, minor2, (0, 0, 1000, 1000), save_path="outputs/day2_large_campus.png"
    )

    print(gen2.get_stats())

    print("\n✅ All test cases complete. Check outputs/ directory.")


if __name__ == "__main__":
    import os

    os.makedirs("outputs", exist_ok=True)
    main()
