"""
Wind Analysis for Campus Planning.

Fetches historical wind data from Open-Meteo API
and calculates optimal road orientations for ventilation.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
import requests
from collections import Counter

# Try to import caching libraries (optional)
try:
    import openmeteo_requests
    import requests_cache
    from retry_requests import retry
    OPENMETEO_AVAILABLE = True
except ImportError:
    OPENMETEO_AVAILABLE = False


@dataclass
class WindData:
    """Wind statistics for a location."""
    dominant_direction: float      # Degrees (0=N, 90=E, 180=S, 270=W)
    dominant_direction_name: str   # "N", "NE", "E", etc.
    average_speed: float           # m/s
    max_speed: float               # m/s
    direction_frequencies: Dict[str, float]  # {"N": 0.15, "NE": 0.12, ...}
    latitude: float
    longitude: float
    data_period_days: int
    
    @property
    def dominant_direction_radians(self) -> float:
        """Dominant direction in radians (math convention: 0=E, π/2=N)."""
        # Convert from meteorological (0=N, clockwise) to math (0=E, counter-clockwise)
        # 0(N) -> 90(math) -> pi/2
        # 90(E) -> 0(math) -> 0
        # 180(S) -> -90(math) -> -pi/2
        # 270(W) -> 180(math) -> pi
        return np.radians(90 - self.dominant_direction)
    
    def direction_to_name(self, degrees: float) -> str:
        """Convert degrees to compass direction name."""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = int((degrees + 22.5) / 45) % 8
        return directions[index]


class WindDataFetcher:
    """
    Fetch historical wind data from Open-Meteo API.
    
    Uses the Open-Meteo Historical Weather API to get wind statistics
    for the past year at a specific location.
    
    Example:
        fetcher = WindDataFetcher()
        data = fetcher.fetch(lat=41.3833, lon=33.7833)
        print(f"Dominant wind: {data.dominant_direction_name} at {data.average_speed:.1f} m/s")
    """
    
    # Open-Meteo Historical Weather API endpoint
    API_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    # Fallback data for Turkey (based on meteorological records)
    TURKEY_FALLBACK = {
        "dominant_direction": 45,  # NE (Poyraz) dominant in Turkey
        "average_speed": 3.5,
        "max_speed": 15.0
    }
    
    def __init__(self, cache_hours: int = 24):
        """
        Initialize the wind data fetcher.
        
        Args:
            cache_hours: Hours to cache API responses
        """
        self.cache_hours = cache_hours
        self._setup_client()
    
    def _setup_client(self):
        """Setup HTTP client with caching if available."""
        if OPENMETEO_AVAILABLE:
            # Setup cached session
            try:
                cache_session = requests_cache.CachedSession(
                    '.wind_cache',
                    expire_after=self.cache_hours * 3600
                )
                retry_session = retry(cache_session, retries=3, backoff_factor=0.5)
                self.client = openmeteo_requests.Client(session=retry_session)
            except Exception as e:
                print(f"Warning: Could not setup cached session: {e}")
                self.client = None
        else:
            self.client = None
    
    def fetch(
        self,
        latitude: float,
        longitude: float,
        days: int = 365
    ) -> WindData:
        """
        Fetch wind data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days of historical data (default: 365)
            
        Returns:
            WindData with statistics
        """
        try:
            return self._fetch_from_api(latitude, longitude, days)
        except Exception as e:
            print(f"Warning: Could not fetch wind data: {e}")
            print("Using fallback data for Turkey region")
            return self._get_fallback(latitude, longitude, days)
    
    def _fetch_from_api(
        self,
        latitude: float,
        longitude: float,
        days: int
    ) -> WindData:
        """Fetch from Open-Meteo API."""
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": ["wind_speed_10m", "wind_direction_10m"],
            "timezone": "auto"
        }
        
        if self.client and OPENMETEO_AVAILABLE:
            responses = self.client.weather_api(self.API_URL, params=params)
            response = responses[0]
            
            hourly = response.Hourly()
            wind_speeds = hourly.Variables(0).ValuesAsNumpy()
            wind_directions = hourly.Variables(1).ValuesAsNumpy()
        else:
            # Fallback to requests
            response = requests.get(self.API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            wind_speeds = np.array(data["hourly"]["wind_speed_10m"])
            wind_directions = np.array(data["hourly"]["wind_direction_10m"])
        
        # Filter out NaN values
        valid_mask = ~np.isnan(wind_speeds) & ~np.isnan(wind_directions)
        wind_speeds = wind_speeds[valid_mask]
        wind_directions = wind_directions[valid_mask]
        
        if len(wind_speeds) == 0:
            raise ValueError("No valid wind data found")
        
        # Calculate statistics
        avg_speed = float(np.mean(wind_speeds))
        max_speed = float(np.max(wind_speeds))
        
        # Find dominant direction using histogram
        # Weight by wind speed (stronger winds are more important)
        direction_bins = np.arange(0, 361, 45)  # 8 directions
        weighted_hist, _ = np.histogram(
            wind_directions,
            bins=direction_bins,
            weights=wind_speeds
        )
        
        # Find dominant bin
        dominant_bin = np.argmax(weighted_hist)
        dominant_direction = float(dominant_bin * 45 + 22.5)  # Center of bin
        
        # Calculate direction frequencies
        direction_names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        total_weight = np.sum(weighted_hist)
        frequencies = {
            name: float(weight / total_weight)
            for name, weight in zip(direction_names, weighted_hist)
        }
        
        return WindData(
            dominant_direction=dominant_direction,
            dominant_direction_name=direction_names[dominant_bin],
            average_speed=avg_speed,
            max_speed=max_speed,
            direction_frequencies=frequencies,
            latitude=latitude,
            longitude=longitude,
            data_period_days=days
        )
    
    def _get_fallback(
        self,
        latitude: float,
        longitude: float,
        days: int
    ) -> WindData:
        """Get fallback data when API fails."""
        return WindData(
            dominant_direction=self.TURKEY_FALLBACK["dominant_direction"],
            dominant_direction_name="NE",
            average_speed=self.TURKEY_FALLBACK["average_speed"],
            max_speed=self.TURKEY_FALLBACK["max_speed"],
            direction_frequencies={
                "N": 0.10, "NE": 0.25, "E": 0.15, "SE": 0.10,
                "S": 0.10, "SW": 0.10, "W": 0.10, "NW": 0.10
            },
            latitude=latitude,
            longitude=longitude,
            data_period_days=days
        )


class WindAlignmentCalculator:
    """
    Calculate wind alignment scores for roads and buildings.
    
    Rewards roads that are aligned with the dominant wind direction,
    creating natural ventilation corridors.
    """
    
    def __init__(self, wind_data: WindData):
        """
        Initialize with wind data.
        
        Args:
            wind_data: WindData from fetcher
        """
        self.wind_data = wind_data
        self.dominant_rad = wind_data.dominant_direction_radians
    
    def road_alignment_score(
        self,
        road_start: Tuple[float, float],
        road_end: Tuple[float, float]
    ) -> float:
        """
        Calculate alignment score for a road segment.
        
        Score = cos²(angle_difference)
        - 1.0 = Road perfectly aligned with wind
        - 0.0 = Road perpendicular to wind
        
        Args:
            road_start: (x, y) start point
            road_end: (x, y) end point
            
        Returns:
            Alignment score 0-1
        """
        # Calculate road direction
        dx = road_end[0] - road_start[0]
        dy = road_end[1] - road_start[1]
        
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            return 0.5  # Degenerate segment
        
        road_angle = np.arctan2(dy, dx)
        
        # Calculate angle difference
        # Roads are bidirectional, so we use the absolute difference mod π
        angle_diff = abs(road_angle - self.dominant_rad)
        angle_diff = angle_diff % np.pi  # Normalize to [0, π]
        if angle_diff > np.pi / 2:
            angle_diff = np.pi - angle_diff  # Mirror for bidirectional
        
        # Score using cos²
        score = np.cos(angle_diff) ** 2
        
        return float(score)
    
    def road_network_score(
        self,
        roads: List[np.ndarray]
    ) -> Tuple[float, Dict]:
        """
        Calculate total alignment score for a road network.
        
        Weights each road segment by its length.
        
        Args:
            roads: List of road polylines (each is np.ndarray of shape (M, 2))
            
        Returns:
            Tuple of (total_score, details_dict)
        """
        total_length = 0.0
        weighted_score = 0.0
        segment_scores = []
        
        for road_idx, road in enumerate(roads):
            if len(road) < 2:
                continue
            
            for i in range(len(road) - 1):
                start = tuple(road[i])
                end = tuple(road[i + 1])
                
                # Calculate segment length
                length = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                
                if length < 1.0:  # Skip very short segments
                    continue
                
                # Calculate alignment score
                score = self.road_alignment_score(start, end)
                
                weighted_score += score * length
                total_length += length
                
                segment_scores.append({
                    "road_idx": road_idx,
                    "segment_idx": i,
                    "length": length,
                    "score": score
                })
        
        if total_length < 1.0:
            return 0.5, {"segment_scores": [], "total_length": 0}
        
        avg_score = weighted_score / total_length
        
        return avg_score, {
            "segment_scores": segment_scores,
            "total_length": total_length,
            "num_segments": len(segment_scores),
            "dominant_direction": self.wind_data.dominant_direction,
            "dominant_direction_name": self.wind_data.dominant_direction_name
        }
    
    def building_orientation_score(
        self,
        building_orientation: float,  # radians
        building_width: float,
        building_depth: float
    ) -> float:
        """
        Calculate wind score for a building orientation.
        
        Buildings with their long axis parallel to wind have better ventilation.
        
        Args:
            building_orientation: Building rotation in radians
            building_width: Building width (x-axis before rotation)
            building_depth: Building depth (y-axis before rotation)
            
        Returns:
            Score 0-1 (higher = better ventilation)
        """
        # Determine which axis is longer
        if building_width >= building_depth:
            # Long axis is along x (before rotation)
            long_axis_angle = building_orientation
        else:
            # Long axis is along y (before rotation)
            long_axis_angle = building_orientation + np.pi / 2
        
        # Calculate alignment with wind
        angle_diff = abs(long_axis_angle - self.dominant_rad)
        angle_diff = angle_diff % np.pi
        if angle_diff > np.pi / 2:
            angle_diff = np.pi - angle_diff
        
        # Score: higher when long axis parallel to wind
        score = np.cos(angle_diff) ** 2
        
        return float(score)


class WindPenaltyCalculator:
    """
    Calculate wind optimization penalties for building layouts.
    
    Integrates with the optimizer to penalize layouts that block
    natural ventilation corridors.
    """
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        wind_data: WindData = None
    ):
        """
        Initialize penalty calculator.
        
        Args:
            latitude: Site latitude
            longitude: Site longitude
            wind_data: Pre-fetched wind data (optional, will fetch if None)
        """
        self.latitude = latitude
        self.longitude = longitude
        
        if wind_data is None:
            fetcher = WindDataFetcher()
            self.wind_data = fetcher.fetch(latitude, longitude)
        else:
            self.wind_data = wind_data
        
        self.alignment_calc = WindAlignmentCalculator(self.wind_data)
    
    def calculate_penalty(
        self,
        roads: List[np.ndarray],
        buildings: List[Tuple[float, float, float]] = None  # (orientation, width, depth)
    ) -> Tuple[float, Dict]:
        """
        Calculate total wind penalty for a layout.
        
        Lower score = worse ventilation = higher penalty
        
        Args:
            roads: List of road polylines
            buildings: Optional list of (orientation, width, depth) tuples
            
        Returns:
            Tuple of (penalty, details)
        """
        # Road alignment score (0-1, higher is better)
        road_score, road_details = self.alignment_calc.road_network_score(roads)
        
        # Convert to penalty (0 = perfect, 1 = worst)
        road_penalty = 1.0 - road_score
        
        # Building orientation score (optional)
        building_penalty = 0.0
        building_scores = []
        
        if buildings:
            for i, (orientation, width, depth) in enumerate(buildings):
                score = self.alignment_calc.building_orientation_score(
                    orientation, width, depth
                )
                building_scores.append({
                    "building_idx": i,
                    "score": score
                })
                building_penalty += (1.0 - score)
            
            if len(buildings) > 0:
                building_penalty /= len(buildings)
        
        # Combined penalty (weight roads more heavily)
        total_penalty = 0.7 * road_penalty + 0.3 * building_penalty
        
        return total_penalty, {
            "road_score": road_score,
            "road_penalty": road_penalty,
            "building_penalty": building_penalty,
            "building_scores": building_scores,
            "total_penalty": total_penalty,
            "wind_data": {
                "dominant_direction": self.wind_data.dominant_direction,
                "dominant_direction_name": self.wind_data.dominant_direction_name,
                "average_speed": self.wind_data.average_speed
            }
        }


# Convenience functions
def fetch_wind_data(
    latitude: float = 41.3833,
    longitude: float = 33.7833,
    days: int = 365
) -> WindData:
    """Fetch wind data for a location."""
    fetcher = WindDataFetcher()
    return fetcher.fetch(latitude, longitude, days)


def quick_wind_score(
    roads: List[np.ndarray],
    latitude: float = 41.3833,
    longitude: float = 33.7833
) -> float:
    """
    Quick wind alignment score for roads.
    
    Returns score 0-1 (higher = better alignment with wind).
    """
    fetcher = WindDataFetcher()
    wind_data = fetcher.fetch(latitude, longitude)
    calc = WindAlignmentCalculator(wind_data)
    score, _ = calc.road_network_score(roads)
    return score
