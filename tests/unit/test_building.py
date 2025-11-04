"""
Unit tests for Building and BuildingType classes
"""
import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType, create_sample_campus


class TestBuildingCreation:
    """Test Building object creation"""

    def test_building_creation_valid(self):
        """Test creating a valid building"""
        building = Building(
            id="test_building",
            type=BuildingType.LIBRARY,
            area=5000.0,
            floors=3,
        )
        assert building.id == "test_building"
        assert building.type == BuildingType.LIBRARY
        assert building.area == 5000.0
        assert building.floors == 3
        assert building.position is None
        assert building.constraints == {}

    def test_building_creation_with_position(self):
        """Test creating building with position"""
        building = Building(
            id="test_building",
            type=BuildingType.EDUCATIONAL,
            area=6000.0,
            floors=4,
            position=(100.0, 200.0),
        )
        assert building.position == (100.0, 200.0)

    def test_building_creation_invalid_area(self):
        """Test creating building with invalid area"""
        with pytest.raises(ValueError, match="Building area must be positive"):
            Building(
                id="test_building",
                type=BuildingType.RESIDENTIAL,
                area=-100.0,
                floors=2,
            )

    def test_building_creation_zero_area(self):
        """Test creating building with zero area"""
        with pytest.raises(ValueError, match="Building area must be positive"):
            Building(
                id="test_building",
                type=BuildingType.RESIDENTIAL,
                area=0.0,
                floors=2,
            )

    def test_building_creation_invalid_floors(self):
        """Test creating building with invalid floors"""
        with pytest.raises(ValueError, match="Building floors must be positive"):
            Building(
                id="test_building",
                type=BuildingType.RESIDENTIAL,
                area=1000.0,
                floors=-1,
            )

    def test_building_creation_invalid_position(self):
        """Test creating building with invalid position"""
        with pytest.raises(ValueError, match="Position must be \\(x, y\\) tuple"):
            Building(
                id="test_building",
                type=BuildingType.RESIDENTIAL,
                area=1000.0,
                floors=2,
                position=(100.0,),  # Invalid: only one coordinate
            )


class TestBuildingProperties:
    """Test Building computed properties"""

    def test_building_footprint_calculation(self):
        """Test footprint calculation"""
        building = Building(id="test_building", type=BuildingType.LIBRARY, area=6000.0, floors=3)
        expected_footprint = 6000.0 / 3
        assert building.footprint == pytest.approx(expected_footprint)

    def test_building_radius_calculation(self):
        """Test radius calculation"""
        building = Building(id="test_building", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        footprint = building.footprint
        expected_radius = np.sqrt(footprint / np.pi)
        assert building.radius == pytest.approx(expected_radius)

    def test_building_importance_calculation(self):
        """Test importance calculation for different building types"""
        # Library should have higher importance weight (2.2)
        library = Building(id="library", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        library_importance = library.importance

        # Residential should have lower importance weight (1.0)
        residential = Building(
            id="residential", type=BuildingType.RESIDENTIAL, area=5000.0, floors=3
        )
        residential_importance = residential.importance

        # Library should have higher importance
        assert library_importance > residential_importance
        assert library_importance == pytest.approx(2.2 * np.sqrt(5000.0))
        assert residential_importance == pytest.approx(1.0 * np.sqrt(5000.0))

    def test_building_importance_all_types(self):
        """Test importance weights for all building types"""
        # Health should have highest weight (2.5)
        health = Building(id="health", type=BuildingType.HEALTH, area=1000.0, floors=1)
        assert health.importance == pytest.approx(2.5 * np.sqrt(1000.0))

        # Residential should have lowest weight (1.0)
        residential = Building(
            id="residential", type=BuildingType.RESIDENTIAL, area=1000.0, floors=1
        )
        assert residential.importance == pytest.approx(1.0 * np.sqrt(1000.0))


class TestBuildingDistance:
    """Test Building distance calculations"""

    def test_building_distance_calculation(self):
        """Test distance calculation between two buildings"""
        building1 = Building(
            id="b1",
            type=BuildingType.LIBRARY,
            area=5000.0,
            floors=3,
            position=(0.0, 0.0),
        )
        building2 = Building(
            id="b2",
            type=BuildingType.EDUCATIONAL,
            area=6000.0,
            floors=4,
            position=(3.0, 4.0),
        )
        distance = building1.distance_to(building2)
        expected_distance = np.sqrt(3.0**2 + 4.0**2)  # 5.0
        assert distance == pytest.approx(expected_distance)

    def test_building_distance_no_position(self):
        """Test distance calculation when position not set"""
        building1 = Building(id="b1", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        building2 = Building(
            id="b2",
            type=BuildingType.EDUCATIONAL,
            area=6000.0,
            floors=4,
            position=(3.0, 4.0),
        )
        with pytest.raises(ValueError, match="doesn't have position set"):
            building1.distance_to(building2)


class TestBuildingOverlap:
    """Test Building overlap detection"""

    def test_building_overlap_no_overlap(self):
        """Test overlap detection when buildings don't overlap"""
        building1 = Building(
            id="b1",
            type=BuildingType.LIBRARY,
            area=5000.0,
            floors=3,
            position=(0.0, 0.0),
        )
        building2 = Building(
            id="b2",
            type=BuildingType.EDUCATIONAL,
            area=6000.0,
            floors=4,
            position=(200.0, 200.0),  # Far apart
        )
        assert not building1.overlaps_with(building2)

    def test_building_overlap_detection(self):
        """Test overlap detection when buildings overlap"""
        building1 = Building(
            id="b1",
            type=BuildingType.LIBRARY,
            area=5000.0,
            floors=3,
            position=(0.0, 0.0),
        )
        radius1 = building1.radius

        # Place building2 very close (within radius + margin)
        building2 = Building(
            id="b2",
            type=BuildingType.EDUCATIONAL,
            area=6000.0,
            floors=4,
            position=(radius1, 0.0),  # Just touching
        )
        # Should overlap due to safety margin
        assert building1.overlaps_with(building2)

    def test_building_overlap_no_position(self):
        """Test overlap when position not set"""
        building1 = Building(id="b1", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        building2 = Building(
            id="b2",
            type=BuildingType.EDUCATIONAL,
            area=6000.0,
            floors=4,
            position=(100.0, 100.0),
        )
        # Should return False when position not set
        assert not building1.overlaps_with(building2)

    def test_building_overlap_custom_margin(self):
        """Test overlap with custom safety margin"""
        building1 = Building(
            id="b1",
            type=BuildingType.LIBRARY,
            area=5000.0,
            floors=3,
            position=(0.0, 0.0),
        )
        building2 = Building(
            id="b2",
            type=BuildingType.EDUCATIONAL,
            area=6000.0,
            floors=4,
            position=(200.0, 200.0),
        )
        # With very large margin, should overlap
        assert building1.overlaps_with(building2, safety_margin=1000.0)


class TestBuildingEquality:
    """Test Building equality and hashing"""

    def test_building_equality(self):
        """Test building equality based on ID"""
        building1 = Building(id="same_id", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        building2 = Building(id="same_id", type=BuildingType.EDUCATIONAL, area=6000.0, floors=4)
        assert building1 == building2

    def test_building_inequality(self):
        """Test building inequality"""
        building1 = Building(id="id1", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        building2 = Building(id="id2", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        assert building1 != building2

    def test_building_hash(self):
        """Test building hashing"""
        building = Building(id="test_id", type=BuildingType.LIBRARY, area=5000.0, floors=3)
        # Should be hashable
        assert hash(building) == hash("test_id")


class TestBuildingRepresentation:
    """Test Building string representation"""

    def test_building_repr_without_position(self):
        """Test building representation without position"""
        building = Building(
            id="test_building",
            type=BuildingType.LIBRARY,
            area=5000.0,
            floors=3,
        )
        repr_str = repr(building)
        assert "test_building" in repr_str
        assert "library" in repr_str.lower()
        assert "unplaced" in repr_str.lower()

    def test_building_repr_with_position(self):
        """Test building representation with position"""
        building = Building(
            id="test_building",
            type=BuildingType.LIBRARY,
            area=5000.0,
            floors=3,
            position=(100.0, 200.0),
        )
        repr_str = repr(building)
        assert "test_building" in repr_str
        assert "(100.0, 200.0)" in repr_str or "100.0" in repr_str


class TestSampleCampus:
    """Test sample campus creation"""

    def test_sample_campus_creation(self):
        """Test creating sample campus"""
        campus = create_sample_campus()
        assert len(campus) == 10
        assert all(isinstance(b, Building) for b in campus)

    def test_sample_campus_types(self):
        """Test sample campus has diverse building types"""
        campus = create_sample_campus()
        building_types = {b.type for b in campus}
        # Should have multiple different types
        assert len(building_types) >= 5

    def test_sample_campus_unique_ids(self):
        """Test sample campus has unique building IDs"""
        campus = create_sample_campus()
        building_ids = [b.id for b in campus]
        assert len(building_ids) == len(set(building_ids))  # All unique
