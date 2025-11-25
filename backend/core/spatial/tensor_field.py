"""
Tensor field blending for road network generation.

This module provides the TensorField class which blends multiple
BasisField instances to create smooth, organic road network patterns.
"""

from typing import List, Tuple
import numpy as np
from .basis_fields import BasisField


class TensorField:
    """
    Blends multiple basis tensor fields using Gaussian-weighted averaging.

    The resulting field defines road directions (major eigenvector) and
    perpendicular directions (minor eigenvector) at each spatial point.
    """

    def __init__(self, basis_fields: List[BasisField]):
        """
        Initialize tensor field with basis components.

        Args:
            basis_fields: List of BasisField instances to blend
        """
        if not basis_fields:
            raise ValueError("At least one basis field required")

        self.basis_fields = basis_fields

    def get_blended_tensor(self, points: np.ndarray) -> np.ndarray:
        """
        Compute Gaussian-weighted blend of all basis tensors.

        Algorithm (Gemini-approved vectorized version):
        1. For each field: compute T_i and w_i
        2. Weighted sum: T_blend = Σ(w_i * T_i) / Σ(w_i)
        3. Fallback to identity if all weights near zero

        Mathematical Properties:
        - Preserves symmetry (symmetric + symmetric = symmetric)
        - Preserves PSD (positive semi-definite)
        - Correctly interpolates orientation and anisotropy

        Args:
            points: (N, 2) array of [x, y] coordinates

        Returns:
            (N, 2, 2) array of blended symmetric tensors
        """
        N = points.shape[0]
        blended = np.zeros((N, 2, 2))
        total_weights = np.zeros(N)

        # Accumulate weighted tensors
        for field in self.basis_fields:
            tensors = field.get_tensor(points)  # (N, 2, 2)
            weights = field.get_weight(points)  # (N,)

            # Broadcasting: (N, 1, 1) * (N, 2, 2)
            blended += weights[:, None, None] * tensors
            total_weights += weights

        # Normalize (avoid division by zero)
        mask = total_weights > 1e-6

        # Valid points: normalize by total weight
        blended[mask] /= total_weights[mask, None, None]

        # Invalid points (far from all fields): use identity (isotropic)
        blended[~mask] = np.eye(2)

        return blended

    def get_eigenvectors(
        self, points: np.ndarray, field_type: str = "major"
    ) -> np.ndarray:
        """
        Extract major or minor eigenvector field.

        The major eigenvector indicates the primary road direction.
        The minor eigenvector is perpendicular (cross-street direction).

        Uses np.linalg.eigh (Gemini recommendation):
        - Specialized for symmetric matrices
        - Returns eigenvalues in ASCENDING order
        - More stable than general eig()

        Args:
            points: (N, 2) array of [x, y] coordinates
            field_type: 'major' (largest eigenvalue) or 'minor' (smallest)

        Returns:
            (N, 2) array of unit eigenvectors
        """
        tensors = self.get_blended_tensor(points)
        N = points.shape[0]
        vectors = np.zeros((N, 2))

        # np.linalg.eigh is vectorized over the first dimension (stack of matrices)
        # It returns eigenvalues (N, 2) and eigenvectors (N, 2, 2)
        eigenvalues, eigenvectors = np.linalg.eigh(tensors)

        if field_type == "major":
            # Largest eigenvalue = index 1 (ascending order)
            vectors = eigenvectors[:, :, 1]
        elif field_type == "minor":
            # Smallest eigenvalue = index 0
            vectors = eigenvectors[:, :, 0]
        else:
            raise ValueError(f"Unknown field_type: {field_type}")

        return vectors

    def get_anisotropy(self, points: np.ndarray) -> np.ndarray:
        """
        Compute anisotropy metric at each point.

        Anisotropy measures how "directional" the field is:
        - High values (→1): Strong directional preference (road)
        - Low values (→0): Isotropic (junction/plaza)

        Formula: 1 - (λ_min / λ_max)

        Args:
            points: (N, 2) array of [x, y] coordinates

        Returns:
            (N,) array of anisotropy values in [0, 1]
        """
        tensors = self.get_blended_tensor(points)

        # Vectorized eigendecomposition
        eigenvalues, _ = np.linalg.eigh(tensors)

        lambda_min = eigenvalues[:, 0]
        lambda_max = eigenvalues[:, 1]

        # Avoid division by zero
        mask = lambda_max > 1e-8

        anisotropy = np.zeros(points.shape[0])
        anisotropy[mask] = 1.0 - (lambda_min[mask] / lambda_max[mask])
        # Degenerate tensors (lambda_max ~ 0) remain 0 (isotropic)

        return anisotropy

    def visualize(
        self,
        bbox: Tuple[float, float, float, float],
        resolution: int = 40,
        show_anisotropy: bool = True,
        show_streamplot: bool = True,
    ):
        """
        Visualize the tensor field for debugging and validation.

        Creates comprehensive visualization with:
        - Streamplot: Shows continuous flow lines (road-like)
        - Anisotropy heatmap: Shows directional strength
        - Quiver (optional): Shows discrete vectors

        Args:
            bbox: (xmin, ymin, xmax, ymax) bounding box
            resolution: Grid resolution (points per axis)
            show_anisotropy: Whether to show anisotropy heatmap
            show_streamplot: Whether to show streamlines
        """
        import matplotlib.pyplot as plt

        # Generate grid of points
        xmin, ymin, xmax, ymax = bbox
        x = np.linspace(xmin, xmax, resolution)
        y = np.linspace(ymin, ymax, resolution)
        X, Y = np.meshgrid(x, y)
        points = np.c_[X.ravel(), Y.ravel()]

        # Get major eigenvector field
        major_vectors = self.get_eigenvectors(points, "major")
        U = major_vectors[:, 0].reshape(X.shape)
        V = major_vectors[:, 1].reshape(X.shape)

        # Create figure
        fig, axes = plt.subplots(
            1, 2 if show_anisotropy else 1, figsize=(15 if show_anisotropy else 10, 8)
        )

        if not show_anisotropy:
            axes = [axes]
        elif not isinstance(axes, np.ndarray):
            axes = [axes]

        # Panel 1: Vector field (streamplot or quiver)
        ax1 = axes[0]

        if show_streamplot:
            # Streamplot: Better for road networks
            ax1.streamplot(
                X, Y, U, V, color="blue", density=1.5, linewidth=1, arrowsize=1.5
            )
            ax1.set_title("Major Eigenvector Field (Streamlines)")
        else:
            # Quiver: Discrete vectors
            ax1.quiver(X, Y, U, V, color="blue", scale=40)
            ax1.set_title("Major Eigenvector Field (Quiver)")

        ax1.set_xlabel("X")
        ax1.set_ylabel("Y")
        ax1.set_aspect("equal")
        ax1.grid(True, alpha=0.3)

        # Panel 2: Anisotropy heatmap (if requested)
        if show_anisotropy:
            ax2 = axes[1]

            anisotropy = self.get_anisotropy(points)
            anisotropy_grid = anisotropy.reshape(X.shape)

            im = ax2.contourf(X, Y, anisotropy_grid, levels=20, cmap="viridis")
            plt.colorbar(im, ax=ax2, label="Anisotropy")

            ax2.set_title("Anisotropy Map\n(High = Road, Low = Junction)")
            ax2.set_xlabel("X")
            ax2.set_ylabel("Y")
            ax2.set_aspect("equal")

        plt.tight_layout()
        return fig
