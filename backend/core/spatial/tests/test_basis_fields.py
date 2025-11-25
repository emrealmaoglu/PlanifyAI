"""Tests for basis field implementations."""

import numpy as np
from backend.core.spatial.basis_fields import GridField, RadialField


class TestGridField:
    """Test GridField implementation."""

    def test_initialization(self):
        """Test GridField constructor."""
        field = GridField(center=(100, 200), size=50, theta=0, decay_radius=150)
        assert field.center[0] == 100
        assert field.center[1] == 200
        assert field.theta == 0

    def test_tensor_orthogonality(self):
        """Test that tensors produce orthogonal eigenvectors."""
        field = GridField(center=(0, 0), size=50, theta=0, decay_radius=100)

        points = np.array([[50, 50]])
        tensors = field.get_tensor(points)

        # Extract eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(tensors[0])

        # Check orthogonality: v1 · v2 = 0
        dot_product = np.dot(eigenvectors[:, 0], eigenvectors[:, 1])
        assert np.abs(dot_product) < 1e-6

    def test_rotation(self):
        """Test that theta parameter rotates the tensor."""
        # No rotation
        field_0 = GridField((0, 0), 50, theta=0, decay_radius=100)
        # 45° rotation
        field_45 = GridField((0, 0), 50, theta=np.pi / 4, decay_radius=100)

        points = np.array([[100, 100]])

        tensor_0 = field_0.get_tensor(points)[0]
        tensor_45 = field_45.get_tensor(points)[0]

        # Tensors should be different after rotation
        assert not np.allclose(tensor_0, tensor_45)

    def test_weight_decay(self):
        """Test Gaussian weight decay."""
        field = GridField((0, 0), 50, theta=0, decay_radius=100)

        # Points at different distances
        points = np.array(
            [
                [0, 0],  # At center: weight ≈ 1
                [100, 0],  # 1 sigma away: weight ≈ 0.6
                [200, 0],  # 2 sigma away: weight ≈ 0.14
            ]
        )

        weights = field.get_weight(points)

        assert weights[0] > 0.99  # Near center
        assert 0.5 < weights[1] < 0.7  # 1 sigma
        assert weights[2] < 0.2  # 2 sigma


class TestRadialField:
    """Test RadialField implementation."""

    def test_initialization(self):
        """Test RadialField constructor."""
        field = RadialField(center=(100, 200), decay_radius=150)
        assert field.center[0] == 100
        assert field.center[1] == 200

    def test_radial_vectors(self):
        """Test that major eigenvector points radially."""
        field = RadialField(center=(0, 0), decay_radius=100)

        # Test point to the right of center
        points = np.array([[100, 0]])
        tensors = field.get_tensor(points)

        # Extract major eigenvector (largest eigenvalue)
        eigenvalues, eigenvectors = np.linalg.eigh(tensors[0])
        major_eigenvector = eigenvectors[:, 1]  # Second column = largest eigenvalue

        # Should point in +x direction (radial from origin)
        expected = np.array([1, 0])
        assert np.allclose(major_eigenvector, expected, atol=1e-6)

    def test_singularity_properties(self):
        """Test behavior near center (singularity)."""
        field = RadialField(center=(0, 0), decay_radius=100)

        # Very close to center
        points = np.array([[1e-3, 1e-3]])
        tensors = field.get_tensor(points)

        # Tensor should still be valid (no NaN/Inf)
        assert np.all(np.isfinite(tensors))

    def test_decay(self):
        """Test weight decay for radial field."""
        field = RadialField(center=(0, 0), decay_radius=100)

        points = np.array(
            [
                [0, 0],
                [100, 0],
                [300, 0],
            ]
        )

        weights = field.get_weight(points)

        # Should decay with distance
        assert weights[0] > weights[1] > weights[2]
