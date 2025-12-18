"""
Debug visualization tool for tensor fields.

Generates plots showing:
1. Eigenvector field (quiver plot)
2. Tensor magnitude heatmap
3. Basis field contributions

Usage:
    python scripts/visualize_tensor_field.py --output debug_field.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spatial.tensor_field import TensorField


def visualize_tensor_field(
    field: TensorField,
    resolution: int = 30,
    save_path: str = None,
):
    """
    Create comprehensive visualization of tensor field.

    Args:
        field: TensorField instance
        resolution: Grid density for visualization
        save_path: Optional path to save figure
    """
    xmin, ymin, xmax, ymax = field.config.bounds

    # Create visualization grid
    x = np.linspace(xmin, xmax, resolution)
    y = np.linspace(ymin, ymax, resolution)
    X, Y = np.meshgrid(x, y)
    points = np.column_stack([X.ravel(), Y.ravel()])

    # Compute eigenvectors
    major_vecs = field.get_eigenvectors(points, field_type="major")
    minor_vecs = field.get_eigenvectors(points, field_type="minor")

    # Compute tensor magnitudes (Frobenius norm)
    tensors = field.get_tensor_at_points(points)
    magnitudes = np.array([np.linalg.norm(T) for T in tensors])

    # Reshape for plotting
    U_major = major_vecs[:, 0].reshape(X.shape)
    V_major = major_vecs[:, 1].reshape(X.shape)
    U_minor = minor_vecs[:, 0].reshape(X.shape)
    V_minor = minor_vecs[:, 1].reshape(X.shape)
    M = magnitudes.reshape(X.shape)

    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Plot 1: Major eigenvector field
    ax1 = axes[0]
    ax1.quiver(X, Y, U_major, V_major, M, cmap="viridis", scale=25)
    ax1.set_title("Major Eigenvector Field (Primary Road Direction)", fontsize=12)
    ax1.set_xlabel("X (meters)")
    ax1.set_ylabel("Y (meters)")
    ax1.set_aspect("equal")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Minor eigenvector field
    ax2 = axes[1]
    ax2.quiver(X, Y, U_minor, V_minor, M, cmap="plasma", scale=25)
    ax2.set_title("Minor Eigenvector Field (Cross Streets)", fontsize=12)
    ax2.set_xlabel("X (meters)")
    ax2.set_ylabel("Y (meters)")
    ax2.set_aspect("equal")
    ax2.grid(True, alpha=0.3)

    # Plot 3: Tensor magnitude heatmap
    ax3 = axes[2]
    im = ax3.contourf(X, Y, M, levels=20, cmap="hot")
    ax3.set_title("Tensor Field Strength", fontsize=12)
    ax3.set_xlabel("X (meters)")
    ax3.set_ylabel("Y (meters)")
    ax3.set_aspect("equal")
    plt.colorbar(im, ax=ax3, label="Magnitude")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ Saved visualization to {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Visualize tensor field")
    parser.add_argument(
        "--output",
        type=str,
        default="tensor_field_debug.png",
        help="Output image path",
    )
    parser.add_argument(
        "--resolution", type=int, default=30, help="Grid resolution for visualization"
    )
    args = parser.parse_args()

    # Create example field
    print("🏗️  Creating example tensor field...")
    field = TensorField(bounds=(0, 0, 1000, 1000), resolution=50)

    # Add basis fields
    field.add_grid_field(angle_degrees=0, strength=0.5)
    field.add_grid_field(angle_degrees=90, strength=0.5)
    field.add_radial_field(center=(500, 500), decay_radius=150, strength=0.8)
    field.add_radial_field(center=(300, 700), decay_radius=100, strength=0.6)

    print(f"📊 Field stats: {field.get_field_stats()}")

    # Visualize
    print("🎨 Generating visualization...")
    visualize_tensor_field(field, resolution=args.resolution, save_path=args.output)

    print("✅ Done!")


if __name__ == "__main__":
    main()
