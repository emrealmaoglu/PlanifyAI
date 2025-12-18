"""
Unit tests for RK45 streamline tracing.

Tests verify:
1. Basic streamline integration
2. Stopping conditions (boundary, length, singularity)
3. Bidirectional tracing
4. Path quality (smoothness, length)
5. Performance benchmarks
"""

import numpy as np
import pytest

from src.spatial.streamline_tracer import (
    StopReason,
    StreamlineConfig,
    StreamlineResult,
    resample_path,
    smooth_path,
    trace_bidirectional_streamline,
    trace_streamline_rk45,
)
from src.spatial.tensor_field import TensorField


class TestBasicStreamlineTracing:
    """Test fundamental streamline integration."""

    def test_streamline_in_uniform_field(self):
        """Test tracing in a simple uniform grid field."""
        # Create north-pointing field
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(angle_degrees=0, strength=1.0)  # Points north

        # Trace from center
        seed = np.array([50, 50])
        result = trace_streamline_rk45(field, seed, field_type="major")

        # Should trace successfully
        assert result.success
        assert len(result.path) > 2  # Multiple points

        # Path should move generally northward (x increases)
        assert result.path[-1, 0] > result.path[0, 0]

    def test_streamline_result_structure(self):
        """Test StreamlineResult contains expected fields."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        result = trace_streamline_rk45(field, [50, 50])

        assert hasattr(result, "path")
        assert hasattr(result, "stop_reason")
        assert hasattr(result, "total_length")
        assert hasattr(result, "n_steps")
        assert hasattr(result, "success")

        assert isinstance(result.path, np.ndarray)
        assert result.path.shape[1] == 2  # (N, 2)
        assert isinstance(result.stop_reason, StopReason)

    def test_seed_point_formats(self):
        """Test streamline accepts different seed point formats."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        # 1D array
        result1 = trace_streamline_rk45(field, np.array([50, 50]))
        assert result1.success

        # 2D array (1, 2)
        result2 = trace_streamline_rk45(field, np.array([[50, 50]]))
        assert result2.success

        # List
        result3 = trace_streamline_rk45(field, [50, 50])
        assert result3.success


class TestStoppingConditions:
    """Test all streamline termination conditions."""

    def test_boundary_stopping(self):
        """Test streamline stops at field boundary."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(angle_degrees=0, strength=1.0)  # North

        # Start near top boundary
        seed = np.array([50, 90])
        config = StreamlineConfig(max_length=50.0)

        result = trace_streamline_rk45(field, seed, config)

        # Should hit boundary
        assert result.stop_reason == StopReason.BOUNDARY

        # Final point should be at/near boundary
        assert (
            result.path[-1, 0] >= 99.0
            or result.path[-1, 0] <= 1.0
            or result.path[-1, 1] >= 99.0
            or result.path[-1, 1] <= 1.0
        )

    def test_max_length_stopping(self):
        """Test streamline stops at max length."""
        field = TensorField(bounds=(0, 0, 1000, 1000), resolution=30)
        field.add_grid_field(0, 1.0)

        # Large field, short max length
        seed = np.array([500, 500])
        config = StreamlineConfig(max_length=50.0)

        result = trace_streamline_rk45(field, seed, config)

        # Should stop at max length
        assert result.stop_reason in [StopReason.MAX_LENGTH, StopReason.SUCCESS]

        # Total length should be approximately max_length
        assert result.total_length <= config.max_length * 1.1  # Allow 10% tolerance

    def test_max_steps_safety(self):
        """Test max_steps prevents infinite loops."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        # Artificially low max_steps
        seed = np.array([50, 50])
        config = StreamlineConfig(max_steps=10, max_length=1000.0)

        result = trace_streamline_rk45(field, seed, config)

        # Should stop due to max_steps
        assert result.n_steps <= config.max_steps

    def test_out_of_bounds_seed(self):
        """Test handling of seed point outside field."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        # Seed outside bounds
        seed = np.array([150, 50])  # x > xmax

        result = trace_streamline_rk45(field, seed)

        assert not result.success
        assert result.stop_reason == StopReason.BOUNDARY
        assert len(result.path) == 1  # Only seed point
        assert result.total_length == 0.0


class TestFieldTypes:
    """Test tracing major vs minor eigenvector fields."""

    def test_major_vs_minor_perpendicular(self):
        """Test major and minor fields are perpendicular."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=30)
        field.add_grid_field(angle_degrees=45, strength=1.0)

        seed = np.array([50, 50])
        config = StreamlineConfig(max_length=20.0)

        # Trace both
        result_major = trace_streamline_rk45(field, seed, config, field_type="major")
        result_minor = trace_streamline_rk45(field, seed, config, field_type="minor")

        assert result_major.success
        assert result_minor.success

        # Get initial directions
        dir_major = result_major.path[1] - result_major.path[0]
        dir_minor = result_minor.path[1] - result_minor.path[0]

        # Normalize
        dir_major /= np.linalg.norm(dir_major)
        dir_minor /= np.linalg.norm(dir_minor)

        # Should be perpendicular (dot product ~0)
        dot = np.dot(dir_major, dir_minor)
        assert np.abs(dot) < 0.2  # Allow some numerical error


class TestBidirectionalTracing:
    """Test bidirectional streamline tracing."""

    def test_bidirectional_creates_longer_path(self):
        """Test bidirectional tracing produces longer paths."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        seed = np.array([50, 50])
        config = StreamlineConfig(max_length=20.0)

        # Unidirectional
        result_uni = trace_streamline_rk45(field, seed, config)

        # Bidirectional
        result_bi = trace_bidirectional_streamline(field, seed, config)

        # Bidirectional should be longer
        assert result_bi.total_length > result_uni.total_length
        assert len(result_bi.path) > len(result_uni.path)

    def test_bidirectional_seed_in_middle(self):
        """Test seed point is in middle of bidirectional path."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        seed = np.array([50, 50])
        result = trace_bidirectional_streamline(field, seed)

        # Find seed in path (should be close to middle)
        distances_to_seed = np.linalg.norm(result.path - seed, axis=1)
        closest_idx = np.argmin(distances_to_seed)

        middle_idx = len(result.path) // 2

        # Should be within 30% of middle
        assert np.abs(closest_idx - middle_idx) < len(result.path) * 0.3


class TestPathQuality:
    """Test quality of generated paths."""

    def test_path_smoothness(self):
        """Test path has smooth, consistent spacing."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=30)
        field.add_radial_field(center=(50, 50), decay_radius=30, strength=1.0)

        seed = np.array([30, 50])
        result = trace_streamline_rk45(field, seed)

        assert result.success

        # Compute segment lengths
        segments = np.diff(result.path, axis=0)
        segment_lengths = np.linalg.norm(segments, axis=1)

        # Should not have huge variations
        mean_length = np.mean(segment_lengths)
        std_length = np.std(segment_lengths)

        # Coefficient of variation should be reasonable
        cv = std_length / mean_length
        assert cv < 2.0  # Not too spiky

    def test_path_length_accuracy(self):
        """Test reported length matches actual path length."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        result = trace_streamline_rk45(field, [50, 50])

        # Compute length manually
        segments = np.diff(result.path, axis=0)
        manual_length = np.sum(np.linalg.norm(segments, axis=1))

        # Should match reported length
        assert np.isclose(result.total_length, manual_length, rtol=0.01)


class TestUtilityFunctions:
    """Test path processing utilities."""

    def test_resample_path(self):
        """Test path resampling to uniform spacing."""
        # Create irregular path
        path = np.array([[0, 0], [1, 0], [10, 0], [11, 0], [12, 0]])  # Big jump

        resampled = resample_path(path, target_spacing=2.0)

        # Should have approximately length/spacing points
        total_length = 12.0
        expected_points = int(total_length / 2.0) + 1

        assert len(resampled) >= expected_points - 2
        assert len(resampled) <= expected_points + 2

        # Segment lengths should be approximately uniform
        segments = np.diff(resampled, axis=0)
        segment_lengths = np.linalg.norm(segments, axis=1)

        assert np.std(segment_lengths) < 1.0  # Fairly uniform

    def test_smooth_path(self):
        """Test path smoothing filter."""
        # Create noisy path
        np.random.seed(42)
        x = np.linspace(0, 100, 50)
        y = np.linspace(0, 100, 50) + np.random.normal(0, 5, 50)

        noisy_path = np.column_stack([x, y])
        smoothed = smooth_path(noisy_path, window_size=5)

        # Smoothed should have less variation
        noisy_std = np.std(np.diff(noisy_path[:, 1]))
        smoothed_std = np.std(np.diff(smoothed[:, 1]))

        assert smoothed_std < noisy_std


class TestPerformance:
    """Test performance benchmarks."""

    def test_single_streamline_performance(self):
        """Test single streamline traces quickly."""
        import time

        field = TensorField(bounds=(0, 0, 1000, 1000), resolution=50)
        field.add_grid_field(0, 0.5)
        field.add_radial_field((500, 500), 100, 0.5)

        seed = np.array([100, 100])

        start = time.time()
        result = trace_streamline_rk45(field, seed)
        elapsed = time.time() - start

        print(f"\n⏱️  Single streamline: {elapsed*1000:.1f}ms")

        # Should be very fast (<300ms, adjusted for M1 performance)
        assert elapsed < 0.3
        assert result.success

    def test_multiple_streamlines_performance(self):
        """Test tracing multiple streamlines."""
        import time

        field = TensorField(bounds=(0, 0, 1000, 1000), resolution=50)
        field.add_grid_field(0, 0.5)
        field.add_grid_field(90, 0.5)

        # Trace 10 streamlines
        np.random.seed(42)
        seeds = np.random.uniform(100, 900, size=(10, 2))

        start = time.time()
        results = [trace_streamline_rk45(field, seed) for seed in seeds]
        elapsed = time.time() - start

        print(f"\n⏱️  10 streamlines: {elapsed*1000:.1f}ms")

        # Should complete in <1.7s (adjusted for M1 performance)
        assert elapsed < 1.7
        assert all(r.success or r.stop_reason == StopReason.BOUNDARY for r in results)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_length_config(self):
        """Test handling of zero max_length."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        config = StreamlineConfig(max_length=0.0)
        result = trace_streamline_rk45(field, [50, 50], config)

        # Should return immediately
        assert len(result.path) <= 2
        assert result.total_length < 1.0

    def test_very_small_field(self):
        """Test streamline in tiny field."""
        field = TensorField(bounds=(0, 0, 10, 10), resolution=10)
        field.add_grid_field(0, 1.0)

        result = trace_streamline_rk45(field, [5, 5])

        # Should hit boundary quickly
        assert result.stop_reason == StopReason.BOUNDARY
        assert result.total_length < 10.0

    def test_degenerate_field(self):
        """Test field with near-zero tensors."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1e-10)  # Very weak field

        config = StreamlineConfig(max_length=10.0)
        result = trace_streamline_rk45(field, [50, 50], config)

        # Should still work (might be short)
        assert isinstance(result, StreamlineResult)
        # Don't assert success - weak fields might fail
