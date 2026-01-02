"""
Unit Tests for Enhanced Research-Based Objectives
==================================================

Tests for objectives_enhanced.py module with research-based metrics.

Created: 2026-01-02 (Week 4 Day 4)
"""

import numpy as np
import pytest

from src.algorithms import Building, BuildingType, Solution
from src.algorithms.objectives_enhanced import (
    ALPHA_GROCERY,
    DETOUR_INDEX_TURKEY,
    LAMBDA_RESIDENTIAL,
    SIGMA_DAILY_SERVICES,
    SIGMA_HEALTHCARE,
    WALKING_SPEED_ELDERLY,
    WALKING_SPEED_HEALTHY,
    calculate_adjacency_score,
    calculate_service_mix_entropy,
    calculate_travel_time,
    enhanced_diversity_score,
    enhanced_walking_accessibility,
    exponential_decay,
    gaussian_decay,
    gravity_model_accessibility,
    network_distance_estimate,
    power_law_decay,
    shannon_entropy,
    simpson_diversity_index,
    toblers_hiking_function,
    two_step_floating_catchment_area,
)


class TestDistanceAndSpeed:
    """Test distance calculation and walking speed functions."""

    def test_toblers_hiking_function_flat(self):
        """Test Tobler's function on flat terrain."""
        speed = toblers_hiking_function(0.0)
        # At 0% slope: W = 6 * exp(-3.5 * |0 + 0.05|) ≈ 5.03 km/h
        assert 5.0 < speed < 5.1

    def test_toblers_hiking_function_downhill_optimal(self):
        """Test Tobler's function at optimal downhill slope (-5%)."""
        speed = toblers_hiking_function(-0.05)
        # At -5% slope: W = 6 * exp(0) = 6.0 km/h (maximum)
        assert abs(speed - 6.0) < 0.01

    def test_toblers_hiking_function_uphill(self):
        """Test Tobler's function on steep uphill."""
        speed_10pct = toblers_hiking_function(0.10)
        speed_20pct = toblers_hiking_function(0.20)
        # Speed should decrease with steeper slope
        assert speed_20pct < speed_10pct < 5.0

    def test_network_distance_estimate(self):
        """Test network distance estimation."""
        euclidean = 100.0
        network = network_distance_estimate(euclidean)
        # Should be 32.4% longer for Turkey
        assert abs(network - 132.4) < 0.1

    def test_network_distance_custom_detour(self):
        """Test with custom detour index."""
        euclidean = 100.0
        network = network_distance_estimate(euclidean, detour_index=1.5)
        assert network == 150.0

    def test_calculate_travel_time_flat(self):
        """Test travel time calculation on flat terrain."""
        distance = 1000.0  # 1 km
        time = calculate_travel_time(distance, walking_speed_kmh=5.0, slope=0.0)
        # 1 km at 5 km/h = 12 minutes = 720 seconds
        assert abs(time - 720.0) < 1.0

    def test_calculate_travel_time_slope(self):
        """Test travel time with slope adjustment."""
        distance = 1000.0
        time_flat = calculate_travel_time(distance, slope=0.0)
        time_uphill = calculate_travel_time(distance, slope=0.15)
        # Uphill should take longer
        assert time_uphill > time_flat


class TestDecayFunctions:
    """Test spatial influence decay functions."""

    def test_gaussian_decay_zero_distance(self):
        """Test Gaussian decay at zero distance."""
        decay = gaussian_decay(np.array([0.0]), sigma=100.0)
        # Should be 1.0 at distance 0
        assert abs(decay[0] - 1.0) < 0.001

    def test_gaussian_decay_far_distance(self):
        """Test Gaussian decay at large distance."""
        decay = gaussian_decay(np.array([1000.0]), sigma=100.0)
        # Should be very small at 10 sigma
        assert decay[0] < 0.001

    def test_gaussian_decay_sigma_effect(self):
        """Test that sigma controls decay rate."""
        distance = np.array([100.0])
        decay_narrow = gaussian_decay(distance, sigma=50.0)
        decay_wide = gaussian_decay(distance, sigma=200.0)
        # Wider sigma should have higher value at same distance
        assert decay_wide[0] > decay_narrow[0]

    def test_exponential_decay_zero_distance(self):
        """Test exponential decay at zero distance."""
        decay = exponential_decay(np.array([0.0]), lambda_param=0.01)
        assert abs(decay[0] - 1.0) < 0.001

    def test_exponential_decay_lambda_effect(self):
        """Test that lambda controls decay rate."""
        distance = np.array([100.0])
        decay_slow = exponential_decay(distance, lambda_param=0.001)
        decay_fast = exponential_decay(distance, lambda_param=0.01)
        # Slower lambda should have higher value
        assert decay_slow[0] > decay_fast[0]

    def test_power_law_decay_zero_distance(self):
        """Test power-law decay at zero distance."""
        decay = power_law_decay(np.array([0.0]), alpha=2.0)
        # Should be finite due to epsilon
        assert np.isfinite(decay[0])
        assert decay[0] > 0

    def test_power_law_decay_alpha_effect(self):
        """Test that alpha controls decay rate."""
        distance = np.array([100.0])
        decay_slow = power_law_decay(distance, alpha=1.5)
        decay_fast = power_law_decay(distance, alpha=3.0)
        # Higher alpha = faster decay
        assert decay_slow[0] > decay_fast[0]


class TestAccessibilityMetrics:
    """Test accessibility metric functions."""

    def test_gravity_model_simple(self):
        """Test gravity model with simple setup."""
        # 2 origins, 3 destinations
        origins = np.array([[0, 0], [100, 100]])
        destinations = np.array([[50, 0], [0, 50], [100, 50]])
        opportunities = np.array([10, 20, 30])

        accessibility = gravity_model_accessibility(
            origins, destinations, opportunities, decay_function="exponential", lambda_param=0.01
        )

        # Should return accessibility for each origin
        assert len(accessibility) == 2
        assert all(accessibility > 0)

    def test_gravity_model_decay_functions(self):
        """Test gravity model with different decay functions."""
        origins = np.array([[0, 0]])
        destinations = np.array([[100, 0]])
        opportunities = np.array([10])

        # Gaussian
        acc_gaussian = gravity_model_accessibility(
            origins, destinations, opportunities, decay_function="gaussian", sigma=100
        )

        # Exponential
        acc_exponential = gravity_model_accessibility(
            origins, destinations, opportunities, decay_function="exponential", lambda_param=0.01
        )

        # Power-law
        acc_power = gravity_model_accessibility(
            origins, destinations, opportunities, decay_function="power_law", alpha=2.0
        )

        # All should be positive
        assert acc_gaussian[0] > 0
        assert acc_exponential[0] > 0
        assert acc_power[0] > 0

    def test_2sfca_basic(self):
        """Test 2SFCA with basic setup."""
        # 3 residential origins, 2 service destinations
        origins = np.array([[0, 0], [100, 0], [200, 0]])
        destinations = np.array([[50, 0], [150, 0]])
        demand = np.array([100, 100, 100])  # Population
        supply = np.array([200, 200])  # Capacity

        supply_ratios, accessibility = two_step_floating_catchment_area(
            origins, destinations, demand, supply, catchment_distance=150, sigma=100
        )

        # Check output shapes
        assert len(supply_ratios) == 2
        assert len(accessibility) == 3

        # All should be non-negative
        assert all(supply_ratios >= 0)
        assert all(accessibility >= 0)

    def test_2sfca_out_of_catchment(self):
        """Test 2SFCA when origins are far from destinations."""
        origins = np.array([[0, 0]])
        destinations = np.array([[1000, 1000]])  # Very far
        demand = np.array([100])
        supply = np.array([100])

        _, accessibility = two_step_floating_catchment_area(
            origins, destinations, demand, supply, catchment_distance=100, sigma=50
        )

        # Should be zero (out of catchment)
        assert accessibility[0] == 0.0


class TestDiversityMetrics:
    """Test diversity measurement functions."""

    def test_shannon_entropy_uniform(self):
        """Test Shannon entropy with uniform distribution."""
        proportions = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = shannon_entropy(proportions)
        # Maximum entropy for 4 categories: ln(4) ≈ 1.386
        assert abs(entropy - np.log(4)) < 0.01

    def test_shannon_entropy_concentrated(self):
        """Test Shannon entropy with concentrated distribution."""
        proportions = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = shannon_entropy(proportions)
        # No diversity
        assert entropy == 0.0

    def test_shannon_entropy_base2(self):
        """Test Shannon entropy with base 2 (bits)."""
        proportions = np.array([0.5, 0.5])
        entropy = shannon_entropy(proportions, base=2)
        # 1 bit of information
        assert abs(entropy - 1.0) < 0.01

    def test_simpson_diversity_uniform(self):
        """Test Simpson's diversity with uniform distribution."""
        proportions = np.array([0.25, 0.25, 0.25, 0.25])
        diversity = simpson_diversity_index(proportions)
        # D = 1 - (0.25^2 + 0.25^2 + 0.25^2 + 0.25^2) = 0.75
        assert abs(diversity - 0.75) < 0.01

    def test_simpson_diversity_concentrated(self):
        """Test Simpson's diversity with concentrated distribution."""
        proportions = np.array([1.0, 0.0, 0.0])
        diversity = simpson_diversity_index(proportions)
        # D = 1 - 1.0 = 0.0
        assert diversity == 0.0

    def test_calculate_service_mix_entropy(self):
        """Test service mix entropy calculation."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B3", BuildingType.EDUCATIONAL, 1500, 3),
            Building("B4", BuildingType.COMMERCIAL, 1000, 2),
        ]

        solution = Solution(
            positions={"B1": (0, 0), "B2": (100, 0), "B3": (0, 100), "B4": (100, 100)}
        )

        entropy = calculate_service_mix_entropy(solution, buildings)

        # Should have positive entropy (3 different types)
        assert entropy > 0


class TestAdjacencyScore:
    """Test building type adjacency scoring."""

    def test_adjacency_score_basic(self):
        """Test adjacency score with basic layout."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.SOCIAL, 1500, 2),  # Recreation
            Building("B3", BuildingType.EDUCATIONAL, 1500, 3),
        ]

        # Place residential close to recreation (high adjacency in matrix)
        solution = Solution(positions={"B1": (0, 0), "B2": (50, 0), "B3": (500, 0)})  # Close  # Far

        score = calculate_adjacency_score(solution, buildings)

        # Should have positive score
        assert score > 0

    def test_adjacency_score_single_building(self):
        """Test adjacency score with single building."""
        buildings = [Building("B1", BuildingType.RESIDENTIAL, 2000, 4)]
        solution = Solution(positions={"B1": (0, 0)})

        score = calculate_adjacency_score(solution, buildings)

        # Should be zero (no pairs)
        assert score == 0.0


class TestEnhancedObjectives:
    """Test complete enhanced objective functions."""

    def test_enhanced_walking_accessibility(self):
        """Test enhanced walking accessibility objective."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
            Building("B3", BuildingType.COMMERCIAL, 1000, 2),
        ]

        solution = Solution(positions={"B1": (0, 0), "B2": (100, 0), "B3": (200, 0)})

        # Healthy population
        accessibility_healthy = enhanced_walking_accessibility(
            solution, buildings, walking_speed_kmh=WALKING_SPEED_HEALTHY
        )

        # Elderly population
        accessibility_elderly = enhanced_walking_accessibility(
            solution, buildings, walking_speed_kmh=WALKING_SPEED_ELDERLY
        )

        # Both should be in [0, 1] and healthy >= elderly
        assert 0 <= accessibility_healthy <= 1
        assert 0 <= accessibility_elderly <= 1
        assert accessibility_healthy >= accessibility_elderly

    def test_enhanced_diversity_score(self):
        """Test enhanced diversity score objective."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 4),
            Building("B2", BuildingType.EDUCATIONAL, 1500, 3),
            Building("B3", BuildingType.COMMERCIAL, 1000, 2),
            Building("B4", BuildingType.SOCIAL, 1500, 2),
        ]

        solution = Solution(
            positions={"B1": (0, 0), "B2": (100, 0), "B3": (0, 100), "B4": (100, 100)}
        )

        diversity = enhanced_diversity_score(solution, buildings)

        # Should be in [0, 1] with 4 different types (high diversity)
        assert 0 <= diversity <= 1
        assert diversity > 0.5  # Good diversity


class TestConstants:
    """Test that research-based constants are defined correctly."""

    def test_walking_speeds(self):
        """Test walking speed constants."""
        assert WALKING_SPEED_HEALTHY == 5.0
        assert WALKING_SPEED_ELDERLY == 3.0
        assert WALKING_SPEED_ELDERLY < WALKING_SPEED_HEALTHY

    def test_detour_index(self):
        """Test detour index constant."""
        assert DETOUR_INDEX_TURKEY == 1.324
        assert DETOUR_INDEX_TURKEY > 1.0  # Network is longer

    def test_decay_parameters(self):
        """Test decay function parameters."""
        assert SIGMA_HEALTHCARE > SIGMA_DAILY_SERVICES  # Healthcare farther
        assert LAMBDA_RESIDENTIAL > 0  # Positive decay
        assert ALPHA_GROCERY > 1.0  # Power-law exponent


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
