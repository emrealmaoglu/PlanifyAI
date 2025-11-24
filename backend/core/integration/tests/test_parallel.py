from backend.core.integration.parallel import ParallelEvaluator
from backend.core.integration import IntegratedCampusProblem
from shapely.geometry import Polygon
import numpy as np
import pytest

def test_parallel_evaluator_init():
    problem = IntegratedCampusProblem(
        Polygon([(0,0),(500,0),(500,500),(0,500)]),
        n_buildings=10, objectives=['cost','road_access']
    )
    evaluator = ParallelEvaluator(problem, n_workers=2)
    assert evaluator.n_workers == 2

def test_parallel_evaluator_execution():
    problem = IntegratedCampusProblem(
        Polygon([(0,0),(500,0),(500,500),(0,500)]),
        n_buildings=10, objectives=['cost','road_access']
    )
    
    evaluator = ParallelEvaluator(problem, n_workers=2)
    X = np.random.rand(10, problem.n_var)
    X = X * (problem.xu - problem.xl) + problem.xl
    
    result = evaluator.evaluate(X)
    
    assert result['F'].shape == (10, 2)
    assert result['G'].shape[0] == 10

def test_parallel_vs_serial():
    problem = IntegratedCampusProblem(
        Polygon([(0,0),(300,0),(300,300),(0,300)]),
        n_buildings=5, objectives=['cost']
    )
    
    X = np.random.rand(4, problem.n_var) # Small population
    X = X * (problem.xu - problem.xl) + problem.xl
    
    # Serial
    out_serial = {}
    problem._evaluate(X, out_serial)
    
    # Parallel
    evaluator = ParallelEvaluator(problem, n_workers=2)
    out_parallel = evaluator.evaluate(X)
    
    assert np.allclose(out_serial['F'], out_parallel['F'], rtol=1e-5)
    assert np.allclose(out_serial['G'], out_parallel['G'], rtol=1e-5)
