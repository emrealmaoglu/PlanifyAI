"""
Unified visualization for integrated roads + buildings.
"""

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon
from typing import List, Dict, Any, Optional

from ..spatial import TensorField

def visualize_integrated_layout(
    roads: List[np.ndarray],
    buildings: List[Dict[str, Any]],
    boundary: Polygon,
    tensor_field: Optional[TensorField] = None,
    title: str = "Integrated Campus Layout"
):
    """
    Visualize complete campus layout with roads and buildings.
    
    Args:
        roads: List of road polylines
        buildings: List of building dicts
        boundary: Campus boundary
        tensor_field: Optional TensorField for background
        title: Plot title
    """
    fig, ax = plt.subplots(figsize=(14, 14))
    
    # Draw boundary
    x, y = boundary.exterior.xy
    ax.plot(x, y, 'k-', linewidth=2, label='Boundary')
    
    # Optional: Draw tensor field streamplot
    if tensor_field:
        bounds = boundary.bounds
        x_grid = np.linspace(bounds[0], bounds[2], 40)
        y_grid = np.linspace(bounds[1], bounds[3], 40)
        X, Y = np.meshgrid(x_grid, y_grid)
        points = np.c_[X.ravel(), Y.ravel()]
        
        vectors = tensor_field.get_eigenvectors(points, 'major')
        U = vectors[:, 0].reshape(X.shape)
        V = vectors[:, 1].reshape(X.shape)
        
        ax.streamplot(X, Y, U, V, color=(0.5, 0.5, 0.5, 0.3), 
                     density=0.8, linewidth=0.5)
    
    # Draw roads
    for road in roads:
        ax.plot(road[:, 0], road[:, 1], 'b-', linewidth=2, alpha=0.7)
    
    # Draw buildings
    for building in buildings:
        pos = building['position']
        # Simple rectangle representation
        rect = plt.Rectangle(
            (pos[0]-10, pos[1]-10), 20, 20,
            color='red', alpha=0.6
        )
        ax.add_patch(rect)
    
    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_title(title)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    return fig
