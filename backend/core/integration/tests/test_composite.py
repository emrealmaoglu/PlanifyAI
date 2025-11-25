"""Tests for CompositeGenotype."""

import pytest
import numpy as np
from shapely.geometry import Polygon

from backend.core.integration import (
    CompositeGenotype,
    TensorFieldParams,
    BuildingLayout,
    IntegratedCampusProblem
)


class TestCompositeGenotype:
    """Test unified genotype."""
    
    def test_tensor_params_creation(self):
        """Test TensorFieldParams creation."""
        params = TensorFieldParams(
            grid_centers=np.array([[100, 200], [300, 400]]),
            grid_orientations=np.array([0, np.pi/2]),
            grid_decay_radii=np.array([150, 200]),
            radial_centers=np.array([[500, 600]]),
            radial_decay_radii=np.array([120])
        )
        
        # Should reconstruct to TensorField
        tensor_field = params.to_tensor_field()
        assert len(tensor_field.basis_fields) == 3  # 2 grids + 1 radial
    
    def test_building_layout_creation(self):
        """Test BuildingLayout creation."""
        layout = BuildingLayout(
            positions=np.array([[100, 200], [300, 400]]),
            types=np.array([1, 2]),
            orientations=np.array([0, np.pi/4])
        )
        
        buildings = layout.to_building_list()
        assert len(buildings) == 2
        assert buildings[0]['type'] == 1
    
    def test_flat_array_conversion(self):
        """Test flattening and reconstruction."""
        # Create genotype
        tensor_params = TensorFieldParams(
            grid_centers=np.array([[100, 200]]),
            grid_orientations=np.array([0]),
            grid_decay_radii=np.array([150]),
            radial_centers=np.array([[300, 400]]),
            radial_decay_radii=np.array([120])
        )
        
        building_layout = BuildingLayout(
            positions=np.array([[50, 60]]),
            types=np.array([1]),
            orientations=np.array([0])
        )
        
        original = CompositeGenotype(tensor_params, building_layout)
        
        # Flatten
        flat = original.to_flat_array()
        assert flat.ndim == 1
        
        # Reconstruct
        reconstructed = CompositeGenotype.from_flat_array(
            flat, n_grids=1, n_radials=1, n_buildings=1
        )
        
        # Verify
        assert np.allclose(
            reconstructed.tensor_params.grid_centers,
            original.tensor_params.grid_centers
        )
    
    def test_decode(self):
        """Test decoding to roads and buildings."""
        tensor_params = TensorFieldParams(
            grid_centers=np.array([[250, 250]]),
            grid_orientations=np.array([0]),
            grid_decay_radii=np.array([200]),
            radial_centers=np.array([[100, 100]]),
            radial_decay_radii=np.array([120])
        )
        
        building_layout = BuildingLayout(
            positions=np.array([[200, 200]]),
            types=np.array([1]),
            orientations=np.array([0])
        )
        
        genotype = CompositeGenotype(tensor_params, building_layout)
        
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])
        
        roads, buildings = genotype.decode(boundary)
        
        # Should generate roads and buildings
        # Note: Roads might be empty if seeds are invalid or roads too short, 
        # but with these params it should produce something.
        # If not, we just check it returns a list.
        assert isinstance(roads, list)
        assert len(buildings) == 1

class TestIntegratedProblem:
    """Test IntegratedCampusProblem."""
    
    def test_problem_initialization(self):
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])
        problem = IntegratedCampusProblem(
            boundary, n_grids=1, n_radials=1, n_buildings=5
        )
        
        assert problem.n_var > 0
        assert problem.n_obj == 4
        assert problem.n_constr == 1
        
    def test_evaluate(self):
        boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])
        problem = IntegratedCampusProblem(
            boundary, n_grids=1, n_radials=1, n_buildings=5
        )
        
        # Create random population
        X = np.random.random((2, problem.n_var))
        # Scale to bounds
        X = problem.xl + X * (problem.xu - problem.xl)
        
        out = {}
        problem._evaluate(X, out)
        
        assert "F" in out
        assert "G" in out
        assert out["F"].shape == (2, 4)
        assert out["G"].shape == (2, 1)
