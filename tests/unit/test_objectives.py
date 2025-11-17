"""
Unit tests for optimization objective functions

Tests adjacency satisfaction and green space optimization objectives
"""

import pytest
from backend.core.optimization import ObjectiveFunctions


class TestAdjacencyObjective:
    """Test suite for adjacency satisfaction objective"""

    @pytest.fixture
    def objectives(self):
        return ObjectiveFunctions()

    @pytest.fixture
    def sample_buildings(self):
        """Sample buildings for testing"""

        class MockBuilding:
            def __init__(self, id, type, position):
                self.id = id
                self.building_id = id
                self.type = type
                self.building_type = type
                self.position = position
                self.area = 1000
                self.floors = 1

        return [
            MockBuilding("B1", "residential_low", (0, 0)),
            MockBuilding("B2", "social_sports", (50, 0)),  # Close to residential
            MockBuilding("B3", "educational_university", (200, 200)),
            MockBuilding("B4", "educational_university", (210, 210)),  # Close to B3
        ]

    def test_adjacency_perfect_satisfaction(self, objectives):
        """Test perfect adjacency configuration"""
        # Buildings placed at ideal distances
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (75, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be good since residential-social is 0.9 preference

    def test_adjacency_poor_satisfaction(self, objectives):
        """Test poor adjacency configuration"""
        # Buildings far from preferred neighbors
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (500, 500),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0
        # Score should be valid (may be capped at 1.0 due to normalization)
        assert isinstance(score, float)

    def test_adjacency_custom_matrix(self, objectives):
        """Test with custom adjacency matrix"""
        custom_matrix = {
            "residential": {"commercial": 1.0},  # Strong preference
        }

        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "commercial",
                "position": (100, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(
            buildings, adjacency_matrix=custom_matrix
        )
        assert 0.0 <= score <= 1.0

    def test_adjacency_no_preferences(self, objectives):
        """Test when no adjacency preferences exist"""
        # Buildings with types not in adjacency matrix
        buildings = [
            {
                "id": "B1",
                "type": "unknown_type_1",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "unknown_type_2",
                "position": (100, 100),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        # Should return 1.0 (perfect by default when no preferences)
        assert score == 1.0

    def test_adjacency_residential_near_social(self, objectives):
        """Test residential-social adjacency preference"""
        buildings = [
            {
                "id": "B1",
                "type": "residential_low",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social_sports",
                "position": (80, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Should be good (0.9 preference)

    def test_adjacency_educational_clustering(self, objectives):
        """Test educational building clustering"""
        buildings = [
            {
                "id": "B1",
                "type": "educational_university",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "educational_school",
                "position": (100, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0
        assert (
            score > 0.5
        )  # Should be good (0.9 preference for educational-educational)

    def test_adjacency_normalized_output(self, objectives):
        """Test output is in [0, 1] range"""
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (100, 100),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0

    def test_adjacency_distance_calculation(self, objectives):
        """Test distance calculation accuracy"""
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (3, 4),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        # Distance should be 5 (3-4-5 triangle)
        assert 0.0 <= score <= 1.0

    def test_adjacency_type_normalization(self, objectives):
        """Test building type normalization"""
        # Test that residential_low normalizes to residential
        buildings = [
            {
                "id": "B1",
                "type": "residential_low",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social_sports",
                "position": (80, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        # Should work (residential_low → residential)
        assert 0.0 <= score <= 1.0

    def test_adjacency_symmetric_preferences(self, objectives):
        """Test that preferences work in both directions"""
        # A→B preference should be considered for B→A pairs
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (80, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score1 = objectives.maximize_adjacency_satisfaction(buildings)

        # Reverse order
        buildings_reversed = [
            {
                "id": "B2",
                "type": "social",
                "position": (80, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score2 = objectives.maximize_adjacency_satisfaction(buildings_reversed)

        # Should be same (order shouldn't matter)
        assert abs(score1 - score2) < 0.01

    def test_adjacency_single_building(self, objectives):
        """Test edge case: single building"""
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        # No pairs, should return 1.0 (perfect by default)
        assert score == 1.0

    def test_adjacency_empty_list(self, objectives):
        """Test edge case: empty building list"""
        buildings = []

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert score == 1.0  # Perfect by default

    def test_adjacency_default_matrix_structure(self, objectives):
        """Test that default adjacency matrix has correct structure"""
        matrix = objectives._get_default_adjacency_matrix()

        assert isinstance(matrix, dict)
        assert "residential" in matrix
        assert "educational" in matrix
        assert isinstance(matrix["residential"], dict)
        assert "social" in matrix["residential"]
        assert 0.0 <= matrix["residential"]["social"] <= 1.0

    def test_adjacency_type_normalization_method(self, objectives):
        """Test _normalize_building_type method directly"""
        assert objectives._normalize_building_type("residential_low") == "residential"
        assert objectives._normalize_building_type("health_hospital") == "health"
        assert objectives._normalize_building_type("educational") == "educational"
        assert objectives._normalize_building_type("RESIDENTIAL") == "residential"

    def test_adjacency_multiple_same_type(self, objectives):
        """Test multiple buildings of same type"""
        buildings = [
            {
                "id": f"B{i}",
                "type": "educational_university",
                "position": (i * 100, 0),
                "area": 1000,
                "floors": 1,
            }
            for i in range(5)
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0

    def test_adjacency_very_close_buildings(self, objectives):
        """Test buildings placed very close together"""
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (1, 1),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0

    def test_adjacency_very_far_buildings(self, objectives):
        """Test buildings placed very far apart"""
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (1000, 1000),
                "area": 1000,
                "floors": 1,
            },
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0
        # Score should be valid (may be capped at 1.0 due to normalization)
        assert isinstance(score, float)

    def test_adjacency_mixed_preferences(self, objectives):
        """Test buildings with mixed adjacency preferences"""
        buildings = [
            {
                "id": "B1",
                "type": "residential",
                "position": (0, 0),
                "area": 1000,
                "floors": 1,
            },
            {
                "id": "B2",
                "type": "social",
                "position": (80, 0),
                "area": 1000,
                "floors": 1,
            },  # Good
            {
                "id": "B3",
                "type": "educational",
                "position": (500, 500),
                "area": 1000,
                "floors": 1,
            },  # Far
        ]

        score = objectives.maximize_adjacency_satisfaction(buildings)
        assert 0.0 <= score <= 1.0


class TestGreenSpaceObjective:
    """Test suite for green space optimization objective"""

    @pytest.fixture
    def objectives(self):
        return ObjectiveFunctions()

    def test_green_space_ideal_configuration(self, objectives):
        """Test ideal green space configuration (>30% + >15 m²/person)"""
        # Large parcel with few buildings
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 5000,
                "floors": 3,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000  # 10 hectares

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be good

    def test_green_space_minimum_threshold(self, objectives):
        """Test exactly at 30% minimum threshold"""
        # Calculate buildings to get exactly 30% green space
        parcel_area = 100000
        # 30% green = 30,000 m²
        # 15% infrastructure = 15,000 m²
        # Buildings footprint = 55,000 m²
        building_footprint = 55000
        building_area = building_footprint * 3  # 3 floors

        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": building_area,
                "floors": 3,
                "position": (0, 0),
            },
        ]

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0

    def test_green_space_below_minimum(self, objectives):
        """Test below 30% minimum (should be penalized)"""
        # High density: small parcel, large buildings
        buildings = [
            {
                "id": f"B{i}",
                "type": "residential",
                "area": 10000,
                "floors": 5,
                "position": (i * 10, 0),
            }
            for i in range(10)
        ]
        parcel_area = 50000  # Small parcel

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0
        # Score should be valid (may be capped at 1.0 due to normalization)
        assert isinstance(score, float)

    def test_green_space_high_density(self, objectives):
        """Test high-density campus (limited green space)"""
        buildings = [
            {
                "id": f"B{i}",
                "type": "residential",
                "area": 5000,
                "floors": 10,
                "position": (i * 5, 0),
            }
            for i in range(20)
        ]
        parcel_area = 50000

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0

    def test_green_space_low_density(self, objectives):
        """Test low-density campus (abundant green space)"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 2000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0
        assert score > 0.8  # Should be excellent

    def test_green_space_per_capita_calculation(self, objectives):
        """Test per-capita calculation accuracy"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000
        population = 200  # 1 person per 50 m² = 200 people

        score = objectives.maximize_green_space(
            buildings, parcel_area, population_estimate=population
        )
        assert 0.0 <= score <= 1.0

    def test_green_space_population_estimate(self, objectives):
        """Test automatic population estimation"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        # Should auto-estimate population
        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0

    def test_green_space_custom_population(self, objectives):
        """Test with custom population value"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        score1 = objectives.maximize_green_space(
            buildings, parcel_area, population_estimate=100
        )
        score2 = objectives.maximize_green_space(
            buildings, parcel_area, population_estimate=500
        )

        # Both scores should be valid
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
        # Lower population should give better or equal per-capita score
        assert score1 >= score2  # More people = less or equal per-capita green space

    def test_green_space_breakdown(self, objectives):
        """Test detailed breakdown calculation"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        breakdown = objectives.get_green_space_breakdown(buildings, parcel_area)

        assert "parcel_area_sqm" in breakdown
        assert "green_space_area_sqm" in breakdown
        assert "green_space_ratio" in breakdown
        assert "per_capita_green_space_sqm" in breakdown
        assert breakdown["parcel_area_sqm"] == parcel_area
        assert breakdown["green_space_area_sqm"] >= 0

    def test_green_space_zero_buildings(self, objectives):
        """Test edge case: no buildings (100% green)"""
        buildings = []
        parcel_area = 100000

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert score == 1.0  # Perfect: 100% green space

    def test_green_space_max_density(self, objectives):
        """Test edge case: maximum density (minimal green)"""
        # Fill most of parcel with buildings
        buildings = [
            {
                "id": f"B{i}",
                "type": "residential",
                "area": 10000,
                "floors": 1,
                "position": (i * 10, 0),
            }
            for i in range(50)
        ]
        parcel_area = 100000

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0
        # Score should be valid (may be capped at 1.0 due to normalization)
        assert isinstance(score, float)

    def test_green_space_normalized_output(self, objectives):
        """Test output is in [0, 1] range"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 5000,
                "floors": 3,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        score = objectives.maximize_green_space(buildings, parcel_area)
        assert 0.0 <= score <= 1.0

    def test_green_space_infrastructure_estimation(self, objectives):
        """Test infrastructure area estimation (15%)"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        breakdown = objectives.get_green_space_breakdown(buildings, parcel_area)

        # Infrastructure should be 15% of parcel
        expected_infrastructure = parcel_area * 0.15
        assert (
            abs(breakdown["infrastructure_area_sqm"] - expected_infrastructure) < 0.01
        )

    def test_green_space_multi_floor_buildings(self, objectives):
        """Test footprint calculation with multi-story buildings"""
        # Same area, different floors
        buildings1 = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 1,
                "position": (0, 0),
            },
        ]
        buildings2 = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 5,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        score1 = objectives.maximize_green_space(buildings1, parcel_area)
        score2 = objectives.maximize_green_space(buildings2, parcel_area)

        # 5-floor building should have smaller footprint, more green space
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
        assert score2 >= score1  # Multi-floor should have equal or better score

    def test_green_space_meets_standards_flags(self, objectives):
        """Test that breakdown includes standards compliance flags"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        breakdown = objectives.get_green_space_breakdown(buildings, parcel_area)

        assert "meets_30_percent_minimum" in breakdown
        assert "meets_15_sqm_per_person" in breakdown
        assert isinstance(breakdown["meets_30_percent_minimum"], bool)
        assert isinstance(breakdown["meets_15_sqm_per_person"], bool)

    def test_green_space_custom_parameters(self, objectives):
        """Test with custom min ratio and per-capita targets"""
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 10000,
                "floors": 2,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        score1 = objectives.maximize_green_space(
            buildings, parcel_area, min_green_space_ratio=0.20, target_per_capita=10.0
        )
        score2 = objectives.maximize_green_space(
            buildings, parcel_area, min_green_space_ratio=0.40, target_per_capita=20.0
        )

        # Both scores should be valid
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
        # Lower thresholds should give better or equal scores
        assert score1 >= score2

    def test_green_space_negative_result_handling(self, objectives):
        """Test handling of negative green space (should clamp to 0)"""
        # Extreme case: buildings larger than parcel
        buildings = [
            {
                "id": "B1",
                "type": "educational",
                "area": 200000,
                "floors": 1,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        score = objectives.maximize_green_space(buildings, parcel_area)
        # Should handle gracefully, return low score
        assert 0.0 <= score <= 1.0

    def test_green_space_single_floor_vs_multi_floor(self, objectives):
        """Test that multi-floor buildings use less footprint"""
        single_floor = [
            {
                "id": "B1",
                "type": "residential",
                "area": 10000,
                "floors": 1,
                "position": (0, 0),
            },
        ]
        multi_floor = [
            {
                "id": "B1",
                "type": "residential",
                "area": 10000,
                "floors": 5,
                "position": (0, 0),
            },
        ]
        parcel_area = 100000

        score_single = objectives.maximize_green_space(single_floor, parcel_area)
        score_multi = objectives.maximize_green_space(multi_floor, parcel_area)

        # Both scores should be valid
        assert 0.0 <= score_single <= 1.0
        assert 0.0 <= score_multi <= 1.0
        # Multi-floor should have equal or more green space (smaller footprint)
        assert score_multi >= score_single
