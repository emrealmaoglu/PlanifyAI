"""
Integration tests for constraint system with H-SAGA.

Created: 2025-11-09
"""

import pytest
from shapely.geometry import Polygon

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA
from src.constraints.spatial_constraints import (
    ConstraintManager,
    CoverageRatioConstraint,
    SetbackConstraint,
)
from src.data.campus_data import CampusData


@pytest.fixture
def sample_campus():
    """Create a sample campus for testing."""
    boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    return CampusData(
        name="Test Campus",
        location="Istanbul, Turkey",
        boundary=boundary,
        buildings=[],
        constraints={"setback_from_boundary": 10.0, "coverage_ratio_max": 0.3},
        metadata={},
    )


@pytest.fixture
def sample_buildings():
    """Create sample buildings for testing."""
    return [
        Building(id="B1", type=BuildingType.EDUCATIONAL, area=500, floors=2),
        Building(id="B2", type=BuildingType.LIBRARY, area=800, floors=3),
        Building(id="B3", type=BuildingType.RESIDENTIAL, area=600, floors=2),
    ]


@pytest.fixture
def constraint_manager():
    """Create a constraint manager with constraints."""
    manager = ConstraintManager()
    manager.add_constraint(SetbackConstraint(setback_distance=10.0))
    manager.add_constraint(CoverageRatioConstraint(max_coverage_ratio=0.3))
    return manager


class TestOptimizerWithConstraints:
    """Test optimizer initialization with constraints."""

    def test_optimizer_with_constraints(self, sample_buildings, sample_campus, constraint_manager):
        """Test optimizer can be initialized with constraints."""
        bounds = sample_campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=sample_campus,
            constraint_manager=constraint_manager,
        )

        assert optimizer.campus_data == sample_campus
        assert optimizer.constraint_manager == constraint_manager
        assert optimizer.buildings == sample_buildings

    def test_optimizer_without_constraints(self, sample_buildings):
        """Test optimizer works without constraints (backwards compatibility)."""
        bounds = (0, 0, 1000, 1000)
        optimizer = HybridSAGA(buildings=sample_buildings, bounds=bounds)

        assert optimizer.campus_data is None
        assert optimizer.constraint_manager is None
        assert optimizer.buildings == sample_buildings


class TestOptimizationWithConstraints:
    """Test optimization with constraints."""

    def test_optimization_with_constraints(
        self, sample_buildings, sample_campus, constraint_manager
    ):
        """Test optimization runs with constraints."""
        bounds = sample_campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=sample_campus,
            constraint_manager=constraint_manager,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        assert "best_solution" in result
        assert "fitness" in result
        assert "constraints" in result
        assert result["fitness"] > 0

    def test_constraint_penalty_application(
        self, sample_buildings, sample_campus, constraint_manager
    ):
        """Test constraint penalties are applied during optimization."""
        bounds = sample_campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=sample_campus,
            constraint_manager=constraint_manager,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        # Check constraint information is present
        assert "constraints" in result
        assert "penalty" in result["constraints"]
        assert "satisfied" in result["constraints"]
        assert "violations" in result["constraints"]

        # Penalty should be non-negative
        assert result["constraints"]["penalty"] >= 0.0

    def test_constraint_violation_tracking(
        self, sample_buildings, sample_campus, constraint_manager
    ):
        """Test constraint violations are tracked."""
        bounds = sample_campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=sample_campus,
            constraint_manager=constraint_manager,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        # Check violations dictionary
        violations = result["constraints"]["violations"]
        assert isinstance(violations, dict)

        # If satisfied, violations should be empty
        if result["constraints"]["satisfied"]:
            assert len(violations) == 0

    def test_optimization_without_constraints(self, sample_buildings):
        """Test optimization works without constraints (backwards compatibility)."""
        bounds = (0, 0, 1000, 1000)
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        assert "best_solution" in result
        assert "fitness" in result
        assert "constraints" in result
        # Constraints should be empty dict when not provided
        assert result["constraints"] == {}
