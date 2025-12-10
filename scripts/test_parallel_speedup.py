
import sys
import time
import argparse
import multiprocessing
import numpy as np
import logging
from typing import Dict, Any

# Ensure project root is in path
import os
sys.path.append(os.getcwd())

from backend.core.domain.geometry.osm_service import CampusContext
from backend.core.optimization.spatial_problem import SpatialOptimizationProblem
from backend.core.optimization.hsaga_runner import HSAGARunner, HSAGARunnerConfig, run_hsaga
from shapely.geometry import Polygon

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_benchmark_problem(n_buildings: int = 50) -> SpatialOptimizationProblem:
    """Create a standard problem for benchmarking."""
    # 1000x1000m boundary
    boundary = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    
    # Mock context
    context = CampusContext(
        boundary=boundary,
        existing_buildings=[],
        existing_roads=[],
        existing_green_areas=[],  # Required field
        existing_walkways=[],
        gateways=[],              # Required field
        center_latlon=(41.0, 29.0),
        crs_local="EPSG:3857",    # Correct field name
        bounds_meters=(0, 0, 1000, 1000) # Required field
    )
    
    # Building counts to reach n_buildings
    counts = {
        "Faculty": int(n_buildings * 0.4),
        "Dormitory": int(n_buildings * 0.4),
        "social": int(n_buildings * 0.2)
    }
    
    return SpatialOptimizationProblem(
        context=context,
        building_counts=counts,
        enable_regulatory=True,  # Enable expensive checks
        enable_wind=False,        # Phase 7 physics disabled for pure SA bench first
        enable_solar=False
    )

def run_benchmark(parallel: bool, n_evals: int = 1000, n_chains: int = 8):
    """Run benchmark with specified configuration."""
    logger.info(f"Preparing benchmark: Parallel={parallel}, Evals={n_evals}, Chains={n_chains}")
    
    problem = create_benchmark_problem(n_buildings=50)
    
    # Configure for pure SA (or mostly SA) to stress test parallel explorer
    config = HSAGARunnerConfig(
        total_evaluations=n_evals,
        sa_fraction=0.99,  # Force mostly SA
        sa_chains=n_chains,
        parallel_sa=parallel,
        verbose=False
    )
    
    logger.info("Starting optimization...")
    start_time = time.time()
    
    runner = HSAGARunner(problem, config)
    result = runner.run()
    
    duration = time.time() - start_time
    logger.info(f"Benchmark completed in {duration:.4f}s")
    
    return duration, result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark H-SAGA Parallel Speedup")
    parser.add_argument("--evals", type=int, default=1000, help="Total evaluations")
    parser.add_argument("--chains", type=int, default=8, help="Number of SA chains")
    parser.add_argument("--compare", action="store_true", help="Run both and compare")
    
    args = parser.parse_args()
    
    print(f"CPU Count: {multiprocessing.cpu_count()}")
    
    if args.compare:
        print("\n=== RUNNING SERIAL BASELINE ===")
        t_serial, _ = run_benchmark(parallel=False, n_evals=args.evals, n_chains=args.chains)
        
        print("\n=== RUNNING PARALEL MODE ===")
        t_parallel, _ = run_benchmark(parallel=True, n_evals=args.evals, n_chains=args.chains)
        
        print("\n" + "="*40)
        print(f"RESULTS (Evals={args.evals}, Chains={args.chains})")
        print("="*40)
        print(f"Serial Time   : {t_serial:.4f}s")
        print(f"Parallel Time : {t_parallel:.4f}s")
        if t_parallel > 0:
            speedup = t_serial / t_parallel
            print(f"Speedup Factor: {speedup:.2f}x")
        else:
            print("Speedup Factor: N/A")
        print("="*40)
    else:
        # Just run parallel by default to test implementation
        run_benchmark(parallel=True, n_evals=args.evals, n_chains=args.chains)
