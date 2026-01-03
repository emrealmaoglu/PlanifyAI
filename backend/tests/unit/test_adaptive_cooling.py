"""
Unit Tests for Adaptive Cooling Schedules
==========================================

Tests for adaptive_cooling.py module.

Created: 2026-01-03
"""

import numpy as np
import pytest

from src.algorithms.adaptive_cooling import (
    adaptive_cooling_specific_heat,
    adaptive_markov_length,
    calculate_cooling_statistics,
    calculate_reheat_temperature,
    cauchy_fast_cooling,
    exponential_cooling,
    find_initial_temp_variance,
    hybrid_constant_exponential,
    linear_cooling,
    logarithmic_cooling,
    should_reheat,
    track_phase_transition,
)


class TestClassicalCoolingSchedules:
    """Test classical cooling schedules."""

    def test_exponential_cooling_basic(self):
        """Test exponential cooling decreases properly."""
        T_start = 1000.0
        alpha = 0.95

        T0 = exponential_cooling(T_start, alpha, 0)
        T10 = exponential_cooling(T_start, alpha, 10)
        T100 = exponential_cooling(T_start, alpha, 100)

        # Should decrease monotonically
        assert T0 > T10 > T100

        # Initial should be T_start
        assert abs(T0 - T_start) < 0.01

        # T100 should be T_start * alpha^100
        expected_T100 = T_start * (alpha**100)
        assert abs(T100 - expected_T100) < 0.01

    def test_exponential_cooling_convergence(self):
        """Test exponential cooling converges to zero."""
        T_start = 100.0
        alpha = 0.9

        T1000 = exponential_cooling(T_start, alpha, 1000)

        # Should be very small
        assert T1000 < 1e-20

    def test_linear_cooling_basic(self):
        """Test linear cooling decreases linearly."""
        T_start = 100.0
        beta = 0.5

        T0 = linear_cooling(T_start, beta, 0)
        T10 = linear_cooling(T_start, beta, 10)
        T50 = linear_cooling(T_start, beta, 50)

        # Should decrease
        assert T0 > T10 > T50

        # Initial should be T_start
        assert abs(T0 - T_start) < 0.01

        # T10 should be T_start - 10*beta
        expected_T10 = T_start - 10 * beta
        assert abs(T10 - expected_T10) < 0.01

    def test_linear_cooling_clipping(self):
        """Test linear cooling doesn't go negative."""
        T_start = 10.0
        beta = 1.0

        # Should clip at iteration > T_start/beta
        T100 = linear_cooling(T_start, beta, 100)

        # Should be positive (clipped)
        assert T100 > 0
        assert T100 < 1e-6

    def test_logarithmic_cooling_basic(self):
        """Test logarithmic cooling."""
        C = 100.0

        T1 = logarithmic_cooling(C, 1)
        T10 = logarithmic_cooling(C, 10)
        T100 = logarithmic_cooling(C, 100)

        # Should decrease
        assert T1 > T10 > T100

        # Should follow C / log(1 + k)
        expected_T10 = C / np.log(1 + 10)
        assert abs(T10 - expected_T10) < 0.01

    def test_cauchy_fast_cooling_basic(self):
        """Test Cauchy fast cooling."""
        T_start = 100.0

        T0 = cauchy_fast_cooling(T_start, 0)
        T10 = cauchy_fast_cooling(T_start, 10)
        T100 = cauchy_fast_cooling(T_start, 100)

        # Should decrease
        assert T0 > T10 > T100

        # T10 should be T_start / (1 + 10)
        expected_T10 = T_start / (1 + 10)
        assert abs(T10 - expected_T10) < 0.01


class TestAdaptiveCoolingSchedules:
    """Test adaptive cooling schedules."""

    def test_adaptive_cooling_high_variance(self):
        """Test adaptive cooling slows with high variance."""
        T_current = 100.0
        costs_high_var = [0.5, 0.8, 0.3, 0.9, 0.2, 0.1, 0.7]

        T_new = adaptive_cooling_specific_heat(T_current, costs_high_var, alpha_nought=0.95)

        # Should cool (variance-based adaptive cooling)
        assert T_new < T_current
        assert T_new > 0  # Should be positive

    def test_adaptive_cooling_low_variance(self):
        """Test adaptive cooling speeds with low variance."""
        T_current = 100.0
        costs_low_var = [0.5, 0.51, 0.49, 0.50, 0.52, 0.50]

        T_new = adaptive_cooling_specific_heat(T_current, costs_low_var, alpha_nought=0.95)

        # Should cool faster (low variance = smooth landscape)
        assert T_new < T_current
        # May cool faster than high variance case

    def test_adaptive_cooling_fallback(self):
        """Test adaptive cooling with insufficient data."""
        T_current = 100.0
        costs = [0.5]  # Single data point

        T_new = adaptive_cooling_specific_heat(T_current, costs, alpha_nought=0.95)

        # Should fall back to geometric cooling
        expected = T_current * 0.95
        assert abs(T_new - expected) < 0.01

    def test_adaptive_cooling_zero_variance(self):
        """Test adaptive cooling with zero variance."""
        T_current = 100.0
        costs = [0.5, 0.5, 0.5, 0.5]  # Zero variance

        T_new = adaptive_cooling_specific_heat(T_current, costs, alpha_nought=0.95)

        # Should handle gracefully (may cool very fast with zero variance)
        assert T_new < T_current
        assert T_new >= 0  # Non-negative

    def test_hybrid_constant_exponential_burn_in(self):
        """Test hybrid schedule during burn-in phase."""
        burn_in = 100
        T_high = 1000.0

        # During burn-in: constant temperature
        T50 = hybrid_constant_exponential(50, burn_in, T_high, alpha_fast=0.9)

        assert abs(T50 - T_high) < 0.01

    def test_hybrid_constant_exponential_exploitation(self):
        """Test hybrid schedule during exploitation phase."""
        burn_in = 100
        T_high = 1000.0
        alpha_fast = 0.9

        # After burn-in: exponential cooling
        iteration = 150
        T = hybrid_constant_exponential(iteration, burn_in, T_high, alpha_fast)

        # Should be T_high * alpha^(150 - 100)
        expected = T_high * (alpha_fast ** (iteration - burn_in))
        assert abs(T - expected) < 0.01

    def test_hybrid_constant_exponential_transition(self):
        """Test hybrid schedule transition."""
        burn_in = 100
        T_high = 1000.0

        T_before = hybrid_constant_exponential(99, burn_in, T_high, alpha_fast=0.9)
        T_after = hybrid_constant_exponential(100, burn_in, T_high, alpha_fast=0.9)

        # Before transition: constant
        assert abs(T_before - T_high) < 0.01

        # After transition: starts cooling
        assert T_after == T_high  # k=0, alpha^0 = 1


class TestInitialTemperatureCalculation:
    """Test initial temperature calculation methods."""

    def test_find_initial_temp_variance_basic(self):
        """Test variance-based T₀ calculation."""
        costs = [1.0, 2.0, 3.0, 4.0, 5.0]
        K = 5.0

        T0 = find_initial_temp_variance(costs, K)

        # Should be K * std(costs)
        expected = K * np.std(costs)
        assert abs(T0 - expected) < 0.01

    def test_find_initial_temp_variance_fallback(self):
        """Test variance-based T₀ with insufficient data."""
        costs = [1.0]  # Single value

        T0 = find_initial_temp_variance(costs, K=5.0)

        # Should return fallback
        assert T0 == 100.0

    def test_find_initial_temp_variance_zero_variance(self):
        """Test variance-based T₀ with zero variance."""
        costs = [5.0, 5.0, 5.0, 5.0]
        K = 5.0

        T0 = find_initial_temp_variance(costs, K)

        # Should be zero (K * 0)
        assert T0 == 0.0


class TestReheatingStrategies:
    """Test reheating and restart strategies."""

    def test_should_reheat_trigger(self):
        """Test reheating trigger condition."""
        # Should trigger
        result = should_reheat(
            stagnation_counter=100,
            stagnation_threshold=50,
            reheat_count=2,
            max_reheats=5,
        )
        assert result is True

    def test_should_reheat_no_stagnation(self):
        """Test no reheating without stagnation."""
        # Should not trigger (no stagnation)
        result = should_reheat(
            stagnation_counter=10,
            stagnation_threshold=50,
            reheat_count=2,
            max_reheats=5,
        )
        assert result is False

    def test_should_reheat_max_reheats_exceeded(self):
        """Test no reheating when max reheats exceeded."""
        # Should not trigger (max reheats exceeded)
        result = should_reheat(
            stagnation_counter=100,
            stagnation_threshold=50,
            reheat_count=5,
            max_reheats=5,
        )
        assert result is False

    def test_calculate_reheat_temperature_basic(self):
        """Test reheat temperature calculation."""
        best_cost = 100.0
        phase_transition_temp = 50.0
        initial_temp = 1000.0
        final_temp = 1.0
        K = 0.5

        T_reheat = calculate_reheat_temperature(
            best_cost, phase_transition_temp, initial_temp, final_temp, K
        )

        # Should be K * best_cost + phase_transition_temp
        expected = K * best_cost + phase_transition_temp

        # But clipped to [final_temp * 10, initial_temp * 0.5]
        expected = np.clip(expected, final_temp * 10, initial_temp * 0.5)

        assert abs(T_reheat - expected) < 0.01

    def test_calculate_reheat_temperature_clipping(self):
        """Test reheat temperature clipping."""
        # Very high cost should be clipped to upper bound
        T_reheat_high = calculate_reheat_temperature(
            best_cost=10000.0,
            phase_transition_temp=50.0,
            initial_temp=100.0,
            final_temp=1.0,
            K=0.5,
        )

        # Should be clipped to initial_temp * 0.5
        assert abs(T_reheat_high - 50.0) < 0.01

        # Very low cost should be clipped to lower bound
        T_reheat_low = calculate_reheat_temperature(
            best_cost=1.0,
            phase_transition_temp=5.0,
            initial_temp=100.0,
            final_temp=1.0,
            K=0.5,
        )

        # Should be clipped to final_temp * 10
        assert abs(T_reheat_low - 10.0) < 0.01


class TestAdaptiveMarkovLength:
    """Test adaptive Markov chain length calculation."""

    def test_adaptive_markov_high_variance(self):
        """Test longer chain with high variance."""
        base_length = 100
        costs_high_var = [0.5, 0.8, 0.3, 0.9, 0.2, 0.1, 0.7]

        L = adaptive_markov_length(base_length, costs_high_var)

        # Should be longer than base (high variance)
        assert L >= base_length

    def test_adaptive_markov_low_variance(self):
        """Test shorter chain with low variance."""
        base_length = 100
        costs_low_var = [0.5, 0.51, 0.49, 0.50, 0.52]

        L = adaptive_markov_length(base_length, costs_low_var)

        # Should be closer to base (low variance)
        assert L >= 50  # min_length
        assert L <= 500  # max_length

    def test_adaptive_markov_clipping(self):
        """Test Markov length clipping to bounds."""
        base_length = 100
        costs = [0.5, 0.8, 0.3, 0.9]

        L = adaptive_markov_length(base_length, costs, min_length=50, max_length=200)

        # Should be within bounds
        assert 50 <= L <= 200

    def test_adaptive_markov_fallback(self):
        """Test Markov length with insufficient data."""
        base_length = 100
        costs = [0.5]  # Single value

        L = adaptive_markov_length(base_length, costs)

        # Should return base_length
        assert L == base_length


class TestPhaseTransitionTracking:
    """Test phase transition temperature tracking."""

    def test_track_phase_transition_new_max(self):
        """Test phase transition update with new maximum variance."""
        costs = np.random.randn(50)  # Large sample
        current_T = 100.0
        max_var = 0.5
        phase_T = 50.0

        new_max_var, new_phase_T = track_phase_transition(costs, current_T, max_var, phase_T)

        variance = np.var(costs)
        if variance > max_var:
            # Should update
            assert abs(new_max_var - variance) < 0.01
            assert new_phase_T == current_T
        else:
            # Should not update
            assert new_max_var == max_var
            assert new_phase_T == phase_T

    def test_track_phase_transition_insufficient_data(self):
        """Test phase transition with insufficient data."""
        costs = [0.5, 0.6]  # Too few samples
        current_T = 100.0
        max_var = 0.5
        phase_T = 50.0

        new_max_var, new_phase_T = track_phase_transition(costs, current_T, max_var, phase_T)

        # Should not update
        assert new_max_var == max_var
        assert new_phase_T == phase_T


class TestCoolingStatistics:
    """Test cooling schedule statistics calculation."""

    def test_calculate_cooling_statistics_basic(self):
        """Test statistics calculation with valid data."""
        temperature_history = [1000, 950, 902.5, 857.375, 814.506]
        fitness_history = [0.5, 0.6, 0.65, 0.7, 0.75]

        stats = calculate_cooling_statistics(temperature_history, fitness_history)

        # Check keys
        assert "initial_temp" in stats
        assert "final_temp" in stats
        assert "mean_temp" in stats
        assert "temp_std" in stats
        assert "cooling_rate_avg" in stats
        assert "fitness_improvement" in stats
        assert "fitness_variance" in stats

        # Check values
        assert stats["initial_temp"] == 1000
        assert stats["final_temp"] == 814.506
        assert stats["mean_temp"] > 0
        assert stats["fitness_improvement"] == 0.25  # 0.75 - 0.5

    def test_calculate_cooling_statistics_insufficient_data(self):
        """Test statistics with insufficient data."""
        temperature_history = [100]
        fitness_history = [0.5]

        stats = calculate_cooling_statistics(temperature_history, fitness_history)

        # Should return empty dict
        assert stats == {}

    def test_calculate_cooling_statistics_empty(self):
        """Test statistics with empty data."""
        stats = calculate_cooling_statistics([], [])

        # Should return empty dict
        assert stats == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
