"""
Phase 8: Spatial Optimization Problem Definition with Regulatory Compliance.

This module provides the PyMOO problem formulation that integrates:
- SiteParameters (Setbacks from Turkish Zoning Laws)
- OptimizationGoals (Weighted objectives including Physics)
- CampusContext (Boundary and existing infrastructure)
- Physics: Wind Blockage and Solar Gain (Phase 7)
- Regulatory: Slope, Dynamic Setbacks, Fire Separation (Phase 8)

The problem uses the encoding from encoding.py and produces
constraint violations and objective values for H-SAGA.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from math import sqrt

from pymoo.core.problem import ElementwiseProblem
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from shapely import prepared
from shapely import STRtree  # R-tree spatial index for O(n log n) queries

# Local imports
from backend.core.optimization.encoding import (
    BuildingGene, BuildingTypeSpec, BUILDING_TYPES,
    GENES_PER_BUILDING, TYPE_ID_TO_NAME, TYPE_NAME_TO_ID,
    array_to_genome, decode_to_polygon, decode_all_to_polygons,
    calculate_variable_bounds, get_building_centroids, get_type_indices
)
from backend.core.domain.geometry.osm_service import CampusContext
from backend.core.schemas.input import SiteParameters, OptimizationGoal

# Phase 7: Physics imports
from backend.core.optimization.physics_objectives import (
    WindBlockageCalculator, SolarGainCalculator,
    PhysicsObjectiveCalculator, WindVector, DEFAULT_WIND
)

# Phase 8: Terrain imports
from backend.core.terrain.elevation import DEMSampler, SlopeCalculator


# =============================================================================
# CONSTRAINT CALCULATORS (Phase 8: Regulatory Enhanced)
# =============================================================================

class ConstraintCalculator:
    """
    Calculates hard constraint violations for spatial layouts.
    
    Phase 8: Now includes regulatory constraints:
    - Slope Analysis (max 15%)
    - Dynamic Setbacks (Front: 5m, Side: 3m)
    - Fire Separation (max(6m, H/2))
    
    All constraints return values where:
        <= 0: Constraint satisfied
        > 0:  Constraint violated (value = violation magnitude)
    """
    
    MAX_SLOPE = 0.15  # 15% slope limit
    BASE_FIRE_SEPARATION = 6.0  # meters
    FACING_ROAD_THRESHOLD = 0.7  # cos(45°) for edge facing detection
    
    def __init__(
        self,
        boundary: Polygon,
        site_params: SiteParameters,
        road_geometries: List[LineString] = None,
        dem_sampler: DEMSampler = None
    ):
        self.boundary = boundary
        self.prepared_boundary = prepared.prep(boundary)
        self.site_params = site_params
        self.road_geometries = road_geometries or []
        
        # Phase 8: DEM for slope analysis
        self.dem_sampler = dem_sampler or DEMSampler(offline_mode=True)
        self.slope_calc = SlopeCalculator(self.dem_sampler)
        
        # Create buffered boundary for setback checks
        self.inner_boundary = boundary.buffer(-site_params.setback_front)
        
    def __getstate__(self):
        """Custom pickling state - remove prepared geometries."""
        state = self.__dict__.copy()
        # prepared objects are not picklable
        if 'prepared_boundary' in state:
            del state['prepared_boundary']
        # STRtree is not picklable in older shapely versions, but is in 2.0+
        # To be safe, we'll exclude it if we were caching it (we aren't currently caching it in __init__)
        return state

    def __setstate__(self, state):
        """Restore state and re-prepare geometries."""
        self.__dict__.update(state)
        # Re-create prepared boundary
        if hasattr(self, 'boundary'):
            self.prepared_boundary = prepared.prep(self.boundary)
    
    def boundary_violation(self, polygons: List[Polygon]) -> float:
        """
        Calculate total area outside the boundary.
        
        Hard Constraint: All buildings must be inside campus boundary.
        """
        total_violation = 0.0
        
        for poly in polygons:
            if not self.prepared_boundary.contains(poly):
                outside = poly.difference(self.boundary)
                if not outside.is_empty:
                    total_violation += outside.area
        
        return total_violation
    
    def overlap_violation(self, polygons: List[Polygon]) -> float:
        """
        Calculate total overlap area between buildings.
        
        Hard Constraint: Buildings must not intersect.
        
        Uses STRtree for O(n log n) spatial queries instead of O(n²).
        """
        if len(polygons) < 2:
            return 0.0
        
        total_overlap = 0.0
        
        # Build R-tree spatial index
        tree = STRtree(polygons)
        
        # Query potential intersections for each polygon
        for i, poly in enumerate(polygons):
            # Get candidate polygons that might intersect
            candidates_idx = tree.query(poly)
            
            for j in candidates_idx:
                # Only check each pair once (j > i)
                if j > i and polygons[i].intersects(polygons[j]):
                    intersection = polygons[i].intersection(polygons[j])
                    if not intersection.is_empty:
                        total_overlap += intersection.area
        
        return total_overlap
    
    def setback_violation(self, polygons: List[Polygon]) -> float:
        """
        Calculate total setback violation from roads (simple version).
        
        Hard Constraint: Buildings must maintain minimum distance from roads.
        """
        if not self.road_geometries:
            return 0.0
        
        total_violation = 0.0
        min_setback = self.site_params.setback_front
        
        for poly in polygons:
            for road in self.road_geometries:
                distance = poly.distance(road)
                if distance < min_setback:
                    total_violation += (min_setback - distance)
        
        return total_violation
    
    def dynamic_setback_violation(self, polygons: List[Polygon]) -> float:
        """
        Phase 8: Dynamic setback with Front (5m) vs Side (3m) detection.
        
        Uses vector dot product to determine if edge faces a road.
        - Edge facing road → Front setback (5m)
        - Edge not facing road → Side setback (3m)
        
        Hard Constraint: Turkish Urban Planning Standards (Planlı Alanlar İmar Yönetmeliği)
        """
        if not self.road_geometries:
            return 0.0
        
        total_violation = 0.0
        front_setback = self.site_params.setback_front
        side_setback = self.site_params.setback_side
        
        for poly in polygons:
            # Get polygon edges
            coords = list(poly.exterior.coords)
            edges = list(zip(coords[:-1], coords[1:]))
            
            for (x1, y1), (x2, y2) in edges:
                edge_line = LineString([(x1, y1), (x2, y2)])
                edge_midpoint = Point((x1 + x2) / 2, (y1 + y2) / 2)
                
                # Calculate edge normal vector
                edge_vec = np.array([x2 - x1, y2 - y1])
                edge_len = np.linalg.norm(edge_vec)
                if edge_len < 1e-6:
                    continue
                
                # Normal vector (perpendicular to edge)
                edge_normal = np.array([-edge_vec[1], edge_vec[0]]) / edge_len
                
                # Find nearest road
                min_dist = float('inf')
                nearest_point = None
                for road in self.road_geometries:
                    dist = edge_line.distance(road)
                    if dist < min_dist:
                        min_dist = dist
                        # Get nearest point on road
                        proj_dist = road.project(edge_midpoint)
                        nearest_point = road.interpolate(proj_dist)
                
                if nearest_point is None:
                    continue
                
                # Vector from edge midpoint to nearest road point
                to_road = np.array([
                    nearest_point.x - edge_midpoint.x,
                    nearest_point.y - edge_midpoint.y
                ])
                to_road_len = np.linalg.norm(to_road)
                if to_road_len < 1e-6:
                    continue
                to_road_norm = to_road / to_road_len
                
                # Check alignment: if edge normal points toward road, it's "front"
                alignment = abs(np.dot(edge_normal, to_road_norm))
                
                if alignment > self.FACING_ROAD_THRESHOLD:
                    required_setback = front_setback  # 5m
                else:
                    required_setback = side_setback   # 3m
                
                # Check violation
                if min_dist < required_setback:
                    total_violation += (required_setback - min_dist)
        
        return total_violation
    
    def separation_violation(self, polygons: List[Polygon], min_sep: float = 6.0) -> float:
        """
        Calculate total separation violation between buildings (fixed minimum).
        
        Hard Constraint: Minimum 6m between buildings (fire code).
        
        Uses STRtree for O(n log n) spatial queries instead of O(n²).
        """
        if len(polygons) < 2:
            return 0.0
        
        total_violation = 0.0
        
        # Build R-tree spatial index
        tree = STRtree(polygons)
        
        # Query potential neighbors for each polygon using buffer
        for i, poly in enumerate(polygons):
            # Buffer the polygon by min_sep to find potential violations
            search_area = poly.buffer(min_sep)
            candidates_idx = tree.query(search_area)
            
            for j in candidates_idx:
                if j > i:  # Only check each pair once
                    distance = polygons[i].distance(polygons[j])
                    if distance < min_sep:
                        total_violation += (min_sep - distance)
        
        return total_violation
    
    def fire_separation_violation(
        self,
        polygons: List[Polygon],
        genes: List[BuildingGene]
    ) -> float:
        """
        Phase 8: Height-dependent fire separation.
        
        Rule: Separation = max(6.0m, taller_height / 2)
        
        Higher buildings require more separation for fire safety and
        emergency vehicle access.
        
        Hard Constraint: Turkish Fire Safety Code (Derz Boşluğu)
        """
        total_violation = 0.0
        n = len(polygons)
        
        for i in range(n):
            for j in range(i + 1, n):
                # Get building heights
                h_i = genes[i].height
                h_j = genes[j].height
                taller_height = max(h_i, h_j)
                
                # Calculate required separation
                required_sep = max(self.BASE_FIRE_SEPARATION, taller_height / 2)
                
                # Calculate actual distance
                actual_dist = polygons[i].distance(polygons[j])
                
                if actual_dist < required_sep:
                    total_violation += (required_sep - actual_dist)
        
        return total_violation
    
    def slope_violation(self, polygons: List[Polygon]) -> float:
        """
        Phase 8: Terrain slope constraint.
        
        Rule: Construction forbidden on slopes > 15%
        
        Hard Constraint: Turkish Urban Planning Standards
        """
        total_violation = 0.0
        
        for poly in polygons:
            coords = list(poly.exterior.coords[:4])  # Sample corners
            
            # Calculate slope using DEM
            slope = self.slope_calc.calculate_slope_at_polygon(coords)
            
            if slope > self.MAX_SLOPE:
                excess = slope - self.MAX_SLOPE
                total_violation += excess * poly.area
        
        return total_violation


# =============================================================================
# OBJECTIVE CALCULATORS (Geometry + Physics)
# =============================================================================

class ObjectiveCalculator:
    """
    Calculates weighted objectives for spatial optimization.
    
    Phase 7: Now includes physics-based objectives (wind, solar).
    
    All objectives are to be MINIMIZED.
    """
    
    def __init__(
        self,
        boundary: Polygon,
        optimization_goals: Dict[OptimizationGoal, float],
        existing_buildings: List[Polygon] = None,
        latitude: float = 41.38,
        wind_data: WindVector = None
    ):
        self.boundary = boundary
        self.goals = optimization_goals
        self.existing_buildings = existing_buildings or []
        self.latitude = latitude
        
        # Precompute boundary centroid
        self.boundary_centroid = np.array([boundary.centroid.x, boundary.centroid.y])
        
        # Phase 7: Physics calculators
        self.wind_calc = WindBlockageCalculator(wind=wind_data or DEFAULT_WIND)
        self.solar_calc = SolarGainCalculator(latitude=latitude)
        
        # Determine if physics is enabled based on goals
        self.enable_wind = self.goals.get(OptimizationGoal.WIND_COMFORT, 0) > 0
        self.enable_solar = self.goals.get(OptimizationGoal.SOLAR_GAIN, 0) > 0
    
    def compactness(self, genes: List[BuildingGene]) -> float:
        """Calculate compactness penalty (spread-out layouts are bad)."""
        weight = self.goals.get(OptimizationGoal.COMPACTNESS, 0.5)
        if weight == 0:
            return 0.0
        
        if len(genes) < 2:
            return 0.0
        
        centroids = get_building_centroids(genes)
        n = len(centroids)
        total_dist = 0.0
        count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(centroids[i] - centroids[j])
                total_dist += dist
                count += 1
        
        mean_dist = total_dist / count if count > 0 else 0.0
        
        boundary_diag = sqrt(
            (self.boundary.bounds[2] - self.boundary.bounds[0]) ** 2 +
            (self.boundary.bounds[3] - self.boundary.bounds[1]) ** 2
        )
        
        normalized = mean_dist / boundary_diag if boundary_diag > 0 else 0.0
        
        return weight * normalized
    
    def adjacency(self, genes: List[BuildingGene]) -> float:
        """Calculate adjacency penalty for related building types."""
        weight = self.goals.get(OptimizationGoal.ADJACENCY, 0.5)
        if weight == 0:
            return 0.0
        
        adjacency_pairs = [
            ("Dormitory", "Dining"),
            ("Dormitory", "Sports"),
            ("Faculty", "Library"),
            ("Faculty", "Research"),
        ]
        
        total_penalty = 0.0
        centroids = get_building_centroids(genes)
        
        for type_a, type_b in adjacency_pairs:
            indices_a = get_type_indices(genes, type_a)
            indices_b = get_type_indices(genes, type_b)
            
            if not indices_a or not indices_b:
                continue
            
            min_dist = float('inf')
            for i in indices_a:
                for j in indices_b:
                    dist = np.linalg.norm(centroids[i] - centroids[j])
                    min_dist = min(min_dist, dist)
            
            if min_dist < float('inf') and min_dist > 100:
                total_penalty += (min_dist - 100) / 100
        
        return weight * total_penalty
    
    def wind_comfort(self, genes: List[BuildingGene], polygons: List[Polygon]) -> float:
        """Calculate wind blockage penalty (Phase 7)."""
        weight = self.goals.get(OptimizationGoal.WIND_COMFORT, 0.0)
        if weight == 0 or not self.enable_wind:
            return 0.0
        
        raw_score = self.wind_calc.calculate_blockage(genes, polygons)
        return weight * raw_score
    
    def solar_gain(self, genes: List[BuildingGene], polygons: List[Polygon]) -> float:
        """Calculate solar access penalty (Phase 7)."""
        weight = self.goals.get(OptimizationGoal.SOLAR_GAIN, 0.0)
        if weight == 0 or not self.enable_solar:
            return 0.0
        
        raw_score = self.solar_calc.calculate_solar_penalty(genes, polygons)
        return weight * raw_score


# =============================================================================
# SPATIAL OPTIMIZATION PROBLEM (Phase 8 Updated)
# =============================================================================

class SpatialOptimizationProblem(ElementwiseProblem):
    """
    PyMOO problem definition for H-SAGA optimization.
    
    Phase 8 Update: Now includes regulatory constraints.
    
    Objectives (to minimize):
        F[0]: Compactness penalty
        F[1]: Adjacency penalty
        F[2]: Wind blockage penalty (Phase 7)
        F[3]: Solar access penalty (Phase 7)
    
    Constraints (satisfied when <= 0):
        G[0]: Boundary violation
        G[1]: Overlap violation
        G[2]: Dynamic setback violation (Phase 8)
        G[3]: Fire separation violation (Phase 8)
        G[4]: Slope violation (Phase 8)
    """
    
    def __init__(
        self,
        context: CampusContext,
        building_counts: Dict[str, int],
        site_parameters: SiteParameters = None,
        optimization_goals: Dict[OptimizationGoal, float] = None,
        enable_wind: bool = True,
        enable_solar: bool = True,
        enable_regulatory: bool = True,
        wind_data: WindVector = None,
        dem_sampler: DEMSampler = None,
        **kwargs
    ):
        """
        Initialize the spatial optimization problem.
        
        Args:
            context: CampusContext from OSM service
            building_counts: Dict of {type_name: count}
            site_parameters: Setback constraints
            optimization_goals: Objective weights
            enable_wind: Enable wind physics (Phase 7)
            enable_solar: Enable solar physics (Phase 7)
            enable_regulatory: Enable regulatory constraints (Phase 8)
            wind_data: Optional custom wind vector
            dem_sampler: Optional DEM sampler for slope analysis
        """
        self.context = context
        self.building_counts = building_counts
        self.site_params = site_parameters or SiteParameters()
        self.enable_wind = enable_wind
        self.enable_solar = enable_solar
        self.enable_regulatory = enable_regulatory
        
        # Default goals with physics
        default_goals = {
            OptimizationGoal.COMPACTNESS: 0.3,
            OptimizationGoal.ADJACENCY: 0.3,
            OptimizationGoal.WIND_COMFORT: 0.2 if enable_wind else 0.0,
            OptimizationGoal.SOLAR_GAIN: 0.2 if enable_solar else 0.0
        }
        self.goals = optimization_goals or default_goals
        
        # Build type sequence
        self.type_sequence = self._build_type_sequence()
        self.num_buildings = len(self.type_sequence)
        
        # Calculate variable bounds
        xl, xu = calculate_variable_bounds(
            context.boundary,
            self.num_buildings,
            num_types=len(BUILDING_TYPES)
        )
        
        # Extract road geometries
        road_geoms = []
        for road in context.existing_roads:
            if hasattr(road, 'geometry'):
                road_geoms.append(road.geometry)
        
        # Phase 8: Initialize constraint calculator with DEM
        self.constraint_calc = ConstraintCalculator(
            context.boundary,
            self.site_params,
            road_geoms,
            dem_sampler=dem_sampler
        )
        
        # Get existing building polygons
        existing_polys = [b.geometry for b in context.existing_buildings]
        
        # Get latitude from context
        lat, _ = context.center_latlon
        
        # Initialize objective calculator
        self.objective_calc = ObjectiveCalculator(
            context.boundary,
            self.goals,
            existing_polys,
            latitude=lat,
            wind_data=wind_data
        )
        
        # Problem dimensions (Phase 8: 5 constraints)
        n_var = self.num_buildings * GENES_PER_BUILDING
        n_obj = 4   # Compactness, Adjacency, Wind, Solar
        n_ieq_constr = 5 if enable_regulatory else 4  # +Slope for Phase 8
        
        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_ieq_constr=n_ieq_constr,
            xl=xl,
            xu=xu,
            **kwargs
        )
    
    def _build_type_sequence(self) -> List[int]:
        """Build ordered list of type IDs based on counts."""
        sequence = []
        for type_name, count in self.building_counts.items():
            if type_name in TYPE_NAME_TO_ID:
                type_id = TYPE_NAME_TO_ID[type_name]
                sequence.extend([type_id] * count)
        return sequence
    
    def _evaluate(self, x, out, *args, **kwargs):
        """
        Evaluate a single solution.
        
        Phase 8: Evaluates 4 objectives + 5 constraints.
        """
        # Decode to genes and polygons
        genes = array_to_genome(x, self.num_buildings)
        
        # Enforce type sequence
        for i, gene in enumerate(genes):
            gene.type_id = self.type_sequence[i]
        
        polygons = decode_all_to_polygons(genes)
        
        # Calculate constraints (Phase 8: regulatory enhanced)
        g_boundary = self.constraint_calc.boundary_violation(polygons)
        g_overlap = self.constraint_calc.overlap_violation(polygons)
        
        if self.enable_regulatory:
            # Phase 8: Use enhanced constraint methods
            g_setback = self.constraint_calc.dynamic_setback_violation(polygons)
            g_separation = self.constraint_calc.fire_separation_violation(polygons, genes)
            g_slope = self.constraint_calc.slope_violation(polygons)
        else:
            # Legacy: Use simple methods
            g_setback = self.constraint_calc.setback_violation(polygons)
            g_separation = self.constraint_calc.separation_violation(polygons)
            g_slope = 0.0
        
        # Calculate objectives
        f_compactness = self.objective_calc.compactness(genes)
        f_adjacency = self.objective_calc.adjacency(genes)
        f_wind = self.objective_calc.wind_comfort(genes, polygons)
        f_solar = self.objective_calc.solar_gain(genes, polygons)
        
        # Set outputs
        out["F"] = np.array([f_compactness, f_adjacency, f_wind, f_solar])
        
        if self.enable_regulatory:
            out["G"] = np.array([g_boundary, g_overlap, g_setback, g_separation, g_slope])
        else:
            out["G"] = np.array([g_boundary, g_overlap, g_setback, g_separation])
    
    def get_type_sequence(self) -> List[int]:
        """Return the expected type sequence for validation."""
        return self.type_sequence.copy()
    
    def decode_solution(self, x: np.ndarray) -> Tuple[List[BuildingGene], List[Polygon]]:
        """Decode a solution for visualization."""
        genes = array_to_genome(x, self.num_buildings)
        for i, gene in enumerate(genes):
            gene.type_id = self.type_sequence[i]
        polygons = decode_all_to_polygons(genes)
        return genes, polygons
    
    def get_objective_names(self) -> List[str]:
        """Return names of objectives for reporting."""
        return ["compactness", "adjacency", "wind_comfort", "solar_gain"]
    
    def get_constraint_names(self) -> List[str]:
        """Return names of constraints for reporting."""
        if self.enable_regulatory:
            return ["boundary", "overlap", "setback", "fire_separation", "slope"]
        return ["boundary", "overlap", "setback", "separation"]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_problem_from_request(
    context: CampusContext,
    request_data: Dict[str, Any]
) -> SpatialOptimizationProblem:
    """Factory function to create problem from OptimizationRequest data."""
    site_params = SiteParameters(**request_data.get("site_parameters", {}))
    
    goals_raw = request_data.get("optimization_goals", {})
    goals = {}
    for goal_key, weight in goals_raw.items():
        try:
            goal_enum = OptimizationGoal(goal_key)
            goals[goal_enum] = float(weight)
        except ValueError:
            pass
    
    building_counts = request_data.get("building_counts", {"Faculty": 2, "Dormitory": 3})
    
    enable_wind = request_data.get("enable_wind", True)
    enable_solar = request_data.get("enable_solar", True)
    enable_regulatory = request_data.get("enable_regulatory", True)
    
    return SpatialOptimizationProblem(
        context=context,
        building_counts=building_counts,
        site_parameters=site_params,
        optimization_goals=goals,
        enable_wind=enable_wind,
        enable_solar=enable_solar,
        enable_regulatory=enable_regulatory
    )
