"""
Enhanced Research-Based Objectives
===================================

Implements advanced spatial planning metrics based on academic research.

Based on research documents:
- 15-Minute City Optimization Analysis
- Spatial Influence Decay Functions Analysis
- Building Typology Spatial Optimization Research

Key Features:
- Tobler's Hiking Function (slope-adjusted walking)
- Gravity Models with multiple decay functions
- Two-Step Floating Catchment Area (2SFCA)
- Shannon Entropy for service diversity
- Building type adjacency optimization

Created: 2026-01-02 (Week 4 Day 4 - Research Integration)
"""

from typing import List, Tuple

import numpy as np
from scipy.spatial.distance import cdist

from .building import Building
from .solution import Solution

# =============================================================================
# CONSTANTS (From Research)
# =============================================================================

# Walking speeds for equity analysis (km/h)
WALKING_SPEED_HEALTHY = 5.0  # Standard baseline
WALKING_SPEED_ELDERLY = 3.0  # Turkish aging population
WALKING_SPEED_DISABLED = 2.88  # Accessibility minimum

# Network distance detour index for Turkey
DETOUR_INDEX_TURKEY = 1.324  # Network is 32.4% longer than Euclidean

# Gaussian decay sigmas (meters)
SIGMA_HEALTHCARE = 2000  # 20-30 min travel time
SIGMA_DAILY_SERVICES = 650  # Local services

# Exponential decay lambdas
LAMBDA_RESIDENTIAL = 0.12  # Steep local falloff

# Power-law decay alphas
ALPHA_GROCERY = 2.2  # Steep decay (won't travel far)
ALPHA_SPECIALIZED = 1.5  # Shallow decay (willing to travel)

# Accessibility thresholds
TIME_15MIN_SECONDS = 900  # 15-minute city standard
DISTANCE_WALKABLE = 450  # UN-Habitat walkability (meters)


# =============================================================================
# DISTANCE & SPEED CALCULATIONS
# =============================================================================


def toblers_hiking_function(slope: float) -> float:
    """
    Calculate walking speed adjusted for terrain slope.

    Formula: W = 6 * exp(-3.5 * |slope + 0.05|)

    Based on: Tobler's Hiking Function (1993)
    Maximum speed: 6 km/h at -5% downhill slope

    Args:
        slope: Gradient (e.g., 0.05 for 5% slope)

    Returns:
        Walking speed in km/h

    Example:
        >>> toblers_hiking_function(0.0)  # Flat terrain
        5.03  # km/h
        >>> toblers_hiking_function(0.10)  # 10% uphill
        2.38  # km/h (much slower)
    """
    return 6.0 * np.exp(-3.5 * np.abs(slope + 0.05))


def network_distance_estimate(
    euclidean_dist: float, detour_index: float = DETOUR_INDEX_TURKEY
) -> float:
    """
    Estimate network distance from Euclidean distance.

    Research shows Turkish cities have average detour index of 1.324.

    Args:
        euclidean_dist: Straight-line distance (meters)
        detour_index: Ratio of network/Euclidean distance

    Returns:
        Estimated network distance (meters)
    """
    return euclidean_dist * detour_index


def calculate_travel_time(
    distance: float,
    walking_speed_kmh: float = WALKING_SPEED_HEALTHY,
    slope: float = 0.0,
) -> float:
    """
    Calculate travel time with slope adjustment.

    Args:
        distance: Distance in meters
        walking_speed_kmh: Base walking speed (km/h)
        slope: Terrain slope (e.g., 0.05 for 5%)

    Returns:
        Travel time in seconds
    """
    # Adjust speed for slope
    if abs(slope) > 0.01:  # Significant slope
        speed_kmh = toblers_hiking_function(slope)
    else:
        speed_kmh = walking_speed_kmh

    # Convert to m/s
    speed_ms = speed_kmh * (1000 / 3600)

    # Calculate time
    time_seconds = distance / speed_ms if speed_ms > 0 else float("inf")

    return time_seconds


# =============================================================================
# DECAY FUNCTIONS (Spatial Influence)
# =============================================================================


def gaussian_decay(distance: np.ndarray, sigma: float, weight: float = 1.0) -> np.ndarray:
    """
    Gaussian distance decay function.

    Formula: f(r) = w × exp(-(r/σ)²)

    Properties:
    - C^∞ continuous (infinitely smooth)
    - Recommended for health facilities, education

    Args:
        distance: Distance array (meters)
        sigma: Bandwidth parameter (controls decay rate)
        weight: Multiplier

    Returns:
        Decay values in [0, w]

    Research: Spatial Influence Decay Functions Analysis.docx
    """
    return weight * np.exp(-((distance / sigma) ** 2))


def exponential_decay(distance: np.ndarray, lambda_param: float, weight: float = 1.0) -> np.ndarray:
    """
    Exponential distance decay function.

    Formula: f(r) = w × exp(-λ × r)

    Properties:
    - Memoryless (constant rate of decay)
    - Recommended for residential, local services

    Args:
        distance: Distance array (meters)
        lambda_param: Decay rate (higher = steeper)
        weight: Multiplier

    Returns:
        Decay values in [0, w]
    """
    return weight * np.exp(-lambda_param * distance)


def power_law_decay(
    distance: np.ndarray, alpha: float, weight: float = 1.0, epsilon: float = 1e-6
) -> np.ndarray:
    """
    Power-law distance decay function.

    Formula: f(r) = w × (r + ε)^(-α)

    Properties:
    - Heavy-tailed distribution
    - Recommended for commercial, specialized services

    Args:
        distance: Distance array (meters)
        alpha: Decay exponent (higher = steeper)
        weight: Multiplier
        epsilon: Small constant to avoid singularity at r=0

    Returns:
        Decay values

    Note: ε stabilizes the function at zero distance
    """
    return weight * (distance + epsilon) ** (-alpha)


# =============================================================================
# ACCESSIBILITY METRICS
# =============================================================================


def gravity_model_accessibility(
    origin_points: np.ndarray,
    destination_points: np.ndarray,
    opportunities: np.ndarray,
    decay_function: str = "gaussian",
    **decay_params,
) -> np.ndarray:
    """
    Calculate accessibility using Gravity Model.

    Formula: A_i = Σ_j [O_j × f(c_ij)]

    Args:
        origin_points: Origin locations (N, 2) array
        destination_points: Destination locations (M, 2) array
        opportunities: Opportunity values at each destination (M,) array
        decay_function: "gaussian", "exponential", or "power_law"
        **decay_params: Parameters for decay function
            - For gaussian: sigma
            - For exponential: lambda_param
            - For power_law: alpha

    Returns:
        Accessibility scores for each origin (N,) array

    Research: 15-Minute City Optimization Analysis.docx Section 1.2.B
    """
    # Calculate pairwise distances (N, M)
    distances = cdist(origin_points, destination_points, metric="euclidean")

    # Apply network adjustment
    distances = network_distance_estimate(distances)

    # Apply decay function
    if decay_function == "gaussian":
        sigma = decay_params.get("sigma", SIGMA_DAILY_SERVICES)
        decay = gaussian_decay(distances, sigma)
    elif decay_function == "exponential":
        lambda_param = decay_params.get("lambda_param", LAMBDA_RESIDENTIAL)
        decay = exponential_decay(distances, lambda_param)
    elif decay_function == "power_law":
        alpha = decay_params.get("alpha", ALPHA_GROCERY)
        decay = power_law_decay(distances, alpha)
    else:
        raise ValueError(f"Unknown decay function: {decay_function}")

    # Weight by opportunities
    weighted_decay = decay * opportunities[np.newaxis, :]  # (N, M)

    # Sum across destinations
    accessibility = np.sum(weighted_decay, axis=1)  # (N,)

    return accessibility


def two_step_floating_catchment_area(
    origin_points: np.ndarray,
    destination_points: np.ndarray,
    origin_demand: np.ndarray,
    destination_supply: np.ndarray,
    catchment_distance: float = 800,
    sigma: float = 500,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate 2SFCA accessibility index.

    Two-Step Floating Catchment Area method for capacity-aware planning.
    Critical for healthcare and education to prevent overcrowding.

    Step 1: Calculate supply-to-demand ratio R_j for each facility
    Step 2: Sum ratios R_j for all facilities accessible to each origin

    Args:
        origin_points: Origin locations (N, 2) - e.g., residential areas
        destination_points: Service locations (M, 2) - e.g., schools
        origin_demand: Demand at each origin (N,) - e.g., population
        destination_supply: Supply at each destination (M,) - e.g., capacity
        catchment_distance: Maximum distance for catchment (meters)
        sigma: Gaussian bandwidth for decay

    Returns:
        Tuple of:
        - supply_ratios: R_j for each destination (M,)
        - accessibility_scores: A_i for each origin (N,)

    Research: 15-Minute City Optimization Analysis.docx Section 1.2.B.2
    """
    # Calculate all pairwise distances
    distances = cdist(origin_points, destination_points, metric="euclidean")
    distances = network_distance_estimate(distances)  # (N, M)

    # Gaussian decay
    decay = gaussian_decay(distances, sigma)  # (N, M)

    # Step 1: Calculate R_j (supply-to-demand ratio)
    supply_ratios = np.zeros(len(destination_points))

    for j in range(len(destination_points)):
        # Find origins within catchment
        within_catchment = distances[:, j] <= catchment_distance

        if not np.any(within_catchment):
            supply_ratios[j] = 0
            continue

        # Sum weighted demand
        total_demand = np.sum(origin_demand[within_catchment] * decay[within_catchment, j])

        # Calculate ratio
        if total_demand > 0:
            supply_ratios[j] = destination_supply[j] / total_demand
        else:
            supply_ratios[j] = 0

    # Step 2: Calculate A_i (accessibility for each origin)
    accessibility_scores = np.zeros(len(origin_points))

    for i in range(len(origin_points)):
        # Find destinations within catchment
        within_catchment = distances[i, :] <= catchment_distance

        if not np.any(within_catchment):
            accessibility_scores[i] = 0
            continue

        # Sum weighted ratios
        accessibility_scores[i] = np.sum(
            supply_ratios[within_catchment] * decay[i, within_catchment]
        )

    return supply_ratios, accessibility_scores


# =============================================================================
# DIVERSITY METRICS
# =============================================================================


def shannon_entropy(proportions: np.ndarray, base: float = np.e) -> float:
    """
    Calculate Shannon entropy for diversity measurement.

    Formula: H = -Σ [p_k × log(p_k)]

    Higher entropy = more diverse mix of services/building types.

    Args:
        proportions: Array of proportions (must sum to 1.0)
        base: Logarithm base (e for nats, 2 for bits)

    Returns:
        Entropy value (higher = more diverse)

    Example:
        >>> # Uniform distribution (maximum diversity)
        >>> shannon_entropy(np.array([0.25, 0.25, 0.25, 0.25]))
        1.386  # ln(4)
        >>> # All concentrated in one category (no diversity)
        >>> shannon_entropy(np.array([1.0, 0.0, 0.0, 0.0]))
        0.0

    Research: 15-Minute City Optimization Analysis.docx Section 1.2.C
    """
    # Filter out zero probabilities
    p = proportions[proportions > 0]

    if len(p) == 0:
        return 0.0

    # Shannon entropy
    if base == np.e:
        entropy = -np.sum(p * np.log(p))
    else:
        entropy = -np.sum(p * np.log(p) / np.log(base))

    return entropy


def simpson_diversity_index(proportions: np.ndarray) -> float:
    """
    Calculate Simpson's Diversity Index.

    Formula: D = 1 - Σ [p_k²]

    Range: [0, 1] where 1 = maximum diversity

    Args:
        proportions: Array of proportions (must sum to 1.0)

    Returns:
        Diversity index
    """
    return 1.0 - np.sum(proportions**2)


def calculate_service_mix_entropy(solution: Solution, buildings: List[Building]) -> float:
    """
    Calculate Shannon entropy of building type mix.

    Measures how diverse the building types are in the solution.

    Args:
        solution: Campus layout solution
        buildings: List of buildings

    Returns:
        Entropy score (higher = more diverse mix)
    """
    from collections import Counter

    # Count building types
    type_counts = Counter(b.type for b in buildings)
    total = len(buildings)

    # Calculate proportions
    proportions = np.array([count / total for count in type_counts.values()])

    # Shannon entropy
    return shannon_entropy(proportions)


# =============================================================================
# BUILDING TYPE INTERACTIONS
# =============================================================================

# Adjacency matrix for campus planning (based on research)
# Rows/Cols: [Residential, Educational, Commercial, Healthcare, Recreation, Administrative]
ADJACENCY_MATRIX_CAMPUS = np.array(
    [
        [0, 2, 3, 1, 5, 0],  # Residential: likes recreation (+5), commercial (+3)
        [2, 4, 1, 1, 3, 2],  # Educational: likes other educational (+4), recreation (+3)
        [3, 1, 2, 0, 1, 0],  # Commercial: likes residential (+3), other commercial (+2)
        [1, 1, 0, 0, 2, 1],  # Healthcare: likes recreation (+2)
        [5, 3, 1, 2, 0, 0],  # Recreation: likes residential (+5), educational (+3)
        [0, 2, 0, 1, 0, 0],  # Administrative: likes educational (+2)
    ]
)


def calculate_adjacency_score(
    solution: Solution,
    buildings: List[Building],
    adjacency_matrix: np.ndarray = ADJACENCY_MATRIX_CAMPUS,
) -> float:
    """
    Calculate building type adjacency satisfaction (QAP-style).

    Measures how well building placements match desired adjacencies.

    Formula: Score = Σ_i Σ_j [F_ij × decay(distance_ij)]

    Args:
        solution: Campus layout solution
        buildings: List of buildings
        adjacency_matrix: Adjacency preference matrix

    Returns:
        Adjacency score (higher = better adjacency matching)

    Research: Building Typology Spatial Optimization Research.docx Section 4.1
    """
    n = len(buildings)

    if n < 2:
        return 0.0

    # Build position matrix
    positions = np.array([solution.positions[b.id] for b in buildings])

    # Build type indices
    type_to_idx = {
        "RESIDENTIAL": 0,
        "EDUCATIONAL": 1,
        "COMMERCIAL": 2,
        "HEALTHCARE": 3,
        "SOCIAL": 4,  # Recreation
        "ADMINISTRATIVE": 5,
    }

    type_indices = [type_to_idx.get(b.type.name, 0) for b in buildings]

    # Calculate distances
    distances = cdist(positions, positions, metric="euclidean")

    # Calculate adjacency score
    total_score = 0.0

    for i in range(n):
        for j in range(i + 1, n):  # Avoid double counting
            # Get adjacency preference
            flow_ij = adjacency_matrix[type_indices[i], type_indices[j]]

            if flow_ij > 0:  # Only consider positive adjacencies
                # Distance penalty (closer is better for positive adjacencies)
                dist_penalty = exponential_decay(
                    np.array([distances[i, j]]),
                    lambda_param=0.002,  # ~500m half-distance
                )[0]

                total_score += flow_ij * dist_penalty

    # Normalize by number of pairs
    n_pairs = n * (n - 1) / 2
    return total_score / n_pairs if n_pairs > 0 else 0.0


# =============================================================================
# COMPLETE OBJECTIVE FUNCTIONS
# =============================================================================


def enhanced_walking_accessibility(
    solution: Solution,
    buildings: List[Building],
    walking_speed_kmh: float = WALKING_SPEED_HEALTHY,
) -> float:
    """
    Calculate walking accessibility with research-based metrics.

    Uses:
    - Network distance adjustment (detour index)
    - Gravity model with exponential decay
    - 15-minute city threshold

    Args:
        solution: Campus layout
        buildings: List of buildings
        walking_speed_kmh: Walking speed for equity analysis

    Returns:
        Accessibility score [0, 1] (higher = better)
    """
    if len(buildings) < 2:
        return 1.0

    # Get positions
    positions = np.array([solution.positions[b.id] for b in buildings])

    # Calculate building "attractiveness" (by area)
    opportunities = np.array([b.area for b in buildings])

    # Normalize opportunities
    opportunities = opportunities / np.sum(opportunities)

    # Calculate accessibility for each building
    accessibility = gravity_model_accessibility(
        origin_points=positions,
        destination_points=positions,
        opportunities=opportunities,
        decay_function="exponential",
        lambda_param=LAMBDA_RESIDENTIAL,
    )

    # Average accessibility
    return np.mean(accessibility)


def enhanced_diversity_score(solution: Solution, buildings: List[Building]) -> float:
    """
    Calculate service diversity using Shannon entropy.

    Measures how balanced the building type mix is.

    Returns:
        Diversity score [0, 1] (normalized entropy)
    """
    entropy = calculate_service_mix_entropy(solution, buildings)

    # Normalize by maximum possible entropy
    n_types = len(set(b.type for b in buildings))
    max_entropy = np.log(n_types) if n_types > 1 else 1.0

    return entropy / max_entropy if max_entropy > 0 else 0.0
