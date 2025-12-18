"""
PlanifyAI Optimization Pipeline Orchestrator (Phase 6.5 Integration).

Unified pipeline that coordinates all optimization components:
- Context fetching (OSMnx, Solar, Wind)
- Constraint management (God Mode)
- Multi-objective optimization (H-SAGA via new engine)
- AI critique and analysis

Example:
    pipeline = OptimizationPipeline()
    result = pipeline.run(
        latitude=41.3833,
        longitude=33.7833,
        building_counts={"Faculty": 2, "Dormitory": 3}
    )
"""

import time
import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np

from shapely.geometry import Polygon, mapping

# Core imports
from backend.core.domain.geometry.osm_service import OSMContextFetcher, CampusContext
from backend.core.schemas.input import OptimizationRequest, SiteParameters, OptimizationGoal
from backend.core.physics.solar import SolarPenaltyCalculator
from backend.core.physics.wind import WindDataFetcher, WindData
from backend.core.constraints.manual_constraints import ManualConstraintManager

# NEW: Phase 6 Engine imports
from backend.core.optimization.encoding import (
    BuildingGene, BUILDING_TYPES, TYPE_ID_TO_NAME,
    array_to_genome, decode_all_to_polygons, GENES_PER_BUILDING
)
from backend.core.optimization.spatial_problem import SpatialOptimizationProblem
from backend.core.optimization.hsaga_runner import HSAGARunner, HSAGARunnerConfig

# AI Critique (optional)
try:
    from backend.core.ai.critique import AICritic, CritiqueConfig, CritiqueResult
    CRITIQUE_AVAILABLE = True
except ImportError:
    CRITIQUE_AVAILABLE = False
    CritiqueResult = None


# =============================================================================
# PIPELINE STATUS
# =============================================================================

class PipelineStage(Enum):
    """Pipeline execution stages."""
    INITIALIZED = "initialized"
    FETCHING_CONTEXT = "fetching_context"
    LOADING_CONSTRAINTS = "loading_constraints"
    SETTING_UP_PROBLEM = "setting_up_problem"
    OPTIMIZING = "optimizing"
    CRITIQUING = "critiquing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageResult:
    """Result of a pipeline stage."""
    stage: PipelineStage
    success: bool
    duration_seconds: float
    message: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    
    # Status
    success: bool
    total_duration: float
    stages: List[StageResult]
    
    # Context
    context: Optional[CampusContext]
    wind_data: Optional[WindData]
    
    # Optimization
    pareto_solutions: Optional[np.ndarray]
    pareto_objectives: Optional[np.ndarray]
    best_solution: Optional[np.ndarray]
    best_objectives: Optional[Dict[str, float]]
    
    # Buildings
    best_genes: Optional[List[BuildingGene]]
    best_polygons: Optional[List[Polygon]]
    
    # Critique
    critique: Optional[Any]  # CritiqueResult if available
    
    # Export
    geojson: Optional[Dict[str, Any]]
    
    def _sanitize_float(self, value: float) -> Optional[float]:
        """Ensure float is JSON compliant (no NaN/Inf)."""
        if value is None:
            return None
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "total_duration": round(self.total_duration, 2),
            "stages": [
                {
                    "stage": s.stage.value,
                    "success": s.success,
                    "duration": round(s.duration_seconds, 2),
                    "message": s.message
                }
                for s in self.stages
            ],
            "context_summary": {
                "boundary_area": self._sanitize_float(self.context.boundary.area) if self.context else None,
                "existing_buildings": len(self.context.existing_buildings) if self.context else 0,
                "existing_roads": len(self.context.existing_roads) if self.context else 0
            } if self.context else None,
            "wind_summary": {
                "dominant_direction": self.wind_data.dominant_direction_name,
                "avg_speed": self._sanitize_float(self.wind_data.average_speed)
            } if self.wind_data else None,
            "optimization_summary": {
                "pareto_size": len(self.pareto_solutions) if self.pareto_solutions is not None else 0,
                "best_objectives": {k: self._sanitize_float(v) for k, v in self.best_objectives.items()} if self.best_objectives else None
            },
            "buildings_summary": {
                "count": len(self.best_genes) if self.best_genes else 0,
                "types": dict(self._count_types()) if self.best_genes else {}
            }
        }
        
        if self.critique:
            result["critique_summary"] = {
                "overall_score": self._sanitize_float(getattr(self.critique, 'overall_score', 0)),
                "num_suggestions": len(getattr(self.critique, 'suggestions', []))
            }
        
        return result
    
    def _count_types(self) -> Dict[str, int]:
        """Count building types."""
        counts = {}
        for gene in self.best_genes:
            t = gene.type_name
            counts[t] = counts.get(t, 0) + 1
        return counts


# =============================================================================
# PIPELINE CONFIGURATION
# =============================================================================

@dataclass
class PipelineConfig:
    """Configuration for the optimization pipeline."""
    
    # Context settings
    fetch_radius: float = 500.0  # meters
    
    # Building settings (used if building_counts not provided)
    default_building_counts: Dict[str, int] = field(default_factory=lambda: {
        "Faculty": 2,
        "Dormitory": 3,
        "Dining": 1,
        "Library": 1
    })
    
    # Site parameters (Turkish standards defaults)
    site_parameters: SiteParameters = field(default_factory=SiteParameters)
    
    # Optimization goals (weights 0-1)
    optimization_goals: Dict[OptimizationGoal, float] = field(default_factory=lambda: {
        OptimizationGoal.COMPACTNESS: 0.5,
        OptimizationGoal.ADJACENCY: 0.5,
        OptimizationGoal.SOLAR_GAIN: 0.0,
        OptimizationGoal.WIND_COMFORT: 0.0
    })
    
    # Physics settings
    enable_solar: bool = False  # Phase 7
    enable_wind: bool = False   # Phase 7
    wind_data_days: int = 30
    
    # H-SAGA settings
    total_evaluations: int = 3000
    sa_fraction: float = 0.30
    population_size: int = 50
    
    # Critique settings
    enable_critique: bool = False  # Disabled by default
    critique_model: str = "llama3.2:3b"
    
    # Output settings
    export_geojson: bool = True
    
    # Performance
    verbose: bool = True


# =============================================================================
# MAIN PIPELINE
# =============================================================================

class OptimizationPipeline:
    """
    Main optimization pipeline orchestrator (Phase 6.5 Integration).
    
    Coordinates all components to produce optimized campus layouts
    using the verified H-SAGA engine.
    
    Example:
        pipeline = OptimizationPipeline()
        
        result = pipeline.run(
            latitude=41.3833,
            longitude=33.7833,
            building_counts={"Faculty": 2, "Dormitory": 3}
        )
        
        print(f"Buildings: {len(result.best_genes)}")
        
        with open("campus.geojson", "w") as f:
            json.dump(result.geojson, f)
    """
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.stages: List[StageResult] = []
        self.current_stage = PipelineStage.INITIALIZED
        
        # Components (initialized during run)
        self.context: Optional[CampusContext] = None
        self.wind_data: Optional[WindData] = None
        self.constraint_manager: Optional[ManualConstraintManager] = None
        self.problem: Optional[SpatialOptimizationProblem] = None
        self.runner: Optional[HSAGARunner] = None
        self.hsaga_result: Optional[Dict] = None
    
    def _sanitize_float(self, value: float) -> Optional[float]:
        """Ensure float is JSON compliant (no NaN/Inf)."""
        if value is None:
            return None
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    
    def _log(self, message: str) -> None:
        """Log message if verbose."""
        if self.config.verbose:
            print(f"[{self.current_stage.value}] {message}")
    
    def _record_stage(
        self,
        stage: PipelineStage,
        success: bool,
        duration: float,
        message: str,
        data: Dict = None
    ) -> None:
        """Record stage result."""
        result = StageResult(
            stage=stage,
            success=success,
            duration_seconds=duration,
            message=message,
            data=data or {}
        )
        self.stages.append(result)

    def run(
        self,
        latitude: float,
        longitude: float,
        building_counts: Dict[str, int] = None,
        site_parameters: SiteParameters = None,
        optimization_goals: Dict[OptimizationGoal, float] = None,
        constraint_geojson: Dict = None,
        boundary_geojson: Dict = None,
        clear_all_existing: bool = False,
        kept_building_ids: List[str] = None,
        callback: callable = None
    ) -> PipelineResult:
        """
        Run the complete optimization pipeline.
        
        Args:
            latitude: Campus center latitude
            longitude: Campus center longitude
            building_counts: Dict of building types and counts (e.g., {"Faculty": 2})
            site_parameters: Setback constraints (default: Turkish standards)
            optimization_goals: Objective weights (default: balanced)
            constraint_geojson: Optional constraint GeoJSON from God Mode
            boundary_geojson: Optional boundary GeoJSON to override automatic detection
            clear_all_existing: If True, remove all existing buildings
            kept_building_ids: Building IDs to preserve even with clear_all_existing
            callback: Optional callback(stage, progress) for UI updates
            
        Returns:
            PipelineResult with all outputs
        """
        start_time = time.time()
        
        # Apply overrides
        self.building_counts = building_counts or self.config.default_building_counts
        self.site_params = site_parameters or self.config.site_parameters
        self.goals = optimization_goals or self.config.optimization_goals
        
        try:
            # Stage 1: Fetch Context
            self._fetch_context(
                latitude, longitude, boundary_geojson,
                clear_all_existing, kept_building_ids, callback
            )
            
            # Stage 2: Load Constraints
            self._load_constraints(constraint_geojson, callback)
            
            # Stage 3: Setup Problem (NEW ENGINE)
            self._setup_problem(callback)
            
            # Stage 4: Optimize (NEW ENGINE)
            self._optimize(callback)
            
            # Stage 5: Critique (optional)
            critique_result = None
            if self.config.enable_critique and CRITIQUE_AVAILABLE:
                critique_result = self._critique(callback)
            
            # Stage 6: Export
            geojson = self._export(callback) if self.config.export_geojson else None
            
            # Complete
            total_duration = time.time() - start_time
            self.current_stage = PipelineStage.COMPLETED
            
            # Extract results from H-SAGA
            best_solution = self.hsaga_result.get("best_solution", {})
            best_X = best_solution.get("x")
            best_F = best_solution.get("F", np.array([0, 0]))
            best_genes = best_solution.get("genes", [])
            best_polygons = best_solution.get("polygons", [])
            
            pareto_data = self.hsaga_result.get("pareto_front", {})
            pareto_X = pareto_data.get("X")
            pareto_F = pareto_data.get("F")
            
            best_objectives = {
                "compactness": float(best_F[0]) if len(best_F) > 0 else 0.0,
                "adjacency": float(best_F[1]) if len(best_F) > 1 else 0.0
            }
            
            if self.config.verbose:
                print("\n" + "=" * 60)
                print("🏆 PIPELINE COMPLETE (Phase 6.5)")
                print("=" * 60)
                print(f"Total time: {total_duration:.2f}s")
                print(f"Buildings: {len(best_genes)}")
                print(f"Pareto solutions: {len(pareto_X) if pareto_X is not None else 0}")
                print(f"Best Compactness: {best_objectives['compactness']:.4f}")
                print(f"Best Adjacency: {best_objectives['adjacency']:.4f}")
            
            return PipelineResult(
                success=True,
                total_duration=total_duration,
                stages=self.stages,
                context=self.context,
                wind_data=self.wind_data,
                pareto_solutions=pareto_X,
                pareto_objectives=pareto_F,
                best_solution=best_X,
                best_objectives=best_objectives,
                best_genes=best_genes,
                best_polygons=best_polygons,
                critique=critique_result,
                geojson=geojson
            )
            
        except Exception as e:
            total_duration = time.time() - start_time
            self.current_stage = PipelineStage.FAILED
            
            self._record_stage(
                PipelineStage.FAILED,
                False,
                total_duration,
                f"Pipeline failed: {str(e)}"
            )
            
            import traceback
            if self.config.verbose:
                traceback.print_exc()
            
            return PipelineResult(
                success=False,
                total_duration=total_duration,
                stages=self.stages,
                context=self.context,
                wind_data=self.wind_data,
                pareto_solutions=None,
                pareto_objectives=None,
                best_solution=None,
                best_objectives=None,
                best_genes=None,
                best_polygons=None,
                critique=None,
                geojson=None
            )
    
    def _fetch_context(
        self,
        latitude: float,
        longitude: float,
        boundary_geojson: Dict,
        clear_all_existing: bool,
        kept_building_ids: List[str],
        callback: callable
    ) -> None:
        """Stage 1: Fetch campus context."""
        self.current_stage = PipelineStage.FETCHING_CONTEXT
        start = time.time()
        
        self._log(f"Fetching context for ({latitude}, {longitude})...")
        
        fetcher = OSMContextFetcher()
        boundary_poly = None
        
        if boundary_geojson:
            self._log("Using user-provided boundary...")
            from shapely.geometry import shape
            try:
                if boundary_geojson.get("type") == "FeatureCollection":
                    features = boundary_geojson.get("features", [])
                    if features:
                        boundary_poly = shape(features[0]["geometry"])
                elif boundary_geojson.get("type") == "Feature":
                    boundary_poly = shape(boundary_geojson["geometry"])
                else:
                    boundary_poly = shape(boundary_geojson)
            except Exception as e:
                self._log(f"Failed to process boundary override: {e}")
        
        self.context = fetcher.fetch_by_point(
            latitude, longitude,
            radius_meters=self.config.fetch_radius,
            boundary_polygon=boundary_poly,
            clear_all_existing=clear_all_existing,
            kept_building_ids=kept_building_ids
        )
        
        self._log(f"Found {len(self.context.existing_buildings)} existing buildings")
        self._log(f"Found {len(self.context.existing_roads)} road segments")
        self._log(f"Found {len(self.context.gateways)} gateways")
        
        # Fetch wind data (Phase 7)
        if self.config.enable_wind:
            try:
                wind_fetcher = WindDataFetcher()
                self.wind_data = wind_fetcher.fetch(
                    latitude, longitude,
                    days=self.config.wind_data_days
                )
                self._log(f"Wind: {self.wind_data.dominant_direction_name} at {self.wind_data.average_speed:.1f} m/s")
            except Exception as e:
                self._log(f"Wind data fetch failed: {e}")
                self.wind_data = None
        
        duration = time.time() - start
        self._record_stage(
            PipelineStage.FETCHING_CONTEXT,
            True,
            duration,
            f"Fetched context: {len(self.context.existing_buildings)} buildings, {len(self.context.existing_roads)} roads"
        )
        
        if callback:
            callback(PipelineStage.FETCHING_CONTEXT, 100)
    
    def _load_constraints(self, constraint_geojson: Dict, callback: callable) -> None:
        """Stage 2: Load manual constraints."""
        self.current_stage = PipelineStage.LOADING_CONSTRAINTS
        start = time.time()
        
        if constraint_geojson:
            self._log("Loading constraints from GeoJSON...")
            self.constraint_manager = ManualConstraintManager.from_geojson(constraint_geojson)
            self._log(f"Loaded {len(self.constraint_manager.constraints)} constraints")
        else:
            self._log("No constraints provided, using empty manager")
            self.constraint_manager = ManualConstraintManager()
        
        duration = time.time() - start
        self._record_stage(
            PipelineStage.LOADING_CONSTRAINTS,
            True,
            duration,
            f"Loaded {len(self.constraint_manager.constraints)} constraints"
        )
        
        if callback:
            callback(PipelineStage.LOADING_CONSTRAINTS, 100)
    
    def _setup_problem(self, callback: callable) -> None:
        """Stage 3: Setup optimization problem (NEW ENGINE)."""
        self.current_stage = PipelineStage.SETTING_UP_PROBLEM
        start = time.time()
        
        num_buildings = sum(self.building_counts.values())
        self._log(f"Setting up SpatialOptimizationProblem with {num_buildings} buildings...")
        self._log(f"  Types: {self.building_counts}")
        self._log(f"  Setbacks: Front={self.site_params.setback_front}m, Side={self.site_params.setback_side}m")
        
        # Create NEW problem using Phase 6 engine
        self.problem = SpatialOptimizationProblem(
            context=self.context,
            building_counts=self.building_counts,
            site_parameters=self.site_params,
            optimization_goals=self.goals
        )
        
        self._log(f"Problem: {self.problem.n_var} variables, {self.problem.n_obj} objectives, {self.problem.n_ieq_constr} constraints")
        
        duration = time.time() - start
        self._record_stage(
            PipelineStage.SETTING_UP_PROBLEM,
            True,
            duration,
            f"Problem setup: {self.problem.n_var} vars, {self.problem.n_obj} obj"
        )
        
        if callback:
            callback(PipelineStage.SETTING_UP_PROBLEM, 100)
    
    def _optimize(self, callback: callable) -> None:
        """Stage 4: Run H-SAGA optimization (NEW ENGINE)."""
        self.current_stage = PipelineStage.OPTIMIZING
        start = time.time()
        
        self._log(f"Starting H-SAGA optimization (budget: {self.config.total_evaluations})...")
        
        # Create H-SAGA config
        hsaga_config = HSAGARunnerConfig(
            total_evaluations=self.config.total_evaluations,
            sa_fraction=self.config.sa_fraction,
            population_size=self.config.population_size,
            verbose=self.config.verbose,
            seed=42
        )
        
        # Run NEW engine
        self.runner = HSAGARunner(self.problem, hsaga_config)
        self.hsaga_result = self.runner.run()
        
        stats = self.hsaga_result.get("stats", {})
        pareto_size = len(self.hsaga_result.get("pareto_front", {}).get("X", []))
        
        self._log(f"Optimization complete: {pareto_size} Pareto solutions")
        
        duration = time.time() - start
        self._record_stage(
            PipelineStage.OPTIMIZING,
            True,
            duration,
            f"Found {pareto_size} Pareto solutions in {duration:.1f}s"
        )
        
        if callback:
            callback(PipelineStage.OPTIMIZING, 100)
    
    def _critique(self, callback: callable) -> Any:
        """Stage 5: AI critique of best solution (optional)."""
        self.current_stage = PipelineStage.CRITIQUING
        start = time.time()
        
        if not CRITIQUE_AVAILABLE:
            self._log("AI critique not available")
            return None
        
        self._log("Generating AI critique...")
        
        best_solution = self.hsaga_result.get("best_solution", {})
        genes = best_solution.get("genes", [])
        polygons = best_solution.get("polygons", [])
        
        critique_config = CritiqueConfig(
            model_name=self.config.critique_model,
            keep_alive=0
        )
        critic = AICritic(critique_config)
        
        result = critic.critique(
            genes,
            polygons,
            {"compactness": best_solution.get("F", [0])[0]},
            self.context.boundary if self.context else None
        )
        
        self._log(f"Critique score: {result.overall_score}/10")
        
        duration = time.time() - start
        self._record_stage(
            PipelineStage.CRITIQUING,
            True,
            duration,
            f"Critique: {result.overall_score}/10"
        )
        
        if callback:
            callback(PipelineStage.CRITIQUING, 100)
        
        return result
    
    def _export(self, callback: callable) -> Dict[str, Any]:
        """Stage 6: Export results as GeoJSON (WGS84 Converted)."""
        self.current_stage = PipelineStage.EXPORTING
        start = time.time()
        
        self._log("Exporting results to GeoJSON (Converting to WGS84)...")
        
        best_solution = self.hsaga_result.get("best_solution", {})
        genes = best_solution.get("genes", [])
        polygons = best_solution.get("polygons", [])
        best_F = best_solution.get("F", np.array([0, 0]))
        
        # Coordinate transformer
        from pyproj import Transformer
        from shapely.ops import transform as shapely_transform
        
        center_lat, center_lon = self.context.center_latlon
        
        # Use the same CRS as osm_service
        transformer = Transformer.from_crs(
            self.context.crs_local,
            "EPSG:4326",
            always_xy=True
        )
        
        def to_wgs84(shapely_geom):
            return shapely_transform(transformer.transform, shapely_geom)
        
        # Build GeoJSON
        features = []
        
        # 1. Add Optimized Buildings
        for i, (gene, polygon) in enumerate(zip(genes, polygons)):
            wgs84_geom = to_wgs84(polygon)
            
            features.append({
                "type": "Feature",
                "id": f"building_{i}",
                "properties": {
                    "layer": "optimized_building",
                    "building_type": gene.type_name,
                    "floors": gene.floors,
                    "height": gene.height,
                    "width": gene.width,
                    "depth": gene.depth,
                    "rotation_deg": np.degrees(gene.rotation),
                    "area": polygon.area
                },
                "geometry": mapping(wgs84_geom)
            })
        
        # 2. Add Site Boundary
        if self.context and self.context.boundary:
            wgs84_boundary = to_wgs84(self.context.boundary)
            features.append({
                "type": "Feature",
                "id": "site_boundary",
                "properties": {"layer": "boundary"},
                "geometry": mapping(wgs84_boundary)
            })
        
        # 3. Add Existing Buildings
        if self.context:
            for i, existing in enumerate(self.context.existing_buildings):
                wgs84_existing = to_wgs84(existing.geometry)
                features.append({
                    "type": "Feature",
                    "id": f"existing_{existing.osm_id}",
                    "properties": {
                        "layer": "existing_building",
                        "height": existing.height or 10.0,
                        "osm_id": existing.osm_id,
                        "name": existing.name,
                        "building_type": existing.building_type or "Existing",
                        "entity_type": existing.entity_type
                    },
                    "geometry": mapping(wgs84_existing)
                })
        
        # 4. Add Gateways
        if self.context:
            for i, gateway in enumerate(self.context.gateways):
                features.append({
                    "type": "Feature",
                    "id": f"gateway_{i}",
                    "properties": {
                        "layer": "gateway",
                        "type": gateway.get("type", "secondary"),
                        "bearing": gateway.get("bearing", 0),
                        "road_name": gateway.get("road_name")
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [gateway["location"][1], gateway["location"][0]]
                    }
                })
        
        # 5. Add Constraints
        if self.constraint_manager:
            for cid, constraint in self.constraint_manager.constraints.items():
                wgs84_constraint = to_wgs84(constraint.geometry)
                features.append({
                    "type": "Feature",
                    "id": cid,
                    "properties": {
                        "layer": "constraint",
                        "constraint_type": constraint.constraint_type.value
                    },
                    "geometry": mapping(wgs84_constraint)
                })
        
        # Final GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "properties": {
                "generated_by": "PlanifyAI (Phase 6.5)",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "center": {"lat": center_lat, "lon": center_lon},
                "crs": "EPSG:4326",
                "num_buildings": len(genes),
                "objectives": {
                    "compactness": self._sanitize_float(best_F[0]) if len(best_F) > 0 else None,
                    "adjacency": self._sanitize_float(best_F[1]) if len(best_F) > 1 else None
                }
            },
            "features": features
        }
        
        duration = time.time() - start
        self._record_stage(
            PipelineStage.EXPORTING,
            True,
            duration,
            f"Exported {len(features)} features to GeoJSON"
        )
        
        if callback:
            callback(PipelineStage.EXPORTING, 100)
        
        return geojson


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_optimization(
    latitude: float,
    longitude: float,
    building_counts: Dict[str, int] = None,
    budget: int = 3000,
    verbose: bool = True
) -> PipelineResult:
    """
    Run a complete campus optimization.
    
    Args:
        latitude: Campus center latitude
        longitude: Campus center longitude
        building_counts: Dict of building types and counts
        budget: Optimization evaluation budget
        verbose: Print progress
        
    Returns:
        PipelineResult
    """
    config = PipelineConfig(
        total_evaluations=budget,
        verbose=verbose
    )
    
    pipeline = OptimizationPipeline(config)
    return pipeline.run(latitude, longitude, building_counts=building_counts)


def quick_run(
    latitude: float = 41.3833,
    longitude: float = 33.7833,
    building_counts: Dict[str, int] = None
) -> PipelineResult:
    """
    Quick pipeline run for testing.
    
    Returns:
        PipelineResult
    """
    if building_counts is None:
        building_counts = {"Faculty": 1, "Dormitory": 2, "Dining": 1}
    
    config = PipelineConfig(
        total_evaluations=500,
        enable_solar=False,
        enable_wind=False,
        enable_critique=False,
        verbose=False
    )
    
    pipeline = OptimizationPipeline(config)
    return pipeline.run(latitude, longitude, building_counts=building_counts)
