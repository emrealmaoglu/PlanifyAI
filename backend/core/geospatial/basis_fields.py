"""
Basis tensor field components for semantic road network generation.

This module implements the simplified "basis field" approach:
- GridField: Uniform directional fields (north-south, east-west)
- RadialField: Circular patterns around key buildings
- Gaussian blending for smooth transitions

Reference: Simplified from Parish & Müller (2001), adapted for campus planning
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass
class BasisFieldConfig:
    """Configuration for basis field generation."""

    strength: float = 1.0
    decay_radius: Optional[float] = None  # For radial fields
    angle_degrees: Optional[float] = None  # For grid fields


class GridField:
    """
    Uniform directional tensor field aligned to a specific angle.

    Creates a field where all tensors point in the same direction,
    useful for modeling predominant road directions (e.g., north-south).

    Mathematical Formulation:
    For a unit vector v = [cos(θ), sin(θ)], the tensor at any point is:
    T = strength * (v ⊗ v) = strength * [[v_x * v_x, v_x * v_y],
                                          [v_x * v_y, v_y * v_y]]

    Example:
        >>> field = GridField(angle_degrees=0, strength=1.0)  # North-south
        >>> tensor = field.get_tensor(np.array([100, 200]))
        >>> # Returns 2x2 symmetric matrix
    """

    def __init__(self, angle_degrees: float, strength: float = 1.0):
        """
        Args:
            angle_degrees: Direction in degrees (0=North, 90=East)
            strength: Field strength multiplier (default: 1.0)
        """
        self.angle_degrees = angle_degrees
        self.strength = strength

        # Precompute direction vector
        theta = np.radians(angle_degrees)
        self.direction = np.array([np.cos(theta), np.sin(theta)])

        # Precompute tensor components (constant for grid field)
        v = self.direction
        self.T_base = strength * np.outer(v, v)

    def get_tensor(self, points: np.ndarray) -> np.ndarray:
        """
        Compute tensor at given points.

        Args:
            points: (N, 2) array of [x, y] coordinates

        Returns:
            (N, 2, 2) array of 2x2 symmetric tensors
        """
        n_points = points.shape[0]

        # Grid field is constant everywhere
        tensors = np.tile(self.T_base, (n_points, 1, 1))

        return tensors

    def __repr__(self):
        return f"GridField(angle={self.angle_degrees}°, strength={self.strength})"


class RadialField:
    """
    Radial tensor field emanating from a center point.

    Creates a field where tensors point radially outward (or inward) from
    a center, useful for modeling roads converging on important buildings.

    Mathematical Formulation:
    For a point p and center c:
    1. r = p - c (vector from center to point)
    2. θ = atan2(r_y, r_x) (angle of radial direction)
    3. v = [cos(θ), sin(θ)] (unit radial vector)
    4. w = strength * exp(-0.5 * (||r|| / decay_radius)²) (Gaussian decay)
    5. T = w * (v ⊗ v)

    Example:
        >>> field = RadialField(center=[500, 500], decay_radius=100, strength=0.8)
        >>> tensor = field.get_tensor(np.array([[550, 500], [600, 600]]))
        >>> # Returns (2, 2, 2) array: 2 points, each with 2x2 tensor
    """

    def __init__(
        self,
        center: Tuple[float, float],
        decay_radius: float = 100.0,
        strength: float = 1.0,
    ):
        """
        Args:
            center: (x, y) center point of radial field
            decay_radius: Gaussian decay radius in meters (field drops to ~0.6 at this distance)
            strength: Field strength multiplier (default: 1.0)
        """
        self.center = np.array(center)
        self.decay_radius = decay_radius
        self.strength = strength

    def get_tensor(self, points: np.ndarray) -> np.ndarray:
        """
        Compute radial tensor at given points.

        Args:
            points: (N, 2) array of [x, y] coordinates

        Returns:
            (N, 2, 2) array of 2x2 symmetric tensors
        """
        # Vector from center to each point
        delta = points - self.center  # (N, 2)

        # Distance and angle
        r = np.linalg.norm(delta, axis=1, keepdims=True)  # (N, 1)

        # Gaussian decay weight
        weight = self.strength * np.exp(-0.5 * (r / self.decay_radius) ** 2)  # (N, 1)

        # Normalized radial direction (handle center singularity)
        # At center, use arbitrary unit direction (e.g., [1, 0])
        r_safe = np.maximum(r, 1e-10)  # Avoid division by zero
        direction = delta / r_safe  # (N, 2)

        # For points exactly at center, set to unit vector [1, 0]
        at_center = r.ravel() < 1e-10
        if np.any(at_center):
            direction[at_center] = np.array([1.0, 0.0])

        # Compute tensor for each point: T = w * (v ⊗ v)
        n_points = points.shape[0]
        tensors = np.zeros((n_points, 2, 2))

        for i in range(n_points):
            v = direction[i]
            w = weight[i, 0]
            tensors[i] = w * np.outer(v, v)

        return tensors

    def __repr__(self):
        return (
            f"RadialField(center={self.center}, "
            f"radius={self.decay_radius}, strength={self.strength})"
        )


# OPTIONAL HELPER FUNCTIONS (if time permits)


def visualize_field(field, bounds, resolution=50, save_path=None):
    """
    Debug visualization of a single basis field.

    Args:
        field: GridField or RadialField instance
        bounds: (xmin, ymin, xmax, ymax)
        resolution: Grid points per dimension
        save_path: Optional path to save plot
    """
    import matplotlib.pyplot as plt

    x = np.linspace(bounds[0], bounds[2], resolution)
    y = np.linspace(bounds[1], bounds[3], resolution)
    X, Y = np.meshgrid(x, y)

    points = np.column_stack([X.ravel(), Y.ravel()])
    tensors = field.get_tensor(points)

    # Extract major eigenvector for visualization
    major_vecs = np.zeros_like(points)
    for i, T in enumerate(tensors):
        eigenvalues, eigenvectors = np.linalg.eigh(T)
        major_vecs[i] = eigenvectors[:, 1]  # Largest eigenvalue

    U = major_vecs[:, 0].reshape(X.shape)
    V = major_vecs[:, 1].reshape(X.shape)

    plt.figure(figsize=(10, 10))
    plt.quiver(X, Y, U, V, scale=20)
    plt.title(f"{field}")
    plt.axis("equal")

    if save_path:
        plt.savefig(save_path, dpi=150)
    else:
        plt.show()
