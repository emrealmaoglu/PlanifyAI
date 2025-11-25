from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import pickle
import numpy as np
from pathlib import Path

class SurrogateTrainer:
    """Train Random Forest surrogate models."""
    
    def __init__(self, data_path):
        with open(data_path, 'rb') as f:
            self.data = pickle.load(f)
    
    def train(self, objective_name, n_estimators=100):
        """Train surrogate for one objective."""
        X = self.data['X']
        if objective_name not in self.data['y']:
            print(f"Objective {objective_name} not found in data.")
            return None, None
            
        y = self.data['y'][objective_name]
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        print(f"{objective_name}:")
        print(f"  R² = {r2:.3f}")
        print(f"  MAE = {mae:.3f}")
        
        return model, {'r2': r2, 'mae': mae}
    
    def train_all(self, objectives=['road_access', 'walkability']):
        """Train surrogates for multiple objectives."""
        models = {}
        metrics = {}
        
        for obj in objectives:
            model, metric = self.train(obj)
            if model is not None:
                models[obj] = model
                metrics[obj] = metric
        
        return models, metrics
    
    def save_models(self, models, output_path):
        """Save trained models."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            pickle.dump(models, f)
        print(f"Models saved to {output_path}")
