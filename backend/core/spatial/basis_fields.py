"""
Tensor field basis components for road network generation.

This module provides the building blocks for semantic tensor fields:
- BasisField: Abstract base class
- GridField: Creates orthogonal grid patterns
- RadialField: Creates radial/curved patterns around a center
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple


class BasisField(ABC):
    """
    Abstract base class for tensor field basis components.

    A basis field generates a 2×2 symmetric tensor at each spatial point,
    along with a weight indicating its influence at that location.
    """

    def __init__(self, center: Tuple[float, float], decay_radius: float):
        """
        Initialize basis field.

        Args:
            center: (x, y) center point of influence
            decay_radius: Gaussian decay radius (sigma)
        """
        self.center = np.array(center, dtype=np.float64)
        self.decay_radius = decay_radius

    @abstractmethod
    def get_tensor(self, points: np.ndarray) -> np.ndarray:
        """
        Compute 2×2 tensor at each point.

        Args:
            points: (N, 2) array of [x, y] coordinates

        Returns:
            (N, 2, 2) array of symmetric tensors
        """
        pass

    def get_weight(self, points: np.ndarray) -> np.ndarray:
        """
        Compute Gaussian influence weight at each point.

        Args:
            points: (N, 2) array of [x, y] coordinates

        Returns:
            (N,) array of weights in [0, 1]
        """
        # Euclidean distance from center
        distances = np.linalg.norm(points - self.center, axis=1)

        # Gaussian decay
        weights = np.exp(-(distances**2) / (2 * self.decay_radius**2))

        return weights


class GridField(BasisField):
    """
    Grid basis field - creates orthogonal road patterns.

    The eigenvectors are aligned with a rotated coordinate system,
    producing straight roads at a specified angle.
    """

    def __init__(
        self,
        center: Tuple[float, float],
        size: float,
        theta: float,
        decay_radius: float,
    ):
        """
        Initialize grid field.

        Args:
            center: (x, y) center of grid
            size: Grid cell size (not used in basic version)
            theta: Rotation angle in radians (0 = aligned with x/y axes)
            decay_radius: Gaussian decay radius
        """
        super().__init__(center, decay_radius)
        self.size = size
        self.theta = theta

        # Pre-compute rotation matrix
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        self.rotation_matrix = np.array([[cos_t, -sin_t], [sin_t, cos_t]])

    def get_tensor(self, points: np.ndarray) -> np.ndarray:
        """
        Compute grid-aligned tensors.

        Strategy:
        1. Start with identity tensor (aligned with x/y)
        2. Rotate it by theta using: R * T * R^T

        Returns:
            (N, 2, 2) tensors with eigenvectors at angle theta
        """
        N = points.shape[0]
        tensors = np.zeros((N, 2, 2))

        # Base tensor with distinct eigenvalues to define orientation
        # Major axis (1.0) along x, Minor axis (0.1) along y
        # This ensures eigenvectors are well-defined and rotatable
        base_tensor = np.diag([1.0, 0.1])

        # Rotate: T' = R * T * R^T
        R = self.rotation_matrix
        rotated_tensor = R @ base_tensor @ R.T

        # All points get the same tensor (uniform grid)
        tensors[:] = rotated_tensor

        return tensors


class RadialField(BasisField):
    """
    Radial basis field - creates roads converging to/from center.

    The major eigenvector points radially (toward/away from center),
    creating curved roads that form a junction at the center.
    """

    def __init__(self, center: Tuple[float, float], decay_radius: float, tangential: bool = False):
        """
        Initialize radial field.

        Args:
            center: (x, y) junction center
            decay_radius: Gaussian decay radius
            tangential: If True, creates flow AROUND the center (tangential)
        """
        super().__init__(center, decay_radius)
        self.tangential = tangential

    def get_tensor(self, points: np.ndarray) -> np.ndarray:
        """
        Compute radially-oriented tensors.

        Strategy:
        1. For each point, compute radial direction (toward center)
        2. Create tensor with major eigenvector = radial direction
        3. Minor eigenvector is perpendicular (tangential)

        Math:
        Given unit radial vector r = [rx, ry]:
        Tensor T = r ⊗ r (outer product) = [rx²    rx*ry]
                                            [rx*ry  ry²  ]

        Returns:
            (N, 2, 2) tensors with radial orientation
        """
        N = points.shape[0]
        tensors = np.zeros((N, 2, 2))

        # Vector from center to each point
        radial_vectors = points - self.center

        # Normalize to unit vectors
        distances = np.linalg.norm(radial_vectors, axis=1, keepdims=True)
        # Avoid division by zero at center
        distances = np.maximum(distances, 1e-6)
        radial_unit = radial_vectors / distances
        
        if self.tangential:
            # Rotate 90 degrees: [x, y] -> [-y, x]
            tangential_unit = np.stack([-radial_unit[:, 1], radial_unit[:, 0]], axis=1)
            direction_unit = tangential_unit
        else:
            direction_unit = radial_unit

        # Create tensor via outer product: T = v ⊗ v
        # AND blend with isotropic tensor (Identity) near center
        # to create a proper singularity (low anisotropy)
        core_radius = 20.0  # Radius where field becomes isotropic
        
        for i in range(N):
            dist = distances[i, 0]
            v = direction_unit[i]
            
            # Pure directional tensor (anisotropy = 1.0)
            T_dir = np.outer(v, v)
            
            if dist < core_radius:
                # Blend with isotropic tensor (0.5 * I has same trace as v*vT)
                # alpha = 0 (center) -> Isotropic
                # alpha = 1 (edge) -> Directional
                alpha = dist / core_radius
                T_iso = np.eye(2) * 0.5
                tensors[i] = alpha * T_dir + (1 - alpha) * T_iso
            else:
                tensors[i] = T_dir
        
        return tensors
