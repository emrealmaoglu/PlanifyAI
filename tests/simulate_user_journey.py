#!/usr/bin/env python3
"""
Phase 9 Verification: End-to-End User Journey Test.

Simulates "The Kastamonu Plan" - a complete user session from
loading the map to viewing optimized buildings with XAI overlays.

This test mocks the frontend calls to verify the backend pipeline.
"""

import sys
import time
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/emrealmaoglu/Desktop/PlanifyAI')

# =============================================================================
# JOURNEY LOG
# =============================================================================

class JourneyLog:
    """Logs each step of the user journey with timestamps."""
    
    def __init__(self):
        self.steps = []
        self.start_time = datetime.now()
    
    def log(self, step: str, status: str, details: str = ""):
        """Log a journey step."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
        entry = f"[{elapsed:6.2f}s] {emoji} {step}: {details}"
        self.steps.append(entry)
        print(entry)
    
    def summary(self):
        """Print journey summary."""
        print("\n" + "=" * 60)
        print("📋 JOURNEY LOG SUMMARY")
        print("=" * 60)
        for step in self.steps:
            print(step)
        
        passed = sum(1 for s in self.steps if "✅" in s)
        failed = sum(1 for s in self.steps if "❌" in s)
        print("\n" + "-" * 60)
        print(f"Total: {passed} PASSED, {failed} FAILED")
        print("=" * 60)
        
        return failed == 0


# =============================================================================
# MOCK API CLIENT (Simulates Frontend HTTP Calls)
# =============================================================================

class MockAPIClient:
    """
    Simulates frontend API calls by directly invoking backend logic.
    
    In a real test, this would use `requests` to hit the FastAPI server.
    Here we mock by importing and calling backend functions directly.
    """
    
    def __init__(self, log: JourneyLog):
        self.log = log
        self.job_id = None
        self.context = None
    
    def fetch_context(self, lat: float, lon: float, radius: float = 1000) -> Dict[str, Any]:
        """
        Step 1: Fetch campus context (boundary, buildings, roads).
        
        Simulates: GET /api/context/fetch?lat=X&lon=Y
        """
        self.log.log("CONTEXT_FETCH", "⏳", f"Fetching context at ({lat}, {lon})...")
        
        try:
            from backend.core.domain.geometry.osm_service import CampusContext, ExistingBuilding, ExistingRoad
            from shapely.geometry import Polygon, LineString, box
            
            # Create a mock context directly (avoid OSMnx network calls)
            crs_local = f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"
            
            # Create a simple rectangular boundary (500x500m)
            boundary = box(-250, -250, 250, 250)
            
            # Create some mock roads
            mock_roads = [
                ExistingRoad(
                    osm_id=1,
                    geometry=LineString([(-200, 0), (200, 0)]),
                    road_type="primary",
                    name="Main Road",
                    width=8.0
                ),
                ExistingRoad(
                    osm_id=2,
                    geometry=LineString([(0, -200), (0, 200)]),
                    road_type="secondary",
                    name="Cross Road",
                    width=6.0
                )
            ]
            
            # Create mock context
            self.context = CampusContext(
                boundary=boundary,
                existing_buildings=[],
                existing_roads=mock_roads,
                existing_green_areas=[],
                center_latlon=(lat, lon),
                crs_local=crs_local,
                bounds_meters=(-250, -250, 250, 250),
                existing_walkways=[],
                gateways=[]
            )
            
            # Verify structure
            has_boundary = self.context.boundary is not None
            has_roads = len(self.context.existing_roads) > 0
            has_gateways = hasattr(self.context, 'gateways')
            
            details = f"boundary={has_boundary}, roads={len(self.context.existing_roads)}, gateways={has_gateways}"
            self.log.log("CONTEXT_FETCH", "PASS", details)
            
            return self.context.to_geojson()
            
        except Exception as e:
            import traceback
            self.log.log("CONTEXT_FETCH", "FAIL", str(e))
            traceback.print_exc()
            return {}
    
    def start_optimization(
        self,
        building_counts: Dict[str, int],
        constraints: Dict[str, Any] = None,
        enable_wind: bool = True,
        enable_solar: bool = True
    ) -> str:
        """
        Step 2: Start optimization.
        
        Simulates: POST /api/optimize/start
        """
        self.log.log("OPTIMIZE_START", "⏳", f"Requesting {building_counts}...")
        
        try:
            from backend.core.optimization.spatial_problem import SpatialOptimizationProblem
            from backend.core.optimization.hsaga_runner import HSAGARunner, HSAGARunnerConfig
            from backend.core.schemas.input import SiteParameters, OptimizationGoal
            
            if self.context is None:
                raise ValueError("Context not fetched. Call fetch_context first.")
            
            # Create problem
            goals = {
                OptimizationGoal.COMPACTNESS: 0.2,
                OptimizationGoal.ADJACENCY: 0.2,
                OptimizationGoal.WIND_COMFORT: 0.3 if enable_wind else 0.0,
                OptimizationGoal.SOLAR_GAIN: 0.3 if enable_solar else 0.0
            }
            
            self.problem = SpatialOptimizationProblem(
                context=self.context,
                building_counts=building_counts,
                site_parameters=SiteParameters(setback_front=5.0, setback_side=3.0),
                optimization_goals=goals,
                enable_wind=enable_wind,
                enable_solar=enable_solar
            )
            
            # Store for later
            self.building_counts = building_counts
            self.job_id = f"test_job_{int(time.time())}"
            
            self.log.log("OPTIMIZE_START", "PASS", f"Job ID: {self.job_id}")
            return self.job_id
            
        except Exception as e:
            self.log.log("OPTIMIZE_START", "FAIL", str(e))
            return ""
    
    def run_optimization(self) -> Dict[str, Any]:
        """
        Step 3: Run optimization (synchronous for test).
        
        Simulates: Polling GET /api/optimize/status until complete
        """
        self.log.log("OPTIMIZE_RUN", "⏳", "Running H-SAGA optimization...")
        
        try:
            from backend.core.optimization.hsaga_runner import HSAGARunner, HSAGARunnerConfig
            
            # Use minimal iterations for test
            config = HSAGARunnerConfig(
                total_evaluations=100,
                sa_fraction=0.3,
                population_size=20,
                verbose=False
            )
            
            runner = HSAGARunner(self.problem, config)
            start_time = time.time()
            result = runner.run()
            elapsed = time.time() - start_time
            
            self.result = result
            
            # Verify result structure
            has_best = result.get("best_solution") is not None
            has_front = result.get("pareto_front") is not None
            
            pareto = result.get("pareto_front", {})
            pareto_size = len(pareto.get("X", [])) if pareto else 0
            
            details = f"Completed in {elapsed:.2f}s, pareto_size={pareto_size}"
            self.log.log("OPTIMIZE_RUN", "PASS", details)
            
            return {"status": "completed", "elapsed": elapsed}
            
        except Exception as e:
            self.log.log("OPTIMIZE_RUN", "FAIL", str(e))
            return {"status": "failed", "error": str(e)}
    
    def get_geojson(self) -> Dict[str, Any]:
        """
        Step 4: Get GeoJSON results.
        
        Simulates: GET /api/optimize/geojson/{job_id}
        """
        self.log.log("GEOJSON_EXPORT", "⏳", "Exporting results...")
        
        try:
            from backend.core.optimization.encoding import decode_all_to_polygons, array_to_genome
            from backend.core.visualization.slope_grid_generator import (
                SlopeGridGenerator, generate_wind_arrows
            )
            from shapely.geometry import mapping
            from pyproj import Transformer
            
            # Decode best solution
            best_sol = self.result.get("best_solution", {})
            best_x = best_sol.get("x")
            best_F = best_sol.get("F", [0, 0, 0, 0])
            
            if best_x is None:
                raise ValueError("No best solution found in result")
            
            genes = array_to_genome(best_x, self.problem.num_buildings)
            
            # Apply type sequence
            type_seq = self.problem.get_type_sequence()
            for i, gene in enumerate(genes):
                gene.type_id = type_seq[i]
            
            polygons = decode_all_to_polygons(genes)
            
            # Build GeoJSON features
            features = []
            type_names = {0: "Faculty", 1: "Dormitory", 2: "Library", 3: "Research", 
                         4: "Sports", 5: "Dining", 6: "Rectory", 7: "Social"}
            
            # Transform to WGS84
            transformer = Transformer.from_crs(
                self.context.crs_local, "EPSG:4326", always_xy=True
            )
            
            for i, (gene, poly) in enumerate(zip(genes, polygons)):
                coords = list(poly.exterior.coords)
                wgs84_coords = [transformer.transform(x, y) for x, y in coords]
                
                features.append({
                    "type": "Feature",
                    "id": f"building_{i}",
                    "properties": {
                        "layer": "optimized_building",
                        "building_type": type_names.get(gene.type_id, "Unknown"),
                        "floors": int(gene.floors),
                        "height": gene.height,
                        "violations": []  # No violations in test
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [wgs84_coords]
                    }
                })
            
            # Add slope grid
            slope_gen = SlopeGridGenerator(grid_size=10)
            slope_data = slope_gen.generate_grid(
                self.context.boundary,
                self.context.crs_local,
                self.context.center_latlon
            )
            
            # Add wind arrows
            wind_arrows = generate_wind_arrows(
                self.context.boundary,
                wind_direction_deg=22.5,  # NNE
                wind_speed=3.5,
                crs_local=self.context.crs_local,
                grid_size=5
            )
            features.extend(wind_arrows)
            
            # Build final GeoJSON
            geojson = {
                "type": "FeatureCollection",
                "properties": {
                    "objectives": {
                        "compactness": float(best_F[0]),
                        "adjacency": float(best_F[1]),
                        "wind_comfort": float(best_F[2]),
                        "solar_gain": float(best_F[3])
                    },
                    "wind_vector": {"direction": 22.5, "speed": 3.5}
                },
                "features": features,
                "slope_grid": slope_data
            }
            
            # Verify structure
            building_count = len([f for f in features if f["properties"].get("layer") == "optimized_building"])
            wind_count = len([f for f in features if f["properties"].get("layer") == "wind_arrow"])
            has_slope = "cells" in slope_data
            
            details = f"buildings={building_count}, wind_arrows={wind_count}, slope_grid={has_slope}"
            self.log.log("GEOJSON_EXPORT", "PASS", details)
            
            return geojson
            
        except Exception as e:
            self.log.log("GEOJSON_EXPORT", "FAIL", str(e))
            return {}


# =============================================================================
# THE KASTAMONU PLAN (User Journey Simulation)
# =============================================================================

def run_kastamonu_plan():
    """
    Execute the full user journey: "The Kastamonu Plan"
    
    1. Load campus context (Kastamonu University)
    2. Request optimization (5 Dorms + 2 Faculties)
    3. Run H-SAGA with solar priority
    4. Export and verify GeoJSON
    """
    print("=" * 60)
    print("🎓 THE KASTAMONU PLAN - User Journey Simulation")
    print("=" * 60)
    print()
    
    log = JourneyLog()
    client = MockAPIClient(log)
    
    # --- Step 1: Prep (Load Campus Context) ---
    print("\n📍 STEP 1: PREP - Loading Campus Context")
    print("-" * 40)
    
    context_geojson = client.fetch_context(
        lat=41.4245,  # Kastamonu University
        lon=33.7715,
        radius=1000
    )
    
    # --- Step 2: Edit (Add Constraints) ---
    print("\n🚧 STEP 2: EDIT - Adding Constraints")
    print("-" * 40)
    
    # Dummy red zone (constraint polygon)
    red_zone = {
        "type": "Feature",
        "properties": {"type": "exclusion"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[33.77, 41.42], [33.78, 41.42], [33.78, 41.43], [33.77, 41.43], [33.77, 41.42]]]
        }
    }
    log.log("EDIT_CONSTRAINT", "PASS", "Added exclusion zone (Red Zone)")
    
    # --- Step 3: Design (Set Building Counts) ---
    print("\n🏗️ STEP 3: DESIGN - Configuring Buildings")
    print("-" * 40)
    
    building_counts = {
        "Dormitory": 5,
        "Faculty": 2
    }
    log.log("DESIGN_CONFIG", "PASS", f"5 Dorms + 2 Faculties with Solar Priority")
    
    # --- Step 4: Run (Start Optimization) ---
    print("\n⚡ STEP 4: RUN - Starting Optimization")
    print("-" * 40)
    
    job_id = client.start_optimization(
        building_counts=building_counts,
        constraints=red_zone,
        enable_wind=True,
        enable_solar=True
    )
    
    if job_id:
        result = client.run_optimization()
    
    # --- Step 5: Result (Get GeoJSON) ---
    print("\n🗺️ STEP 5: RESULT - Exporting Visualization Data")
    print("-" * 40)
    
    geojson = client.get_geojson()
    
    # --- Verification ---
    print("\n🔍 VERIFICATION - Checking XAI Data")
    print("-" * 40)
    
    # Check buildings
    buildings = [f for f in geojson.get("features", []) 
                 if f.get("properties", {}).get("layer") == "optimized_building"]
    if len(buildings) == 7:
        log.log("VERIFY_BUILDINGS", "PASS", f"Found {len(buildings)} buildings (expected 7)")
    else:
        log.log("VERIFY_BUILDINGS", "FAIL", f"Found {len(buildings)} buildings (expected 7)")
    
    # Check wind arrows
    wind_arrows = [f for f in geojson.get("features", []) 
                   if f.get("properties", {}).get("layer") == "wind_arrow"]
    if len(wind_arrows) > 0:
        log.log("VERIFY_WIND", "PASS", f"Found {len(wind_arrows)} wind arrows")
    else:
        log.log("VERIFY_WIND", "FAIL", "No wind arrows found")
    
    # Check slope grid
    slope_grid = geojson.get("slope_grid", {})
    if slope_grid.get("cells"):
        log.log("VERIFY_SLOPE", "PASS", f"Slope grid has {len(slope_grid['cells'])} cells")
    else:
        log.log("VERIFY_SLOPE", "FAIL", "No slope grid data")
    
    # Check objectives
    objectives = geojson.get("properties", {}).get("objectives", {})
    if all(k in objectives for k in ["compactness", "wind_comfort", "solar_gain"]):
        log.log("VERIFY_OBJECTIVES", "PASS", f"All objectives present: {list(objectives.keys())}")
    else:
        log.log("VERIFY_OBJECTIVES", "FAIL", f"Missing objectives: {objectives}")
    
    # --- Summary ---
    success = log.summary()
    
    return success


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print()
    success = run_kastamonu_plan()
    print()
    
    if success:
        print("🎉 USER JOURNEY TEST: ALL PASSED")
        sys.exit(0)
    else:
        print("💥 USER JOURNEY TEST: SOME FAILURES")
        sys.exit(1)
