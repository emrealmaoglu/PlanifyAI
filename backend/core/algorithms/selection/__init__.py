"""
Selection Operators for Evolutionary Algorithms

Extracted from monolithic hsaga.py to improve modularity and testability.

Available Selectors:
- TournamentSelector: Binary/k-way tournament selection
- DominanceSelector: Pareto dominance-based selection (future)
"""

from .tournament import BinaryTournamentSelector, TournamentSelector

__all__ = ["TournamentSelector", "BinaryTournamentSelector"]
