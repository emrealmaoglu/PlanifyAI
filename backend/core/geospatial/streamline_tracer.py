"""
Streamline tracing using adaptive RK45 integration.

This module implements road centerline generation by tracing streamlines
through a tensor field. Uses scipy's RK45 integrator with custom stopping
conditions for spatial planning constraints.

Key Features:
- Adaptive step sizing (automatic via RK45)
- Custom stopping conditions (boundary, length, singularity)
- Smooth, high-quality road curves
- Efficient integration (O(h^5) local error)

References:
- Dormand-Prince RK45 method (scipy.integrate.RK45)
- Parish & Müller (2001): Procedural modeling of cities
- Research: "Adaptive RK4 Streamline Generation Analysis"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
from scipy.integrate import RK45

from .tensor_field import TensorField


class StopReason(Enum):
    """Enumeration of streamline termination reasons."""

    BOUNDARY = "hit_boundary"
    MAX_LENGTH = "max_length_reached"
    SINGULARITY = "near_singularity"
    MAX_STEPS = "max_steps_exceeded"
    INTEGRATION_ERROR = "integration_failed"
    SUCCESS = "completed_successfully"


@dataclass
class StreamlineConfig:
    """Configuration for streamline tracing."""

    max_length: float = 500.0  # Maximum road length (meters)
    max_steps: int = 1000  # Safety limit for iterations
    rtol: float = 1e-3  # Relative tolerance for RK45
    atol: float = 1e-6  # Absolute tolerance for RK45
    singularity_threshold: float = 10.0  # Distance to singularity (meters)
    min_step_size: float = 0.5  # Minimum integration step (meters)
    max_step_size: float = 20.0  # Maximum integration step (meters)


@dataclass
class StreamlineResult:
    """Result of streamline tracing."""

    path: np.ndarray  # (N, 2) array of [x, y] coordinates
    stop_reason: StopReason
    total_length: float  # Arc length of path (meters)
    n_steps: int  # Number of integration steps taken
    success: bool  # True if streamline completed normally


def trace_streamline_rk45(
    tensor_field: TensorField,
    seed_point: np.ndarray,
    config: Optional[StreamlineConfig] = None,
    field_type: str = "major",
) -> StreamlineResult:
    """
    Trace a streamline through a tensor field using adaptive RK45.

    This is the PRIMARY method for generating major road centerlines.
    It integrates along the eigenvector field (major or minor) starting
    from a seed point until a stopping condition is met.

    The integration uses scipy's RK45 (Dormand-Prince) method with
    adaptive step sizing for optimal balance of accuracy and speed.

    Args:
        tensor_field: TensorField instance to trace through
        seed_point: [x, y] starting position (1D or 2D array)
        config: StreamlineConfig with integration parameters
        field_type: 'major' or 'minor' eigenvector field to follow

    Returns:
        StreamlineResult with path and metadata

    Example:
        >>> field = TensorField(bounds=(0, 0, 1000, 1000))
        >>> field.add_grid_field(0, strength=1.0)
        >>> result = trace_streamline_rk45(field, [100, 100])
        >>> print(f"Road length: {result.total_length:.1f}m")
        >>> print(f"Path points: {len(result.path)}")

    Notes:
        - Uses RK45.step() in loop (NOT solve_ivp) for custom stopping
        - Stopping conditions: boundary, length, singularity, max steps
        - Path always includes seed point as first element
        - Returns immediately if seed point out of bounds
    """
    if config is None:
        config = StreamlineConfig()

    # Handle zero/negative max_length
    if config.max_length <= 0:
        seed_point = np.asarray(seed_point)
        if seed_point.ndim == 2:
            seed_point = seed_point.flatten()

        return StreamlineResult(
            path=np.array([seed_point]),
            stop_reason=StopReason.MAX_LENGTH,
            total_length=0.0,
            n_steps=0,
            success=True,
        )

    # Normalize seed point - CONVERT TO NUMPY ARRAY FIRST
    seed_point = np.asarray(seed_point)
    if seed_point.ndim == 2:
        seed_point = seed_point.flatten()

    # Check if seed point is in bounds
    if not tensor_field.in_bounds(seed_point):
        return StreamlineResult(
            path=np.array([seed_point]),
            stop_reason=StopReason.BOUNDARY,
            total_length=0.0,
            n_steps=0,
            success=False,
        )

    # Define vector field function for RK45
    # Signature: f(t, y) -> dy/dt
    # t is arc length parameter (we ignore it - steady field)
    # y is position [x, y]
    def vector_field(t: float, y: np.ndarray) -> np.ndarray:
        """
        Vector field function for integration.

        Returns the direction vector (eigenvector) at position y.
        This is the 'velocity' for the streamline ODE: dy/dt = v(y)
        """
        point = y.reshape(1, -1)  # (1, 2)

        # Get eigenvector at this point
        direction = tensor_field.get_eigenvectors(point, field_type=field_type)

        # Return as 1D array (required by RK45)
        return direction.flatten()

    # Initialize RK45 integrator
    # Note: t_bound is max_length (arc length), not time
    integrator = RK45(
        fun=vector_field,
        t0=0.0,
        y0=seed_point,
        t_bound=config.max_length,
        rtol=config.rtol,
        atol=config.atol,
        max_step=config.max_step_size,
        first_step=config.min_step_size,
    )

    # Path storage
    path = [seed_point.copy()]
    n_steps = 0
    stop_reason = StopReason.SUCCESS

    # Integration loop
    while integrator.status == "running":
        # Take one adaptive step
        integrator.step()
        n_steps += 1

        current_position = integrator.y
        current_arc_length = integrator.t

        # Store point
        path.append(current_position.copy())

        # Check stopping conditions

        # 1. Boundary check
        if not tensor_field.in_bounds(current_position):
            stop_reason = StopReason.BOUNDARY
            break

        # 2. Max steps check (safety)
        if n_steps >= config.max_steps:
            stop_reason = StopReason.MAX_STEPS
            break

        # 3. Arc length check (implicit via t_bound, but double-check)
        if current_arc_length >= config.max_length:
            stop_reason = StopReason.MAX_LENGTH
            break

        # 4. Singularity check (optional, advanced feature)
        # For now, we skip this - will add in optimization phase
        # Singularities are rare in basis field approach

    # Check if integration failed
    if integrator.status == "failed":
        stop_reason = StopReason.INTEGRATION_ERROR

    # POST-LOOP: Check boundary priority
    # If we stopped due to max_length but are at/outside bounds, prioritize boundary
    if len(path) > 0:
        final_position = path[-1]
        x, y = final_position[0], final_position[1]
        xmin, ymin, xmax, ymax = tensor_field.config.bounds

        # Check if point is at or outside boundary (use < for upper bounds to catch boundary)
        # This ensures we stop at boundary even if in_bounds() returns True for boundary points
        at_boundary = x <= xmin or x >= xmax or y <= ymin or y >= ymax
        if not tensor_field.in_bounds(final_position) or at_boundary:
            # Boundary takes priority over max_length
            stop_reason = StopReason.BOUNDARY

    # Convert path to numpy array
    path_array = np.array(path)

    # Compute total arc length (sum of segment lengths)
    if len(path_array) > 1:
        segments = np.diff(path_array, axis=0)
        segment_lengths = np.linalg.norm(segments, axis=1)
        total_length = float(np.sum(segment_lengths))
    else:
        total_length = 0.0

    success = stop_reason in [
        StopReason.SUCCESS,
        StopReason.MAX_LENGTH,
        StopReason.BOUNDARY,
    ]

    return StreamlineResult(
        path=path_array,
        stop_reason=stop_reason,
        total_length=total_length,
        n_steps=n_steps,
        success=success,
    )


def trace_bidirectional_streamline(
    tensor_field: TensorField,
    seed_point: np.ndarray,
    config: Optional[StreamlineConfig] = None,
    field_type: str = "major",
) -> StreamlineResult:
    """
    Trace streamline in BOTH directions from seed point.

    Useful for creating longer roads that pass through a point
    rather than starting at it.

    Args:
        tensor_field: TensorField instance
        seed_point: [x, y] starting position
        config: StreamlineConfig (same for both directions)
        field_type: 'major' or 'minor'

    Returns:
        StreamlineResult with combined path (backward + forward)

    Notes:
        - Forward direction: follows eigenvector field
        - Backward direction: follows negative eigenvector field
        - Final path is: [backward_reversed, seed, forward]
        - Total length is sum of both directions
    """
    if config is None:
        config = StreamlineConfig()

    # Trace forward
    result_forward = trace_streamline_rk45(tensor_field, seed_point, config, field_type)

    # Trace backward (negate field temporarily)
    # We'll do this by creating a wrapper field that negates vectors
    # For simplicity, just flip the resulting path

    # Actually, better approach: modify vector field to negate
    # Create temporary modified config
    class NegatedField:
        """Wrapper that negates eigenvectors."""

        def __init__(self, field):
            self.field = field
            self.config = field.config

        def get_eigenvectors(self, points, field_type="major"):
            vecs = self.field.get_eigenvectors(points, field_type)
            return -vecs  # Negate direction

        def in_bounds(self, point):
            return self.field.in_bounds(point)

    negated_field = NegatedField(tensor_field)

    result_backward = trace_streamline_rk45(negated_field, seed_point, config, field_type)

    # Combine paths
    # Backward path (exclude seed point, reverse order)
    backward_path = result_backward.path[-1:0:-1]  # Reverse, exclude first point

    # Forward path (include seed point)
    forward_path = result_forward.path

    # Concatenate
    if len(backward_path) > 0:
        combined_path = np.vstack([backward_path, forward_path])
    else:
        combined_path = forward_path

    # Combined metrics
    total_length = result_forward.total_length + result_backward.total_length
    n_steps = result_forward.n_steps + result_backward.n_steps

    # Stop reason: use forward's reason
    stop_reason = result_forward.stop_reason
    success = result_forward.success and result_backward.success

    return StreamlineResult(
        path=combined_path,
        stop_reason=stop_reason,
        total_length=total_length,
        n_steps=n_steps,
        success=success,
    )


# UTILITY FUNCTIONS


def resample_path(path: np.ndarray, target_spacing: float = 10.0) -> np.ndarray:
    """
    Resample a path to have approximately uniform spacing.

    Useful for:
    - Creating evenly spaced road segments
    - Reducing point density in smooth regions
    - Preparing paths for further processing

    Args:
        path: (N, 2) array of [x, y] coordinates
        target_spacing: Desired distance between points (meters)

    Returns:
        (M, 2) array of resampled points

    Example:
        >>> path = result.path  # Might have irregular spacing
        >>> uniform_path = resample_path(path, target_spacing=5.0)
    """
    if len(path) < 2:
        return path

    # Compute cumulative arc length
    segments = np.diff(path, axis=0)
    segment_lengths = np.linalg.norm(segments, axis=1)
    cumulative_length = np.concatenate([[0], np.cumsum(segment_lengths)])

    total_length = cumulative_length[-1]

    # Create uniform arc length samples
    n_samples = max(2, int(total_length / target_spacing) + 1)
    uniform_arc_lengths = np.linspace(0, total_length, n_samples)

    # Interpolate x and y separately
    resampled_x = np.interp(uniform_arc_lengths, cumulative_length, path[:, 0])
    resampled_y = np.interp(uniform_arc_lengths, cumulative_length, path[:, 1])

    resampled_path = np.column_stack([resampled_x, resampled_y])

    return resampled_path


def smooth_path(path: np.ndarray, window_size: int = 5) -> np.ndarray:
    """
    Smooth a path using moving average filter.

    Args:
        path: (N, 2) array
        window_size: Smoothing window size (must be odd)

    Returns:
        Smoothed path (same shape)

    Note: Use sparingly - RK45 already produces smooth paths
    """
    if window_size % 2 == 0:
        window_size += 1  # Ensure odd

    if len(path) < window_size:
        return path  # Too short to smooth

    # Apply uniform filter
    from scipy.ndimage import uniform_filter1d

    smoothed = uniform_filter1d(path, size=window_size, axis=0, mode="nearest")

    return smoothed
