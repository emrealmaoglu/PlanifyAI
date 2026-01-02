"""
Operator Credit Assignment
===========================

Tracks operator performance and assigns credit for improvements.

Design: Multi-Armed Bandit inspired credit assignment
- Tracks success rate and improvement magnitude
- Uses sliding window for recent performance
- Exponential moving average for long-term trends

Created: 2026-01-02 (Week 4 Day 3)
"""

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np


@dataclass
class OperatorCredit:
    """
    Credit tracking for a single operator.

    Attributes:
        name: Operator name
        uses: Number of times operator was used
        successes: Number of successful applications
        total_improvement: Cumulative fitness improvement
        recent_improvements: Sliding window of recent improvements
        ema_improvement: Exponential moving average of improvement
        success_rate: Success rate (0-1)
        avg_improvement: Average improvement per use
    """

    name: str
    uses: int = 0
    successes: int = 0
    total_improvement: float = 0.0
    recent_improvements: List[float] = field(default_factory=list)
    ema_improvement: float = 0.0

    def __post_init__(self):
        """Initialize computed fields."""
        if not self.recent_improvements:
            self.recent_improvements = []

    @property
    def success_rate(self) -> float:
        """Success rate (0-1)."""
        if self.uses == 0:
            return 0.5  # Neutral prior
        return self.successes / self.uses

    @property
    def avg_improvement(self) -> float:
        """Average improvement per use."""
        if self.uses == 0:
            return 0.0
        return self.total_improvement / self.uses

    def update(
        self,
        improvement: float,
        success: bool,
        window_size: int = 50,
        ema_alpha: float = 0.1,
    ) -> None:
        """
        Update credit based on operator application result.

        Args:
            improvement: Fitness improvement (can be negative)
            success: Whether operator was successful (improvement > 0)
            window_size: Size of sliding window for recent improvements
            ema_alpha: EMA smoothing factor (0-1, higher = more weight on recent)
        """
        self.uses += 1
        if success:
            self.successes += 1

        self.total_improvement += improvement

        # Update recent improvements (sliding window)
        self.recent_improvements.append(improvement)
        if len(self.recent_improvements) > window_size:
            self.recent_improvements.pop(0)

        # Update EMA
        if self.uses == 1:
            self.ema_improvement = improvement
        else:
            self.ema_improvement = ema_alpha * improvement + (1 - ema_alpha) * self.ema_improvement


class CreditAssignment:
    """
    Credit assignment system for adaptive operator selection.

    Tracks performance of multiple operators and provides selection probabilities.

    Design inspired by:
    - Multi-Armed Bandit algorithms (UCB, Thompson Sampling)
    - Adaptive Pursuit (Thierens, 2005)
    - Probability Matching (Goldberg, 1990)

    Example:
        >>> credit = CreditAssignment()
        >>> credit.update("gaussian", improvement=0.05, success=True)
        >>> credit.update("swap", improvement=-0.01, success=False)
        >>> probs = credit.get_selection_probabilities()
        >>> print(probs)  # {'gaussian': 0.7, 'swap': 0.3}
    """

    def __init__(
        self,
        min_probability: float = 0.05,
        max_probability: float = 0.95,
        exploration_rate: float = 0.1,
    ):
        """
        Initialize credit assignment system.

        Args:
            min_probability: Minimum selection probability (exploration)
            max_probability: Maximum selection probability (prevent lock-in)
            exploration_rate: Probability of random selection (ε-greedy)
        """
        self.credits: Dict[str, OperatorCredit] = {}
        self.min_probability = min_probability
        self.max_probability = max_probability
        self.exploration_rate = exploration_rate

    def register_operator(self, name: str) -> None:
        """Register a new operator."""
        if name not in self.credits:
            self.credits[name] = OperatorCredit(name=name)

    def update(
        self,
        operator_name: str,
        improvement: float,
        success: bool,
        window_size: int = 50,
        ema_alpha: float = 0.1,
    ) -> None:
        """
        Update operator credit based on application result.

        Args:
            operator_name: Name of operator that was used
            improvement: Fitness improvement (can be negative)
            success: Whether operator was successful
            window_size: Sliding window size
            ema_alpha: EMA smoothing factor
        """
        if operator_name not in self.credits:
            self.register_operator(operator_name)

        self.credits[operator_name].update(improvement, success, window_size, ema_alpha)

    def get_selection_probabilities(
        self,
        strategy: str = "adaptive_pursuit",
        temperature: float = 1.0,
    ) -> Dict[str, float]:
        """
        Calculate selection probabilities for each operator.

        Args:
            strategy: Selection strategy
                - "uniform": Equal probabilities
                - "greedy": Best operator gets all probability
                - "adaptive_pursuit": Probability matching with learning rate
                - "ucb": Upper Confidence Bound
                - "softmax": Boltzmann selection
            temperature: Temperature parameter for softmax (higher = more exploration)

        Returns:
            Dict mapping operator names to selection probabilities
        """
        if not self.credits:
            return {}

        if strategy == "uniform":
            return self._uniform_probabilities()
        elif strategy == "greedy":
            return self._greedy_probabilities()
        elif strategy == "adaptive_pursuit":
            return self._adaptive_pursuit_probabilities()
        elif strategy == "ucb":
            return self._ucb_probabilities()
        elif strategy == "softmax":
            return self._softmax_probabilities(temperature)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _uniform_probabilities(self) -> Dict[str, float]:
        """Equal probability for all operators."""
        n = len(self.credits)
        return {name: 1.0 / n for name in self.credits.keys()}

    def _greedy_probabilities(self) -> Dict[str, float]:
        """Best operator gets maximum probability, others minimum."""
        # Find best operator (highest EMA improvement)
        best_name = max(self.credits.keys(), key=lambda name: self.credits[name].ema_improvement)

        probs = {name: self.min_probability for name in self.credits.keys()}
        probs[best_name] = self.max_probability

        # Normalize
        total = sum(probs.values())
        return {name: p / total for name, p in probs.items()}

    def _adaptive_pursuit_probabilities(self, learning_rate: float = 0.1) -> Dict[str, float]:
        """
        Adaptive Pursuit: Gradually increase probability of best operators.

        Based on Thierens (2005) "Adaptive Pursuit".
        """
        # Find best operator
        best_name = max(self.credits.keys(), key=lambda name: self.credits[name].ema_improvement)

        # Initialize probabilities if first call
        if not hasattr(self, "_pursuit_probs"):
            n = len(self.credits)
            self._pursuit_probs = {name: 1.0 / n for name in self.credits.keys()}

        # Update probabilities (pursuit rule)
        for name in self.credits.keys():
            if name == best_name:
                # Increase probability of best operator
                target = self.max_probability
            else:
                # Decrease probability of others
                target = self.min_probability / (len(self.credits) - 1)

            # Move towards target with learning rate
            self._pursuit_probs[name] += learning_rate * (target - self._pursuit_probs[name])

        # Normalize
        total = sum(self._pursuit_probs.values())
        return {name: p / total for name, p in self._pursuit_probs.items()}

    def _ucb_probabilities(self, c: float = 2.0) -> Dict[str, float]:
        """
        Upper Confidence Bound (UCB1).

        Balances exploitation and exploration via confidence intervals.

        Args:
            c: Exploration constant (higher = more exploration)
        """
        total_uses = sum(credit.uses for credit in self.credits.values())

        if total_uses == 0:
            return self._uniform_probabilities()

        # Calculate UCB scores
        ucb_scores = {}
        for name, credit in self.credits.items():
            if credit.uses == 0:
                ucb_scores[name] = float("inf")  # Unexplored operators get priority
            else:
                exploration_bonus = c * np.sqrt(np.log(total_uses) / credit.uses)
                ucb_scores[name] = credit.avg_improvement + exploration_bonus

        # Convert to probabilities via softmax
        scores = np.array(list(ucb_scores.values()))
        scores = scores - scores.max()  # Numerical stability
        exp_scores = np.exp(scores)
        probs = exp_scores / exp_scores.sum()

        return {name: float(p) for name, p in zip(ucb_scores.keys(), probs)}

    def _softmax_probabilities(self, temperature: float = 1.0) -> Dict[str, float]:
        """
        Boltzmann/Softmax selection.

        Higher temperature = more exploration.
        Lower temperature = more exploitation.

        Args:
            temperature: Temperature parameter (T > 0)
        """
        # Get EMA improvements
        improvements = np.array([credit.ema_improvement for credit in self.credits.values()])

        # Softmax with temperature
        scaled = improvements / temperature
        scaled = scaled - scaled.max()  # Numerical stability
        exp_scaled = np.exp(scaled)
        probs = exp_scaled / exp_scaled.sum()

        return {name: float(p) for name, p in zip(self.credits.keys(), probs)}

    def get_best_operator(self) -> str:
        """Get operator with highest average improvement."""
        if not self.credits:
            raise ValueError("No operators registered")

        return max(self.credits.keys(), key=lambda name: self.credits[name].ema_improvement)

    def get_statistics(self) -> Dict[str, Dict]:
        """
        Get statistics for all operators.

        Returns:
            Dict mapping operator names to their statistics
        """
        return {
            name: {
                "uses": credit.uses,
                "successes": credit.successes,
                "success_rate": credit.success_rate,
                "total_improvement": credit.total_improvement,
                "avg_improvement": credit.avg_improvement,
                "ema_improvement": credit.ema_improvement,
                "recent_avg": (
                    np.mean(credit.recent_improvements) if credit.recent_improvements else 0.0
                ),
            }
            for name, credit in self.credits.items()
        }

    def reset(self) -> None:
        """Reset all credits."""
        self.credits.clear()
        if hasattr(self, "_pursuit_probs"):
            delattr(self, "_pursuit_probs")
