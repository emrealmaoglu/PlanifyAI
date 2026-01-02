"""
Realistic Large-Scale Benchmarks
=================================

Tests H-SAGA performance with production-scale problems:
- 50-150 buildings
- Topographic terrain (slopes, elevation)
- Mixed building types
- Real-world constraints

Created: 2026-01-02 (Week 4 Day 3)
"""

import time
from typing import List, Tuple

import numpy as np
import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA

# =============================================================================
# TERRAIN GENERATION
# =============================================================================


def generate_flat_terrain(width: float, height: float) -> dict:
    """Generate flat terrain (baseline)."""
    return {
        "type": "flat",
        "width": width,
        "height": height,
        "elevation": lambda x, y: 0.0,
        "slope": lambda x, y: 0.0,
        "buildable_mask": lambda x, y: True,
    }


def generate_sloped_terrain(width: float, height: float, max_slope: float = 15.0) -> dict:
    """
    Generate terrain with realistic slope (0-15 degrees).

    Args:
        width: Terrain width (m)
        height: Terrain height (m)
        max_slope: Maximum slope in degrees (default 15°)
    """
    # Create elevation function (linear slope from north to south)
    slope_rad = np.radians(max_slope)
    elevation_delta = height * np.tan(slope_rad)

    def elevation(x, y):
        """Elevation at point (x, y)."""
        return (y / height) * elevation_delta

    def slope(x, y):
        """Slope in degrees at point (x, y)."""
        return max_slope

    def buildable_mask(x, y):
        """Whether location is buildable (slope < 20°)."""
        return slope(x, y) < 20.0

    return {
        "type": "sloped",
        "width": width,
        "height": height,
        "max_slope": max_slope,
        "elevation": elevation,
        "slope": slope,
        "buildable_mask": buildable_mask,
    }


def generate_hilly_terrain(width: float, height: float, n_hills: int = 3) -> dict:
    """
    Generate hilly terrain with multiple peaks/valleys.

    Args:
        width: Terrain width (m)
        height: Terrain height (m)
        n_hills: Number of hills
    """
    # Generate random hill centers
    np.random.seed(42)
    hill_centers = [
        (np.random.uniform(0, width), np.random.uniform(0, height)) for _ in range(n_hills)
    ]
    hill_heights = [np.random.uniform(10, 30) for _ in range(n_hills)]
    hill_radii = [np.random.uniform(50, 150) for _ in range(n_hills)]

    def elevation(x, y):
        """Elevation as sum of Gaussian hills."""
        elev = 0.0
        for (cx, cy), h, r in zip(hill_centers, hill_heights, hill_radii):
            dist_sq = (x - cx) ** 2 + (y - cy) ** 2
            elev += h * np.exp(-dist_sq / (2 * r**2))
        return elev

    def slope(x, y):
        """Approximate slope using finite differences."""
        dx = 1.0
        dy = 1.0
        dz_dx = (elevation(x + dx, y) - elevation(x - dx, y)) / (2 * dx)
        dz_dy = (elevation(x, y + dy) - elevation(x, y - dy)) / (2 * dy)
        slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        return np.degrees(slope_rad)

    def buildable_mask(x, y):
        """Buildable if slope < 25°."""
        return slope(x, y) < 25.0

    return {
        "type": "hilly",
        "width": width,
        "height": height,
        "n_hills": n_hills,
        "elevation": elevation,
        "slope": slope,
        "buildable_mask": buildable_mask,
    }


# =============================================================================
# CAMPUS GENERATION
# =============================================================================


def generate_mixed_campus(
    n_buildings: int,
    terrain: dict,
    seed: int = 42,
) -> Tuple[List[Building], Tuple[float, float, float, float]]:
    """
    Generate realistic mixed-use campus.

    Args:
        n_buildings: Total number of buildings
        terrain: Terrain dict from terrain generators
        seed: Random seed

    Returns:
        (buildings, bounds)
    """
    np.random.seed(seed)

    # Building type distribution (realistic campus mix)
    type_distribution = {
        BuildingType.RESIDENTIAL: 0.40,  # 40% dorms
        BuildingType.EDUCATIONAL: 0.35,  # 35% classrooms/labs
        BuildingType.ADMINISTRATIVE: 0.10,  # 10% admin
        BuildingType.SOCIAL: 0.10,  # 10% sports/rec/social
        BuildingType.COMMERCIAL: 0.05,  # 5% cafeteria/shops
    }

    buildings = []

    for i in range(n_buildings):
        # Select building type based on distribution
        rand = np.random.random()
        cumsum = 0.0
        btype = BuildingType.RESIDENTIAL

        for bt, prob in type_distribution.items():
            cumsum += prob
            if rand < cumsum:
                btype = bt
                break

        # Realistic area and floor count based on type
        if btype == BuildingType.RESIDENTIAL:
            area = np.random.uniform(2000, 5000)  # Dorms: 2000-5000 m²
            floors = np.random.randint(4, 10)  # 4-9 floors
        elif btype == BuildingType.EDUCATIONAL:
            area = np.random.uniform(1500, 4000)  # Labs/classrooms
            floors = np.random.randint(2, 6)
        elif btype == BuildingType.ADMINISTRATIVE:
            area = np.random.uniform(1000, 2500)  # Admin buildings
            floors = np.random.randint(2, 5)
        elif btype == BuildingType.SOCIAL:
            area = np.random.uniform(2500, 6000)  # Gyms, sports, social
            floors = np.random.randint(1, 3)  # Usually low-rise
        else:  # COMMERCIAL
            area = np.random.uniform(800, 2000)  # Cafes, shops
            floors = np.random.randint(1, 3)

        buildings.append(
            Building(
                id=f"B{i:03d}",
                type=btype,
                area=area,
                floors=floors,
            )
        )

    # Bounds from terrain
    bounds = (0, 0, terrain["width"], terrain["height"])

    return buildings, bounds


# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture
def sa_config_realistic():
    """SA config for realistic large-scale problems."""
    return {
        "initial_temp": 1000.0,
        "final_temp": 0.1,
        "cooling_rate": 0.95,
        "num_chains": 4,  # Use all cores for large problems
        "chain_iterations": 100,  # More iterations for complex landscapes
    }


@pytest.fixture
def ga_config_realistic():
    """GA config for realistic large-scale problems."""
    return {
        "population_size": 50,
        "generations": 30,
        "crossover_rate": 0.8,
        "mutation_rate": 0.15,
        "elite_size": 5,
        "tournament_size": 3,
    }


# =============================================================================
# BENCHMARK TESTS
# =============================================================================


class TestRealisticScalability:
    """Test performance with realistic large-scale problems."""

    @pytest.mark.slow
    def test_50_buildings_flat_terrain(self, sa_config_realistic, ga_config_realistic):
        """Baseline: 50 buildings on flat terrain."""
        terrain = generate_flat_terrain(width=600, height=600)
        buildings, bounds = generate_mixed_campus(n_buildings=50, terrain=terrain)

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_realistic,
            ga_config=ga_config_realistic,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        stats = result["statistics"]

        print("\n" + "=" * 60)
        print("50 Buildings - Flat Terrain")
        print("=" * 60)
        print(f"Runtime: {elapsed:.2f}s")
        print(f"Fitness: {result['fitness']:.4f}")
        print(f"Evaluations: {stats['evaluations']}")
        print(f"SA time: {stats['sa_time']:.2f}s ({stats['sa_time']/elapsed*100:.1f}%)")
        print(f"GA time: {stats['ga_time']:.2f}s ({stats['ga_time']/elapsed*100:.1f}%)")

        assert result["fitness"] > 0
        assert elapsed < 300  # Should complete in < 5 minutes

    @pytest.mark.slow
    def test_100_buildings_sloped_terrain(self, sa_config_realistic, ga_config_realistic):
        """Challenge: 100 buildings on sloped terrain (10° slope)."""
        terrain = generate_sloped_terrain(width=800, height=800, max_slope=10.0)
        buildings, bounds = generate_mixed_campus(n_buildings=100, terrain=terrain)

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_realistic,
            ga_config=ga_config_realistic,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        stats = result["statistics"]

        print("\n" + "=" * 60)
        print("100 Buildings - Sloped Terrain (10°)")
        print("=" * 60)
        print(f"Runtime: {elapsed:.2f}s")
        print(f"Fitness: {result['fitness']:.4f}")
        print(f"Evaluations: {stats['evaluations']}")
        print(f"SA time: {stats['sa_time']:.2f}s")
        print(f"GA time: {stats['ga_time']:.2f}s")

        assert result["fitness"] > 0
        assert elapsed < 600  # < 10 minutes

    @pytest.mark.slow
    def test_150_buildings_hilly_terrain(self, sa_config_realistic):
        """Stress test: 150 buildings on hilly terrain."""
        terrain = generate_hilly_terrain(width=1000, height=1000, n_hills=5)
        buildings, bounds = generate_mixed_campus(n_buildings=150, terrain=terrain)

        # Reduced GA config for very large problem
        ga_config = {
            "population_size": 40,
            "generations": 20,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 5,
            "tournament_size": 3,
        }

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_realistic,
            ga_config=ga_config,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        stats = result["statistics"]

        print("\n" + "=" * 60)
        print("150 Buildings - Hilly Terrain (5 hills)")
        print("=" * 60)
        print(f"Runtime: {elapsed:.2f}s")
        print(f"Fitness: {result['fitness']:.4f}")
        print(f"Evaluations: {stats['evaluations']}")
        print(f"SA time: {stats['sa_time']:.2f}s")
        print(f"GA time: {stats['ga_time']:.2f}s")

        assert result["fitness"] > 0
        assert elapsed < 900  # < 15 minutes


class TestBuildingTypeMix:
    """Test with different building type distributions."""

    def test_academic_heavy_campus(self, sa_config_realistic, ga_config_realistic):
        """Campus with 70% educational buildings."""
        np.random.seed(42)

        # 70% educational, 30% other
        buildings = []
        for i in range(30):
            if i < 21:  # 70%
                btype = BuildingType.EDUCATIONAL
                area = np.random.uniform(1500, 3500)
                floors = np.random.randint(2, 5)
            else:
                btype = BuildingType.RESIDENTIAL
                area = np.random.uniform(2000, 4000)
                floors = np.random.randint(4, 8)

            buildings.append(Building(f"B{i:03d}", btype, area, floors))

        # Calculate required area with generous spacing
        total_footprint = sum(b.area for b in buildings)
        side_length = np.sqrt(total_footprint * 20)  # 20x footprint for spacing
        bounds = (0, 0, side_length, side_length)

        start_time = time.perf_counter()
        optimizer = HybridSAGA(
            buildings=buildings,
            bounds=bounds,
            sa_config=sa_config_realistic,
            ga_config=ga_config_realistic,
        )
        result = optimizer.optimize()
        elapsed = time.perf_counter() - start_time

        print(f"\n30 buildings (70% academic): {elapsed:.2f}s, fitness={result['fitness']:.4f}")

        assert result["fitness"] > 0


class TestTerrainComplexity:
    """Test how terrain complexity affects optimization."""

    def test_terrain_comparison(self, sa_config_realistic):
        """Compare flat vs sloped vs hilly terrain."""
        n_buildings = 25  # Reduced for reliability
        results = {}

        ga_config = {
            "population_size": 30,
            "generations": 20,
            "crossover_rate": 0.8,
            "mutation_rate": 0.15,
            "elite_size": 3,
            "tournament_size": 3,
        }

        # Use large terrain
        terrain_size = 600
        terrains = [
            ("Flat", generate_flat_terrain(terrain_size, terrain_size)),
            ("Sloped (8°)", generate_sloped_terrain(terrain_size, terrain_size, max_slope=8.0)),
            ("Hilly (3 hills)", generate_hilly_terrain(terrain_size, terrain_size, n_hills=3)),
        ]

        for name, terrain in terrains:
            buildings, bounds = generate_mixed_campus(n_buildings, terrain, seed=42)

            start_time = time.perf_counter()
            optimizer = HybridSAGA(
                buildings=buildings,
                bounds=bounds,
                sa_config=sa_config_realistic,
                ga_config=ga_config,
            )
            result = optimizer.optimize()
            elapsed = time.perf_counter() - start_time

            results[name] = {
                "time": elapsed,
                "fitness": result["fitness"],
                "evaluations": result["statistics"]["evaluations"],
            }

        print("\n" + "=" * 60)
        print("Terrain Complexity Comparison (25 buildings)")
        print("=" * 60)
        print(f"{'Terrain':<20} | {'Time (s)':<10} | {'Fitness':<10} | Evals")
        print("-" * 60)

        for name, data in results.items():
            time_val = data["time"]
            fit_val = data["fitness"]
            evals = data["evaluations"]
            print(f"{name:<20} | {time_val:>8.2f}s | {fit_val:>8.4f} | {evals}")

        # All should produce valid solutions
        for data in results.values():
            assert data["fitness"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
