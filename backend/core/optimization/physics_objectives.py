"""
Phase 7: Physics Objectives for H-SAGA Optimization.

This module implements environmental physics calculations:
- Wind Blockage: Penalize buildings that block prevailing wind flow
- Solar Gain: Reward south-facing facades and penalize self-shadowing

Research Sources:
- 3D Urban Design Optimization Analysis (Wind Rose Logic)
- Building Energy Modeling Integration (Solar Access)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from shapely.geometry import Polygon, Point, LineString, box
from shapely.affinity import rotate

from backend.core.optimization.encoding import (
    BuildingGene, BUILDING_TYPES, TYPE_ID_TO_NAME,
    get_building_centroids
)


# =============================================================================
# WIND DATA STRUCTURES
# =============================================================================

@dataclass
class WindVector:
    """Represents prevailing wind conditions."""
    direction_deg: float    # Degrees from North (0=N, 90=E, 180=S, 270=W)
    speed_ms: float         # Average wind speed in m/s
    
    @property
    def direction_rad(self) -> float:
        """Direction in radians."""
        return np.radians(self.direction_deg)
    
    @property
    def vector(self) -> np.ndarray:
        """Unit vector pointing in wind direction (from source to target)."""
        # North = 0°, East = 90° (meteorological convention)
        angle_rad = np.radians(self.direction_deg)
        return np.array([np.sin(angle_rad), np.cos(angle_rad)])
    
    @classmethod
    def from_dominant_direction(cls, direction_name: str, speed: float = 5.0) -> "WindVector":
        """Create from compass direction name."""
        directions = {
            "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
            "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
            "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
            "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5
        }
        return cls(directions.get(direction_name.upper(), 0), speed)


# Kastamonu Default Wind (NNE = North-Northeast)
DEFAULT_WIND = WindVector(direction_deg=22.5, speed_ms=3.5)


# =============================================================================
# WIND BLOCKAGE CALCULATOR
# =============================================================================

class WindBlockageCalculator:
    """
    Calculates wind blockage penalty for building layouts.
    
    Physics Model:
    - Buildings perpendicular to wind create "blockage" (bad)
    - Buildings aligned with wind create "corridors" (good)
    - Downstream buildings in wake zone receive penalty
    
    Research Reference: 3D Urban Design Optimization Analysis.docx
    """
    
    def __init__(
        self,
        wind: WindVector = None,
        wake_length_factor: float = 3.0,  # Wake extends 3x building width
        blockage_penalty_factor: float = 1.0
    ):
        self.wind = wind or DEFAULT_WIND
        self.wake_length_factor = wake_length_factor
        self.blockage_penalty_factor = blockage_penalty_factor
    
    def calculate_blockage(
        self,
        genes: List[BuildingGene],
        polygons: List[Polygon]
    ) -> float:
        """
        Calculate total wind blockage penalty.
        
        Penalty Components:
        1. Perpendicular Exposure: Wide facades facing wind
        2. Wake Zone Overlap: Buildings in upstream wake
        
        Returns:
            Normalized penalty score (lower = better wind flow)
        """
        if len(genes) < 2:
            return 0.0
        
        total_penalty = 0.0
        wind_vec = self.wind.vector
        wind_angle = self.wind.direction_rad
        
        centroids = get_building_centroids(genes)
        n = len(genes)
        
        # Component 1: Perpendicular Exposure
        for i, gene in enumerate(genes):
            exposed_width = self._calculate_exposed_width(gene, wind_angle)
            # Normalize by building footprint area
            footprint = gene.footprint_area
            if footprint > 0:
                exposure_ratio = exposed_width / np.sqrt(footprint)
                total_penalty += exposure_ratio * self.blockage_penalty_factor
        
        # Component 2: Wake Zone Interference
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                # Check if building j is in wake of building i
                wake_penalty = self._calculate_wake_penalty(
                    centroids[i], genes[i],
                    centroids[j], genes[j],
                    wind_vec
                )
                total_penalty += wake_penalty
        
        # Normalize by building count
        normalized = total_penalty / max(n, 1)
        
        return normalized
    
    def _calculate_exposed_width(
        self,
        gene: BuildingGene,
        wind_angle: float
    ) -> float:
        """
        Calculate effective width of building perpendicular to wind.
        
        A building rotated to align with wind has lower exposed width.
        """
        # Building rotation relative to wind
        relative_angle = gene.rotation - wind_angle
        
        # Effective dimensions exposed to wind
        # cos(θ) of building width + sin(θ) of building depth
        abs_cos = abs(np.cos(relative_angle))
        abs_sin = abs(np.sin(relative_angle))
        
        exposed_width = gene.width * abs_cos + gene.depth * abs_sin
        
        return exposed_width
    
    def _calculate_wake_penalty(
        self,
        upstream_pos: np.ndarray,
        upstream_gene: BuildingGene,
        downstream_pos: np.ndarray,
        downstream_gene: BuildingGene,
        wind_vec: np.ndarray
    ) -> float:
        """
        Calculate penalty for building in wake zone of another.
        
        Wake zone extends downwind from each building.
        """
        # Vector from upstream to downstream
        delta = downstream_pos - upstream_pos
        distance = np.linalg.norm(delta)
        
        if distance < 1e-6:
            return 0.0
        
        # Check if downstream is actually downstream (in wind direction)
        direction = delta / distance
        alignment = np.dot(direction, wind_vec)
        
        if alignment < 0.3:  # Not in downstream direction
            return 0.0
        
        # Wake extends based on upstream building width
        wake_length = upstream_gene.width * self.wake_length_factor
        
        if distance > wake_length:  # Beyond wake zone
            return 0.0
        
        # Wake penalty decreases with distance
        wake_strength = 1.0 - (distance / wake_length)
        
        # Scale by downstream building size
        penalty = wake_strength * downstream_gene.footprint_area / 1000.0
        
        return penalty * alignment  # Stronger when directly aligned


# =============================================================================
# SOLAR GAIN CALCULATOR
# =============================================================================

class SolarGainCalculator:
    """
    Calculates solar access and shading penalties.
    
    Physics Model:
    - South-facing facades receive more solar radiation (Northern Hemisphere)
    - Buildings create shadows that affect neighbors
    - Shadow length depends on building height and sun angle
    
    Research Reference: Building Energy Modeling Integration.docx
    """
    
    def __init__(
        self,
        latitude: float = 41.38,  # Kastamonu default
        winter_sun_altitude: float = 25.0,  # Degrees above horizon (winter solstice)
        solar_penalty_factor: float = 1.0
    ):
        self.latitude = latitude
        self.winter_sun_altitude = winter_sun_altitude
        self.solar_penalty_factor = solar_penalty_factor
        
        # Sun comes from South in Northern Hemisphere
        self.sun_azimuth = 180.0  # Degrees (South)
        
        # Shadow multiplier (height * multiplier = shadow length)
        self.shadow_multiplier = 1.0 / np.tan(np.radians(winter_sun_altitude))
    
    def calculate_solar_penalty(
        self,
        genes: List[BuildingGene],
        polygons: List[Polygon]
    ) -> float:
        """
        Calculate total solar penalty.
        
        Penalty Components:
        1. Orientation Penalty: Facades not facing south
        2. Shadow Penalty: Buildings in shadow of taller neighbors
        
        Returns:
            Normalized penalty score (lower = better solar access)
        """
        if len(genes) < 1:
            return 0.0
        
        total_penalty = 0.0
        centroids = get_building_centroids(genes)
        n = len(genes)
        
        # Component 1: Orientation Penalty
        for gene in genes:
            orientation_penalty = self._calculate_orientation_penalty(gene)
            total_penalty += orientation_penalty * self.solar_penalty_factor
        
        # Component 2: Shadow Interference
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                shadow_penalty = self._calculate_shadow_penalty(
                    centroids[i], genes[i],
                    centroids[j], genes[j]
                )
                total_penalty += shadow_penalty
        
        # Normalize
        normalized = total_penalty / max(n, 1)
        
        return normalized
    
    def _calculate_orientation_penalty(self, gene: BuildingGene) -> float:
        """
        Penalize buildings not oriented toward south.
        
        Optimal: Long facade facing south (rotation = π/2 or -π/2)
        """
        # Convert building rotation to facade direction
        # Building with rotation=0 has long facade facing East/West
        # Building with rotation=π/2 has long facade facing North/South
        
        # We want long facade (width > depth) to face south
        rotation_deg = np.degrees(gene.rotation) % 360
        
        # Ideal rotation for south-facing long facade: 0° or 180°
        # (perpendicular to south = long side faces south)
        
        angle_diff = abs((rotation_deg % 180) - 90)  # Distance from 90° or 270°
        
        # Normalize: 0 at ideal, 1 at worst
        penalty = angle_diff / 90.0
        
        # Weight by building floor area (larger buildings = larger penalty)
        weight = gene.total_floor_area / 5000.0  # Normalize by typical building
        
        return penalty * weight
    
    def _calculate_shadow_penalty(
        self,
        caster_pos: np.ndarray,
        caster_gene: BuildingGene,
        receiver_pos: np.ndarray,
        receiver_gene: BuildingGene
    ) -> float:
        """
        Calculate penalty for building in shadow of another.
        
        Shadow is cast northward (sun from south).
        """
        # Shadow direction (opposite of sun = northward)
        shadow_direction = np.array([0.0, 1.0])  # North
        
        # Vector from caster to receiver
        delta = receiver_pos - caster_pos
        distance = np.linalg.norm(delta)
        
        if distance < 1e-6:
            return 0.0
        
        direction = delta / distance
        
        # Check if receiver is north of caster (in shadow zone)
        alignment = np.dot(direction, shadow_direction)
        
        if alignment < 0.3:  # Not north enough
            return 0.0
        
        # Calculate shadow length from caster height
        shadow_length = caster_gene.height * self.shadow_multiplier
        
        if distance > shadow_length:  # Beyond shadow
            return 0.0
        
        # Shadow intensity decreases with distance
        shadow_intensity = 1.0 - (distance / shadow_length)
        
        # Check lateral overlap (is receiver within shadow width?)
        lateral_distance = abs(np.dot(delta, np.array([1.0, 0.0])))
        caster_half_width = caster_gene.width / 2
        
        if lateral_distance > caster_half_width + receiver_gene.width / 2:
            return 0.0  # No lateral overlap
        
        # Penalty proportional to receiver's solar-dependent area
        # Dormitories and Social buildings care more about sunlight
        type_weight = self._get_solar_sensitivity(receiver_gene.type_name)
        
        penalty = shadow_intensity * alignment * type_weight
        
        return penalty
    
    def _get_solar_sensitivity(self, building_type: str) -> float:
        """
        Get solar sensitivity weight by building type.
        
        Some buildings benefit more from sunlight.
        """
        sensitivities = {
            "Dormitory": 1.5,   # Students need natural light
            "Library": 1.3,    # Reading areas
            "Social": 1.2,     # Gathering spaces
            "Dining": 1.0,     # Moderate need
            "Faculty": 0.8,    # Offices - moderate
            "Research": 0.7,   # Labs may prefer controlled light
            "Sports": 0.5,     # Less dependent
            "Rectory": 0.8,    # Administrative
        }
        return sensitivities.get(building_type, 1.0)


# =============================================================================
# PHYSICS OBJECTIVE INTEGRATOR
# =============================================================================

class PhysicsObjectiveCalculator:
    """
    Unified calculator for all physics-based objectives.
    
    Integrates wind and solar calculations with configurable weights.
    """
    
    def __init__(
        self,
        wind_calculator: WindBlockageCalculator = None,
        solar_calculator: SolarGainCalculator = None,
        enable_wind: bool = True,
        enable_solar: bool = True
    ):
        self.wind_calc = wind_calculator or WindBlockageCalculator()
        self.solar_calc = solar_calculator or SolarGainCalculator()
        self.enable_wind = enable_wind
        self.enable_solar = enable_solar
    
    def calculate_all(
        self,
        genes: List[BuildingGene],
        polygons: List[Polygon],
        weights: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        Calculate all physics objectives.
        
        Args:
            genes: Building genes
            polygons: Decoded polygons
            weights: Optional weight overrides
        
        Returns:
            Dict with 'wind' and 'solar' penalties
        """
        weights = weights or {"wind": 1.0, "solar": 1.0}
        
        results = {}
        
        if self.enable_wind:
            wind_raw = self.wind_calc.calculate_blockage(genes, polygons)
            results["wind"] = wind_raw * weights.get("wind", 1.0)
        else:
            results["wind"] = 0.0
        
        if self.enable_solar:
            solar_raw = self.solar_calc.calculate_solar_penalty(genes, polygons)
            results["solar"] = solar_raw * weights.get("solar", 1.0)
        else:
            results["solar"] = 0.0
        
        return results
    
    def get_wind_score(
        self,
        genes: List[BuildingGene],
        polygons: List[Polygon],
        weight: float = 1.0
    ) -> float:
        """Get weighted wind blockage score."""
        if not self.enable_wind:
            return 0.0
        return self.wind_calc.calculate_blockage(genes, polygons) * weight
    
    def get_solar_score(
        self,
        genes: List[BuildingGene],
        polygons: List[Polygon],
        weight: float = 1.0
    ) -> float:
        """Get weighted solar penalty score."""
        if not self.enable_solar:
            return 0.0
        return self.solar_calc.calculate_solar_penalty(genes, polygons) * weight
