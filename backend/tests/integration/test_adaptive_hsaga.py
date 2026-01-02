"""
Integration Tests for Adaptive H-SAGA
======================================

Tests for adaptive H-SAGA optimizer with operator selection.

Created: 2026-01-02 (Week 4 Day 3)
"""

import numpy as np
import pytest

from src.algorithms import AdaptiveHSAGA, Building, BuildingType
from src.algorithms.adaptive import SelectionStrategy


@pytest.fixture
def small_campus():
    """Create small test campus (5 buildings)."""
    return [
        Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
        Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
        Building("B3", BuildingType.ADMINISTRATIVE, 1200, 2),
        Building("B4", BuildingType.SOCIAL, 1800, 2),
        Building("B5", BuildingType.COMMERCIAL, 1000, 1),
    ]


@pytest.fixture
def bounds_small():
    """Bounds for small campus."""
    return (0, 0, 300, 300)


@pytest.fixture
def fast_sa_config():
    """Fast SA config for testing."""
    return {
        "initial_temp": 100.0,
        "final_temp": 0.1,
        "cooling_rate": 0.95,
        "num_chains": 2,
        "chain_iterations": 50,
    }


@pytest.fixture
def fast_ga_config():
    """Fast GA config for testing."""
    return {
        "population_size": 20,
        "generations": 20,
        "crossover_rate": 0.8,
        "mutation_rate": 0.15,
        "elite_size": 3,
        "tournament_size": 3,
    }


class TestAdaptiveHSAGABasic:
    """Basic functionality tests for Adaptive H-SAGA."""

    def test_initialization(self, small_campus, bounds_small):
        """Test adaptive H-SAGA initialization."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            selection_strategy=SelectionStrategy.ADAPTIVE_PURSUIT,
        )

        assert optimizer.enable_adaptive is True
        assert len(optimizer.buildings) == 5
        assert optimizer.operator_selector is not None
        assert optimizer.parameter_tuner is not None

    def test_initialization_without_adaptive(self, small_campus, bounds_small):
        """Test initialization with adaptive disabled."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus, bounds=bounds_small, enable_adaptive=False
        )

        assert optimizer.enable_adaptive is False

    def test_operators_registered(self, small_campus, bounds_small):
        """Test that operators are registered correctly."""
        optimizer = AdaptiveHSAGA(buildings=small_campus, bounds=bounds_small)

        # Check perturbation operators
        stats = optimizer.operator_selector.get_perturbation_statistics()
        assert "gaussian" in stats
        assert "swap" in stats
        assert "reset" in stats

        # Check mutation operators
        stats = optimizer.operator_selector.get_mutation_statistics()
        assert "gaussian" in stats
        assert "swap" in stats
        assert "reset" in stats

        # Check crossover operators
        stats = optimizer.operator_selector.get_crossover_statistics()
        assert "uniform" in stats
        assert "pmx" in stats

        # Check selection operators
        stats = optimizer.operator_selector.get_selection_statistics()
        assert "tournament" in stats
        assert "roulette" in stats

    def test_parameter_schedules_configured(self, small_campus, bounds_small):
        """Test that parameter schedules are configured."""
        optimizer = AdaptiveHSAGA(buildings=small_campus, bounds=bounds_small)

        params = optimizer.parameter_tuner.list_parameters()
        assert "mutation_rate" in params
        assert "temperature" in params
        assert "crossover_rate" in params


class TestAdaptiveHSAGAOptimization:
    """Test adaptive H-SAGA optimization."""

    def test_optimize_small_problem(
        self, small_campus, bounds_small, fast_sa_config, fast_ga_config
    ):
        """Test optimization on small problem."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
        )

        result = optimizer.optimize()

        # Check result structure
        assert "best_solution" in result
        assert "fitness" in result
        assert "statistics" in result
        assert "operator_stats" in result
        assert "selection_probabilities" in result

        # Check solution validity
        assert result["best_solution"] is not None
        assert result["fitness"] > 0
        assert len(result["best_solution"].positions) == 5

        # Check that operators were used
        op_stats = result["operator_stats"]
        total_uses = sum(
            stats["uses"] for op_type_stats in op_stats.values() for stats in op_type_stats.values()
        )
        assert total_uses > 0

    def test_adaptive_vs_non_adaptive(
        self, small_campus, bounds_small, fast_sa_config, fast_ga_config
    ):
        """Test adaptive vs non-adaptive performance."""
        np.random.seed(42)

        # Adaptive version
        optimizer_adaptive = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
            enable_adaptive=True,
        )
        result_adaptive = optimizer_adaptive.optimize()

        np.random.seed(42)

        # Non-adaptive version
        optimizer_non_adaptive = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
            enable_adaptive=False,
        )
        result_non_adaptive = optimizer_non_adaptive.optimize()

        # Both should produce valid results
        assert result_adaptive["fitness"] > 0
        assert result_non_adaptive["fitness"] > 0

        # Adaptive should have operator stats
        assert "operator_stats" in result_adaptive
        assert "operator_stats" not in result_non_adaptive


class TestAdaptiveHSAGASelectionStrategies:
    """Test different selection strategies."""

    @pytest.mark.parametrize(
        "strategy",
        [
            SelectionStrategy.UNIFORM,
            SelectionStrategy.GREEDY,
            SelectionStrategy.ADAPTIVE_PURSUIT,
            SelectionStrategy.UCB,
            SelectionStrategy.SOFTMAX,
        ],
    )
    def test_selection_strategies(
        self, small_campus, bounds_small, fast_sa_config, fast_ga_config, strategy
    ):
        """Test different operator selection strategies."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
            selection_strategy=strategy,
        )

        result = optimizer.optimize()

        # Should complete successfully
        assert result["fitness"] > 0
        assert "operator_stats" in result


class TestAdaptiveHSAGAParameterTuning:
    """Test parameter tuning functionality."""

    def test_parameter_adaptation(self, small_campus, bounds_small, fast_sa_config, fast_ga_config):
        """Test that parameters adapt during optimization."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
        )

        # Get parameters at different generations
        params_gen_0 = optimizer.parameter_tuner.get_parameters(0, fast_ga_config["generations"])
        params_gen_final = optimizer.parameter_tuner.get_parameters(
            fast_ga_config["generations"] - 1, fast_ga_config["generations"]
        )

        # Mutation rate should decrease
        assert params_gen_0["mutation_rate"] > params_gen_final["mutation_rate"]

        # Crossover rate should decrease
        assert params_gen_0["crossover_rate"] >= params_gen_final["crossover_rate"]


class TestAdaptiveHSAGAOperatorTracking:
    """Test operator performance tracking."""

    def test_operator_credit_assignment(
        self, small_campus, bounds_small, fast_sa_config, fast_ga_config
    ):
        """Test that operator credits are tracked."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
        )

        result = optimizer.optimize()

        # Check that operator statistics are available
        op_stats = result["operator_stats"]

        # Check perturbation operators (used in SA)
        perturbation_stats = op_stats["perturbation"]
        assert len(perturbation_stats) > 0

        # At least one operator should have been used
        total_perturbation_uses = sum(stats["uses"] for stats in perturbation_stats.values())
        assert total_perturbation_uses > 0

        # Check that success rates are computed
        for stats in perturbation_stats.values():
            if stats["uses"] > 0:
                assert 0 <= stats["success_rate"] <= 1.0

    def test_selection_probabilities_change(
        self, small_campus, bounds_small, fast_sa_config, fast_ga_config
    ):
        """Test that selection probabilities adapt during optimization."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
            selection_strategy=SelectionStrategy.ADAPTIVE_PURSUIT,
        )

        # Get initial probabilities
        initial_probs = optimizer.operator_selector.get_selection_probabilities()

        # Run optimization
        result = optimizer.optimize()

        # Get final probabilities
        final_probs = result["selection_probabilities"]

        # Probabilities should have changed for perturbation operators
        # (used extensively in SA phase)
        initial_pert = initial_probs["perturbation"]
        final_pert = final_probs["perturbation"]

        if initial_pert and final_pert:
            # At least one probability should be different
            prob_changed = any(
                abs(final_pert.get(name, 0) - initial_pert.get(name, 0)) > 0.01
                for name in initial_pert.keys()
            )
            assert prob_changed


class TestAdaptiveHSAGAConvergence:
    """Test convergence tracking."""

    def test_convergence_history_recorded(
        self, small_campus, bounds_small, fast_sa_config, fast_ga_config
    ):
        """Test that convergence history is recorded."""
        optimizer = AdaptiveHSAGA(
            buildings=small_campus,
            bounds=bounds_small,
            sa_config=fast_sa_config,
            ga_config=fast_ga_config,
        )

        result = optimizer.optimize()

        # Check convergence data
        convergence = result["convergence"]

        assert "ga_best_history" in convergence
        assert "ga_avg_history" in convergence

        # GA history should have entries for each generation
        assert len(convergence["ga_best_history"]) == fast_ga_config["generations"]
        assert len(convergence["ga_avg_history"]) == fast_ga_config["generations"]

        # Best fitness should be non-decreasing (elitism)
        ga_best = convergence["ga_best_history"]
        for i in range(1, len(ga_best)):
            assert ga_best[i] >= ga_best[i - 1] - 1e-6  # Allow small numerical error


@pytest.mark.benchmark
class TestAdaptiveHSAGAPerformance:
    """Performance benchmarks for adaptive H-SAGA."""

    def test_performance_overhead(
        self, small_campus, bounds_small, fast_sa_config, fast_ga_config, benchmark
    ):
        """Test performance overhead of adaptive selection."""

        def run_adaptive():
            optimizer = AdaptiveHSAGA(
                buildings=small_campus,
                bounds=bounds_small,
                sa_config=fast_sa_config,
                ga_config=fast_ga_config,
                enable_adaptive=True,
            )
            return optimizer.optimize()

        result = benchmark(run_adaptive)
        assert result["fitness"] > 0
