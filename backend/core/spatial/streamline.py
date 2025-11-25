"""
Streamline integration for road network generation.

This module traces smooth curves through tensor fields using
adaptive Runge-Kutta integration (RK45).
"""

from typing import Tuple, List
import numpy as np
from scipy.integrate import RK45
from shapely.geometry import Polygon, Point

from .tensor_field import TensorField


class StreamlineIntegrator:
    """
    Traces streamlines through a tensor field using adaptive RK45 integration.

    Implements bidirectional tracing and anisotropy-based singularity detection.
    """

    def __init__(
        self,
        tensor_field: TensorField,
        boundary_polygon: Polygon,
        max_step: float = 5.0,
        rtol: float = 1e-3,
        atol: float = 1e-6,
    ):
        """
        Initialize streamline integrator.

        Args:
            tensor_field: TensorField to integrate through
            boundary_polygon: Shapely Polygon defining valid region
            max_step: Maximum integration step size (meters)
            rtol: Relative tolerance for RK45
            atol: Absolute tolerance for RK45
        """
        self.tensor_field = tensor_field
        self.boundary = boundary_polygon
        self.max_step = max_step
        self.rtol = rtol
        self.atol = atol

        # Cache bounding box for fast pre-check
        bounds = boundary_polygon.bounds
        self.bbox = {
            "xmin": bounds[0],
            "ymin": bounds[1],
            "xmax": bounds[2],
            "ymax": bounds[3],
        }

    def _is_within_boundary(self, point: np.ndarray) -> bool:
        """
        Check if point is within boundary (optimized).

        Uses bbox pre-check before expensive polygon test.
        """
        x, y = point[0], point[1]

        # Fast bbox check first
        if not (
            self.bbox["xmin"] <= x <= self.bbox["xmax"]
            and self.bbox["ymin"] <= y <= self.bbox["ymax"]
        ):
            return False

        # Precise polygon check
        return self.boundary.contains(Point(x, y))

    def _trace_direction(
        self,
        seed_point: np.ndarray,
        direction_sign: float,  # +1 or -1
        max_length: float,
        min_anisotropy: float,
        field_type: str,
    ) -> np.ndarray:
        """
        Trace streamline in one direction from seed.

        Args:
            seed_point: (2,) starting position
            direction_sign: +1 for forward, -1 for backward
            max_length: Maximum arc length to trace
            min_anisotropy: Stop if anisotropy < this (junction detection)
            field_type: 'major' or 'minor'

        Returns:
            (N, 2) array of streamline points
        """

        # Vector field function for RK45
        def vector_field(t, y):
            """ODE: dy/dt = direction * eigenvector"""
            point = y.reshape(1, 2)
            direction = self.tensor_field.get_eigenvectors(point, field_type)[0]

            # Apply direction sign for bidirectional tracing
            return direction_sign * direction

        # Initialize RK45 solver
        solver = RK45(
            fun=vector_field,
            t0=0,
            y0=seed_point,
            t_bound=max_length,
            max_step=self.max_step,
            rtol=self.rtol,
            atol=self.atol,
        )

        # Collect points
        points = [seed_point.copy()]

        # Integration loop
        while solver.status == "running":
            # Advance one step
            solver.step()

            current_point = solver.y

            # Termination Check 1: Boundary exit
            if not self._is_within_boundary(current_point):
                break

            # Termination Check 2: Singularity (junction center)
            point_reshaped = current_point.reshape(1, 2)
            anisotropy = self.tensor_field.get_anisotropy(point_reshaped)[0]

            if anisotropy < min_anisotropy:
                # Low anisotropy = isotropic region = junction
                points.append(current_point.copy())  # Include junction point
                break

            # Store valid point
            points.append(current_point.copy())

        return np.array(points)

    def trace(
        self,
        seed_point: np.ndarray,
        max_length: float = 500.0,
        min_anisotropy: float = 0.1,
        field_type: str = "major",
    ) -> np.ndarray:
        """
        Trace complete streamline (bidirectional).

        Algorithm:
        1. Trace backward (direction = -1)
        2. Trace forward (direction = +1)
        3. Concatenate: reverse(backward) + forward

        Args:
            seed_point: (2,) starting position [x, y]
            max_length: Maximum length per direction
            min_anisotropy: Junction detection threshold
            field_type: 'major' (roads) or 'minor' (cross-streets)

        Returns:
            (N, 2) complete streamline
        """
        seed_point = np.array(seed_point, dtype=np.float64)

        # Trace backward (direction = -1)
        backward = self._trace_direction(
            seed_point=seed_point,
            direction_sign=-1.0,
            max_length=max_length,
            min_anisotropy=min_anisotropy,
            field_type=field_type,
        )

        # Trace forward (direction = +1)
        forward = self._trace_direction(
            seed_point=seed_point,
            direction_sign=+1.0,
            max_length=max_length,
            min_anisotropy=min_anisotropy,
            field_type=field_type,
        )

        # Concatenate: reverse(backward) + forward
        # Skip last point of backward to avoid duplicating seed
        if len(backward) > 1:
            backward_reversed = np.flip(backward[:-1], axis=0)
            complete_streamline = np.vstack([backward_reversed, forward])
        else:
            complete_streamline = forward

        return complete_streamline


class RoadNetworkGenerator:
    """
    Generates complete road networks from multiple seed points.

    Uses anisotropy-weighted seeding strategy.
    """

    def __init__(self, integrator: StreamlineIntegrator):
        """
        Initialize generator.

        Args:
            integrator: Configured StreamlineIntegrator
        """
        self.integrator = integrator

    def generate_seed_points(
        self,
        bbox: Tuple[float, float, float, float],
        grid_spacing: float = 50.0,
        min_anisotropy: float = 0.5,
    ) -> np.ndarray:
        """
        Generate seed points using anisotropy-weighted strategy.

        Args:
            bbox: (xmin, ymin, xmax, ymax)
            grid_spacing: Distance between candidate points
            min_anisotropy: Minimum anisotropy to seed

        Returns:
            (N, 2) array of seed points
        """
        xmin, ymin, xmax, ymax = bbox

        # Create candidate grid
        x = np.arange(xmin, xmax, grid_spacing)
        y = np.arange(ymin, ymax, grid_spacing)
        X, Y = np.meshgrid(x, y)
        candidates = np.c_[X.ravel(), Y.ravel()]

        # Compute anisotropy (vectorized)
        anisotropy = self.integrator.tensor_field.get_anisotropy(candidates)

        # Filter: Keep high-anisotropy points
        mask = anisotropy > min_anisotropy
        seed_points = candidates[mask]

        return seed_points

    def generate_network(
        self,
        seed_points: np.ndarray,
        field_type: str = "major",
        min_road_length: float = 20.0,
    ) -> List[np.ndarray]:
        """
        Generate road network from seed points.

        Args:
            seed_points: (N, 2) array of starting positions
            field_type: 'major' or 'minor'
            min_road_length: Discard roads shorter than this

        Returns:
            List of road polylines (each is np.ndarray)
        """
        roads = []

        for i, seed in enumerate(seed_points):
            # Trace streamline
            streamline = self.integrator.trace(seed, field_type=field_type)

            # Compute road length
            if len(streamline) < 2:
                continue

            segments = np.diff(streamline, axis=0)
            road_length = np.sum(np.linalg.norm(segments, axis=1))

            # Filter by minimum length
            if road_length >= min_road_length:
                roads.append(streamline)

        return roads

    def export_geojson(self, roads: List[np.ndarray], filepath: str):
        """
        Export road network to GeoJSON format.

        Args:
            roads: List of road polylines
            filepath: Output file path
        """
        import json

        features = []

        for i, road in enumerate(roads):
            # Convert to GeoJSON LineString
            coordinates = [[float(x), float(y)] for x, y in road]

            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "road_id": i,
                    "length": float(
                        np.sum(np.linalg.norm(np.diff(road, axis=0), axis=1))
                    ),
                },
            }
            features.append(feature)

        geojson = {"type": "FeatureCollection", "features": features}

        with open(filepath, "w") as f:
            json.dump(geojson, f, indent=2)

        print(f"✅ Exported {len(roads)} roads to {filepath}")
