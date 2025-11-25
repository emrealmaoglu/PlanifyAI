import numpy as np
from shapely.geometry import Point

class TurkishStandardsValidator:
    def __init__(self, boundary, min_green_ratio=0.30, 
                 max_density=0.40, min_spacing=15.0):
        self.boundary = boundary
        self.campus_area = boundary.area
        self.min_green = min_green_ratio
        self.max_density = max_density
        self.min_spacing = min_spacing
    
    def calculate_constraint_violations(self, buildings, roads):
        """Returns (total_violation, details_dict)."""
        v = {}
        
        # Green space
        building_area = len(buildings) * 400
        green_ratio = 1.0 - (building_area / self.campus_area)
        v['green_space'] = max(0, (self.min_green - green_ratio) * 1000)
        
        # Density
        density = building_area / self.campus_area
        v['density'] = max(0, (density - self.max_density) * 1000)
        
        # Spacing
        if len(buildings) >= 2:
            positions = np.array([b['position'] for b in buildings])
            dists = np.linalg.norm(positions[:, None] - positions[None, :], axis=2)
            np.fill_diagonal(dists, np.inf)
            min_dist = np.min(dists)
            v['spacing'] = max(0, (self.min_spacing - min_dist) * 10)
        else:
            v['spacing'] = 0
        
        # Boundary
        v['boundary'] = sum(
            Point(b['position']).distance(self.boundary) * 50
            for b in buildings
            if not self.boundary.contains(Point(b['position']))
        )
        
        # Road overlap
        if roads:
            road_points = np.vstack(roads)
            v['road_overlap'] = sum(
                max(0, (10 - np.min(np.linalg.norm(road_points - b['position'], axis=1))) * 20)
                for b in buildings
            )
        else:
            v['road_overlap'] = 0
        
        return sum(v.values()), v
