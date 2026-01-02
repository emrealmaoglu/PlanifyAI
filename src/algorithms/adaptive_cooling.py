"""
Adaptive Cooling Schedules for Simulated Annealing
===================================================

Implements research-based adaptive cooling strategies for SA optimization.

Based on research:
- "A Quantitative Analysis of Simulated Annealing Cooling Schedules"
- Empirical comparison of classical vs. adaptive cooling schedules
- Fitness variance-based cooling (Specific Heat method)
- Acceptance ratio-based T₀ calculation
- Reheating and restart strategies

Key Features:
- Automatic T₀ calculation via acceptance ratio heuristic
- Variance-based adaptive cooling (slows in rugged regions)
- Reheating mechanism for escaping local minima
- Adaptive Markov chain length
- 2-2.25x improvement over geometric cooling

Created: 2026-01-02 (Week 4 Day 4 - Adaptive Cooling)
"""

import logging
from typing import Callable

import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# CLASSICAL COOLING SCHEDULES (for comparison)
# =============================================================================


def exponential_cooling(T_start: float, alpha: float, iteration: int) -> float:
    """
    Geometric/Exponential cooling schedule.

    Formula: T(k) = T₀ · α^k

    Current default in H-SAGA. Performance: ~27.5% global optimum rate.

    Args:
        T_start: Initial temperature
        alpha: Cooling rate (typically 0.95)
        iteration: Current iteration number

    Returns:
        Temperature at iteration k

    Example:
        >>> T = exponential_cooling(1000.0, 0.95, 100)
        >>> print(f"{T:.2f}")  # ~5.92
    """
    return T_start * (alpha**iteration)


def linear_cooling(T_start: float, beta: float, iteration: int) -> float:
    """
    Linear cooling schedule.

    Formula: T(k) = T₀ - k · β

    Performance: POOR - Often premature convergence.

    Args:
        T_start: Initial temperature
        beta: Linear cooling constant
        iteration: Current iteration number

    Returns:
        Temperature (clipped to avoid T<=0)
    """
    T_new = T_start - beta * iteration
    return max(T_new, 1e-8)


def logarithmic_cooling(T_start_or_C: float, iteration: int) -> float:
    """
    Logarithmic (Boltzmann) cooling schedule.

    Formula: T(k) = C / log(1 + k)

    Performance: Theoretical guarantee but impractically slow.

    Args:
        T_start_or_C: Constant (often set as T_start)
        iteration: Current iteration number

    Returns:
        Temperature
    """
    return T_start_or_C / (1e-8 + np.log(1 + iteration))


def cauchy_fast_cooling(T_start: float, iteration: int) -> float:
    """
    Cauchy (Fast) cooling schedule.

    Formula: T(k) = T₀ / (1 + k)

    Performance: VERY POOR - Cools too aggressively (~12.94% global optimum).

    Args:
        T_start: Initial temperature
        iteration: Current iteration number

    Returns:
        Temperature
    """
    return T_start / (1.0 + iteration)


# =============================================================================
# ADAPTIVE COOLING SCHEDULES (Recommended)
# =============================================================================


def adaptive_cooling_specific_heat(
    T_current: float,
    costs_at_T: list,
    alpha_nought: float = 0.95,
) -> float:
    """
    Fitness variance-based adaptive cooling (Specific Heat method).

    Uses variance of fitness values as feedback signal. High variance
    indicates rugged landscape → slow cooling. Low variance → fast cooling.

    Formula: T_{j+1} = T_j · exp(-α₀ · T_j / σ(T_j))

    Research shows: 55-62% global optimum rate (vs. 27.5% for geometric).

    Args:
        T_current: Current temperature
        costs_at_T: List of fitness values sampled at current temperature
        alpha_nought: Base cooling rate (default: 0.95)

    Returns:
        Updated temperature

    Example:
        >>> costs = [0.5, 0.8, 0.3, 0.9, 0.2]  # High variance
        >>> T_new = adaptive_cooling_specific_heat(100.0, costs)
        >>> print(f"High variance → slow cooling: {T_new:.2f}")
        >>>
        >>> costs = [0.5, 0.51, 0.49, 0.50, 0.52]  # Low variance
        >>> T_new = adaptive_cooling_specific_heat(100.0, costs)
        >>> print(f"Low variance → fast cooling: {T_new:.2f}")
    """
    if len(costs_at_T) < 2:
        # Not enough data, use simple geometric
        return T_current * alpha_nought

    std_dev = np.std(costs_at_T)

    # Avoid division by zero and stabilize
    if std_dev < 1e-6:
        std_dev = 1e-6

    # T_new = T_current * exp(- (alpha_0 * T_current) / std_dev)
    exponent = -(alpha_nought * T_current) / std_dev
    T_new = T_current * np.exp(exponent)

    # Ensure cooling is not too aggressive, but still cools
    return min(T_new, T_current * 0.99)


def hybrid_constant_exponential(
    iteration: int,
    burn_in_iterations: int,
    T_high: float,
    alpha_fast: float = 0.9,
) -> float:
    """
    Hybrid schedule: Constant temperature → Fast exponential.

    Best performing schedule in empirical studies (62.44% global optimum).

    Phase 1: Exploration at constant high T
    Phase 2: Exploitation with fast exponential cooling

    Args:
        iteration: Current iteration
        burn_in_iterations: Length of exploration phase
        T_high: High constant temperature for exploration
        alpha_fast: Fast cooling rate for exploitation (default: 0.9)

    Returns:
        Current temperature
    """
    if iteration < burn_in_iterations:
        # Phase 1: Constant exploration
        return T_high
    else:
        # Phase 2: Fast exploitation
        k = iteration - burn_in_iterations
        return T_high * (alpha_fast**k)


# =============================================================================
# INITIAL TEMPERATURE (T₀) CALCULATION
# =============================================================================


def find_initial_temp_acceptance_ratio(
    cost_func: Callable,
    generate_neighbor_func: Callable,
    initial_state,
    target_acceptance: float = 0.8,
    n_trials: int = 100,
    max_temp: float = 10000.0,
) -> float:
    """
    Find optimal initial temperature T₀ using acceptance ratio heuristic.

    Automatically determines T₀ that produces initial acceptance ratio
    χ₀ ≥ target (default: 0.8 = 80% acceptance).

    Algorithm:
    1. Start with low temperature (T = 1.0)
    2. Run n_trials random moves
    3. Calculate acceptance ratio χ
    4. If χ < target, multiply T by 2 and repeat
    5. If χ ≥ target, return T as optimal T₀

    Args:
        cost_func: Fitness evaluation function
        generate_neighbor_func: Function to generate random neighbor
        initial_state: Starting solution
        target_acceptance: Target acceptance ratio (default: 0.8)
        n_trials: Number of trial moves per temperature test
        max_temp: Safety limit for temperature

    Returns:
        Optimal initial temperature T₀

    Example:
        >>> def my_cost_func(solution):
        ...     return evaluator.evaluate(solution)
        >>>
        >>> def my_neighbor_func(solution):
        ...     return perturb(solution)
        >>>
        >>> T0 = find_initial_temp_acceptance_ratio(
        ...     my_cost_func,
        ...     my_neighbor_func,
        ...     initial_solution,
        ...     target_acceptance=0.8
        ... )
        >>> print(f"Optimal T₀: {T0:.2f}")
    """
    T = 1.0
    current_cost = cost_func(initial_state)

    logger.info(
        f"Calculating T₀ with target acceptance={target_acceptance:.1%}, " f"n_trials={n_trials}"
    )

    iteration = 0
    while T < max_temp:
        accepted = 0

        for _ in range(n_trials):
            neighbor = generate_neighbor_func(initial_state)
            neighbor_cost = cost_func(neighbor)

            # Calculate delta (assume maximization)
            delta = neighbor_cost - current_cost

            # Metropolis criterion
            if delta > 0 or np.random.rand() < np.exp(delta / T):
                accepted += 1

        acceptance_ratio = accepted / n_trials

        logger.debug(f"Iteration {iteration}: T={T:.2f}, χ={acceptance_ratio:.3f}")

        if acceptance_ratio >= target_acceptance:
            logger.info(f"✅ Optimal T₀ found: {T:.2f} (χ={acceptance_ratio:.1%})")
            return T
        else:
            T *= 2.0  # Increase temperature
            iteration += 1

    # Fallback if max_temp reached
    logger.warning(f"Max temperature {max_temp:.2f} reached. Using as T₀.")
    return T


def find_initial_temp_variance(costs: list, K: float = 5.0) -> float:
    """
    Estimate T₀ from variance of initial cost samples.

    Formula: T₀ = K · σ

    Quick approximation method (less robust than acceptance ratio).

    Args:
        costs: Sample of fitness values
        K: Scaling constant (typically 5-10)

    Returns:
        Estimated T₀
    """
    if len(costs) < 2:
        return 100.0  # Default fallback

    std_dev = np.std(costs)
    return K * std_dev


# =============================================================================
# REHEATING AND RESTART STRATEGIES
# =============================================================================


def should_reheat(
    stagnation_counter: int,
    stagnation_threshold: int,
    reheat_count: int,
    max_reheats: int,
) -> bool:
    """
    Determine if reheating should be triggered.

    Triggers when:
    - No improvement for stagnation_threshold iterations
    - Have not exceeded max_reheats

    Args:
        stagnation_counter: Iterations since last improvement
        stagnation_threshold: Threshold for triggering reheat
        reheat_count: Number of reheats so far
        max_reheats: Maximum allowed reheats

    Returns:
        True if should reheat
    """
    return stagnation_counter >= stagnation_threshold and reheat_count < max_reheats


def calculate_reheat_temperature(
    best_cost: float,
    phase_transition_temp: float,
    initial_temp: float,
    final_temp: float,
    K: float = 0.5,
) -> float:
    """
    Calculate reheating temperature (RFC - Reheating as Function of Cost).

    Formula: T_new = K · C_best + T_phase_transition

    Args:
        best_cost: Current best fitness value
        phase_transition_temp: Temperature at max specific heat
        initial_temp: Original T₀ (for bounds)
        final_temp: Final temperature (for bounds)
        K: Scaling constant (default: 0.5)

    Returns:
        Reheating temperature (clipped to reasonable bounds)
    """
    T_reheat = K * best_cost + phase_transition_temp

    # Clip to reasonable range
    T_reheat = np.clip(T_reheat, final_temp * 10, initial_temp * 0.5)

    return T_reheat


# =============================================================================
# ADAPTIVE MARKOV CHAIN LENGTH
# =============================================================================


def adaptive_markov_length(
    base_length: int,
    costs_at_temp: list,
    min_length: int = 50,
    max_length: int = 500,
) -> int:
    """
    Calculate adaptive Markov chain length based on fitness variance.

    High variance regions (rugged landscape) → longer chain.
    Low variance regions (smooth landscape) → shorter chain.

    Args:
        base_length: Base number of iterations (e.g., 100)
        costs_at_temp: Fitness values at current temperature
        min_length: Minimum chain length
        max_length: Maximum chain length

    Returns:
        Adaptive chain length

    Example:
        >>> costs_high_var = [0.5, 0.8, 0.3, 0.9, 0.2]
        >>> L = adaptive_markov_length(100, costs_high_var)
        >>> print(f"High variance → longer chain: {L}")
        >>>
        >>> costs_low_var = [0.5, 0.51, 0.49, 0.50, 0.52]
        >>> L = adaptive_markov_length(100, costs_low_var)
        >>> print(f"Low variance → shorter chain: {L}")
    """
    if len(costs_at_temp) < 2:
        return base_length

    # Calculate variance
    variance = np.var(costs_at_temp)

    # High variance → longer chain
    # Cap variance factor at 2.0 (max 2x base length)
    variance_factor = min(variance * 100, 2.0)

    L_adaptive = int(base_length * variance_factor)

    return int(np.clip(L_adaptive, min_length, max_length))


# =============================================================================
# COOLING SCHEDULE METRICS AND ANALYSIS
# =============================================================================


def track_phase_transition(
    costs_at_temp: list,
    current_temperature: float,
    max_variance: float,
    phase_transition_temp: float,
) -> tuple:
    """
    Track phase transition temperature (max specific heat).

    The temperature at which variance is highest indicates the
    "critical temperature" where the landscape is most rugged.

    Args:
        costs_at_temp: Fitness values at current temperature
        current_temperature: Current T
        max_variance: Current maximum variance observed
        phase_transition_temp: Current phase transition temperature

    Returns:
        Tuple of (new_max_variance, new_phase_transition_temp)
    """
    if len(costs_at_temp) < 10:
        return max_variance, phase_transition_temp

    variance = np.var(costs_at_temp)

    if variance > max_variance:
        return variance, current_temperature
    else:
        return max_variance, phase_transition_temp


def calculate_cooling_statistics(
    temperature_history: list,
    fitness_history: list,
) -> dict:
    """
    Calculate statistics about cooling schedule performance.

    Args:
        temperature_history: List of temperatures over time
        fitness_history: List of best fitness values over time

    Returns:
        Dict with cooling statistics
    """
    if len(temperature_history) < 2:
        return {}

    stats = {
        "initial_temp": temperature_history[0],
        "final_temp": temperature_history[-1],
        "mean_temp": np.mean(temperature_history),
        "temp_std": np.std(temperature_history),
        "cooling_rate_avg": np.mean(
            [
                temperature_history[i] / temperature_history[i + 1]
                for i in range(len(temperature_history) - 1)
                if temperature_history[i + 1] > 0
            ]
        ),
        "fitness_improvement": fitness_history[-1] - fitness_history[0] if fitness_history else 0,
        "fitness_variance": np.var(fitness_history) if fitness_history else 0,
    }

    return stats
