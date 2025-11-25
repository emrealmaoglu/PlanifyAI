"""
Unified representation for co-optimization of roads and buildings.

This module defines the "DNA" of a campus layout, containing both
infrastructure (roads) and structures (buildings).
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import numpy as np
from shapely.geometry import Polygon

from ..spatial import BasisField, GridField, RadialField, TensorField, StreamlineIntegrator, RoadNetworkGenerator


@dataclass
class TensorFieldParams:
    """
    Parametric representation of a tensor field.
    
    Instead of storing BasisField objects directly (not serializable),
    we store their parameters and reconstruct on-demand.
    """
    
    # Grid field parameters
    grid_centers: np.ndarray        # (N_grids, 2)
    grid_orientations: np.ndarray   # (N_grids,) in radians
    grid_decay_radii: np.ndarray    # (N_grids,)
    
    # Radial field parameters  
    radial_centers: np.ndarray      # (N_radials, 2)
    radial_decay_radii: np.ndarray  # (N_radials,)
    
    def to_tensor_field(self) -> TensorField:
        """Reconstruct TensorField from parameters."""
        fields = []
        
        # Create grid fields
        for i in range(len(self.grid_centers)):
            field = GridField(
                center=tuple(self.grid_centers[i]),
                size=50.0,  # Fixed for now
                theta=self.grid_orientations[i],
                decay_radius=self.grid_decay_radii[i]
            )
            fields.append(field)
        
        # Create radial fields
        for i in range(len(self.radial_centers)):
            field = RadialField(
                center=tuple(self.radial_centers[i]),
                decay_radius=self.radial_decay_radii[i]
            )
            fields.append(field)
        
        return TensorField(fields)


@dataclass  
class BuildingLayout:
    """
    Parametric representation of building positions.
    """
    
    positions: np.ndarray      # (N_buildings, 2) - [x, y]
    types: np.ndarray          # (N_buildings,) - BuildingType codes
    orientations: np.ndarray   # (N_buildings,) - rotation in radians
    
    def to_building_list(self) -> List[Dict[str, Any]]:
        """Convert to list of building dictionaries."""
        buildings = []
        for i in range(len(self.positions)):
            buildings.append({
                'position': self.positions[i],
                'type': int(self.types[i]),
                'orientation': self.orientations[i]
            })
        return buildings


class CompositeGenotype:
    """
    Unified chromosome for co-optimization of roads and buildings.
    
    This is the "DNA" that NSGA-III will evolve. Each individual
    in the population is one CompositeGenotype.
    """
    
    def __init__(
        self,
        tensor_params: TensorFieldParams,
        building_layout: BuildingLayout
    ):
        """
        Initialize composite genotype.
        
        Args:
            tensor_params: Road network parameters
            building_layout: Building placement parameters
        """
        self.tensor_params = tensor_params
        self.building_layout = building_layout
    
    def to_flat_array(self) -> np.ndarray:
        """
        Flatten to 1D array for evolutionary algorithms.
        
        Required by pymoo - chromosomes must be numeric arrays.
        
        Returns:
            1D array containing all parameters
        """
        parts = [
            self.tensor_params.grid_centers.ravel(),
            self.tensor_params.grid_orientations,
            self.tensor_params.grid_decay_radii,
            self.tensor_params.radial_centers.ravel(),
            self.tensor_params.radial_decay_radii,
            self.building_layout.positions.ravel(),
            self.building_layout.types,
            self.building_layout.orientations
        ]
        
        return np.concatenate(parts)
    
    @staticmethod
    def from_flat_array(
        array: np.ndarray,
        n_grids: int,
        n_radials: int,
        n_buildings: int
    ) -> 'CompositeGenotype':
        """
        Reconstruct from flattened array.
        
        Args:
            array: 1D parameter array
            n_grids: Number of grid fields
            n_radials: Number of radial fields  
            n_buildings: Number of buildings
            
        Returns:
            CompositeGenotype instance
        """
        # Parse array sections
        idx = 0
        
        # Grid parameters
        grid_centers = array[idx:idx + n_grids*2].reshape(n_grids, 2)
        idx += n_grids * 2
        
        grid_orientations = array[idx:idx + n_grids]
        idx += n_grids
        
        grid_decay_radii = array[idx:idx + n_grids]
        idx += n_grids
        
        # Radial parameters
        radial_centers = array[idx:idx + n_radials*2].reshape(n_radials, 2)
        idx += n_radials * 2
        
        radial_decay_radii = array[idx:idx + n_radials]
        idx += n_radials
        
        # Building parameters
        building_positions = array[idx:idx + n_buildings*2].reshape(n_buildings, 2)
        idx += n_buildings * 2
        
        building_types = array[idx:idx + n_buildings].astype(int)
        idx += n_buildings
        
        building_orientations = array[idx:idx + n_buildings]
        
        # Reconstruct objects
        tensor_params = TensorFieldParams(
            grid_centers=grid_centers,
            grid_orientations=grid_orientations,
            grid_decay_radii=grid_decay_radii,
            radial_centers=radial_centers,
            radial_decay_radii=radial_decay_radii
        )
        
        building_layout = BuildingLayout(
            positions=building_positions,
            types=building_types,
            orientations=building_orientations
        )
        
        return CompositeGenotype(tensor_params, building_layout)
    
    def decode(self, boundary_polygon: Polygon) -> Tuple[List[np.ndarray], List[Dict[str, Any]]]:
        """
        Decode genotype into physical roads and buildings.
        
        Args:
            boundary_polygon: Campus boundary for road generation
            
        Returns:
            (roads, buildings) tuple
        """
        # Generate road network
        tensor_field = self.tensor_params.to_tensor_field()
        
        integrator = StreamlineIntegrator(tensor_field, boundary_polygon)
        generator = RoadNetworkGenerator(integrator)
        
        # Smart seeding based on anisotropy
        bbox = boundary_polygon.bounds
        seeds = generator.generate_seed_points(
            bbox=bbox,
            grid_spacing=80,
            min_anisotropy=0.6
        )
        
        roads = generator.generate_network(seeds, min_road_length=30)
        
        # Decode buildings
        buildings = self.building_layout.to_building_list()
        
        return roads, buildings
