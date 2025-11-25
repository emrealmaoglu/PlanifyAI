"""Tests for TensorField blending implementation."""

import numpy as np
from backend.core.spatial.basis_fields import GridField, RadialField
from backend.core.spatial.tensor_field import TensorField


class TestTensorFieldBlending:
    """Test tensor blending logic."""

    def test_single_field_passthrough(self):
        """Single field should pass through unchanged."""
        field = GridField((0, 0), 50, theta=0, decay_radius=100)
        tensor_field = TensorField([field])

        points = np.array([[50, 50]])

        # Get tensor from TensorField
        blended = tensor_field.get_blended_tensor(points)[0]

        # Get tensor directly from field
        direct = field.get_tensor(points)[0]

        # Should be identical (no blending artifacts)
        assert np.allclose(blended, direct)

    def test_two_grids_perpendicular(self):
        """
        CRITICAL TEST (Gemini recommendation):
        Two equal-strength orthogonal grids → isotropic tensor.
        """
        # Grid at 0° (horizontal roads)
        field1 = GridField((250, 250), 50, theta=0, decay_radius=150)

        # Grid at 90° (vertical roads)
        field2 = GridField((250, 250), 50, theta=np.pi / 2, decay_radius=150)

        tensor_field = TensorField([field1, field2])

        # Test at center (equal weights)
        points = np.array([[250, 250]])

        # Get eigenvalues
        tensors = tensor_field.get_blended_tensor(points)
        eigenvalues, _ = np.linalg.eigh(tensors[0])

        # Eigenvalues should be approximately equal (isotropic)
        ratio = eigenvalues[0] / eigenvalues[1]
        assert 0.8 < ratio < 1.2, f"Expected isotropic, got ratio {ratio}"

    def test_weight_normalization(self):
        """Blended tensor should be properly normalized."""
        fields = [
            GridField((100, 100), 50, theta=0, decay_radius=100),
            RadialField((300, 300), decay_radius=120),
        ]
        tensor_field = TensorField(fields)

        points = np.array([[200, 200]])
        tensors = tensor_field.get_blended_tensor(points)

        # Tensor should be finite and symmetric
        assert np.all(np.isfinite(tensors))
        assert np.allclose(tensors[0], tensors[0].T)

    def test_eigenvector_orthogonality(self):
        """Major and minor eigenvectors must be orthogonal."""
        field = GridField((0, 0), 50, theta=np.pi / 6, decay_radius=100)
        tensor_field = TensorField([field])

        points = np.array([[50, 50]])

        major = tensor_field.get_eigenvectors(points, "major")[0]
        minor = tensor_field.get_eigenvectors(points, "minor")[0]

        # Dot product should be zero
        dot = np.dot(major, minor)
        assert np.abs(dot) < 1e-6

    def test_zero_weight_fallback(self):
        """Points far from all fields should get identity tensor."""
        # Small decay radius
        field = GridField((0, 0), 50, theta=0, decay_radius=10)
        tensor_field = TensorField([field])

        # Very far point
        points = np.array([[1000, 1000]])
        tensors = tensor_field.get_blended_tensor(points)

        # Should be identity
        assert np.allclose(tensors[0], np.eye(2))

    def test_field_smoothness(self):
        """Field should vary smoothly (no discontinuities)."""
        field = RadialField((250, 250), decay_radius=150)
        tensor_field = TensorField([field])

        # Line of points approaching center
        points = np.array([[250 + i, 250] for i in range(10, 101, 10)])

        vectors = tensor_field.get_eigenvectors(points, "major")

        # Adjacent vectors should be similar (smooth field)
        for i in range(len(vectors) - 1):
            # Cosine similarity (1 = parallel, 0 = perpendicular)
            similarity = np.abs(np.dot(vectors[i], vectors[i + 1]))
            assert similarity > 0.7, f"Discontinuity detected at step {i}"


class TestAnisotropy:
    """Test anisotropy computation."""

    def test_anisotropy_range(self):
        """Anisotropy should be in [0, 1]."""
        field = GridField((0, 0), 50, theta=0, decay_radius=100)
        tensor_field = TensorField([field])

        points = np.random.uniform(-100, 100, (50, 2))
        anisotropy = tensor_field.get_anisotropy(points)

        assert np.all(anisotropy >= 0)
        assert np.all(anisotropy <= 1)

    def test_isotropic_crossing(self):
        """
        NEW TEST (Gemini recommendation):
        Crossing equal grids → low anisotropy.
        """
        field1 = GridField((250, 250), 50, theta=0, decay_radius=150)
        field2 = GridField((250, 250), 50, theta=np.pi / 2, decay_radius=150)
        tensor_field = TensorField([field1, field2])

        # At center (equal weights)
        points = np.array([[250, 250]])
        anisotropy = tensor_field.get_anisotropy(points)

        # Should be low (near 0 = isotropic)
        assert anisotropy[0] < 0.3, f"Expected low anisotropy, got {anisotropy[0]}"

    def test_directional_field(self):
        """Pure grid → high anisotropy."""
        field = GridField((0, 0), 50, theta=0, decay_radius=100)
        tensor_field = TensorField([field])

        points = np.array([[50, 50]])
        anisotropy = tensor_field.get_anisotropy(points)

        # Should be high (near 1 = directional)
        assert anisotropy[0] > 0.7


class TestVisualization:
    """Test visualization methods."""

    def test_visualize_runs(self):
        """Visualization should run without errors."""
        fields = [
            GridField((250, 250), 50, theta=0, decay_radius=150),
            RadialField((100, 100), decay_radius=120),
        ]
        tensor_field = TensorField(fields)

        # Should not raise
        fig = tensor_field.visualize(
            bbox=(0, 0, 500, 500),
            resolution=20,  # Low res for speed
            show_anisotropy=True,
            show_streamplot=True,
        )

        assert fig is not None
