import pytest
import numpy as np
from shapely.geometry import Polygon
from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.optimizer import AdvancedOptimizer
from backend.core.integration.constraints import TurkishStandardsValidator

def test_nsga3_reference_dirs():
    problem = IntegratedCampusProblem(
        Polygon([(0,0),(500,0),(500,500),(0,500)]),
        n_buildings=10,
        objectives=['cost','adjacency','green_space','road_access']
    )
    optimizer = AdvancedOptimizer(problem, population_size=50)
    assert len(optimizer.ref_dirs) > 0

def test_turkish_standards_green_space():
    boundary = Polygon([(0,0),(500,0),(500,500),(0,500)])
    validator = TurkishStandardsValidator(boundary)
    
    # Create buildings that cover too much area
    # 50 buildings * 400m2 = 20000m2
    # Boundary area = 250000m2
    # Green ratio = 1 - 20000/250000 = 1 - 0.08 = 0.92 > 0.30 (PASS)
    
    # Let's make it fail
    # Need > 70% coverage to fail min_green=0.30
    # 250000 * 0.7 = 175000m2
    # 175000 / 400 = 437.5 buildings
    
    buildings = [{'position': [0, 0]} for _ in range(450)]
    _, details = validator.calculate_constraint_violations(buildings, [])
    
    assert details['green_space'] > 0

def test_turkish_standards_spacing():
    boundary = Polygon([(0,0),(500,0),(500,500),(0,500)])
    validator = TurkishStandardsValidator(boundary, min_spacing=15.0)
    
    # Two buildings too close
    buildings = [
        {'position': [100, 100]},
        {'position': [100, 110]}  # 10m distance < 15m
    ]
    _, details = validator.calculate_constraint_violations(buildings, [])
    
    assert details['spacing'] > 0

def test_end_to_end():
    problem = IntegratedCampusProblem(
        Polygon([(0,0),(400,0),(400,400),(0,400)]),
        n_buildings=10, objectives=['cost','road_access'],
        enable_turkish_standards=True
    )
    optimizer = AdvancedOptimizer(problem, population_size=20, n_generations=5)
    result = optimizer.optimize()
    
    assert result.F is not None
    best = optimizer.extract_best_solution(result)
    roads, buildings = best.decode(problem.boundary)
    assert len(roads) > 0 or len(buildings) > 0 # Roads might be empty if adaptive fails or not generated
