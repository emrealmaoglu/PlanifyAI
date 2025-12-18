"""
Integration tests for TensorField class.

Tests verify:
1. Field construction from basis fields
2. Interpolation accuracy
3. Eigenvector computation
4. Boundary checking
5. Integration with Building objects (when available)
"""

import numpy as np
import pytest

from src.spatial.tensor_field import TensorField, create_campus_tensor_field


class TestTensorFieldConstruction:
    """Test tensor field creation and manipulation."""

    def test_initialization(self):
        """Test empty field initializes correctly."""
        field = TensorField(bounds=(0, 0, 1000, 1000), resolution=50)

        assert field.config.bounds == (0, 0, 1000, 1000)
        assert field.config.resolution == 50
        assert field.T_xx.shape == (50, 50)
        assert field.T_yy.shape == (50, 50)
        assert field.T_xy.shape == (50, 50)

        # Empty field should be zeros
        assert np.allclose(field.T_xx, 0)
        assert np.allclose(field.T_yy, 0)
        assert np.allclose(field.T_xy, 0)

    def test_add_single_grid_field(self):
        """Test adding a grid field updates tensor components."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=10)
        field.add_grid_field(angle_degrees=0, strength=1.0)

        # After adding a north-pointing field, T_xx should be nonzero
        assert not np.allclose(field.T_xx, 0)
        assert len(field.basis_fields) == 1

    def test_add_multiple_fields(self):
        """Test adding multiple basis fields accumulates correctly."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=10)

        field.add_grid_field(angle_degrees=0, strength=0.5)
        field.add_grid_field(angle_degrees=90, strength=0.5)
        field.add_radial_field(center=(50, 50), decay_radius=20, strength=0.3)

        assert len(field.basis_fields) == 3

        # Combined field should have nonzero components
        assert not np.allclose(field.T_xx, 0)
        assert not np.allclose(field.T_yy, 0)


class TestTensorInterpolation:
    """Test interpolation at arbitrary points."""

    def test_interpolation_at_grid_points(self):
        """Test interpolation matches exactly at grid points."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=11)
        field.add_grid_field(angle_degrees=0, strength=1.0)

        # Query at a grid point (should be exact)
        grid_point = np.array([[50, 50]])
        tensors = field.get_tensor_at_points(grid_point)

        assert tensors.shape == (1, 2, 2)
        # Symmetric
        assert np.allclose(tensors[0], tensors[0].T)

    def test_interpolation_between_grid_points(self):
        """Test cubic interpolation works between grid points."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=11)
        field.add_grid_field(angle_degrees=0, strength=1.0)

        # Query at non-grid point
        query_point = np.array([[47.3, 52.1]])
        tensors = field.get_tensor_at_points(query_point)

        assert tensors.shape == (1, 2, 2)
        assert not np.any(np.isnan(tensors))

    def test_batch_interpolation(self):
        """Test interpolating multiple points simultaneously."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_radial_field(center=(50, 50), decay_radius=30, strength=1.0)

        # Query 100 random points
        np.random.seed(42)
        points = np.random.uniform(0, 100, size=(100, 2))
        tensors = field.get_tensor_at_points(points)

        assert tensors.shape == (100, 2, 2)

        # All tensors should be symmetric (vectorized check for speed)
        assert np.allclose(tensors, tensors.transpose(0, 2, 1))


class TestEigenvectorComputation:
    """Test eigenvector field extraction."""

    def test_major_eigenvector_grid_field(self):
        """Test major eigenvector of a grid field points in correct direction."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(angle_degrees=45, strength=1.0)

        # Query at center
        point = np.array([[50, 50]])
        major_vec = field.get_eigenvectors(point, field_type="major")

        # Should point at 45°
        expected = np.array([np.cos(np.radians(45)), np.sin(np.radians(45))])

        # Allow for small numerical error
        assert np.allclose(major_vec[0], expected, atol=0.01) or np.allclose(
            major_vec[0], -expected, atol=0.01
        )  # 180° ambiguity

    def test_minor_eigenvector_perpendicular(self):
        """Test minor eigenvector is perpendicular to major."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(angle_degrees=0, strength=1.0)

        point = np.array([[50, 50]])
        major_vec = field.get_eigenvectors(point, field_type="major")
        minor_vec = field.get_eigenvectors(point, field_type="minor")

        # Dot product should be ~0 (perpendicular)
        dot = np.dot(major_vec[0], minor_vec[0])
        assert np.abs(dot) < 0.01

    def test_eigenvectors_unit_length(self):
        """Test all eigenvectors are normalized."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(angle_degrees=0, strength=2.5)  # Non-unit strength
        field.add_radial_field(center=(50, 50), decay_radius=30, strength=1.8)

        # Query multiple points
        points = np.array([[25, 25], [50, 50], [75, 75]])
        major_vecs = field.get_eigenvectors(points, field_type="major")
        minor_vecs = field.get_eigenvectors(points, field_type="minor")

        # All vectors should have unit length
        for v in major_vecs:
            assert np.allclose(np.linalg.norm(v), 1.0, atol=1e-6)
        for v in minor_vecs:
            assert np.allclose(np.linalg.norm(v), 1.0, atol=1e-6)

    def test_radial_field_eigenvector_direction(self):
        """Test radial field eigenvector points radially."""
        field = TensorField(bounds=(0, 0, 100, 100), resolution=30)
        field.add_radial_field(center=(50, 50), decay_radius=20, strength=1.0)

        # Test point east of center
        point_east = np.array([[70, 50]])
        major_vec = field.get_eigenvectors(point_east, field_type="major")

        # Should point outward (east = [1, 0])
        expected_east = np.array([1, 0])
        assert np.allclose(np.abs(major_vec[0]), np.abs(expected_east), atol=0.1)


class TestBoundaryChecking:
    """Test boundary detection."""

    def test_point_inside_bounds(self):
        """Test in_bounds returns True for interior points."""
        field = TensorField(bounds=(0, 0, 100, 100))

        assert field.in_bounds(np.array([50, 50]))
        assert field.in_bounds(np.array([[25, 75]]))

    def test_point_outside_bounds(self):
        """Test in_bounds returns False for exterior points."""
        field = TensorField(bounds=(0, 0, 100, 100))

        assert not field.in_bounds(np.array([-10, 50]))
        assert not field.in_bounds(np.array([50, 150]))
        assert not field.in_bounds(np.array([[110, 110]]))

    def test_point_on_boundary(self):
        """Test edge case: point exactly on boundary."""
        field = TensorField(bounds=(0, 0, 100, 100))

        assert field.in_bounds(np.array([0, 50]))  # Left edge
        assert field.in_bounds(np.array([100, 50]))  # Right edge
        assert field.in_bounds(np.array([50, 0]))  # Bottom
        assert field.in_bounds(np.array([50, 100]))  # Top


class TestFieldStatistics:
    """Test debugging utilities."""

    def test_get_field_stats(self):
        """Test field statistics method."""
        field = TensorField(bounds=(0, 0, 1000, 1000), resolution=50)
        field.add_grid_field(0, strength=1.0)
        field.add_radial_field((500, 500), decay_radius=100, strength=0.5)

        stats = field.get_field_stats()

        assert stats["bounds"] == (0, 0, 1000, 1000)
        assert stats["resolution"] == 50
        assert stats["n_basis_fields"] == 2
        assert "GridField" in stats["basis_field_types"]
        assert "RadialField" in stats["basis_field_types"]


# INTEGRATION TEST (if Building class available)
def test_create_campus_tensor_field():
    """Test factory function with mock buildings."""
    from src.algorithms.building import Building, BuildingType

    buildings = [
        Building(
            "ADM-01",
            BuildingType.ADMINISTRATIVE,
            1200,
            3,
            position=(500, 500),
        ),
        Building("LIB-01", BuildingType.LIBRARY, 1500, 2, position=(700, 700)),
        Building("RES-01", BuildingType.RESIDENTIAL, 800, 5, position=(300, 300)),
    ]

    field = create_campus_tensor_field(buildings, bounds=(0, 0, 1000, 1000), resolution=50)

    # Should have 2 grid + N radial (for ADMINISTRATIVE, LIBRARY)
    assert len(field.basis_fields) >= 4

    # Field should be non-trivial
    assert not np.allclose(field.T_xx, 0)
