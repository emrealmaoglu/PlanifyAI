"""
Unit Tests for AdaptiveHSAGA Runner
====================================

Tests for adaptive_hsaga_runner.py module with ObjectiveProfile support.

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
from core.optimization.adaptive_hsaga_runner import (
    AdaptiveHSAGARunner,
    AdaptiveHSAGARunnerConfig,
    run_adaptive_hsaga,
)

from src.algorithms import Building, BuildingType, ObjectiveProfile, ProfileType


class TestAdaptiveHSAGARunnerConfig:
    """Test AdaptiveHSAGA runner configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AdaptiveHSAGARunnerConfig()

        assert config.population_size == 50
        assert config.n_iterations == 50
        assert config.initial_temp == 1000.0
        assert config.final_temp == 0.1
        assert config.cooling_rate == 0.95
        assert config.num_chains == 4
        assert config.generations == 50
        assert config.enable_adaptive is True
        assert config.seed == 42
        assert config.verbose is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = AdaptiveHSAGARunnerConfig(
            population_size=30,
            generations=30,
            initial_temp=500.0,
            num_chains=2,
            enable_adaptive=False,
            seed=123,
            verbose=False,
        )

        assert config.population_size == 30
        assert config.generations == 30
        assert config.initial_temp == 500.0
        assert config.num_chains == 2
        assert config.enable_adaptive is False
        assert config.seed == 123
        assert config.verbose is False


class TestAdaptiveHSAGARunner:
    """Test AdaptiveHSAGA runner."""

    @pytest.fixture
    def simple_buildings(self):
        """Create simple building set."""
        return [
            Building(id="library", type=BuildingType.LIBRARY, area=2000, floors=3),
            Building(id="dorm", type=BuildingType.RESIDENTIAL, area=3000, floors=5),
            Building(id="cafe", type=BuildingType.DINING, area=1500, floors=2),
        ]

    @pytest.fixture
    def bounds(self):
        """Simple bounds."""
        return (0, 0, 500, 500)

    def test_initialization(self, simple_buildings, bounds):
        """Test runner initialization."""
        config = AdaptiveHSAGARunnerConfig(
            population_size=20, generations=10, num_chains=2, verbose=False
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)

        assert runner.buildings == simple_buildings
        assert runner.bounds == bounds
        assert runner.config == config
        assert runner.optimizer is not None
        assert runner.evaluator is not None

    def test_run_basic(self, simple_buildings, bounds):
        """Test basic optimization run."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        # Check result structure
        assert "best_solution" in result
        assert "pareto_front" in result
        assert "pareto_objectives" in result
        assert "statistics" in result
        assert "convergence" in result
        assert "best_compromise" in result

        # Check Pareto front
        assert len(result["pareto_front"]) > 0

        # Check statistics
        assert result["statistics"]["evaluations"] > 0
        assert runner.stats["runtime"] > 0

    def test_objective_profile_standard(self, simple_buildings, bounds):
        """Test with STANDARD objective profile."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            objective_profile=ProfileType.STANDARD,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        # Check profile configuration
        assert runner.objective_profile.name == "Standard"
        assert runner.objective_profile.use_enhanced is False

        # Check result
        assert result["success"] is True
        assert "objective_profile" in result
        assert result["objective_profile"]["name"] == "Standard"

    def test_objective_profile_research_enhanced(self, simple_buildings, bounds):
        """Test with RESEARCH_ENHANCED objective profile."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            objective_profile=ProfileType.RESEARCH_ENHANCED,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        # Check profile configuration
        assert runner.objective_profile.name == "Research-Enhanced"
        assert runner.objective_profile.use_enhanced is True

        # Check result
        assert result["success"] is True
        assert result["objective_profile"]["name"] == "Research-Enhanced"
        assert result["objective_profile"]["use_enhanced"] is True

    def test_objective_profile_fifteen_minute_city(self, simple_buildings, bounds):
        """Test with FIFTEEN_MINUTE_CITY objective profile."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            objective_profile=ProfileType.FIFTEEN_MINUTE_CITY,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        # Check profile configuration
        assert runner.objective_profile.name == "15-Minute City"
        assert result["objective_profile"]["name"] == "15-Minute City"

    def test_objective_profile_campus_planning(self, simple_buildings, bounds):
        """Test with CAMPUS_PLANNING objective profile."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            objective_profile=ProfileType.CAMPUS_PLANNING,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        # Check profile configuration
        assert runner.objective_profile.name == "Campus Planning"
        assert result["objective_profile"]["name"] == "Campus Planning"

    def test_objective_profile_string_input(self, simple_buildings, bounds):
        """Test profile resolution from string."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            objective_profile="research_enhanced",
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)

        assert runner.objective_profile.name == "Research-Enhanced"

    def test_objective_profile_object_input(self, simple_buildings, bounds):
        """Test profile resolution from ObjectiveProfile object."""
        np.random.seed(42)

        custom_profile = ObjectiveProfile(
            name="Custom Test",
            description="Custom test profile",
            use_enhanced=True,
            weights={"cost": 0.25, "walking": 0.25, "adjacency": 0.25, "diversity": 0.25},
            walking_speed_kmh=4.5,
        )

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            objective_profile=custom_profile,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)

        assert runner.objective_profile.name == "Custom Test"
        assert runner.objective_profile.use_enhanced is True

    def test_best_compromise_selection(self, simple_buildings, bounds):
        """Test best compromise solution selection."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        best_compromise = result["best_compromise"]

        if best_compromise is not None:
            assert "solution" in best_compromise
            assert "objectives" in best_compromise
            assert "normalized_objectives" in best_compromise
            assert "index" in best_compromise
            assert "buildings" in best_compromise

            # Check that index is valid
            assert 0 <= best_compromise["index"] < len(result["pareto_front"])

    def test_adaptive_operators_enabled(self, simple_buildings, bounds):
        """Test with adaptive operator selection enabled."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            enable_adaptive=True,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        # Should have operator statistics
        assert "operator_stats" in result
        assert "selection_probabilities" in result

    def test_adaptive_operators_disabled(self, simple_buildings, bounds):
        """Test with adaptive operator selection disabled."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            enable_adaptive=False,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        # Should still succeed
        assert result["success"] is True

    def test_convenience_function(self, simple_buildings, bounds):
        """Test convenience function."""
        np.random.seed(42)

        result = run_adaptive_hsaga(
            buildings=simple_buildings,
            bounds=bounds,
            population_size=20,
            generations=10,
            objective_profile=ProfileType.RESEARCH_ENHANCED,
            verbose=False,
            seed=42,
        )

        assert result["success"] is True
        assert "best_solution" in result
        assert "pareto_front" in result

    def test_statistics_tracking(self, simple_buildings, bounds):
        """Test that statistics are properly tracked."""
        np.random.seed(42)

        config = AdaptiveHSAGARunnerConfig(
            population_size=20,
            generations=10,
            num_chains=2,
            chain_iterations=50,
            verbose=False,
        )

        runner = AdaptiveHSAGARunner(simple_buildings, bounds, config)
        result = runner.run()

        stats = result["statistics"]

        assert "runtime" in stats
        assert "evaluations" in stats
        assert "sa_time" in stats
        assert "ga_time" in stats
        assert "sa_chains" in stats
        assert "ga_generations" in stats

        assert stats["runtime"] > 0
        assert stats["evaluations"] > 0
        assert stats["sa_chains"] == 2
        assert stats["ga_generations"] == 10
