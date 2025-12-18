"""Isolated benchmark for ZonedCampusCache."""

import time
import numpy as np
from shapely.geometry import Polygon
from backend.core.integration.zone_cache import ZonedCampusCache

def benchmark_isolated():
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    cache = ZonedCampusCache(boundary, zone_size=100.0)
    
    # Create dummy buildings
    buildings = []
    for i in range(50):
        buildings.append({
            'position': (np.random.uniform(0, 1000), np.random.uniform(0, 1000)),
            'orientation': 0,
            'type': 'academic',
            'area': 400
        })
    
    roads = [] # Empty roads
    
    def dummy_evaluator(b, r):
        # Simulate real work (e.g. 0.01s per zone)
        time.sleep(0.01)
        return {'green_space': 0.1, 'road_overlap': 0.0}
    
    print("Running Isolated Benchmark...")
    
    # 1. Cache Miss
    start = time.time()
    cache.evaluate_with_cache(buildings, roads, dummy_evaluator)
    t_miss = time.time() - start
    print(f"Cache Miss: {t_miss:.4f}s")
    
    # 2. Cache Hit
    start = time.time()
    cache.evaluate_with_cache(buildings, roads, dummy_evaluator)
    t_hit = time.time() - start
    print(f"Cache Hit:  {t_hit:.4f}s")
    
    # 3. Partial Hit (Move 1 building)
    buildings[0]['position'] = (buildings[0]['position'][0] + 10, buildings[0]['position'][1])
    
    start = time.time()
    cache.evaluate_with_cache(buildings, roads, dummy_evaluator)
    t_partial = time.time() - start
    print(f"Partial Hit: {t_partial:.4f}s")
    
    print("\nStats:", cache.stats)

if __name__ == "__main__":
    benchmark_isolated()
