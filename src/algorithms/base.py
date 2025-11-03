"""
Base Classes for Optimizers
============================

Abstract base classes for optimization algorithms.

Created: 2025-11-03
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from .building import Building
from .solution import Solution


class Optimizer(ABC):
    """
    Abstract base class for optimization algorithms
    
    All optimizers (H-SAGA, NSGA-III, etc.) should inherit from this.
    """
    
    def __init__(
        self,
        buildings: List[Building],
        bounds: tuple,
        config: Dict
    ):
        """
        Initialize optimizer
        
        Args:
            buildings: List of Building objects to place
            bounds: Area bounds (x_min, y_min, x_max, y_max)
            config: Algorithm configuration dict
        """
        self.buildings = buildings
        self.bounds = bounds
        self.config = config
        
        # Statistics tracking
        self.stats = {
            'iterations': 0,
            'evaluations': 0,
            'best_fitness': float('-inf'),
            'convergence_history': []
        }
    
    @abstractmethod
    def optimize(self) -> Dict:
        """
        Run optimization
        
        Returns:
            Dict with results:
                - best_solution: Best Solution found
                - fitness: Best fitness score
                - statistics: Algorithm statistics
                - convergence: Convergence history
        """
        pass
    
    @abstractmethod
    def evaluate_solution(self, solution: Solution) -> float:
        """
        Evaluate fitness of a solution
        
        Args:
            solution: Solution to evaluate
            
        Returns:
            Fitness score
        """
        pass
    
    def _log_iteration(self, iteration: int, best_fitness: float):
        """Log iteration progress"""
        self.stats['iterations'] = iteration
        self.stats['best_fitness'] = best_fitness
        self.stats['convergence_history'].append(best_fitness)
