import numpy as np
import pickle
from pathlib import Path
from shapely.geometry import Polygon
from tqdm import tqdm

class SurrogateDataGenerator:
    """Generate training data for surrogate models."""
    
    def __init__(self, problem, n_samples=1000, output_dir="data/surrogate"):
        self.problem = problem
        self.n_samples = n_samples
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self):
        """Generate diverse layouts and evaluate."""
        print(f"Generating {self.n_samples} training samples...")
        
        X_features = []
        y_objectives = {}
        
        # Use problem bounds for random generation
        xl = self.problem.xl
        xu = self.problem.xu
        
        for i in tqdm(range(self.n_samples)):
            # Random individual
            x = np.random.rand(self.problem.n_var)
            x = x * (xu - xl) + xl
            
            # Decode
            genotype = self.problem._decode_individual(x)
            roads, buildings = genotype.decode(self.problem.boundary)
            
            # Extract features
            features = self._extract_features(buildings, roads)
            X_features.append(features)
            
            # Evaluate objectives
            objectives = self.problem._calculate_objectives(buildings, roads)
            
            for j, obj_name in enumerate(self.problem.objective_names):
                if obj_name not in y_objectives:
                    y_objectives[obj_name] = []
                y_objectives[obj_name].append(objectives[j])
        
        # Save
        data = {
            'X': np.array(X_features),
            'y': {k: np.array(v) for k, v in y_objectives.items()},
            'feature_names': self._get_feature_names()
        }
        
        filepath = self.output_dir / f"training_data_{self.n_samples}.pkl"
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"Saved to {filepath}")
        return data
    
    def _extract_features(self, buildings, roads):
        """Extract numerical features from layout."""
        features = []
        
        # Building features
        features.append(len(buildings))  # count
        
        if buildings:
            positions = np.array([b['position'] for b in buildings])
            
            # Spatial statistics
            features.append(np.mean(positions[:, 0]))  # mean x
            features.append(np.mean(positions[:, 1]))  # mean y
            features.append(np.std(positions[:, 0]))   # std x
            features.append(np.std(positions[:, 1]))   # std y
            
            # Pairwise distances
            if len(buildings) > 1:
                dists = np.linalg.norm(positions[:, None] - positions[None, :], axis=2)
                np.fill_diagonal(dists, 1e6) # Use large finite number instead of inf
                features.append(np.min(dists))   # closest pair
                features.append(np.mean(dists))  # avg distance
                features.append(np.max(dists))   # farthest pair
            else:
                features.extend([0, 0, 0])
        else:
            features.extend([0, 0, 0, 0, 0, 0, 0])
        
        # Road features
        features.append(len(roads))  # road count
        
        if roads:
            # Calculate total road length
            total_length = 0
            for road in roads:
                if len(road) > 1:
                    total_length += np.sum(np.linalg.norm(np.diff(road, axis=0), axis=1))
            features.append(total_length)
        else:
            features.append(0)
        
        return features
    
    def _get_feature_names(self):
        return [
            'n_buildings', 'mean_x', 'mean_y', 'std_x', 'std_y',
            'min_distance', 'avg_distance', 'max_distance',
            'n_roads', 'total_road_length'
        ]
