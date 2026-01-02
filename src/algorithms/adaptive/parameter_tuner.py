"""
Adaptive Parameter Tuning
==========================

Self-tuning parameters for optimization operators.

Provides parameter schedules that adapt based on:
- Search phase (exploration vs exploitation)
- Generation number
- Population diversity
- Convergence status

Created: 2026-01-02 (Week 4 Day 3)
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional

import numpy as np


class ParameterSchedule(Enum):
    """Parameter schedule types."""

    CONSTANT = "constant"  # Fixed value
    LINEAR = "linear"  # Linear decay/growth
    EXPONENTIAL = "exponential"  # Exponential decay/growth
    ADAPTIVE = "adaptive"  # Adapt based on search state
    COSINE = "cosine"  # Cosine annealing


class BaseParameterSchedule(ABC):
    """Base class for parameter schedules."""

    @abstractmethod
    def get_value(self, generation: int, max_generations: int, **kwargs) -> float:
        """
        Get parameter value for current generation.

        Args:
            generation: Current generation number
            max_generations: Maximum generations
            **kwargs: Additional state information

        Returns:
            Parameter value
        """
        pass


class ConstantSchedule(BaseParameterSchedule):
    """Constant parameter value."""

    def __init__(self, value: float):
        """Initialize with constant value."""
        self.value = value

    def get_value(self, generation: int, max_generations: int, **kwargs) -> float:
        """Return constant value."""
        return self.value


class LinearSchedule(BaseParameterSchedule):
    """Linear parameter schedule."""

    def __init__(self, start_value: float, end_value: float):
        """
        Initialize linear schedule.

        Args:
            start_value: Initial value at generation 0
            end_value: Final value at max_generations
        """
        self.start_value = start_value
        self.end_value = end_value

    def get_value(self, generation: int, max_generations: int, **kwargs) -> float:
        """Linear interpolation between start and end."""
        if max_generations <= 1:
            return self.start_value

        progress = generation / (max_generations - 1)
        progress = min(1.0, max(0.0, progress))  # Clamp to [0, 1]

        return self.start_value + progress * (self.end_value - self.start_value)


class ExponentialSchedule(BaseParameterSchedule):
    """Exponential parameter schedule."""

    def __init__(self, start_value: float, end_value: float, decay_rate: Optional[float] = None):
        """
        Initialize exponential schedule.

        Args:
            start_value: Initial value
            end_value: Final value
            decay_rate: Decay rate (None = auto-calculate from start/end)
        """
        self.start_value = start_value
        self.end_value = end_value

        if decay_rate is None:
            # Calculate decay rate to reach end_value
            if start_value > 0 and end_value > 0:
                self.decay_rate = (end_value / start_value) ** (1.0 / 100)  # Default 100 steps
            else:
                self.decay_rate = 0.95
        else:
            self.decay_rate = decay_rate

    def get_value(self, generation: int, max_generations: int, **kwargs) -> float:
        """Exponential decay/growth."""
        return self.start_value * (self.decay_rate**generation)


class CosineSchedule(BaseParameterSchedule):
    """Cosine annealing schedule."""

    def __init__(self, start_value: float, end_value: float, n_cycles: int = 1):
        """
        Initialize cosine schedule.

        Args:
            start_value: Initial value
            end_value: Final value (minimum)
            n_cycles: Number of cosine cycles
        """
        self.start_value = start_value
        self.end_value = end_value
        self.n_cycles = n_cycles

    def get_value(self, generation: int, max_generations: int, **kwargs) -> float:
        """Cosine annealing."""
        if max_generations <= 1:
            return self.start_value

        progress = generation / (max_generations - 1)
        cosine_term = 0.5 * (1 + np.cos(np.pi * progress * self.n_cycles))

        return self.end_value + (self.start_value - self.end_value) * cosine_term


class AdaptiveSchedule(BaseParameterSchedule):
    """Adaptive schedule based on search state."""

    def __init__(
        self,
        start_value: float,
        end_value: float,
        diversity_weight: float = 0.5,
        convergence_weight: float = 0.5,
    ):
        """
        Initialize adaptive schedule.

        Args:
            start_value: Value for high diversity/low convergence
            end_value: Value for low diversity/high convergence
            diversity_weight: Weight for diversity factor
            convergence_weight: Weight for convergence factor
        """
        self.start_value = start_value
        self.end_value = end_value
        self.diversity_weight = diversity_weight
        self.convergence_weight = convergence_weight

    def get_value(self, generation: int, max_generations: int, **kwargs) -> float:
        """
        Adapt based on diversity and convergence.

        Args:
            generation: Current generation
            max_generations: Max generations
            **kwargs: Should include 'diversity' and 'convergence_rate'

        Returns:
            Adapted parameter value
        """
        # Default linear fallback
        progress = generation / max(1, max_generations - 1)

        # Get state information
        diversity = kwargs.get("diversity", 1.0 - progress)  # Default: decrease with time
        convergence_rate = kwargs.get("convergence_rate", progress)  # Default: increase with time

        # Normalize to [0, 1]
        diversity = max(0.0, min(1.0, diversity))
        convergence_rate = max(0.0, min(1.0, convergence_rate))

        # Calculate adaptation factor
        # High diversity or low convergence → use start_value (exploration)
        # Low diversity or high convergence → use end_value (exploitation)
        exploration_factor = self.diversity_weight * diversity + self.convergence_weight * (
            1.0 - convergence_rate
        )
        exploration_factor /= self.diversity_weight + self.convergence_weight

        return self.end_value + (self.start_value - self.end_value) * exploration_factor


class AdaptiveParameterTuner:
    """
    Adaptive parameter tuning for optimization operators.

    Manages parameter schedules for multiple parameters.

    Example:
        >>> tuner = AdaptiveParameterTuner()
        >>> tuner.add_parameter("mutation_rate", LinearSchedule(0.3, 0.05))
        >>> tuner.add_parameter("temperature", ExponentialSchedule(1000.0, 0.1))
        >>>
        >>> # Get current values
        >>> params = tuner.get_parameters(generation=10, max_generations=100)
        >>> print(params["mutation_rate"])  # 0.275
    """

    def __init__(self):
        """Initialize parameter tuner."""
        self.schedules: Dict[str, BaseParameterSchedule] = {}

    def add_parameter(self, name: str, schedule: BaseParameterSchedule) -> None:
        """
        Add parameter with schedule.

        Args:
            name: Parameter name
            schedule: Parameter schedule
        """
        self.schedules[name] = schedule

    def add_constant(self, name: str, value: float) -> None:
        """Add constant parameter."""
        self.schedules[name] = ConstantSchedule(value)

    def add_linear(self, name: str, start_value: float, end_value: float) -> None:
        """Add linear schedule."""
        self.schedules[name] = LinearSchedule(start_value, end_value)

    def add_exponential(
        self,
        name: str,
        start_value: float,
        end_value: float,
        decay_rate: Optional[float] = None,
    ) -> None:
        """Add exponential schedule."""
        self.schedules[name] = ExponentialSchedule(start_value, end_value, decay_rate)

    def add_cosine(
        self,
        name: str,
        start_value: float,
        end_value: float,
        n_cycles: int = 1,
    ) -> None:
        """Add cosine annealing schedule."""
        self.schedules[name] = CosineSchedule(start_value, end_value, n_cycles)

    def add_adaptive(
        self,
        name: str,
        start_value: float,
        end_value: float,
        diversity_weight: float = 0.5,
        convergence_weight: float = 0.5,
    ) -> None:
        """Add adaptive schedule."""
        self.schedules[name] = AdaptiveSchedule(
            start_value,
            end_value,
            diversity_weight,
            convergence_weight,
        )

    def get_parameter(self, name: str, generation: int, max_generations: int, **kwargs) -> float:
        """
        Get single parameter value.

        Args:
            name: Parameter name
            generation: Current generation
            max_generations: Maximum generations
            **kwargs: Additional state information

        Returns:
            Parameter value

        Raises:
            KeyError: If parameter not registered
        """
        if name not in self.schedules:
            raise KeyError(f"Parameter '{name}' not registered")

        return self.schedules[name].get_value(generation, max_generations, **kwargs)

    def get_parameters(self, generation: int, max_generations: int, **kwargs) -> Dict[str, float]:
        """
        Get all parameter values.

        Args:
            generation: Current generation
            max_generations: Maximum generations
            **kwargs: Additional state information

        Returns:
            Dict mapping parameter names to values
        """
        return {
            name: schedule.get_value(generation, max_generations, **kwargs)
            for name, schedule in self.schedules.items()
        }

    def remove_parameter(self, name: str) -> None:
        """Remove parameter."""
        if name in self.schedules:
            del self.schedules[name]

    def reset(self) -> None:
        """Clear all parameters."""
        self.schedules.clear()

    def list_parameters(self) -> list[str]:
        """List all registered parameters."""
        return list(self.schedules.keys())
