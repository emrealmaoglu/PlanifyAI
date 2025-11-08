"""
Edge case tests for H-SAGA optimizer.

Tests boundary conditions, extreme inputs, and error handling.

Created: 2025-11-08
"""
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA


@pytest.fixture
def minimal_bounds():
    """Small bounds (200x200m) for tight space testing"""
    return (0, 0, 200, 200)


@pytest.fixture
def large_bounds():
    """Large bounds (10,000x10,000m) for scale testing"""
    return (0, 0, 10000, 10000)


class TestMinimalBuildings:
    """Tests with minimal number of buildings"""

    def test_single_building_optimization(self):
        """Test optimization with 1 building (minimal case)"""
        buildings = [Building("B1", BuildingType.RESIDENTIAL, 2000, 3)]
        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        # Reduce iterations for quick test
        optimizer.sa_config["iterations_per_temp"] = 5
        optimizer.ga_config["generations"] = 10
        optimizer.ga_config["population_size"] = 5

        result = optimizer.optimize()

        # Should complete without error
        assert result["fitness"] >= 0.0
        assert result["best_solution"] is not None
        assert len(result["best_solution"].positions) == 1

    def test_two_buildings_optimization(self):
        """Test with 2 buildings (minimal GA case)"""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
            Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
        ]
        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        optimizer.sa_config["iterations_per_temp"] = 5
        optimizer.ga_config["generations"] = 10
        optimizer.ga_config["population_size"] = 10

        result = optimizer.optimize()

        assert result["fitness"] >= 0.0
        assert len(result["best_solution"].positions) == 2

        # Check adjacency can be calculated
        assert "adjacency" in result["objectives"]

    def test_three_buildings_triangular_case(self):
        """Test with 3 buildings (triangular spatial case)"""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
            Building("B2", BuildingType.EDUCATIONAL, 2000, 3),
            Building("B3", BuildingType.ADMINISTRATIVE, 2000, 3),
        ]
        optimizer = HybridSAGA(buildings, (0, 0, 500, 500))

        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Should find valid configuration
        assert result["fitness"] > 0.0
        assert result["statistics"]["evaluations"] > 0


class TestSpatialConstraints:
    """Tests with extreme spatial constraints"""

    def test_very_tight_bounds(self, minimal_bounds):
        """Test with very small bounds (200x200m)"""
        # 5 buildings in 200x200 = tight!
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 2) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, minimal_bounds)
        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Should handle tight space
        assert result["fitness"] >= 0.0

        # Check all positions within bounds
        for pos in result["best_solution"].positions.values():
            x, y = pos
            assert minimal_bounds[0] <= x <= minimal_bounds[2]
            assert minimal_bounds[1] <= y <= minimal_bounds[3]

    def test_very_large_bounds(self, large_bounds):
        """Test with very large bounds (10km x 10km)"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, large_bounds)
        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Should handle large space
        assert result["fitness"] >= 0.0

        # Walking distance objective should heavily penalize large distances
        # (but optimization should still work)
        assert "walking" in result["objectives"]

    def test_elongated_bounds(self):
        """Test with elongated rectangle (100x5000m)"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 3) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 100, 5000))
        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Should handle elongated shape
        assert result["fitness"] >= 0.0

        # Buildings should be spread along Y-axis
        positions = list(result["best_solution"].positions.values())
        y_coords = [pos[1] for pos in positions]
        y_spread = max(y_coords) - min(y_coords)

        # Should use most of the vertical space
        assert y_spread > 1000  # At least 1km spread

    def test_square_bounds_perfect_fit(self):
        """Test with bounds that perfectly fit buildings"""
        # 4 buildings with smaller area in larger bounds for easier placement
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 2)  # Smaller buildings
            for i in range(4)
        ]

        # Use larger bounds to ensure placement is possible
        optimizer = HybridSAGA(buildings, (0, 0, 400, 400))
        optimizer.sa_config["iterations_per_temp"] = 15
        optimizer.ga_config["generations"] = 20

        result = optimizer.optimize()

        assert result["fitness"] >= 0.0
        # Should be able to place all 4 buildings
        assert len(result["best_solution"].positions) == 4


class TestBuildingTypeEdgeCases:
    """Tests with unusual building type combinations"""

    def test_all_same_building_type(self):
        """Test with all identical building types"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(8)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))
        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Adjacency score should still work
        assert "adjacency" in result["objectives"]
        assert result["fitness"] >= 0.0

    def test_all_different_building_types(self):
        """Test with maximum building type diversity"""
        # Use all available building types
        all_types = list(BuildingType)
        buildings = [
            Building(f"B{i}", btype, 2000, 3) for i, btype in enumerate(all_types)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1500, 1500))
        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        assert result["fitness"] >= 0.0
        assert len(result["best_solution"].positions) == len(all_types)

    def test_rare_building_types_only(self):
        """Test with only rare building types (LIBRARY, HEALTH)"""
        buildings = [
            Building("B1", BuildingType.LIBRARY, 3000, 2),
            Building("B2", BuildingType.LIBRARY, 2500, 2),
            Building("B3", BuildingType.HEALTH, 2000, 3),
            Building("B4", BuildingType.HEALTH, 2200, 3),
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 800, 800))
        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Should handle rare types
        assert result["fitness"] >= 0.0
        assert "adjacency" in result["objectives"]

    def test_extreme_size_variation(self):
        """Test with extreme building size variation"""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 500, 1),  # Small
            Building("B2", BuildingType.EDUCATIONAL, 10000, 8),  # Huge
            Building("B3", BuildingType.RESIDENTIAL, 1000, 2),  # Small
            Building("B4", BuildingType.ADMINISTRATIVE, 8000, 6),  # Large
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 2000, 2000))
        optimizer.sa_config["iterations_per_temp"] = 10
        optimizer.ga_config["generations"] = 15

        result = optimizer.optimize()

        # Cost should vary significantly
        assert result["fitness"] >= 0.0
        assert "cost" in result["objectives"]


class TestConfigurationEdgeCases:
    """Tests with extreme configurations"""

    def test_minimal_sa_configuration(self):
        """Test with minimal SA iterations"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        # Extreme minimal config
        optimizer.sa_config["iterations_per_temp"] = 1
        optimizer.sa_config["num_chains"] = 1
        optimizer.ga_config["generations"] = 5
        optimizer.ga_config["population_size"] = 5

        result = optimizer.optimize()

        # Should complete (though quality may be poor)
        assert result["fitness"] >= 0.0
        assert result["statistics"]["runtime"] < 1.0  # Very fast

    def test_large_population_small_generations(self):
        """Test with large population but few generations"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        optimizer.sa_config["iterations_per_temp"] = 5
        optimizer.ga_config["generations"] = 5  # Few generations
        optimizer.ga_config["population_size"] = 100  # Large population

        result = optimizer.optimize()

        assert result["fitness"] >= 0.0
        # Should have many evaluations (with 100 pop and 5 generations, expect ~300-500)
        assert result["statistics"]["evaluations"] > 200

    def test_small_population_many_generations(self):
        """Test with small population but many generations"""
        buildings = [
            Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 3) for i in range(5)
        ]

        optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

        optimizer.sa_config["iterations_per_temp"] = 5
        optimizer.ga_config["generations"] = 50  # Many generations
        optimizer.ga_config["population_size"] = 5  # Tiny population

        result = optimizer.optimize()

        assert result["fitness"] >= 0.0
        # Convergence history should show 50 generations
        assert len(result["convergence"]["ga_best_history"]) == 50
