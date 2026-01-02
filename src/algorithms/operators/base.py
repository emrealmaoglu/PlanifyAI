"""
Base Operator Classes
=====================

Abstract base classes for all optimization operators.

Design Pattern: Strategy Pattern
Each operator type (mutation, crossover, etc.) has a common interface,
allowing operators to be swapped at runtime.

Created: 2026-01-02 (Week 4 Day 3)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Type

from ..building import Building
from ..solution import Solution


class PerturbationOperator(ABC):
    """
    Base class for SA perturbation operators.

    Perturbation operators generate neighbor solutions for Simulated Annealing.
    """

    @abstractmethod
    def perturb(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
        temperature: float,
    ) -> Solution:
        """
        Generate neighbor solution.

        Args:
            solution: Current solution
            buildings: List of buildings (for radius lookup)
            bounds: Site boundaries
            temperature: Current SA temperature

        Returns:
            New solution (neighbor)
        """
        pass

    @property
    def name(self) -> str:
        """Operator name for logging/registry."""
        return self.__class__.__name__


class MutationOperator(ABC):
    """
    Base class for GA mutation operators.

    Mutation operators introduce random changes to solutions.
    """

    @abstractmethod
    def mutate(
        self,
        solution: Solution,
        buildings: List[Building],
        bounds: Tuple[float, float, float, float],
    ) -> Solution:
        """
        Mutate solution (in-place).

        Args:
            solution: Solution to mutate
            buildings: List of buildings
            bounds: Site boundaries

        Returns:
            Mutated solution (same object)
        """
        pass

    @property
    def name(self) -> str:
        """Operator name for logging/registry."""
        return self.__class__.__name__


class CrossoverOperator(ABC):
    """
    Base class for GA crossover operators.

    Crossover operators combine two parent solutions to create offspring.
    """

    @abstractmethod
    def crossover(
        self,
        parent1: Solution,
        parent2: Solution,
    ) -> Tuple[Solution, Solution]:
        """
        Create offspring from two parents.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Tuple of two offspring solutions
        """
        pass

    @property
    def name(self) -> str:
        """Operator name for logging/registry."""
        return self.__class__.__name__


class SelectionOperator(ABC):
    """
    Base class for GA selection operators.

    Selection operators choose individuals for reproduction.
    """

    @abstractmethod
    def select(
        self,
        population: List[Solution],
        n_select: int = 1,
    ) -> List[Solution]:
        """
        Select individuals from population.

        Args:
            population: Current population (must have fitness)
            n_select: Number of individuals to select

        Returns:
            List of selected solutions (deep copies)
        """
        pass

    @property
    def name(self) -> str:
        """Operator name for logging/registry."""
        return self.__class__.__name__


class OperatorRegistry:
    """
    Registry for operators (Factory pattern).

    Allows operators to be registered and instantiated by name.

    Example:
        >>> registry = OperatorRegistry()
        >>> registry.register_mutation("gaussian", GaussianMutation)
        >>> op = registry.get_mutation("gaussian", sigma=30.0)
    """

    def __init__(self):
        """Initialize empty registries."""
        self._perturbations: Dict[str, Type[PerturbationOperator]] = {}
        self._mutations: Dict[str, Type[MutationOperator]] = {}
        self._crossovers: Dict[str, Type[CrossoverOperator]] = {}
        self._selections: Dict[str, Type[SelectionOperator]] = {}

    def register_perturbation(self, name: str, cls: Type[PerturbationOperator]) -> None:
        """Register perturbation operator."""
        self._perturbations[name] = cls

    def register_mutation(self, name: str, cls: Type[MutationOperator]) -> None:
        """Register mutation operator."""
        self._mutations[name] = cls

    def register_crossover(self, name: str, cls: Type[CrossoverOperator]) -> None:
        """Register crossover operator."""
        self._crossovers[name] = cls

    def register_selection(self, name: str, cls: Type[SelectionOperator]) -> None:
        """Register selection operator."""
        self._selections[name] = cls

    def get_perturbation(self, name: str, **kwargs) -> PerturbationOperator:
        """Get perturbation operator instance."""
        if name not in self._perturbations:
            raise ValueError(f"Perturbation '{name}' not registered")
        return self._perturbations[name](**kwargs)

    def get_mutation(self, name: str, **kwargs) -> MutationOperator:
        """Get mutation operator instance."""
        if name not in self._mutations:
            raise ValueError(f"Mutation '{name}' not registered")
        return self._mutations[name](**kwargs)

    def get_crossover(self, name: str, **kwargs) -> CrossoverOperator:
        """Get crossover operator instance."""
        if name not in self._crossovers:
            raise ValueError(f"Crossover '{name}' not registered")
        return self._crossovers[name](**kwargs)

    def get_selection(self, name: str, **kwargs) -> SelectionOperator:
        """Get selection operator instance."""
        if name not in self._selections:
            raise ValueError(f"Selection '{name}' not registered")
        return self._selections[name](**kwargs)

    def list_perturbations(self) -> List[str]:
        """List all registered perturbation operators."""
        return list(self._perturbations.keys())

    def list_mutations(self) -> List[str]:
        """List all registered mutation operators."""
        return list(self._mutations.keys())

    def list_crossovers(self) -> List[str]:
        """List all registered crossover operators."""
        return list(self._crossovers.keys())

    def list_selections(self) -> List[str]:
        """List all registered selection operators."""
        return list(self._selections.keys())
