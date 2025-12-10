"""
Phase 9: Slope Grid Generator for XAI Visualization.

Generates a grid of slope values over the campus boundary
for frontend heatmap visualization.
"""

import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass

from shapely.geometry import Polygon, Point, box
from pyproj import Transformer

from backend.core.terrain.elevation import DEMSampler


@dataclass
class SlopeCell:
    """A single cell in the slope grid."""
    center_lat: float
    center_lon: float
    slope: float  # As decimal (0.15 = 15%)
    
    @property
    def slope_percent(self) -> float:
        return self.slope * 100
    
    @property
    def is_buildable(self) -> bool:
        return self.slope <= 0.15


class SlopeGridGenerator:
    """
    Generates a grid of slope values over a campus boundary.
    
    Used for frontend XAI visualization (heatmap layer).
    """
    
    MAX_BUILDABLE_SLOPE = 0.15
    
    def __init__(
        self,
        grid_size: int = 25,  # 25x25 grid = 625 cells
        dem_sampler: DEMSampler = None
    ):
        """
        Initialize the slope grid generator.
        
        Args:
            grid_size: Number of cells per dimension (grid_size x grid_size)
            dem_sampler: DEM sampler for elevation queries
        """
        self.grid_size = grid_size
        self.dem = dem_sampler or DEMSampler(offline_mode=True)
    
    def generate_grid(
        self,
        boundary: Polygon,
        crs_local: str,
        center_latlon: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Generate slope grid for a campus boundary.
        
        Args:
            boundary: Campus boundary polygon (in local CRS)
            crs_local: Local CRS string
            center_latlon: (lat, lon) of campus center
        
        Returns:
            Dict with grid metadata and cell values
        """
        # Get bounding box
        minx, miny, maxx, maxy = boundary.bounds
        
        # Create grid points
        x_step = (maxx - minx) / self.grid_size
        y_step = (maxy - miny) / self.grid_size
        
        # Transformer for local -> WGS84
        transformer = Transformer.from_crs(crs_local, "EPSG:4326", always_xy=True)
        
        cells = []
        values = []
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Cell center in local coordinates
                x = minx + (i + 0.5) * x_step
                y = miny + (j + 0.5) * y_step
                
                cell_center = Point(x, y)
                
                # Skip cells outside boundary
                if not boundary.contains(cell_center):
                    continue
                
                # Transform to WGS84
                lon, lat = transformer.transform(x, y)
                
                # Sample elevations for slope calculation
                # Use 4 corners of cell
                corners = [
                    (x - x_step/2, y - y_step/2),
                    (x + x_step/2, y - y_step/2),
                    (x - x_step/2, y + y_step/2),
                    (x + x_step/2, y + y_step/2)
                ]
                
                # Transform corners to WGS84 for API query
                corner_wgs84 = []
                for cx, cy in corners:
                    clon, clat = transformer.transform(cx, cy)
                    corner_wgs84.append((clat, clon))
                
                # Get elevations
                elevations = self.dem.sample_batch(corner_wgs84)
                
                # Calculate slope
                if len(elevations) >= 4 and not all(e == 0 for e in elevations):
                    elev_range = max(elevations) - min(elevations)
                    cell_diag = np.sqrt(x_step**2 + y_step**2)
                    slope = elev_range / cell_diag if cell_diag > 0 else 0
                else:
                    slope = 0.0  # Flat fallback
                
                cells.append({
                    "lat": lat,
                    "lon": lon,
                    "slope": round(slope, 4),
                    "buildable": slope <= self.MAX_BUILDABLE_SLOPE
                })
                values.append(round(slope, 4))
        
        return {
            "type": "slope_grid",
            "grid_size": self.grid_size,
            "cell_count": len(cells),
            "bounds": {
                "min_lat": center_latlon[0] - 0.01,
                "max_lat": center_latlon[0] + 0.01,
                "min_lon": center_latlon[1] - 0.01,
                "max_lon": center_latlon[1] + 0.01
            },
            "max_slope": max(values) if values else 0,
            "min_slope": min(values) if values else 0,
            "cells": cells
        }
    
    def generate_geojson_grid(
        self,
        boundary: Polygon,
        crs_local: str,
        center_latlon: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Generate slope grid as GeoJSON FeatureCollection.
        
        More compatible with Mapbox but larger payload.
        """
        grid_data = self.generate_grid(boundary, crs_local, center_latlon)
        
        features = []
        for cell in grid_data["cells"]:
            # Determine color class
            if cell["slope"] <= 0.05:
                color_class = "safe"      # Green
            elif cell["slope"] <= 0.15:
                color_class = "caution"   # Yellow
            else:
                color_class = "danger"    # Red
            
            features.append({
                "type": "Feature",
                "properties": {
                    "layer": "slope_grid",
                    "slope": cell["slope"],
                    "slope_percent": round(cell["slope"] * 100, 1),
                    "buildable": cell["buildable"],
                    "color_class": color_class
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [cell["lon"], cell["lat"]]
                }
            })
        
        return {
            "type": "FeatureCollection",
            "properties": {
                "layer_type": "slope_grid",
                "max_slope": grid_data["max_slope"],
                "grid_size": grid_data["grid_size"]
            },
            "features": features
        }


def generate_wind_arrows(
    boundary: Polygon,
    wind_direction_deg: float,
    wind_speed: float,
    crs_local: str,
    grid_size: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate wind arrow positions for visualization.
    
    Args:
        boundary: Campus boundary
        wind_direction_deg: Wind direction in degrees from North
        wind_speed: Wind speed in m/s
        crs_local: Local CRS string
        grid_size: Number of arrows per dimension
    
    Returns:
        List of arrow features for GeoJSON
    """
    minx, miny, maxx, maxy = boundary.bounds
    x_step = (maxx - minx) / grid_size
    y_step = (maxy - miny) / grid_size
    
    transformer = Transformer.from_crs(crs_local, "EPSG:4326", always_xy=True)
    
    arrows = []
    
    for i in range(grid_size):
        for j in range(grid_size):
            x = minx + (i + 0.5) * x_step
            y = miny + (j + 0.5) * y_step
            
            if not boundary.contains(Point(x, y)):
                continue
            
            lon, lat = transformer.transform(x, y)
            
            arrows.append({
                "type": "Feature",
                "properties": {
                    "layer": "wind_arrow",
                    "direction": wind_direction_deg,
                    "speed": wind_speed,
                    "rotation": wind_direction_deg  # For icon rotation
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            })
    
    return arrows
