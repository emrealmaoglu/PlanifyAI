"""Spatial indexing for efficient geometric queries."""

import numpy as np
from scipy.spatial import cKDTree
from typing import List, Tuple

class SpatialRoadIndex:
    """KD-tree index for road network proximity queries."""
    
    def __init__(self, roads: List[np.ndarray], leafsize: int = 64):
        """
        Build spatial index for road network.
        
        Args:
            roads: List of road polylines (each Nx2 array)
            leafsize: KDTree leaf size (32-64 optimal for M1)
        """
        # Flatten all road points into single array
        if not roads:
            self.road_points = np.empty((0, 2))
            self.tree = None
            return
        
        self.road_points = np.vstack(roads)
        
        # Build KD-tree (optimized for M1)
        self.tree = cKDTree(
            self.road_points,
            leafsize=leafsize,
            balanced_tree=True,
            compact_nodes=True
        )
    
    def query_nearest(
        self, 
        building_positions: np.ndarray,
        min_clearance: float = 10.0
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Find nearest road point for each building.
        
        Args:
            building_positions: (N, 2) array of building centers
            min_clearance: Minimum required clearance (meters)
            
        Returns:
            (distances, indices, violation_score)
        """
        if self.tree is None or len(building_positions) == 0:
            return np.array([]), np.array([]), 0.0
        
        # Batch query (workers=1 optimal for small N on M1)
        distances, indices = self.tree.query(
            building_positions, 
            k=1,
            workers=1
        )
        
        # Calculate violation
        violations = np.maximum(0, min_clearance - distances)
        total_violation = np.sum(violations)
        
        return distances, indices, total_violation
