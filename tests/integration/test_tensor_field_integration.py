"""
Integration tests: tensor field + existing H-SAGA optimizer.

Verifies tensor field can consume Building objects from Week 1.
"""

import time

import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType
from src.spatial.tensor_field import create_campus_tensor_field


def test_tensor_field_from_hsaga_buildings():
    """Test creating tensor field from H-SAGA optimization result."""

    # Mock buildings (same format as H-SAGA output)
    buildings = [
        Building("ADM-01", BuildingType.ADMINISTRATIVE, 1200, 3, position=(500, 500)),
        Building("LIB-01", BuildingType.LIBRARY, 1500, 2, position=(750, 250)),
        Building("RES-01", BuildingType.RESIDENTIAL, 800, 5, position=(250, 750)),
        Building("EDU-01", BuildingType.EDUCATIONAL, 1000, 3, position=(250, 250)),
        Building("DIN-01", BuildingType.DINING, 600, 2, position=(750, 750)),
    ]

    # Create field
    field = create_campus_tensor_field(buildings, bounds=(0, 0, 1000, 1000), resolution=50)

    # Verify field is functional
    assert len(field.basis_fields) >= 4  # 2 grid + N radial

    # Test eigenvector extraction
    test_points = np.array([[500, 500], [250, 250], [750, 750]])
    major_vecs = field.get_eigenvectors(test_points, field_type="major")

    assert major_vecs.shape == (3, 2)
    assert np.allclose(np.linalg.norm(major_vecs, axis=1), 1.0)


def test_performance_with_realistic_building_count():
    """Test performance with 50 buildings (realistic campus)."""

    # Create 50 mock buildings
    np.random.seed(42)
    buildings = []
    for i in range(50):
        pos = np.random.uniform(0, 1000, size=2)
        area = np.random.uniform(500, 2000)
        floors = np.random.randint(1, 6)
        building_type = np.random.choice(
            [
                BuildingType.RESIDENTIAL,
                BuildingType.EDUCATIONAL,
                BuildingType.ADMINISTRATIVE,
                BuildingType.LIBRARY,
            ]
        )

        buildings.append(
            Building(
                f"BLD-{i:02d}",
                building_type,
                area,
                floors,
                position=tuple(pos),
            )
        )

    # Time field creation
    start = time.time()
    field = create_campus_tensor_field(buildings, (0, 0, 1000, 1000), resolution=50)
    elapsed = time.time() - start

    print(f"\n⏱️  Field creation time (50 buildings): {elapsed:.3f}s")

    # Should be fast (<1 second)
    assert elapsed < 1.0, f"Field creation too slow: {elapsed:.3f}s"

    # Time eigenvector queries
    test_points = np.random.uniform(0, 1000, size=(1000, 2))

    start = time.time()
    vectors = field.get_eigenvectors(test_points, field_type="major")
    elapsed = time.time() - start

    print(f"⏱️  Eigenvector query time (1000 points): {elapsed:.3f}s")

    # Should be very fast (<0.3 second for 1000 points, adjusted for M1 performance)
    assert elapsed < 0.3, f"Eigenvector query too slow: {elapsed:.3f}s"
