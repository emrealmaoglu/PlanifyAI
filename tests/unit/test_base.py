"""
Unit tests for Optimizer abstract base class
"""
import pytest
from abc import ABC
from src.algorithms.base import Optimizer
from src.algorithms.building import Building, BuildingType
from src.algorithms.solution import Solution


class ConcreteOptimizer(Optimizer):
    """Concrete implementation of Optimizer for testing"""

    def optimize(self):
        """Dummy optimize implementation"""
        return {
            "best_solution": None,
            "fitness": 0.0,
            "statistics": self.stats,
            "convergence": [],
        }

    def evaluate_solution(self, solution):
        """Dummy evaluate implementation"""
        self.stats["evaluations"] += 1
        return 0.5


class TestOptimizerAbstractClass:
    """Test Optimizer abstract class behavior"""

    def test_optimizer_is_abstract(self):
        """Test that Optimizer cannot be instantiated directly"""
        buildings = [Building("b1", BuildingType.LIBRARY, 5000.0, 3)]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        config = {}

        with pytest.raises(TypeError):
            # Should fail because optimize() and evaluate_solution() are abstract
            Optimizer(buildings, bounds, config)

    def test_optimizer_can_be_subclassed(self):
        """Test that Optimizer can be subclassed"""
        buildings = [Building("b1", BuildingType.LIBRARY, 5000.0, 3)]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        config = {}

        optimizer = ConcreteOptimizer(buildings, bounds, config)
        assert isinstance(optimizer, Optimizer)
        assert isinstance(optimizer, ABC)


class TestOptimizerInitialization:
    """Test Optimizer initialization"""

    def test_optimizer_initialization(self):
        """Test optimizer initialization with valid parameters"""
        buildings = [
            Building("b1", BuildingType.LIBRARY, 5000.0, 3),
            Building("b2", BuildingType.EDUCATIONAL, 6000.0, 4),
        ]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        config = {"max_iterations": 100, "temperature": 1.0}

        optimizer = ConcreteOptimizer(buildings, bounds, config)

        assert optimizer.buildings == buildings
        assert optimizer.bounds == bounds
        assert optimizer.config == config

    def test_optimizer_initial_stats(self):
        """Test optimizer initial statistics"""
        buildings = [Building("b1", BuildingType.LIBRARY, 5000.0, 3)]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        config = {}

        optimizer = ConcreteOptimizer(buildings, bounds, config)

        assert optimizer.stats["iterations"] == 0
        assert optimizer.stats["evaluations"] == 0
        assert optimizer.stats["best_fitness"] == float("-inf")
        assert optimizer.stats["convergence_history"] == []


class TestOptimizerStatsTracking:
    """Test Optimizer statistics tracking"""

    def test_optimizer_log_iteration(self):
        """Test logging iteration progress"""
        buildings = [Building("b1", BuildingType.LIBRARY, 5000.0, 3)]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        config = {}

        optimizer = ConcreteOptimizer(buildings, bounds, config)

        optimizer._log_iteration(1, 0.5)
        assert optimizer.stats["iterations"] == 1
        assert optimizer.stats["best_fitness"] == 0.5
        assert len(optimizer.stats["convergence_history"]) == 1
        assert optimizer.stats["convergence_history"][0] == 0.5

        optimizer._log_iteration(2, 0.7)
        assert optimizer.stats["iterations"] == 2
        assert optimizer.stats["best_fitness"] == 0.7
        assert len(optimizer.stats["convergence_history"]) == 2
        assert optimizer.stats["convergence_history"][1] == 0.7

    def test_optimizer_evaluate_increments_evaluations(self):
        """Test that evaluate_solution increments evaluation count"""
        buildings = [Building("b1", BuildingType.LIBRARY, 5000.0, 3)]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        config = {}

        optimizer = ConcreteOptimizer(buildings, bounds, config)
        solution = Solution({"b1": (100.0, 100.0)})

        assert optimizer.stats["evaluations"] == 0
        optimizer.evaluate_solution(solution)
        assert optimizer.stats["evaluations"] == 1
        optimizer.evaluate_solution(solution)
        assert optimizer.stats["evaluations"] == 2

    def test_optimizer_optimize_returns_dict(self):
        """Test that optimize returns expected dict structure"""
        buildings = [Building("b1", BuildingType.LIBRARY, 5000.0, 3)]
        bounds = (0.0, 0.0, 1000.0, 1000.0)
        config = {}

        optimizer = ConcreteOptimizer(buildings, bounds, config)
        result = optimizer.optimize()

        assert isinstance(result, dict)
        assert "best_solution" in result
        assert "fitness" in result
        assert "statistics" in result
        assert "convergence" in result
