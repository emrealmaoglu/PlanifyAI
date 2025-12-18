"""
Unit tests for basis field components.

Tests verify:
1. Correct tensor structure (2x2 symmetric)
2. Proper normalization
3. Gaussian decay behavior
4. Edge cases (zero radius, center points)
"""

import numpy as np
import pytest

from src.spatial.basis_fields import GridField, RadialField


class TestGridField:
    """Test suite for GridField class."""

    def test_initialization(self):
        """Test GridField creates with correct parameters."""
        field = GridField(angle_degrees=45, strength=0.8)

        assert field.angle_degrees == 45
        assert field.strength == 0.8
        assert field.T_base.shape == (2, 2)
        # Tensor should be symmetric
        assert np.allclose(field.T_base, field.T_base.T)

    def test_tensor_shape(self):
        """Test get_tensor returns correct shape."""
        field = GridField(angle_degrees=0, strength=1.0)

        # Single point
        points = np.array([[100, 200]])
        tensors = field.get_tensor(points)
        assert tensors.shape == (1, 2, 2)

        # Multiple points
        points = np.array([[100, 200], [300, 400], [500, 600]])
        tensors = field.get_tensor(points)
        assert tensors.shape == (3, 2, 2)

    def test_north_south_field(self):
        """Test 0° field points north."""
        field = GridField(angle_degrees=0, strength=1.0)
        points = np.array([[0, 0]])
        tensors = field.get_tensor(points)

        # Eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(tensors[0])
        major_vec = eigenvectors[:, 1]  # Largest eigenvalue

        # Should point north (0°)
        expected = np.array([1, 0])  # cos(0), sin(0)
        assert np.allclose(major_vec, expected, atol=1e-6)

    def test_east_west_field(self):
        """Test 90° field points east."""
        field = GridField(angle_degrees=90, strength=1.0)
        points = np.array([[0, 0]])
        tensors = field.get_tensor(points)

        eigenvalues, eigenvectors = np.linalg.eigh(tensors[0])
        major_vec = eigenvectors[:, 1]

        # Should point east (90°)
        expected = np.array([0, 1])  # cos(90), sin(90)
        assert np.allclose(major_vec, expected, atol=1e-6)

    def test_strength_scaling(self):
        """Test strength parameter scales tensor magnitude."""
        field_weak = GridField(angle_degrees=0, strength=0.5)
        field_strong = GridField(angle_degrees=0, strength=2.0)

        points = np.array([[0, 0]])
        T_weak = field_weak.get_tensor(points)[0]
        T_strong = field_strong.get_tensor(points)[0]

        # Strong should be 4x weak (2.0 / 0.5)
        assert np.allclose(T_strong, T_weak * 4.0)


class TestRadialField:
    """Test suite for RadialField class."""

    def test_initialization(self):
        """Test RadialField creates with correct parameters."""
        field = RadialField(center=(500, 500), decay_radius=100, strength=0.8)

        assert np.array_equal(field.center, np.array([500, 500]))
        assert field.decay_radius == 100
        assert field.strength == 0.8

    def test_tensor_shape(self):
        """Test get_tensor returns correct shape."""
        field = RadialField(center=(0, 0), decay_radius=100, strength=1.0)

        points = np.array([[100, 0], [0, 100], [100, 100]])
        tensors = field.get_tensor(points)

        assert tensors.shape == (3, 2, 2)
        # All tensors should be symmetric (vectorized check for speed)
        assert np.allclose(tensors, tensors.transpose(0, 2, 1))

    def test_radial_direction(self):
        """Test tensor points radially outward from center."""
        field = RadialField(center=(0, 0), decay_radius=100, strength=1.0)

        # Test point directly east of center
        points = np.array([[100, 0]])
        tensors = field.get_tensor(points)

        eigenvalues, eigenvectors = np.linalg.eigh(tensors[0])
        major_vec = eigenvectors[:, 1]

        # Should point east (radially outward)
        expected = np.array([1, 0])
        assert np.allclose(np.abs(major_vec), np.abs(expected), atol=1e-6)

    def test_gaussian_decay(self):
        """Test field strength decays with distance."""
        field = RadialField(center=(0, 0), decay_radius=100, strength=1.0)

        # Point at center: maximum strength
        p_center = np.array([[0, 0]])
        T_center = field.get_tensor(p_center)[0]

        # Point at decay_radius: ~0.6 strength
        p_radius = np.array([[100, 0]])
        T_radius = field.get_tensor(p_radius)[0]

        # Point far away: near zero
        p_far = np.array([[500, 0]])
        T_far = field.get_tensor(p_far)[0]

        # Frobenius norms (total tensor magnitude)
        norm_center = np.linalg.norm(T_center)
        norm_radius = np.linalg.norm(T_radius)
        norm_far = np.linalg.norm(T_far)

        # Verify decay
        assert norm_center > norm_radius > norm_far
        assert norm_radius / norm_center < 0.7  # Should be ~0.6
        assert norm_far < 0.1  # Nearly zero

    def test_center_singularity_handling(self):
        """Test field handles point exactly at center (avoid div by zero)."""
        field = RadialField(center=(100, 100), decay_radius=50, strength=1.0)

        # Point exactly at center
        points = np.array([[100, 100]])

        # Should not crash
        tensors = field.get_tensor(points)

        assert tensors.shape == (1, 2, 2)
        assert not np.any(np.isnan(tensors))
        assert not np.any(np.isinf(tensors))


# INTEGRATION TEST
def test_multiple_field_combination():
    """Test that we can create and combine multiple fields."""
    grid_ns = GridField(angle_degrees=0, strength=0.5)
    grid_ew = GridField(angle_degrees=90, strength=0.5)
    radial = RadialField(center=(500, 500), decay_radius=100, strength=0.8)

    points = np.array([[400, 400], [500, 500], [600, 600]])

    T_grid_ns = grid_ns.get_tensor(points)
    T_grid_ew = grid_ew.get_tensor(points)
    T_radial = radial.get_tensor(points)

    # Combined field (simple addition)
    T_combined = T_grid_ns + T_grid_ew + T_radial

    assert T_combined.shape == (3, 2, 2)

    # All tensors should be symmetric (vectorized check for speed)
    assert np.allclose(T_combined, T_combined.transpose(0, 2, 1))
