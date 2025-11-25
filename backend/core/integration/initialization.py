import numpy as np
from shapely.geometry import Point

class SmartInitializer:
    """Generate semi-feasible initial layouts using heuristics."""
    
    def __init__(self, boundary, n_buildings, min_spacing=15.0):
        self.boundary = boundary
        self.n_buildings = n_buildings
        self.min_spacing = min_spacing
        
        bounds = boundary.bounds
        self.x_range = (bounds[0] + 50, bounds[2] - 50)
        self.y_range = (bounds[1] + 50, bounds[3] - 50)
    
    def generate_grid_layout(self):
        """Grid-based placement with guaranteed spacing."""
        positions = []
        types = []
        orientations = []
        
        # Calculate grid dimensions
        # Spacing: min_spacing (15) + building_size (20) + road_buffer (15) = 50
        spacing = self.min_spacing + 35.0
        
        cols = int((self.x_range[1] - self.x_range[0]) / spacing)
        rows = int(np.ceil(self.n_buildings / cols))
        
        x_start = self.x_range[0] + spacing / 2
        y_start = self.y_range[0] + spacing / 2
        
        count = 0
        for i in range(rows):
            for j in range(cols):
                if count >= self.n_buildings:
                    break
                
                x = x_start + j * spacing
                y = y_start + i * spacing
                
                # Check boundary
                if self.boundary.contains(Point(x, y)):
                    positions.append([x, y])
                    types.append(np.random.randint(0, 11))
                    orientations.append(np.random.uniform(0, 2*np.pi))
                    count += 1
            
            if count >= self.n_buildings:
                break
        
        # Pad if needed
        while len(positions) < self.n_buildings:
            x = np.random.uniform(*self.x_range)
            y = np.random.uniform(*self.y_range)
            if self.boundary.contains(Point(x, y)):
                positions.append([x, y])
                types.append(np.random.randint(0, 11))
                orientations.append(0)
        
        return np.array(positions), np.array(types), np.array(orientations)
    
    def generate_clustered_layout(self, n_clusters=3):
        """Cluster-based placement for better road accessibility."""
        positions = []
        types = []
        orientations = []
        
        # Generate cluster centers
        cluster_centers = []
        for _ in range(n_clusters):
            x = np.random.uniform(*self.x_range)
            y = np.random.uniform(*self.y_range)
            cluster_centers.append([x, y])
        
        buildings_per_cluster = self.n_buildings // n_clusters
        
        for center in cluster_centers:
            for _ in range(buildings_per_cluster):
                # Place within cluster radius with spacing
                angle = np.random.uniform(0, 2*np.pi)
                # Radius must be large enough to fit buildings
                min_radius = self.min_spacing + 20
                radius = np.random.uniform(min_radius, 150)
                
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)
                
                # Clamp to boundary
                x = np.clip(x, *self.x_range)
                y = np.clip(y, *self.y_range)
                
                if self.boundary.contains(Point(x, y)):
                    positions.append([x, y])
                    types.append(np.random.randint(0, 11))
                    orientations.append(angle)
        
        # Fill remaining
        while len(positions) < self.n_buildings:
            x = np.random.uniform(*self.x_range)
            y = np.random.uniform(*self.y_range)
            if self.boundary.contains(Point(x, y)):
                positions.append([x, y])
                types.append(np.random.randint(0, 11))
                orientations.append(0)
        
        return np.array(positions[:self.n_buildings]), \
               np.array(types[:self.n_buildings]), \
               np.array(orientations[:self.n_buildings])
