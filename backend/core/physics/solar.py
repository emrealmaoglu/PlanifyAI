"""
Solar Position and Shadow Analysis for Campus Planning.

Uses pysolar for accurate sun position calculations.
Implements shadow casting geometry for building optimization.
"""

import numpy as np
from datetime import datetime, timezone
from typing import Tuple, List, Optional
from dataclasses import dataclass
from pysolar.solar import get_altitude, get_azimuth
from shapely.geometry import Polygon, LineString, Point
from shapely.affinity import translate


@dataclass
class SunPosition:
    """Sun position at a specific time and location."""
    altitude: float      # Degrees above horizon (0-90)
    azimuth: float       # Degrees from North, clockwise (0-360)
    timestamp: datetime
    latitude: float
    longitude: float
    
    @property
    def is_daytime(self) -> bool:
        """Check if sun is above horizon."""
        return self.altitude > 0
    
    @property
    def shadow_direction(self) -> float:
        """
        Direction shadows point (opposite to sun azimuth).
        Returns angle in radians, 0 = East, π/2 = North.
        """
        # Sun azimuth is from North clockwise
        # Shadow points opposite direction
        shadow_azimuth = (self.azimuth + 180) % 360
        
        # Convert to math angle (0 = East, counter-clockwise)
        # North (0°) → π/2, East (90°) → 0, South (180°) → -π/2
        math_angle = np.radians(90 - shadow_azimuth)
        return math_angle
    
    def shadow_length_multiplier(self) -> float:
        """
        Shadow length as multiple of object height.
        shadow_length = height * multiplier
        """
        if self.altitude <= 0:
            return float('inf')  # No sun
        if self.altitude >= 90:
            return 0.0  # Sun directly overhead
        return 1.0 / np.tan(np.radians(self.altitude))


class SolarCalculator:
    """
    Calculate sun positions for a specific location.
    
    Example:
        calc = SolarCalculator(lat=41.3833, lon=33.7833)  # Kastamonu
        pos = calc.get_position(datetime(2024, 12, 21, 12, 0))
        print(f"Sun altitude: {pos.altitude}°")
    """
    
    def __init__(self, latitude: float, longitude: float):
        """
        Initialize calculator for a location.
        
        Args:
            latitude: Degrees north (negative for south)
            longitude: Degrees east (negative for west)
        """
        self.latitude = latitude
        self.longitude = longitude
    
    def get_position(self, dt: datetime) -> SunPosition:
        """
        Get sun position at a specific time.
        
        Args:
            dt: Datetime (should be timezone-aware, defaults to UTC)
            
        Returns:
            SunPosition with altitude and azimuth
        """
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        altitude = get_altitude(self.latitude, self.longitude, dt)
        azimuth = get_azimuth(self.latitude, self.longitude, dt)
        
        return SunPosition(
            altitude=altitude,
            azimuth=azimuth,
            timestamp=dt,
            latitude=self.latitude,
            longitude=self.longitude
        )
    
    def get_daily_positions(
        self,
        date: datetime,
        hours: List[int] = None
    ) -> List[SunPosition]:
        """
        Get sun positions throughout a day.
        
        Args:
            date: Date to analyze
            hours: List of hours (default: 6-18)
            
        Returns:
            List of SunPosition for each hour
        """
        if hours is None:
            hours = list(range(6, 19))  # 6 AM to 6 PM
        
        positions = []
        for hour in hours:
            dt = date.replace(hour=hour, minute=0, second=0, tzinfo=timezone.utc)
            positions.append(self.get_position(dt))
        
        return positions
    
    def get_worst_case_date(self) -> datetime:
        """
        Get winter solstice date (worst case for shadows).
        Northern hemisphere: Dec 21
        Southern hemisphere: Jun 21
        """
        year = datetime.now().year
        if self.latitude >= 0:
            return datetime(year, 12, 21, 12, 0, tzinfo=timezone.utc)
        else:
            return datetime(year, 6, 21, 12, 0, tzinfo=timezone.utc)


@dataclass
class Shadow:
    """A shadow cast by a building."""
    source_building_id: int
    source_polygon: Polygon
    shadow_polygon: Polygon
    sun_position: SunPosition
    
    @property
    def area(self) -> float:
        return self.shadow_polygon.area


class ShadowCalculator:
    """
    Calculate shadows cast by buildings.
    
    Shadow geometry is computed by:
    1. Projecting each vertex of building footprint in shadow direction
    2. Projection distance = height * shadow_length_multiplier
    3. Creating polygon from original + projected vertices
    """
    
    def __init__(self, solar_calc: SolarCalculator):
        """
        Initialize shadow calculator.
        
        Args:
            solar_calc: SolarCalculator for the site location
        """
        self.solar_calc = solar_calc
    
    def calculate_shadow(
        self,
        building_polygon: Polygon,
        building_height: float,
        sun_position: SunPosition,
        building_id: int = 0
    ) -> Optional[Shadow]:
        """
        Calculate shadow cast by a building.
        
        Args:
            building_polygon: Building footprint (Shapely Polygon)
            building_height: Building height in meters
            sun_position: Current sun position
            building_id: ID for tracking
            
        Returns:
            Shadow object or None if no shadow (sun below horizon)
        """
        if not sun_position.is_daytime:
            return None
        
        # Calculate shadow projection
        multiplier = sun_position.shadow_length_multiplier()
        shadow_length = building_height * multiplier
        
        # Cap shadow length to reasonable maximum (500m)
        shadow_length = min(shadow_length, 500)
        
        # Shadow direction (in radians, math convention)
        direction = sun_position.shadow_direction
        
        # Calculate offset vector
        dx = shadow_length * np.cos(direction)
        dy = shadow_length * np.sin(direction)
        
        # Project building footprint
        projected = translate(building_polygon, xoff=dx, yoff=dy)
        
        # Create shadow polygon by combining original and projected
        # This creates a "stretched" shadow shape
        try:
            shadow_polygon = building_polygon.union(projected).convex_hull
        except Exception:
            # Fallback: just use projected polygon
            shadow_polygon = projected
        
        return Shadow(
            source_building_id=building_id,
            source_polygon=building_polygon,
            shadow_polygon=shadow_polygon,
            sun_position=sun_position
        )
    
    def calculate_all_shadows(
        self,
        buildings: List[Tuple[int, Polygon, float]],  # (id, polygon, height)
        sun_position: SunPosition
    ) -> List[Shadow]:
        """
        Calculate shadows for all buildings.
        
        Args:
            buildings: List of (id, polygon, height) tuples
            sun_position: Current sun position
            
        Returns:
            List of Shadow objects
        """
        shadows = []
        for building_id, polygon, height in buildings:
            shadow = self.calculate_shadow(polygon, height, sun_position, building_id)
            if shadow:
                shadows.append(shadow)
        return shadows


class SolarPenaltyCalculator:
    """
    Calculate solar access penalties for building layouts.
    
    Penalty is based on:
    1. Shadow overlap with other buildings' south facades
    2. Shadow coverage during peak sun hours (10:00-14:00)
    3. Winter solstice worst-case analysis
    """
    
    # Peak hours for shadow analysis
    PEAK_HOURS = [10, 11, 12, 13, 14]
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        south_facade_weight: float = 2.0
    ):
        """
        Initialize penalty calculator.
        
        Args:
            latitude: Site latitude
            longitude: Site longitude
            south_facade_weight: Extra penalty for south facade shadows
        """
        self.solar_calc = SolarCalculator(latitude, longitude)
        self.shadow_calc = ShadowCalculator(self.solar_calc)
        self.south_facade_weight = south_facade_weight
    
    def get_south_facade(self, polygon: Polygon, buffer: float = 5.0) -> Polygon:
        """
        Get the south-facing portion of a building.
        
        South facade is the southern edge of the bounding box,
        buffered slightly for shadow detection.
        """
        minx, miny, maxx, maxy = polygon.bounds
        
        # South facade is bottom edge
        south_line = LineString([(minx, miny), (maxx, miny)])
        
        # Buffer to create a strip
        return south_line.buffer(buffer)
    
    def calculate_penalty(
        self,
        buildings: List[Tuple[int, Polygon, float]],  # (id, polygon, height)
        analysis_date: datetime = None
    ) -> Tuple[float, dict]:
        """
        Calculate total solar penalty for a building layout.
        
        Args:
            buildings: List of (id, polygon, height) tuples
            analysis_date: Date for analysis (default: winter solstice)
            
        Returns:
            Tuple of (total_penalty, details_dict)
        """
        if analysis_date is None:
            analysis_date = self.solar_calc.get_worst_case_date()
        
        total_penalty = 0.0
        details = {
            "analysis_date": analysis_date.isoformat(),
            "peak_hours": self.PEAK_HOURS,
            "hour_penalties": {},
            "shadow_overlaps": []
        }
        
        # Analyze each peak hour
        for hour in self.PEAK_HOURS:
            dt = analysis_date.replace(hour=hour, minute=0, second=0)
            sun_pos = self.solar_calc.get_position(dt)
            
            if not sun_pos.is_daytime:
                continue
            
            # Calculate all shadows
            shadows = self.shadow_calc.calculate_all_shadows(buildings, sun_pos)
            
            hour_penalty = 0.0
            
            # Check shadow overlap with other buildings
            for shadow in shadows:
                for other_id, other_polygon, other_height in buildings:
                    # Skip self-shadowing
                    if other_id == shadow.source_building_id:
                        continue
                    
                    # Check if shadow hits building
                    if shadow.shadow_polygon.intersects(other_polygon):
                        overlap = shadow.shadow_polygon.intersection(other_polygon)
                        overlap_area = overlap.area
                        
                        # Extra penalty for south facade
                        south_facade = self.get_south_facade(other_polygon)
                        if shadow.shadow_polygon.intersects(south_facade):
                            south_overlap = shadow.shadow_polygon.intersection(south_facade)
                            overlap_area += south_overlap.area * self.south_facade_weight
                        
                        hour_penalty += overlap_area
                        
                        details["shadow_overlaps"].append({
                            "hour": hour,
                            "source_building": shadow.source_building_id,
                            "affected_building": other_id,
                            "overlap_area": overlap_area
                        })
            
            details["hour_penalties"][hour] = hour_penalty
            total_penalty += hour_penalty
        
        # Normalize by number of hours
        total_penalty /= len(self.PEAK_HOURS)
        
        return total_penalty, details
    
    def calculate_building_pair_penalty(
        self,
        building1: Tuple[Polygon, float],  # (polygon, height)
        building2: Tuple[Polygon, float],
        analysis_date: datetime = None
    ) -> float:
        """
        Quick penalty check for two buildings.
        Useful for incremental evaluation during optimization.
        """
        if analysis_date is None:
            analysis_date = self.solar_calc.get_worst_case_date()
        
        poly1, height1 = building1
        poly2, height2 = building2
        
        total_penalty = 0.0
        
        # Check noon shadow only (quick approximation)
        dt = analysis_date.replace(hour=12, minute=0, second=0)
        sun_pos = self.solar_calc.get_position(dt)
        
        if not sun_pos.is_daytime:
            return 0.0
        
        # Building 1 shadows Building 2
        shadow1 = self.shadow_calc.calculate_shadow(poly1, height1, sun_pos)
        if shadow1 and shadow1.shadow_polygon.intersects(poly2):
            overlap = shadow1.shadow_polygon.intersection(poly2)
            total_penalty += overlap.area
        
        # Building 2 shadows Building 1
        shadow2 = self.shadow_calc.calculate_shadow(poly2, height2, sun_pos)
        if shadow2 and shadow2.shadow_polygon.intersects(poly1):
            overlap = shadow2.shadow_polygon.intersection(poly1)
            total_penalty += overlap.area
        
        return total_penalty


# Convenience functions
def create_solar_penalty_calculator(
    latitude: float = 41.3833,  # Kastamonu default
    longitude: float = 33.7833
) -> SolarPenaltyCalculator:
    """Create a solar penalty calculator for a location."""
    return SolarPenaltyCalculator(latitude, longitude)


def quick_shadow_check(
    buildings: List[Tuple[Polygon, float]],
    latitude: float = 41.3833,
    longitude: float = 33.7833
) -> float:
    """
    Quick shadow penalty calculation for a building layout.
    
    Args:
        buildings: List of (polygon, height) tuples
        latitude: Site latitude
        longitude: Site longitude
        
    Returns:
        Total shadow penalty (lower is better)
    """
    calc = SolarPenaltyCalculator(latitude, longitude)
    
    # Convert to expected format
    building_tuples = [(i, poly, height) for i, (poly, height) in enumerate(buildings)]
    
    penalty, _ = calc.calculate_penalty(building_tuples)
    return penalty
