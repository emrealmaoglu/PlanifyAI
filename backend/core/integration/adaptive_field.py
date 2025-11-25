"""
Adaptive tensor field generation based on building clusters.

This module implements the "building-aware" road generation logic,
where tensor field parameters shift dynamically to service buildings.
"""

import numpy as np
from scipy.cluster.vq import kmeans2
from typing import List
from shapely.geometry import Polygon

from ..spatial import GridField, RadialField, TensorField


class AdaptiveTensorFieldGenerator:
    """
    Generates tensor fields that adapt to building distributions.
    
    Strategy:
    1. Cluster buildings using k-means
    2. Place radial fields at cluster centers (junctions)
    3. Place grid fields to connect clusters (main roads)
    4. Decay radii proportional to cluster size
    """
    
    def __init__(
        self,
        n_grid_fields: int = 3,
        n_radial_fields: int = 2,
        min_decay_radius: float = 50.0,
        max_decay_radius: float = 300.0
    ):
        """
        Initialize adaptive generator.
        
        Args:
            n_grid_fields: Number of grid fields to create
            n_radial_fields: Number of radial fields (junctions)
            min_decay_radius: Minimum influence radius
            max_decay_radius: Maximum influence radius
        """
        self.n_grid_fields = n_grid_fields
        self.n_radial_fields = n_radial_fields
        self.min_decay = min_decay_radius
        self.max_decay = max_decay_radius
    
    def generate_from_buildings(
        self,
        building_positions: np.ndarray,
        boundary_polygon: Polygon
    ) -> TensorField:
        """
        Generate tensor field adapted to building layout.
        
        Algorithm:
        1. Cluster buildings into N groups
        2. Place radial fields at cluster centroids
        3. Place grid fields along cluster connections
        4. Scale decay radii by cluster density
        
        Args:
            building_positions: (N, 2) array of building [x, y]
            boundary_polygon: Campus boundary
            
        Returns:
            Adaptive TensorField
        """
        if len(building_positions) < 5:
            # Fallback: Use boundary-based fields
            return self._generate_boundary_based(boundary_polygon)
        
        fields = []
        
        # Step 1: Cluster buildings (k-means)
        # Ensure we don't ask for more clusters than unique points
        unique_points = np.unique(building_positions, axis=0)
        n_clusters = min(self.n_radial_fields, len(unique_points), len(building_positions) // 3)
        
        if n_clusters < 1:
             return self._generate_boundary_based(boundary_polygon)

        try:
            centroids, labels = kmeans2(
                building_positions,
                n_clusters,
                minit='points'
            )
        except Exception:
             # Fallback if clustering fails
             return self._generate_boundary_based(boundary_polygon)
        
        # Step 2: Create radial fields at cluster centers
        for i, center in enumerate(centroids):
            # Count buildings in cluster
            cluster_size = np.sum(labels == i)
            
            # Larger clusters = stronger field (larger decay)
            decay_radius = self.min_decay + (
                (self.max_decay - self.min_decay) * 
                (cluster_size / len(building_positions))
            )
            
            field = RadialField(
                center=tuple(center),
                decay_radius=decay_radius
            )
            fields.append(field)
        
        # Step 3: Create grid fields connecting clusters
        if n_clusters >= 2:
            # Find principal axis connecting clusters
            pca_axis = self._compute_principal_axis(centroids)
            
            # Place grid field along this axis
            center = np.mean(centroids, axis=0)
            
            field = GridField(
                center=tuple(center),
                size=50.0,
                theta=pca_axis,
                decay_radius=self.max_decay
            )
            fields.append(field)
            
            # Perpendicular grid field for cross-connections
            field = GridField(
                center=tuple(center),
                size=50.0,
                theta=pca_axis + np.pi/2,
                decay_radius=self.max_decay * 0.7
            )
            fields.append(field)
        else:
             # If only 1 cluster, align grid with boundary or default
             center = centroids[0]
             field = GridField(
                center=tuple(center),
                size=50.0,
                theta=0.0,
                decay_radius=self.max_decay
            )
             fields.append(field)
             
        # Step 4: Add repulsive (tangential) fields around each building
        # This prevents roads from going through buildings
        for pos in building_positions:
            field = RadialField(
                center=tuple(pos),
                decay_radius=30.0,  # Small influence radius
                tangential=True     # Force flow AROUND building
            )
            fields.append(field)

        
        return TensorField(fields)
    
    def _compute_principal_axis(self, points: np.ndarray) -> float:
        """
        Compute principal axis angle using PCA.
        
        Args:
            points: (N, 2) array of cluster centers
            
        Returns:
            Angle in radians
        """
        if len(points) < 2:
            return 0.0
            
        # Center points
        centered = points - np.mean(points, axis=0)
        
        # Covariance matrix
        cov = np.cov(centered.T)
        
        # Eigenvectors (PCA)
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
            
            # Principal axis = eigenvector with largest eigenvalue
            # eigh returns eigenvalues in ascending order
            principal = eigenvectors[:, 1]
            
            # Convert to angle
            angle = np.arctan2(principal[1], principal[0])
            return angle
        except np.linalg.LinAlgError:
            return 0.0
    
    def _generate_boundary_based(self, boundary_polygon: Polygon) -> TensorField:
        """Fallback: Generate fields based on boundary only."""
        bounds = boundary_polygon.bounds
        center = np.array([
            (bounds[0] + bounds[2]) / 2,
            (bounds[1] + bounds[3]) / 2
        ])
        
        fields = [
            GridField(
                center=tuple(center),
                size=50.0,
                theta=0,
                decay_radius=200
            ),
            GridField(
                center=tuple(center),
                size=50.0,
                theta=np.pi/2,
                decay_radius=200
            )
        ]
        
        return TensorField(fields)
