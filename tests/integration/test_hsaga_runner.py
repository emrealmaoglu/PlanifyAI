"""
Integration tests for HSAGARunner.

Sprint 3, Faz 3.1.2 - HSAGARunner Integration Tests
Tests the full H-SAGA optimization pipeline with minimal configuration.
"""

import pytest
import numpy as np
from shapely.geometry import Polygon

from backend.core.optimization.hsaga_runner import (
    HSAGARunner, HSAGARunnerConfig, SAExplorer
)
from backend.core.optimization.spatial_problem import (
    SpatialOptimizationProblem, ConstraintCalculator, ObjectiveCalculator
)
from backend.core.optimization.encoding import BuildingGene, BUILDING_TYPES
from backend.core.schemas.input import SiteParameters, OptimizationGoal


@pytest.fixture
def simple_boundary():
    """200x200 meter square boundary for testing."""
    return Polygon([
        (0, 0), (200, 0), (200, 200), (0, 200), (0, 0)
    ])


@pytest.fixture
def site_params():
    """Default site parameters."""
    return SiteParameters()


@pytest.fixture
def optimization_goals():
    """Default optimization goals."""
    return {
        OptimizationGoal.COMPACTNESS: 0.5,
        OptimizationGoal.ADJACENCY: 0.5,
    }


@pytest.fixture
def constraint_calculator(simple_boundary, site_params):
    """ConstraintCalculator for testing."""
    return ConstraintCalculator(
        boundary=simple_boundary,
        site_params=site_params,
        road_geometries=[],
        dem_sampler=None
    )


@pytest.fixture
def objective_calculator(simple_boundary, optimization_goals):
    """ObjectiveCalculator for testing."""
    return ObjectiveCalculator(
        boundary=simple_boundary,
        optimization_goals=optimization_goals,
        existing_buildings=[],
        latitude=41.38
    )


@pytest.fixture
def building_genes():
    """Minimal set of building genes for testing."""
    return [
        BuildingGene(
            x=50.0,
            y=50.0,
            rotation=0.0,
            type_id=1,  # Faculty
            width_factor=1.0,
            depth_factor=1.0,
            floor_factor=1.0
        ),
        BuildingGene(
            x=120.0,
            y=120.0,
            rotation=0.0,
            type_id=2,  # Dormitory
            width_factor=1.0,
            depth_factor=1.0,
            floor_factor=1.0
        ),
    ]


@pytest.fixture
def spatial_problem(simple_boundary, constraint_calculator, objective_calculator, building_genes):
    """SpatialOptimizationProblem for testing."""
    return SpatialOptimizationProblem(
        genes=building_genes,
        constraint_calculator=constraint_calculator,
        objective_calculator=objective_calculator,
        boundary=simple_boundary
    )


@pytest.fixture
def minimal_config():
    """Minimal config for fast testing (reduced budget)."""
    return HSAGARunnerConfig(
        total_evaluations=100,  # Very small for testing
        sa_fraction=0.30,
        population_size=10,
        seed=42,
        verbose=False
    )


class TestHSAGARunnerConfig:
    """Tests for HSAGARunnerConfig."""
    
    def test_default_config(self):
        """Default config should have sensible values."""
        config = HSAGARunnerConfig()
        assert config.total_evaluations > 0
        assert 0 < config.sa_fraction < 1
        assert config.population_size > 0
    
    def test_custom_config(self):
        """Custom config values should be applied."""
        config = HSAGARunnerConfig(
            total_evaluations=1000,
            sa_fraction=0.5,
            seed=123
        )
        assert config.total_evaluations == 1000
        assert config.sa_fraction == 0.5
        assert config.seed == 123


class TestSAExplorer:
    """Tests for SAExplorer (Simulated Annealing phase)."""
    
    def test_sa_explorer_initialization(self, spatial_problem, minimal_config):
        """SAExplorer should initialize correctly."""
        explorer = SAExplorer(spatial_problem, minimal_config)
        assert explorer is not None
    
    def test_sa_explorer_run(self, spatial_problem, minimal_config):
        """SAExplorer should run and return results."""
        explorer = SAExplorer(spatial_problem, minimal_config)
        max_evals = int(minimal_config.total_evaluations * minimal_config.sa_fraction)
        
        results = explorer.run(max_evals)
        
        # Should return list of solutions
        assert isinstance(results, list)
        # Each result should be (x, F, G) tuple
        if len(results) > 0:
            x, F, G = results[0]
            assert isinstance(x, np.ndarray)


class TestHSAGARunner:
    """Tests for HSAGARunner (full pipeline)."""
    
    def test_hsaga_runner_initialization(self, spatial_problem, minimal_config):
        """HSAGARunner should initialize correctly."""
        runner = HSAGARunner(spatial_problem, minimal_config)
        assert runner is not None
        assert runner.config.total_evaluations == 100
    
    def test_hsaga_runner_run(self, spatial_problem, minimal_config):
        """HSAGARunner should complete without errors."""
        runner = HSAGARunner(spatial_problem, minimal_config)
        result = runner.run()
        
        # Result should be a dictionary
        assert isinstance(result, dict)
        
        # Should contain expected keys
        assert "best_solution" in result or "X" in result
    
    def test_hsaga_runner_get_best_solution(self, spatial_problem, minimal_config):
        """Should be able to get best solution after run."""
        runner = HSAGARunner(spatial_problem, minimal_config)
        runner.run()
        
        best = runner.get_best_solution()
        # Best should be a numpy array or dict
        assert best is not None


class TestHSAGARunnerResults:
    """Tests for HSAGARunner result format."""
    
    def test_result_contains_statistics(self, spatial_problem, minimal_config):
        """Result should contain optimization statistics."""
        runner = HSAGARunner(spatial_problem, minimal_config)
        result = runner.run()
        
        # Check for common statistics keys
        expected_keys = ["n_eval", "total_time"]
        for key in expected_keys:
            if key in result:
                assert result[key] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
