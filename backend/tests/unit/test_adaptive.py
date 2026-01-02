"""
Unit Tests for Adaptive Operator Selection
===========================================

Tests for credit assignment, operator selection, and parameter tuning.

Created: 2026-01-02 (Week 4 Day 3)
"""

import numpy as np
import pytest

from src.algorithms.adaptive import (
    AdaptiveOperatorSelector,
    AdaptiveParameterTuner,
    CreditAssignment,
    OperatorCredit,
    SelectionStrategy,
)
from src.algorithms.adaptive.parameter_tuner import (
    AdaptiveSchedule,
    ConstantSchedule,
    CosineSchedule,
    ExponentialSchedule,
    LinearSchedule,
)
from src.algorithms.building import Building, BuildingType
from src.algorithms.operators.registry import create_default_registry
from src.algorithms.solution import Solution

# =============================================================================
# CREDIT ASSIGNMENT TESTS
# =============================================================================


class TestOperatorCredit:
    """Test OperatorCredit dataclass."""

    def test_initialization(self):
        """Test credit initialization."""
        credit = OperatorCredit(name="gaussian")

        assert credit.name == "gaussian"
        assert credit.uses == 0
        assert credit.successes == 0
        assert credit.total_improvement == 0.0
        assert credit.success_rate == 0.5  # Neutral prior
        assert credit.avg_improvement == 0.0

    def test_update_success(self):
        """Test successful update."""
        credit = OperatorCredit(name="gaussian")
        credit.update(improvement=0.1, success=True)

        assert credit.uses == 1
        assert credit.successes == 1
        assert credit.total_improvement == 0.1
        assert credit.success_rate == 1.0
        assert credit.avg_improvement == 0.1
        assert credit.ema_improvement == 0.1

    def test_update_failure(self):
        """Test failed update."""
        credit = OperatorCredit(name="gaussian")
        credit.update(improvement=-0.05, success=False)

        assert credit.uses == 1
        assert credit.successes == 0
        assert credit.total_improvement == -0.05
        assert credit.success_rate == 0.0
        assert credit.avg_improvement == -0.05

    def test_sliding_window(self):
        """Test sliding window for recent improvements."""
        credit = OperatorCredit(name="gaussian")

        # Add more than window size
        for i in range(60):
            credit.update(improvement=i * 0.01, success=True, window_size=50)

        assert len(credit.recent_improvements) == 50  # Window limit
        assert credit.recent_improvements[0] == 10 * 0.01  # Oldest in window
        assert credit.recent_improvements[-1] == 59 * 0.01  # Most recent


class TestCreditAssignment:
    """Test CreditAssignment class."""

    def test_initialization(self):
        """Test credit assignment initialization."""
        credit = CreditAssignment()

        assert len(credit.credits) == 0
        assert credit.min_probability == 0.05
        assert credit.max_probability == 0.95

    def test_register_operator(self):
        """Test operator registration."""
        credit = CreditAssignment()
        credit.register_operator("gaussian")
        credit.register_operator("swap")

        assert "gaussian" in credit.credits
        assert "swap" in credit.credits

    def test_update_creates_operator(self):
        """Test that update auto-registers operator."""
        credit = CreditAssignment()
        credit.update("gaussian", improvement=0.1, success=True)

        assert "gaussian" in credit.credits
        assert credit.credits["gaussian"].uses == 1

    def test_uniform_probabilities(self):
        """Test uniform selection probabilities."""
        credit = CreditAssignment()
        credit.register_operator("gaussian")
        credit.register_operator("swap")
        credit.register_operator("reset")

        probs = credit.get_selection_probabilities(strategy="uniform")

        assert len(probs) == 3
        assert all(abs(p - 1.0 / 3) < 1e-6 for p in probs.values())

    def test_greedy_probabilities(self):
        """Test greedy selection (best operator gets high probability)."""
        credit = CreditAssignment()
        credit.update("gaussian", improvement=0.5, success=True)
        credit.update("swap", improvement=0.1, success=True)
        credit.update("reset", improvement=0.05, success=True)

        probs = credit.get_selection_probabilities(strategy="greedy")

        # Gaussian should have highest probability
        assert probs["gaussian"] > probs["swap"]
        assert probs["gaussian"] > probs["reset"]

    def test_softmax_probabilities(self):
        """Test softmax selection."""
        credit = CreditAssignment()
        credit.update("gaussian", improvement=0.5, success=True)
        credit.update("swap", improvement=0.1, success=True)

        probs = credit.get_selection_probabilities(strategy="softmax", temperature=1.0)

        # Should sum to 1
        assert abs(sum(probs.values()) - 1.0) < 1e-6

        # Better operator should have higher probability
        assert probs["gaussian"] > probs["swap"]

    def test_get_best_operator(self):
        """Test getting best operator."""
        credit = CreditAssignment()
        credit.update("gaussian", improvement=0.5, success=True)
        credit.update("swap", improvement=0.8, success=True)
        credit.update("reset", improvement=0.3, success=True)

        best = credit.get_best_operator()
        assert best == "swap"  # Highest EMA improvement

    def test_get_statistics(self):
        """Test statistics retrieval."""
        credit = CreditAssignment()
        credit.update("gaussian", improvement=0.1, success=True)
        credit.update("gaussian", improvement=0.2, success=True)

        stats = credit.get_statistics()

        assert "gaussian" in stats
        assert stats["gaussian"]["uses"] == 2
        assert stats["gaussian"]["successes"] == 2
        assert stats["gaussian"]["success_rate"] == 1.0


# =============================================================================
# OPERATOR SELECTOR TESTS
# =============================================================================


class TestAdaptiveOperatorSelector:
    """Test AdaptiveOperatorSelector class."""

    @pytest.fixture
    def selector(self):
        """Create selector with default registry."""
        registry = create_default_registry()
        return AdaptiveOperatorSelector(registry)

    def test_initialization(self, selector):
        """Test selector initialization."""
        assert selector.strategy == SelectionStrategy.ADAPTIVE_PURSUIT
        assert len(selector._mutations) == 0
        assert len(selector._crossovers) == 0

    def test_register_mutation(self, selector):
        """Test mutation registration."""
        selector.register_mutation("gaussian", sigma=30.0)

        assert "gaussian" in selector._mutations
        assert selector._mutations["gaussian"]["sigma"] == 30.0

    def test_select_mutation(self, selector):
        """Test mutation selection."""
        selector.register_mutation("gaussian", sigma=30.0)
        selector.register_mutation("swap")

        name, operator = selector.select_mutation()

        assert name in ["gaussian", "swap"]
        assert operator is not None

    def test_update_mutation_credit(self, selector):
        """Test credit update for mutation."""
        selector.register_mutation("gaussian")

        selector.update_mutation_credit("gaussian", improvement=0.1, success=True)

        stats = selector.get_mutation_statistics()
        assert stats["gaussian"]["uses"] == 1
        assert stats["gaussian"]["successes"] == 1

    def test_selection_probabilities_change(self, selector):
        """Test that probabilities adapt to performance."""
        selector.register_mutation("gaussian")
        selector.register_mutation("swap")

        # Simulate gaussian performing better
        for _ in range(10):
            selector.update_mutation_credit("gaussian", improvement=0.1, success=True)
            selector.update_mutation_credit("swap", improvement=0.01, success=True)

        probs = selector.get_selection_probabilities()["mutation"]

        # Gaussian should have higher probability
        assert probs["gaussian"] > probs["swap"]

    def test_get_all_statistics(self, selector):
        """Test getting all statistics."""
        selector.register_mutation("gaussian")
        selector.register_crossover("uniform")

        selector.update_mutation_credit("gaussian", 0.1, True)

        stats = selector.get_all_statistics()

        assert "mutation" in stats
        assert "crossover" in stats
        assert "gaussian" in stats["mutation"]


# =============================================================================
# PARAMETER SCHEDULE TESTS
# =============================================================================


class TestConstantSchedule:
    """Test ConstantSchedule."""

    def test_constant_value(self):
        """Test that value stays constant."""
        schedule = ConstantSchedule(0.5)

        assert schedule.get_value(0, 100) == 0.5
        assert schedule.get_value(50, 100) == 0.5
        assert schedule.get_value(99, 100) == 0.5


class TestLinearSchedule:
    """Test LinearSchedule."""

    def test_linear_interpolation(self):
        """Test linear interpolation."""
        schedule = LinearSchedule(start_value=1.0, end_value=0.0)

        assert schedule.get_value(0, 100) == 1.0
        assert abs(schedule.get_value(50, 100) - 0.5) < 0.01
        assert abs(schedule.get_value(99, 100) - 0.0) < 0.01

    def test_linear_growth(self):
        """Test linear growth (increasing)."""
        schedule = LinearSchedule(start_value=0.0, end_value=1.0)

        assert schedule.get_value(0, 100) == 0.0
        assert abs(schedule.get_value(50, 100) - 0.5) < 0.01
        assert abs(schedule.get_value(99, 100) - 1.0) < 0.01


class TestExponentialSchedule:
    """Test ExponentialSchedule."""

    def test_exponential_decay(self):
        """Test exponential decay."""
        schedule = ExponentialSchedule(start_value=1.0, end_value=0.1, decay_rate=0.9)

        val_0 = schedule.get_value(0, 100)
        val_50 = schedule.get_value(50, 100)

        assert val_0 == 1.0
        assert val_50 < val_0  # Decaying
        assert val_50 > 0.0  # Still positive


class TestCosineSchedule:
    """Test CosineSchedule."""

    def test_cosine_annealing(self):
        """Test cosine annealing."""
        schedule = CosineSchedule(start_value=1.0, end_value=0.0, n_cycles=1)

        val_0 = schedule.get_value(0, 100)
        val_50 = schedule.get_value(50, 100)
        val_99 = schedule.get_value(99, 100)

        assert val_0 == 1.0  # Start high
        assert val_50 < val_0  # Decreasing
        assert abs(val_99 - 0.0) < 0.1  # End low


class TestAdaptiveSchedule:
    """Test AdaptiveSchedule."""

    def test_adaptive_based_on_diversity(self):
        """Test adaptation based on diversity."""
        schedule = AdaptiveSchedule(start_value=1.0, end_value=0.1)

        # High diversity → use start_value
        val_high_div = schedule.get_value(10, 100, diversity=0.9, convergence_rate=0.1)

        # Low diversity → use end_value
        val_low_div = schedule.get_value(10, 100, diversity=0.1, convergence_rate=0.9)

        assert val_high_div > val_low_div


# =============================================================================
# PARAMETER TUNER TESTS
# =============================================================================


class TestAdaptiveParameterTuner:
    """Test AdaptiveParameterTuner class."""

    def test_initialization(self):
        """Test tuner initialization."""
        tuner = AdaptiveParameterTuner()

        assert len(tuner.schedules) == 0

    def test_add_constant(self):
        """Test adding constant parameter."""
        tuner = AdaptiveParameterTuner()
        tuner.add_constant("mutation_rate", 0.15)

        value = tuner.get_parameter("mutation_rate", 10, 100)
        assert value == 0.15

    def test_add_linear(self):
        """Test adding linear schedule."""
        tuner = AdaptiveParameterTuner()
        tuner.add_linear("mutation_rate", start_value=0.3, end_value=0.05)

        val_0 = tuner.get_parameter("mutation_rate", 0, 100)
        val_50 = tuner.get_parameter("mutation_rate", 50, 100)

        assert val_0 == 0.3
        assert abs(val_50 - 0.175) < 0.01  # Midpoint

    def test_get_all_parameters(self):
        """Test getting all parameters."""
        tuner = AdaptiveParameterTuner()
        tuner.add_constant("mutation_rate", 0.15)
        tuner.add_linear("temperature", 1000.0, 0.1)

        params = tuner.get_parameters(50, 100)

        assert "mutation_rate" in params
        assert "temperature" in params
        assert params["mutation_rate"] == 0.15

    def test_remove_parameter(self):
        """Test removing parameter."""
        tuner = AdaptiveParameterTuner()
        tuner.add_constant("mutation_rate", 0.15)
        tuner.remove_parameter("mutation_rate")

        assert "mutation_rate" not in tuner.schedules

    def test_parameter_not_found(self):
        """Test error when parameter not registered."""
        tuner = AdaptiveParameterTuner()

        with pytest.raises(KeyError):
            tuner.get_parameter("unknown", 10, 100)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestAdaptiveIntegration:
    """Integration tests for adaptive system."""

    @pytest.fixture
    def selector(self):
        """Create configured selector."""
        registry = create_default_registry()
        selector = AdaptiveOperatorSelector(registry, strategy=SelectionStrategy.ADAPTIVE_PURSUIT)

        # Register operators
        selector.register_mutation("gaussian", sigma=30.0)
        selector.register_mutation("swap")
        selector.register_mutation("reset", margin=10.0)

        return selector

    @pytest.fixture
    def solution(self):
        """Create test solution."""
        positions = {
            "B0": (50, 50),
            "B1": (100, 50),
            "B2": (150, 50),
        }
        return Solution(positions=positions)

    @pytest.fixture
    def buildings(self):
        """Create test buildings."""
        return [Building(f"B{i}", BuildingType.RESIDENTIAL, 1500, 4) for i in range(3)]

    @pytest.fixture
    def bounds(self):
        """Create test bounds."""
        return (0, 0, 200, 200)

    def test_adaptive_operator_selection_workflow(self, selector, solution, buildings, bounds):
        """Test complete adaptive operator workflow."""
        # Simulate optimization with feedback
        for _ in range(20):
            # Select operator
            name, operator = selector.select_mutation()

            # Apply operator
            operator.mutate(solution.copy(), buildings, bounds)

            # Simulate fitness improvement
            improvement = np.random.uniform(-0.1, 0.1)
            success = improvement > 0

            # Update credit
            selector.update_mutation_credit(name, improvement, success)

        # Check that statistics are tracked
        stats = selector.get_mutation_statistics()

        assert len(stats) == 3
        total_uses = sum(s["uses"] for s in stats.values())
        assert total_uses == 20

    def test_parameter_tuning_with_selection(self):
        """Test parameter tuning integrated with operator selection."""
        # Create tuner
        tuner = AdaptiveParameterTuner()
        tuner.add_linear("mutation_rate", start_value=0.3, end_value=0.05)
        tuner.add_exponential("temperature", start_value=1000.0, end_value=0.1)

        # Simulate generations
        for gen in range(100):
            params = tuner.get_parameters(gen, 100)

            # Mutation rate should be in valid range (allow small tolerance)
            assert 0.04 <= params["mutation_rate"] <= 0.31

            # Temperature should decrease
            assert params["temperature"] > 0
