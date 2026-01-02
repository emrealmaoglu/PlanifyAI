"""
Adaptive Operator Selector
===========================

Intelligently selects operators based on performance tracking.

Integrates credit assignment with operator registry for runtime selection.

Created: 2026-01-02 (Week 4 Day 3)
"""

from enum import Enum
from typing import Dict, Optional

import numpy as np

from ..operators.base import (
    CrossoverOperator,
    MutationOperator,
    PerturbationOperator,
    SelectionOperator,
)
from ..operators.registry import OperatorRegistry
from .credit_assignment import CreditAssignment


class SelectionStrategy(Enum):
    """Operator selection strategies."""

    UNIFORM = "uniform"  # Equal probability
    GREEDY = "greedy"  # Best operator only
    ADAPTIVE_PURSUIT = "adaptive_pursuit"  # Probability matching
    UCB = "ucb"  # Upper Confidence Bound
    SOFTMAX = "softmax"  # Boltzmann selection


class AdaptiveOperatorSelector:
    """
    Adaptive operator selector with performance tracking.

    Automatically selects best operators based on historical performance.

    Example:
        >>> from src.algorithms.operators.registry import DEFAULT_REGISTRY
        >>> selector = AdaptiveOperatorSelector(DEFAULT_REGISTRY)
        >>> selector.register_mutation("gaussian")
        >>> selector.register_mutation("swap")
        >>>
        >>> # Use operators
        >>> mutation = selector.select_mutation()
        >>> mutated = mutation.mutate(solution, buildings, bounds)
        >>>
        >>> # Update credit
        >>> improvement = new_fitness - old_fitness
        >>> selector.update_mutation_credit("gaussian", improvement, success=True)
    """

    def __init__(
        self,
        registry: OperatorRegistry,
        strategy: SelectionStrategy = SelectionStrategy.ADAPTIVE_PURSUIT,
        min_probability: float = 0.05,
        exploration_rate: float = 0.1,
    ):
        """
        Initialize adaptive operator selector.

        Args:
            registry: Operator registry for instantiation
            strategy: Default selection strategy
            min_probability: Minimum selection probability
            exploration_rate: Probability of random exploration
        """
        self.registry = registry
        self.strategy = strategy

        # Credit assignment for each operator type
        self.perturbation_credit = CreditAssignment(
            min_probability=min_probability,
            exploration_rate=exploration_rate,
        )
        self.mutation_credit = CreditAssignment(
            min_probability=min_probability,
            exploration_rate=exploration_rate,
        )
        self.crossover_credit = CreditAssignment(
            min_probability=min_probability,
            exploration_rate=exploration_rate,
        )
        self.selection_credit = CreditAssignment(
            min_probability=min_probability,
            exploration_rate=exploration_rate,
        )

        # Registered operators and their parameters
        self._perturbations: Dict[str, Dict] = {}
        self._mutations: Dict[str, Dict] = {}
        self._crossovers: Dict[str, Dict] = {}
        self._selections: Dict[str, Dict] = {}

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def register_perturbation(self, name: str, **kwargs) -> None:
        """Register perturbation operator with default parameters."""
        self._perturbations[name] = kwargs
        self.perturbation_credit.register_operator(name)

    def register_mutation(self, name: str, **kwargs) -> None:
        """Register mutation operator with default parameters."""
        self._mutations[name] = kwargs
        self.mutation_credit.register_operator(name)

    def register_crossover(self, name: str, **kwargs) -> None:
        """Register crossover operator with default parameters."""
        self._crossovers[name] = kwargs
        self.crossover_credit.register_operator(name)

    def register_selection(self, name: str, **kwargs) -> None:
        """Register selection operator with default parameters."""
        self._selections[name] = kwargs
        self.selection_credit.register_operator(name)

    # =========================================================================
    # SELECTION
    # =========================================================================

    def select_perturbation(
        self,
        strategy: Optional[SelectionStrategy] = None,
        **override_kwargs,
    ) -> tuple[str, PerturbationOperator]:
        """
        Select perturbation operator adaptively.

        Args:
            strategy: Selection strategy (None = use default)
            **override_kwargs: Override default operator parameters

        Returns:
            Tuple of (operator_name, operator_instance)
        """
        if not self._perturbations:
            raise ValueError("No perturbation operators registered")

        strategy = strategy or self.strategy
        probs = self.perturbation_credit.get_selection_probabilities(strategy=strategy.value)

        # Select operator
        names = list(probs.keys())
        probabilities = list(probs.values())
        selected_name = np.random.choice(names, p=probabilities)

        # Get operator with parameters
        params = {**self._perturbations[selected_name], **override_kwargs}
        operator = self.registry.get_perturbation(selected_name, **params)

        return selected_name, operator

    def select_mutation(
        self,
        strategy: Optional[SelectionStrategy] = None,
        **override_kwargs,
    ) -> tuple[str, MutationOperator]:
        """Select mutation operator adaptively."""
        if not self._mutations:
            raise ValueError("No mutation operators registered")

        strategy = strategy or self.strategy
        probs = self.mutation_credit.get_selection_probabilities(strategy=strategy.value)

        names = list(probs.keys())
        probabilities = list(probs.values())
        selected_name = np.random.choice(names, p=probabilities)

        params = {**self._mutations[selected_name], **override_kwargs}
        operator = self.registry.get_mutation(selected_name, **params)

        return selected_name, operator

    def select_crossover(
        self,
        strategy: Optional[SelectionStrategy] = None,
        **override_kwargs,
    ) -> tuple[str, CrossoverOperator]:
        """Select crossover operator adaptively."""
        if not self._crossovers:
            raise ValueError("No crossover operators registered")

        strategy = strategy or self.strategy
        probs = self.crossover_credit.get_selection_probabilities(strategy=strategy.value)

        names = list(probs.keys())
        probabilities = list(probs.values())
        selected_name = np.random.choice(names, p=probabilities)

        params = {**self._crossovers[selected_name], **override_kwargs}
        operator = self.registry.get_crossover(selected_name, **params)

        return selected_name, operator

    def select_selection(
        self,
        strategy: Optional[SelectionStrategy] = None,
        **override_kwargs,
    ) -> tuple[str, SelectionOperator]:
        """Select selection operator adaptively."""
        if not self._selections:
            raise ValueError("No selection operators registered")

        strategy = strategy or self.strategy
        probs = self.selection_credit.get_selection_probabilities(strategy=strategy.value)

        names = list(probs.keys())
        probabilities = list(probs.values())
        selected_name = np.random.choice(names, p=probabilities)

        params = {**self._selections[selected_name], **override_kwargs}
        operator = self.registry.get_selection(selected_name, **params)

        return selected_name, operator

    # =========================================================================
    # CREDIT UPDATE
    # =========================================================================

    def update_perturbation_credit(
        self,
        operator_name: str,
        improvement: float,
        success: bool,
    ) -> None:
        """Update perturbation operator credit."""
        self.perturbation_credit.update(operator_name, improvement, success)

    def update_mutation_credit(
        self,
        operator_name: str,
        improvement: float,
        success: bool,
    ) -> None:
        """Update mutation operator credit."""
        self.mutation_credit.update(operator_name, improvement, success)

    def update_crossover_credit(
        self,
        operator_name: str,
        improvement: float,
        success: bool,
    ) -> None:
        """Update crossover operator credit."""
        self.crossover_credit.update(operator_name, improvement, success)

    def update_selection_credit(
        self,
        operator_name: str,
        improvement: float,
        success: bool,
    ) -> None:
        """Update selection operator credit."""
        self.selection_credit.update(operator_name, improvement, success)

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_perturbation_statistics(self) -> Dict:
        """Get perturbation operator statistics."""
        return self.perturbation_credit.get_statistics()

    def get_mutation_statistics(self) -> Dict:
        """Get mutation operator statistics."""
        return self.mutation_credit.get_statistics()

    def get_crossover_statistics(self) -> Dict:
        """Get crossover operator statistics."""
        return self.crossover_credit.get_statistics()

    def get_selection_statistics(self) -> Dict:
        """Get selection operator statistics."""
        return self.selection_credit.get_statistics()

    def get_all_statistics(self) -> Dict:
        """Get statistics for all operator types."""
        return {
            "perturbation": self.get_perturbation_statistics(),
            "mutation": self.get_mutation_statistics(),
            "crossover": self.get_crossover_statistics(),
            "selection": self.get_selection_statistics(),
        }

    def get_selection_probabilities(self) -> Dict:
        """Get current selection probabilities for all operators."""
        strategy = self.strategy.value
        return {
            "perturbation": (
                self.perturbation_credit.get_selection_probabilities(strategy=strategy)
                if self._perturbations
                else {}
            ),
            "mutation": (
                self.mutation_credit.get_selection_probabilities(strategy=strategy)
                if self._mutations
                else {}
            ),
            "crossover": (
                self.crossover_credit.get_selection_probabilities(strategy=strategy)
                if self._crossovers
                else {}
            ),
            "selection": (
                self.selection_credit.get_selection_probabilities(strategy=strategy)
                if self._selections
                else {}
            ),
        }

    def reset(self) -> None:
        """Reset all operator credits."""
        self.perturbation_credit.reset()
        self.mutation_credit.reset()
        self.crossover_credit.reset()
        self.selection_credit.reset()
