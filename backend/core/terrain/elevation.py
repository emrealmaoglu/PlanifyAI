"""
Phase 8: Elevation/Terrain Module.

Provides DEM (Digital Elevation Model) sampling for slope analysis.
Uses Open-Elevation API for development, with fallback for offline mode.
"""

import requests
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache
import warnings


# =============================================================================
# DEM SAMPLER
# =============================================================================

class DEMSampler:
    """
    Digital Elevation Model sampler for terrain analysis.
    
    Uses Open-Elevation API to query elevation at specific coordinates.
    Includes caching to minimize API calls and fallback for offline mode.
    
    Example:
        sampler = DEMSampler()
        elevation = sampler.sample(41.3833, 33.7833)  # Returns meters
    """
    
    API_URL = "https://api.open-elevation.com/api/v1/lookup"
    TIMEOUT = 10  # seconds
    
    def __init__(
        self,
        use_cache: bool = True,
        fallback_elevation: float = 0.0,
        offline_mode: bool = False
    ):
        """
        Initialize the DEM sampler.
        
        Args:
            use_cache: Enable LRU caching of elevation queries
            fallback_elevation: Default elevation when API fails
            offline_mode: If True, skip API calls entirely (use fallback)
        """
        self.use_cache = use_cache
        self.fallback_elevation = fallback_elevation
        self.offline_mode = offline_mode
        self._cache: Dict[Tuple[float, float], float] = {}
    
    def sample(self, lat: float, lon: float) -> float:
        """
        Sample elevation at a specific coordinate.
        
        Args:
            lat: Latitude (WGS84)
            lon: Longitude (WGS84)
        
        Returns:
            Elevation in meters above sea level
        """
        if self.offline_mode:
            return self.fallback_elevation
        
        # Check cache
        cache_key = (round(lat, 5), round(lon, 5))
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            elevation = self._query_api(lat, lon)
            self._cache[cache_key] = elevation
            return elevation
        except Exception as e:
            warnings.warn(f"Elevation API failed: {e}. Using fallback.")
            return self.fallback_elevation
    
    def sample_batch(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        """
        Sample elevation at multiple coordinates (batched API call).
        
        Args:
            coordinates: List of (lat, lon) tuples
        
        Returns:
            List of elevations in meters
        """
        if self.offline_mode:
            return [self.fallback_elevation] * len(coordinates)
        
        if not coordinates:
            return []
        
        try:
            return self._query_api_batch(coordinates)
        except Exception as e:
            warnings.warn(f"Batch elevation API failed: {e}. Using fallback.")
            return [self.fallback_elevation] * len(coordinates)
    
    def _query_api(self, lat: float, lon: float) -> float:
        """Query single point from Open-Elevation API."""
        payload = {
            "locations": [{"latitude": lat, "longitude": lon}]
        }
        
        response = requests.post(
            self.API_URL,
            json=payload,
            timeout=self.TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        if results and "elevation" in results[0]:
            return float(results[0]["elevation"])
        
        return self.fallback_elevation
    
    def _query_api_batch(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        """Query multiple points from Open-Elevation API."""
        payload = {
            "locations": [
                {"latitude": lat, "longitude": lon}
                for lat, lon in coordinates
            ]
        }
        
        response = requests.post(
            self.API_URL,
            json=payload,
            timeout=self.TIMEOUT * 2  # Longer timeout for batch
        )
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        elevations = []
        for i, result in enumerate(results):
            elev = result.get("elevation", self.fallback_elevation)
            elevations.append(float(elev))
            # Cache the result
            cache_key = (round(coordinates[i][0], 5), round(coordinates[i][1], 5))
            self._cache[cache_key] = float(elev)
        
        return elevations
    
    def clear_cache(self) -> None:
        """Clear the elevation cache."""
        self._cache.clear()


# =============================================================================
# SLOPE CALCULATOR
# =============================================================================

class SlopeCalculator:
    """
    Calculates terrain slope for building placement validation.
    
    Uses DEM sampling to determine if terrain is suitable for construction.
    Turkish law prohibits construction on slopes > 15%.
    """
    
    MAX_LEGAL_SLOPE = 0.15  # 15% = 8.5 degrees
    
    def __init__(self, dem_sampler: DEMSampler = None):
        """
        Initialize slope calculator.
        
        Args:
            dem_sampler: DEM sampler instance (created if None)
        """
        self.dem = dem_sampler or DEMSampler(offline_mode=True)
    
    def calculate_slope_at_polygon(
        self,
        polygon_coords: List[Tuple[float, float]],
        local_to_wgs84_transform: callable = None
    ) -> float:
        """
        Calculate average slope across a building footprint.
        
        Args:
            polygon_coords: List of (x, y) coordinates in local CRS
            local_to_wgs84_transform: Transform function to convert to lat/lon
        
        Returns:
            Slope as decimal (0.15 = 15%)
        """
        if len(polygon_coords) < 3:
            return 0.0
        
        # If no transform provided, assume coordinates are already lat/lon
        if local_to_wgs84_transform:
            wgs84_coords = [local_to_wgs84_transform(x, y) for x, y in polygon_coords]
        else:
            # Assume x=lon, y=lat (common GIS convention)
            wgs84_coords = [(y, x) for x, y in polygon_coords]
        
        # Sample elevation at corners
        elevations = self.dem.sample_batch(wgs84_coords)
        
        if not elevations or all(e == self.dem.fallback_elevation for e in elevations):
            return 0.0  # Can't determine slope
        
        # Calculate slope from elevation range
        max_elev = max(elevations)
        min_elev = min(elevations)
        elev_diff = max_elev - min_elev
        
        # Calculate horizontal distance (approximate from coordinates)
        xs = [c[0] for c in polygon_coords]
        ys = [c[1] for c in polygon_coords]
        diagonal = np.sqrt(
            (max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2
        )
        
        if diagonal < 1e-6:
            return 0.0
        
        slope = elev_diff / diagonal
        return slope
    
    def check_slope_violation(
        self,
        slope: float,
        area: float = 1.0
    ) -> float:
        """
        Check if slope exceeds legal limit.
        
        Args:
            slope: Calculated slope (decimal)
            area: Building footprint area (for weighting)
        
        Returns:
            Violation magnitude (0 if compliant)
        """
        if slope <= self.MAX_LEGAL_SLOPE:
            return 0.0
        
        # Violation weighted by how much over limit
        excess = slope - self.MAX_LEGAL_SLOPE
        return excess * area


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def get_elevation(lat: float, lon: float, offline: bool = False) -> float:
    """
    Quick elevation lookup.
    
    Args:
        lat: Latitude
        lon: Longitude
        offline: Use offline fallback
    
    Returns:
        Elevation in meters
    """
    sampler = DEMSampler(offline_mode=offline)
    return sampler.sample(lat, lon)
