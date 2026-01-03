"""
Unit Tests for NSGA-III Runner
================================

Tests for nsga3_runner.py module.

Created: 2026-01-03
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Direct imports to avoid circular dependencies
from core.optimization.nsga3_runner import NSGA3Runner, NSGA3RunnerConfig, run_nsga3

from src.algorithms import Building, BuildingType


class TestNSGA3RunnerConfig:
    """Test NSGA-III runner configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = NSGA3RunnerConfig()

        assert config.population_size == 100
        assert config.n_generations == 100
        assert config.n_partitions == 12
        assert config.crossover_rate == 0.9
        assert config.mutation_rate == 0.15
        assert config.seed == 42
        assert config.verbose is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = NSGA3RunnerConfig(
            population_size=50,
            n_generations=50,
            n_partitions=6,
            crossover_rate=0.8,
            mutation_rate=0.2,
            seed=123,
            verbose=False,
        )

        assert config.population_size == 50
        assert config.n_generations == 50
        assert config.n_partitions == 6
        assert config.crossover_rate == 0.8
        assert config.mutation_rate == 0.2
        assert config.seed == 123
        assert config.verbose is False


class TestNSGA3Runner:
    """Test NSGA-III runner."""

    @pytest.fixture
    def simple_buildings(self):
        """Create simple building set."""
        return [
            Building("Library", BuildingType.EDUCATIONAL, 2000, 3),
            Building("Dorm", BuildingType.RESIDENTIAL, 3000, 5),
            Building("Cafe", BuildingType.COMMERCIAL, 1500, 2),
        ]

    @pytest.fixture
    def bounds(self):
        """Simple bounds."""
        return (0, 0, 500, 500)

    def test_initialization(self, simple_buildings, bounds):
        """Test runner initialization."""
        config = NSGA3RunnerConfig(population_size=20, n_generations=10, verbose=False)

        runner = NSGA3Runner(simple_buildings, bounds, config)

        assert runner.buildings == simple_buildings
        assert runner.bounds == bounds
        assert runner.config == config
        assert runner.optimizer is not None

    def test_run_basic(self, simple_buildings, bounds):
        """Test basic optimization run."""
        np.random.seed(42)

        config = NSGA3RunnerConfig(population_size=20, n_generations=10, verbose=False)

        runner = NSGA3Runner(simple_buildings, bounds, config)
        result = runner.run()

        # Check result structure
        assert "pareto_front" in result
        assert "pareto_objectives" in result
        assert "reference_points" in result
        assert "statistics" in result
        assert "convergence" in result
        assert "best_compromise" in result

        # Check Pareto front
        assert len(result["pareto_front"]) > 0
        assert len(result["pareto_objectives"]) > 0

        # Check statistics
        assert result["statistics"]["evaluations"] > 0
        assert runner.stats["runtime"] > 0

    def test_best_compromise_selection(self, simple_buildings, bounds):
        """Test best compromise solution selection."""
        np.random.seed(42)

        config = NSGA3RunnerConfig(population_size=20, n_generations=10, verbose=False)

        runner = NSGA3Runner(simple_buildings, bounds, config)
        result = runner.run()

        best_compromise = result["best_compromise"]

        assert best_compromise is not None
        assert "solution" in best_compromise
        assert "objectives" in best_compromise
        assert "normalized_objectives" in best_compromise
        assert "index" in best_compromise

        # Check that index is valid
        assert 0 <= best_compromise["index"] < len(result["pareto_front"])

    def test_find_best_compromise_normalization(self, simple_buildings, bounds):
        """Test that best compromise uses normalized objectives."""
        np.random.seed(42)

        config = NSGA3RunnerConfig(population_size=20, n_generations=10, verbose=False)

        runner = NSGA3Runner(simple_buildings, bounds, config)
        result = runner.run()

        best_compromise = result["best_compromise"]
        normalized_objs = best_compromise["normalized_objectives"]

        # All normalized objectives should be in [0, 1]
        assert np.all(normalized_objs >= 0)
        assert np.all(normalized_objs <= 1)

    def test_statistics_tracking(self, simple_buildings, bounds):
        """Test that statistics are properly tracked."""
        np.random.seed(42)

        config = NSGA3RunnerConfig(population_size=20, n_generations=10, verbose=False)

        runner = NSGA3Runner(simple_buildings, bounds, config)
        result = runner.run()

        # Check stats
        assert runner.stats["evaluations"] > 0
        assert runner.stats["generations"] == 10
        assert runner.stats["runtime"] > 0
        assert runner.stats["pareto_size"] > 0
        assert runner.stats["pareto_size"] == len(result["pareto_front"])


class TestNSGA3RunnerWithCustomReferencePoints:
    """Test NSGA-III runner with custom reference points."""

    def test_custom_reference_points(self):
        """Test with custom reference points."""
        np.random.seed(42)

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        ]
        bounds = (0, 0, 500, 500)

        # Custom 3D reference points (for 3 objectives: cost, walking, adjacency)
        custom_ref_points = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.33, 0.33, 0.33],
            ]
        )

        config = NSGA3RunnerConfig(
            population_size=10,
            n_generations=5,
            reference_points=custom_ref_points,
            verbose=False,
        )

        runner = NSGA3Runner(buildings, bounds, config)
        result = runner.run()

        # Should use custom reference points
        assert len(result["reference_points"]) == 4
        assert np.allclose(result["reference_points"], custom_ref_points)

    def test_two_layer_reference_points(self):
        """Test with two-layer reference points."""
        np.random.seed(42)

        buildings = [Building(f"B{i}", BuildingType.RESIDENTIAL, 2000, 4) for i in range(4)]
        bounds = (0, 0, 800, 800)

        config = NSGA3RunnerConfig(
            population_size=30,
            n_generations=10,
            n_partitions=6,
            use_two_layer=True,
            n_partitions_inner=3,
            verbose=False,
        )

        runner = NSGA3Runner(buildings, bounds, config)
        result = runner.run()

        # Two-layer should have more reference points
        assert len(result["reference_points"]) > 6


class TestConvenienceFunction:
    """Test convenience function."""

    def test_run_nsga3_function(self):
        """Test run_nsga3 convenience function."""
        np.random.seed(42)

        buildings = [
            Building("Library", BuildingType.EDUCATIONAL, 2000, 3),
            Building("Dorm", BuildingType.RESIDENTIAL, 3000, 5),
        ]
        bounds = (0, 0, 500, 500)

        result = run_nsga3(
            buildings,
            bounds,
            population_size=20,
            n_generations=10,
            n_partitions=12,
            verbose=False,
            seed=42,
        )

        # Should return complete result
        assert "pareto_front" in result
        assert "pareto_objectives" in result
        assert "best_compromise" in result
        assert len(result["pareto_front"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
