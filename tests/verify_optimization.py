#!/usr/bin/env python3
"""
Phase 6 Verification: H-SAGA Engine Logic Audit.

This script performs a 3-Level Audit of the optimization engine:
1. Genome Encoding/Decoding
2. Problem Evaluation (Objectives & Constraints)
3. H-SAGA Algorithm Integration

Run from project root:
    python3 tests/verify_optimization.py
"""

import sys
import os
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shapely.geometry import Polygon, box
from shapely import prepared


# =============================================================================
# MOCK CONTEXT (For isolated testing without OSM)
# =============================================================================

def create_mock_context():
    """Create a synthetic CampusContext for testing."""
    from dataclasses import dataclass, field
    from typing import List, Tuple, Dict, Any
    
    @dataclass
    class MockRoad:
        osm_id: int
        geometry: any
        road_type: str
        name: str
        width: float
    
    @dataclass
    class MockBuilding:
        osm_id: int
        geometry: Polygon
        building_type: str
        name: str
        height: float
        levels: int
        entity_type: str
    
    @dataclass
    class MockContext:
        boundary: Polygon
        existing_buildings: List[MockBuilding]
        existing_roads: List[MockRoad]
        existing_green_areas: List[MockBuilding]
        center_latlon: Tuple[float, float]
        crs_local: str
        bounds_meters: Tuple[float, float, float, float]
        existing_walkways: List[MockRoad] = field(default_factory=list)
        gateways: List[Dict[str, Any]] = field(default_factory=list)
    
    # Create a 500m x 500m campus boundary centered at origin
    boundary = box(-250, -250, 250, 250)
    
    # A few existing buildings
    existing = [
        MockBuilding(
            osm_id=1001,
            geometry=box(-200, -200, -150, -150),
            building_type="Faculty",
            name="Existing Faculty",
            height=15.0,
            levels=4,
            entity_type="building"
        ),
        MockBuilding(
            osm_id=1002,
            geometry=box(150, 150, 200, 200),
            building_type="Library",
            name="Existing Library",
            height=12.0,
            levels=3,
            entity_type="building"
        )
    ]
    
    return MockContext(
        boundary=boundary,
        existing_buildings=existing,
        existing_roads=[],
        existing_green_areas=[],
        center_latlon=(41.3833, 33.7833),
        crs_local="EPSG:32636",
        bounds_meters=(-250, -250, 250, 250),
        existing_walkways=[],
        gateways=[]
    )


# =============================================================================
# LEVEL 1: GENOME UNIT TEST
# =============================================================================

def test_level1_genome_encoding():
    """Test genome encoding and decoding."""
    print("\n" + "="*60)
    print("LEVEL 1: GENOME ENCODING/DECODING TEST")
    print("="*60)
    
    from backend.core.optimization.encoding import (
        SmartInitializer, decode_to_polygon, array_to_genome,
        GENES_PER_BUILDING, BUILDING_TYPES
    )
    
    # Create mock context
    context = create_mock_context()
    boundary = context.boundary
    
    # Test configuration
    building_counts = {
        "Faculty": 2,
        "Dormitory": 2,
        "Dining": 1,
        "Library": 1
    }
    
    print(f"  Boundary: {boundary.bounds}")
    print(f"  Building Counts: {building_counts}")
    
    # Initialize
    initializer = SmartInitializer(
        boundary=boundary,
        building_counts=building_counts,
        min_separation=5.0
    )
    
    print(f"  Total Buildings to Place: {initializer.num_buildings}")
    
    # Generate population
    rng = np.random.default_rng(42)
    pop_size = 10
    population = initializer.generate_population(pop_size, rng)
    
    print(f"  Generated Population Shape: {population.shape}")
    
    # Validate each individual
    all_valid = True
    for i in range(pop_size):
        individual = population[i]
        genes = array_to_genome(individual, initializer.num_buildings)
        
        for j, gene in enumerate(genes):
            polygon = decode_to_polygon(gene)
            
            # Check 1: Valid Shapely polygon
            if not polygon.is_valid:
                print(f"  ❌ Individual {i}, Building {j}: Invalid polygon")
                all_valid = False
                continue
            
            # Check 2: Non-zero area
            if polygon.area <= 0:
                print(f"  ❌ Individual {i}, Building {j}: Zero area")
                all_valid = False
                continue
            
            # Check 3: Centroid within boundary (allowing some tolerance)
            centroid = polygon.centroid
            if not boundary.buffer(50).contains(centroid):
                print(f"  ❌ Individual {i}, Building {j}: Centroid outside boundary")
                all_valid = False
    
    if all_valid:
        print("  ✅ All polygons valid and positioned correctly")
    
    assert all_valid, "Genome encoding/decoding failed"
    print("\n✅ LEVEL 1: Genome Encoding/Decoding Valid")
    return True


# =============================================================================
# LEVEL 2: PROBLEM EVALUATION TEST
# =============================================================================

def test_level2_problem_evaluation():
    """Test problem evaluation (objectives and constraints)."""
    print("\n" + "="*60)
    print("LEVEL 2: PROBLEM EVALUATION TEST")
    print("="*60)
    
    from backend.core.optimization.encoding import SmartInitializer
    from backend.core.optimization.spatial_problem import SpatialOptimizationProblem
    from backend.core.schemas.input import SiteParameters, OptimizationGoal
    
    # Create mock context
    context = create_mock_context()
    
    # Test configuration
    building_counts = {
        "Faculty": 2,
        "Dormitory": 2,
        "Dining": 1
    }
    
    site_params = SiteParameters(
        setback_front=5.0,
        setback_side=3.0,
        setback_rear=3.0
    )
    
    goals = {
        OptimizationGoal.COMPACTNESS: 0.6,
        OptimizationGoal.ADJACENCY: 0.4
    }
    
    print(f"  Site Parameters: Front={site_params.setback_front}m, Side={site_params.setback_side}m")
    print(f"  Goals: {goals}")
    
    # Create problem
    problem = SpatialOptimizationProblem(
        context=context,
        building_counts=building_counts,
        site_parameters=site_params,
        optimization_goals=goals
    )
    
    print(f"  Problem Dimensions:")
    print(f"    Variables: {problem.n_var}")
    print(f"    Objectives: {problem.n_obj}")
    print(f"    Constraints: {problem.n_ieq_constr}")
    
    # Generate test population
    initializer = SmartInitializer(
        boundary=context.boundary,
        building_counts=building_counts
    )
    
    rng = np.random.default_rng(42)
    X = initializer.generate_population(5, rng)
    
    print(f"  Test Population Shape: {X.shape}")
    
    # Evaluate
    F_all = []
    G_all = []
    
    for i in range(len(X)):
        out = {}
        problem._evaluate(X[i], out)
        F_all.append(out["F"])
        G_all.append(out["G"])
    
    F = np.array(F_all)
    G = np.array(G_all)
    
    print(f"\n  Objectives (F):")
    print(f"    Shape: {F.shape}")
    print(f"    Min: {F.min(axis=0)}")
    print(f"    Max: {F.max(axis=0)}")
    print(f"    Contains NaN: {np.any(np.isnan(F))}")
    print(f"    Contains Inf: {np.any(np.isinf(F))}")
    
    print(f"\n  Constraints (G):")
    print(f"    Shape: {G.shape}")
    print(f"    Min: {G.min(axis=0)}")
    print(f"    Max: {G.max(axis=0)}")
    print(f"    Contains NaN: {np.any(np.isnan(G))}")
    print(f"    Contains Inf: {np.any(np.isinf(G))}")
    
    # Assertions
    assert F.shape[1] == 4, f"Expected 4 objectives, got {F.shape[1]}"
    assert G.shape[1] == 5, f"Expected 5 constraints, got {G.shape[1]}"
    assert not np.any(np.isnan(F)), "Objectives contain NaN"
    assert not np.any(np.isinf(F)), "Objectives contain Inf"
    assert not np.any(np.isnan(G)), "Constraints contain NaN"
    
    # Check feasibility
    n_feasible = np.sum(np.all(G <= 0, axis=1))
    print(f"\n  Feasible Solutions: {n_feasible}/{len(X)}")
    
    print("\n✅ LEVEL 2: Problem Evaluation Successful (F & G calculated)")
    return True


# =============================================================================
# LEVEL 3: ALGORITHM INTEGRATION TEST
# =============================================================================

def test_level3_algorithm_integration():
    """Test H-SAGA algorithm integration."""
    print("\n" + "="*60)
    print("LEVEL 3: H-SAGA ALGORITHM INTEGRATION TEST")
    print("="*60)
    
    from backend.core.optimization.spatial_problem import SpatialOptimizationProblem
    from backend.core.optimization.hsaga_runner import HSAGARunner, HSAGARunnerConfig
    from backend.core.schemas.input import SiteParameters, OptimizationGoal
    
    # Create mock context
    context = create_mock_context()
    
    # Minimal test configuration
    building_counts = {
        "Faculty": 1,
        "Dormitory": 2,
        "Dining": 1
    }
    
    site_params = SiteParameters()
    goals = {
        OptimizationGoal.COMPACTNESS: 0.5,
        OptimizationGoal.ADJACENCY: 0.5
    }
    
    # Create problem
    problem = SpatialOptimizationProblem(
        context=context,
        building_counts=building_counts,
        site_parameters=site_params,
        optimization_goals=goals
    )
    
    # Micro-simulation config
    config = HSAGARunnerConfig(
        total_evaluations=200,  # Very small for testing
        sa_fraction=0.30,
        sa_chains=2,            # Reduced for speed
        population_size=10,     # Minimal
        seed=42,
        verbose=True
    )
    
    print(f"  Micro-Simulation Config:")
    print(f"    Total Evaluations: {config.total_evaluations}")
    print(f"    SA Fraction: {config.sa_fraction}")
    print(f"    Population Size: {config.population_size}")
    
    # Run H-SAGA
    print("\n  Running H-SAGA...")
    
    runner = HSAGARunner(problem, config)
    result = runner.run()
    
    # Validate result
    assert result is not None, "Result is None"
    assert "success" in result, "Result missing 'success' key"
    assert "stats" in result, "Result missing 'stats' key"
    
    print(f"\n  Result Summary:")
    print(f"    Success: {result['success']}")
    print(f"    SA Evaluations: {result['stats']['sa_evaluations']}")
    print(f"    GA Evaluations: {result['stats']['ga_evaluations']}")
    print(f"    Total Time: {result['stats']['total_time']:.2f}s")
    
    if result.get("best_solution"):
        best = result["best_solution"]
        print(f"\n  Best Solution:")
        print(f"    Objectives (F): {best['F']}")
        print(f"    Buildings Placed: {len(best['genes'])}")
        
        # Verify genes decoded correctly
        for i, gene in enumerate(best['genes']):
            print(f"      Building {i+1}: Type={gene.type_name}, Pos=({gene.x:.1f}, {gene.y:.1f})")
    
    assert result["success"], "H-SAGA did not complete successfully"
    assert result.get("best_solution") is not None, "No best solution found"
    
    print("\n✅ LEVEL 3: H-SAGA Loop Completed Successfully")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all verification tests."""
    print("\n" + "#"*60)
    print("#  PHASE 6 VERIFICATION: H-SAGA ENGINE LOGIC AUDIT")
    print("#"*60)
    
    try:
        # Level 1
        test_level1_genome_encoding()
        
        # Level 2
        test_level2_problem_evaluation()
        
        # Level 3
        test_level3_algorithm_integration()
        
        # Final verdict
        print("\n" + "="*60)
        print("✅ ✅ ✅  PHASE 6 ENGINE VERIFIED  ✅ ✅ ✅")
        print("="*60)
        print("\nThe H-SAGA optimization engine is operational.")
        print("Ready for integration with orchestrator.py")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
