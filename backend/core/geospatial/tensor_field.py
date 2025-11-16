"""
Main tensor field class for road network generation.

Combines multiple basis fields into a single, continuous tensor field
and provides methods to query eigenvectors at arbitrary points.

Key Capabilities:
1. Add multiple basis fields (grid + radial)
2. Blend fields smoothly using addition
3. Compute eigenvector fields for streamline tracing
4. Interpolate tensors at arbitrary points (not just grid)

Usage:
    >>> field = TensorField(bounds=(0, 0, 1000, 1000), resolution=100)
    >>> field.add_grid_field(angle_degrees=0, strength=0.5)
    >>> field.add_radial_field(center=(500, 500), decay_radius=100)
    >>> major_vecs = field.get_eigenvectors(points, field_type='major')
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from .basis_fields import GridField, RadialField


@dataclass
class TensorFieldConfig:
    """Configuration for tensor field generation."""

    bounds: Tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax)
    resolution: int = 50  # Grid points per dimension
    min_eigenvalue: float = 1e-6  # Numerical stability threshold


class TensorField:
    """
    Continuous 2D tensor field for semantic road network generation.

    This class manages a gridded representation of a tensor field,
    built by blending multiple basis fields (grids and radials).

    The tensor field is stored as three 2D grids:
    - T_xx: (resolution, resolution) - T[0,0] component
    - T_xy: (resolution, resolution) - T[0,1] = T[1,0] component
    - T_yy: (resolution, resolution) - T[1,1] component

    At each grid point (i, j), the 2x2 symmetric tensor is:
    T = [[T_xx[i,j], T_xy[i,j]],
         [T_xy[i,j], T_yy[i,j]]]

    For querying at non-grid points, we use cubic interpolation.
    """

    def __init__(
        self,
        bounds: Tuple[float, float, float, float],
        resolution: int = 50,
    ):
        """
        Initialize an empty tensor field.

        Args:
            bounds: (xmin, ymin, xmax, ymax) in meters
            resolution: Number of grid points per dimension (default: 50)
                       Higher = more accurate but slower. 50-100 is typical.
        """
        self.config = TensorFieldConfig(bounds=bounds, resolution=resolution)

        # Create spatial grid
        x = np.linspace(bounds[0], bounds[2], resolution)
        y = np.linspace(bounds[1], bounds[3], resolution)
        self.grid_x = x
        self.grid_y = y
        self.X, self.Y = np.meshgrid(x, y)

        # Flatten grid for vectorized operations
        self.grid_points = np.column_stack([self.X.ravel(), self.Y.ravel()])

        # Initialize tensor components (will accumulate basis fields)
        self.T_xx = np.zeros((resolution, resolution), dtype=np.float64)
        self.T_xy = np.zeros((resolution, resolution), dtype=np.float64)
        self.T_yy = np.zeros((resolution, resolution), dtype=np.float64)

        # Track added fields for debugging
        self.basis_fields: List[GridField | RadialField] = []

        # Interpolators (lazy initialization)
        self._interpolators: Optional[Tuple] = None

    def add_grid_field(
        self,
        angle_degrees: float,
        strength: float = 1.0,
    ) -> None:
        """
        Add a uniform directional grid field.

        Args:
            angle_degrees: Direction in degrees (0=North, 90=East)
            strength: Field strength (default: 1.0)

        Example:
            >>> field.add_grid_field(0, strength=0.5)    # North-South roads
            >>> field.add_grid_field(90, strength=0.5)   # East-West roads
        """
        grid = GridField(angle_degrees=angle_degrees, strength=strength)
        self.basis_fields.append(grid)

        # Compute tensor at all grid points
        tensors = grid.get_tensor(self.grid_points)  # (N, 2, 2)

        # Accumulate into field components
        self.T_xx += tensors[:, 0, 0].reshape(self.X.shape)
        self.T_xy += tensors[:, 0, 1].reshape(self.X.shape)
        self.T_yy += tensors[:, 1, 1].reshape(self.X.shape)

        # Invalidate interpolators (need recompute)
        self._interpolators = None

    def add_radial_field(
        self,
        center: Tuple[float, float],
        decay_radius: float = 100.0,
        strength: float = 1.0,
    ) -> None:
        """
        Add a radial field centered on a building.

        Args:
            center: (x, y) center point
            decay_radius: Gaussian decay radius in meters
            strength: Field strength (default: 1.0)

        Example:
            >>> # Add radial field around main admin building
            >>> field.add_radial_field((500, 500), decay_radius=100, strength=0.8)
        """
        radial = RadialField(center=center, decay_radius=decay_radius, strength=strength)
        self.basis_fields.append(radial)

        # Compute tensor at all grid points
        tensors = radial.get_tensor(self.grid_points)  # (N, 2, 2)

        # Accumulate into field components
        self.T_xx += tensors[:, 0, 0].reshape(self.X.shape)
        self.T_xy += tensors[:, 0, 1].reshape(self.X.shape)
        self.T_yy += tensors[:, 1, 1].reshape(self.X.shape)

        # Invalidate interpolators
        self._interpolators = None

    def _build_interpolators(self) -> Tuple:
        """
        Build cubic interpolators for tensor components.

        Allows querying tensors at arbitrary (non-grid) points.
        Uses scipy's RegularGridInterpolator with cubic method.

        Returns:
            (interp_xx, interp_xy, interp_yy): Interpolator functions
        """
        interp_xx = RegularGridInterpolator(
            (self.grid_x, self.grid_y),
            self.T_xx.T,  # Transpose for correct axis order
            method="cubic",
            bounds_error=False,
            fill_value=0.0,
        )

        interp_xy = RegularGridInterpolator(
            (self.grid_x, self.grid_y),
            self.T_xy.T,
            method="cubic",
            bounds_error=False,
            fill_value=0.0,
        )

        interp_yy = RegularGridInterpolator(
            (self.grid_x, self.grid_y),
            self.T_yy.T,
            method="cubic",
            bounds_error=False,
            fill_value=0.0,
        )

        return (interp_xx, interp_xy, interp_yy)

    def get_tensor_at_points(self, points: np.ndarray) -> np.ndarray:
        """
        Interpolate tensor at arbitrary points.

        Args:
            points: (N, 2) array of [x, y] coordinates

        Returns:
            tensors: (N, 2, 2) array of symmetric 2x2 tensors
        """
        # Lazy build interpolators
        if self._interpolators is None:
            self._interpolators = self._build_interpolators()

        interp_xx, interp_xy, interp_yy = self._interpolators

        # Interpolate each component
        T_xx_vals = interp_xx(points)
        T_xy_vals = interp_xy(points)
        T_yy_vals = interp_yy(points)

        # Reconstruct tensors
        n_points = points.shape[0]
        tensors = np.zeros((n_points, 2, 2))

        tensors[:, 0, 0] = T_xx_vals
        tensors[:, 0, 1] = T_xy_vals
        tensors[:, 1, 0] = T_xy_vals  # Symmetric
        tensors[:, 1, 1] = T_yy_vals

        return tensors

    def get_eigenvectors(
        self,
        points: np.ndarray,
        field_type: Literal["major", "minor"] = "major",
    ) -> np.ndarray:
        """
        Compute eigenvector field at given points.

        This is the KEY method for road generation. It returns normalized
        direction vectors that streamline tracing will follow.

        Args:
            points: (N, 2) array of [x, y] coordinates
            field_type: 'major' (larger eigenvalue) or 'minor' (smaller)

        Returns:
            vectors: (N, 2) array of unit direction vectors

        Notes:
            - Major eigenvector: direction of maximum anisotropy (main roads)
            - Minor eigenvector: perpendicular direction (cross streets)
            - For a radial field, major points outward, minor is tangential
        """
        tensors = self.get_tensor_at_points(points)

        n_points = points.shape[0]
        vectors = np.zeros((n_points, 2))

        for i in range(n_points):
            T = tensors[i]

            # Compute eigenvalues and eigenvectors
            # np.linalg.eigh returns sorted eigenvalues (smallest first)
            eigenvalues, eigenvectors = np.linalg.eigh(T)

            # Add small epsilon to avoid zero eigenvalues
            eigenvalues = np.maximum(eigenvalues, self.config.min_eigenvalue)

            if field_type == "major":
                # Largest eigenvalue (index 1)
                vectors[i] = eigenvectors[:, 1]
            else:
                # Smallest eigenvalue (index 0)
                vectors[i] = eigenvectors[:, 0]

            # Ensure unit length
            norm = np.linalg.norm(vectors[i])
            if norm > 1e-10:
                vectors[i] /= norm

        return vectors

    def in_bounds(self, point: np.ndarray) -> bool:
        """
        Check if a point is within field bounds.

        Args:
            point: [x, y] coordinate (can be 1D or 2D array)

        Returns:
            True if point inside bounds, False otherwise
        """
        if point.ndim == 1:
            x, y = point[0], point[1]
        else:
            x, y = point[0, 0], point[0, 1]

        xmin, ymin, xmax, ymax = self.config.bounds
        return xmin <= x <= xmax and ymin <= y <= ymax

    def get_field_stats(self) -> dict:
        """
        Get statistics about the field for debugging.

        Returns:
            Dictionary with field metadata
        """
        return {
            "bounds": self.config.bounds,
            "resolution": self.config.resolution,
            "n_basis_fields": len(self.basis_fields),
            "basis_field_types": [type(f).__name__ for f in self.basis_fields],
            "T_xx_range": (self.T_xx.min(), self.T_xx.max()),
            "T_yy_range": (self.T_yy.min(), self.T_yy.max()),
            "T_xy_range": (self.T_xy.min(), self.T_xy.max()),
        }

    def __repr__(self):
        return (
            f"TensorField(bounds={self.config.bounds}, "
            f"resolution={self.config.resolution}, "
            f"n_fields={len(self.basis_fields)})"
        )


# UTILITY FUNCTIONS


def create_campus_tensor_field(
    buildings: List,  # Type hint: List[Building] when integrated
    bounds: Tuple[float, float, float, float],
    resolution: int = 50,
) -> TensorField:
    """
    Factory function to create a semantic tensor field from building layout.

    This implements the "semantic" part of semantic tensor fields:
    different building types influence the field differently.

    Strategy:
    1. Add global grid fields (campus-wide road orientation)
    2. Add radial fields around important buildings (admin, library, dining)
    3. Stronger radial fields for larger/more important buildings

    Args:
        buildings: List of Building objects from H-SAGA optimizer
        bounds: (xmin, ymin, xmax, ymax) in meters
        resolution: Grid resolution (default: 50)

    Returns:
        Configured TensorField ready for streamline tracing

    Example:
        >>> from src.algorithms.building import Building, BuildingType
        >>> buildings = [
        ...     Building('ADM-01', BuildingType.ADMINISTRATIVE, 1000, 3),
        ...     Building('RES-01', BuildingType.RESIDENTIAL, 800, 5)
        ... ]
        >>> field = create_campus_tensor_field(buildings, (0, 0, 1000, 1000))
    """
    field = TensorField(bounds=bounds, resolution=resolution)

    # 1. Add global grid fields (orthogonal roads)
    field.add_grid_field(angle_degrees=0, strength=0.4)  # North-South
    field.add_grid_field(angle_degrees=90, strength=0.4)  # East-West

    # 2. Add radial fields for important buildings
    IMPORTANT_TYPES = [
        "administrative",
        "library",
        "dining",
        "social",
    ]  # Match BuildingType enum values

    for building in buildings:
        if building.type.value in IMPORTANT_TYPES:
            # Strength based on building area
            strength = min(1.0, building.area / 1000.0)  # Normalize by typical area

            # Decay radius based on building footprint
            decay_radius = np.sqrt(building.footprint) * 2.0  # ~2x building "radius"

            # Get position from building
            if building.position:
                field.add_radial_field(
                    center=(building.position[0], building.position[1]),
                    decay_radius=decay_radius,
                    strength=strength * 0.6,  # Scale down to not overwhelm grid
                )

    return field
