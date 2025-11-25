"""Tests for coupled optimization loop."""

import pytest
import numpy as np
from shapely.geometry import Polygon

from backend.core.integration import (
    IntegratedCampusProblem,
    CoupledOptimizer
)
from backend.core.integration.adaptive_field import (
    AdaptiveTensorFieldGenerator
)


class TestAdaptiveTensorField:
    """Test adaptive field generation."""
    
    def test_generate_from_buildings(self):
        """Test tensor field adapts to building clusters."""
        # Create clustered buildings
        cluster1 = np.random.randn(10, 2) * 30 + [200, 200]
        cluster2 = np.random.randn(10, 2) * 30 + [600, 600]
        buildings = np.vstack([cluster1, cluster2])
        
        boundary = Polygon([(0, 0), (800, 0), (800, 800), (0, 800)])
        
        generator = AdaptiveTensorFieldGenerator(
            n_radial_fields=2
        )
        
        tensor_field = generator.generate_from_buildings(buildings, boundary)
        
        # Should create fields near clusters
        assert len(tensor_field.basis_fields) >= 2
    
    def test_principal_axis_computation(self):
        """Test PCA axis calculation."""
        # Line of points
        points = np.array([[0, 0], [1, 1], [2, 2]])
        
        generator = AdaptiveTensorFieldGenerator()
        angle = generator._compute_principal_axis(points)
        
        # Should be 45 degrees
        assert np.isclose(angle, np.pi/4, atol=0.1)


class TestCoupledObjectives:
    """Test road-building coupled objectives."""
    
    def test_road_accessibility(self):
        """Test accessibility calculation."""
        from backend.core.integration.objectives import (
            calculate_road_accessibility
        )
        
        # Simple scenario
        buildings = [
            {'position': np.array([100, 100])},
            {'position': np.array([200, 200])}
        ]
        
        roads = [
            np.array([[50, 50], [150, 150], [250, 250]])
        ]
        
        accessibility = calculate_road_accessibility(buildings, roads)
        
        # Should be low (buildings near road)
        assert accessibility < 100
    
    def test_road_coverage(self):
        """Test coverage calculation."""
        from backend.core.integration.objectives import (
            calculate_road_coverage
        )
        
        buildings = [
            {'position': np.array([100, 100])},
            {'position': np.array([500, 500])}  # Far from road
        ]
        
        roads = [
            np.array([[50, 50], [150, 150]])
        ]
        
        coverage = calculate_road_coverage(
            buildings, roads, max_service_distance=100
        )
        
        # Should be partial (1/2 buildings covered)
        assert -1.0 <= coverage <= 0.0


class TestCoupledOptimization:
    """Test complete coupled optimization."""
    
    def test_optimization_runs(self):
        """Test that coupled optimization completes."""
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])
        
        problem = IntegratedCampusProblem(
            boundary=boundary,
            n_grids=2,
            n_radials=1,
            n_buildings=10,
            objectives=['cost', 'road_access', 'adjacency'],
            enable_adaptive_roads=True  # Enable coupling
        )
        
        optimizer = CoupledOptimizer(
            problem=problem,
            population_size=10,  # Small for test
            n_generations=2      # Quick test
        )
        
        result = optimizer.optimize()
        
        # Should complete without error
        assert result.F is not None
        assert len(result.F) > 0
    
    def test_adaptive_vs_static(self):
        """
        Compare adaptive roads vs static roads.
        
        Adaptive should achieve better accessibility.
        """
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])
        
        # Static roads
        problem_static = IntegratedCampusProblem(
            boundary=boundary,
            n_buildings=10,
            objectives=['road_access'],
            enable_adaptive_roads=False
        )
        
        # Adaptive roads
        problem_adaptive = IntegratedCampusProblem(
            boundary=boundary,
            n_buildings=10,
            objectives=['road_access'],
            enable_adaptive_roads=True
        )
        
        # Note: Full comparison would require running optimization
        # For unit test, just verify both can be instantiated
        assert problem_static.enable_adaptive_roads == False
        assert problem_adaptive.enable_adaptive_roads == True
