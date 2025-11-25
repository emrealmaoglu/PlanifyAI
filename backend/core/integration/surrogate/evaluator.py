import numpy as np
from .data_generator import SurrogateDataGenerator

class SurrogateAssistedEvaluator:
    """Use surrogates for pre-screening."""
    
    def __init__(self, problem, surrogate_models, threshold=0.8):
        self.problem = problem
        self.models = surrogate_models
        self.threshold = threshold
        # Create a generator instance for feature extraction
        self.generator = SurrogateDataGenerator(problem, n_samples=0)
    
    def evaluate(self, X):
        """Evaluate population with surrogate pre-screening."""
        pop_size = X.shape[0]
        
        # Extract features for all
        features = []
        decoded = []
        
        for x in X:
            genotype = self.problem._decode_individual(x)
            roads, buildings = genotype.decode(self.problem.boundary)
            
            feat = self.generator._extract_features(buildings, roads)
            
            features.append(feat)
            decoded.append((roads, buildings))
        
        features = np.array(features)
        
        # Predict with surrogate
        predictions = {}
        for obj_name, model in self.models.items():
            predictions[obj_name] = model.predict(features)
        
        # Select promising candidates (top 80%)
        # We assume minimization for all objectives for simplicity in ranking
        # If some are maximization, we'd need to handle signs. 
        # PlanifyAI objectives are generally minimization (cost, distance, etc.)
        # except maybe 'walkability' if it's a score? 
        # Let's check problem definition or assume minimization for now.
        # Actually, let's normalize and sum predictions to get a "predicted fitness"
        
        # Simple ranking: sum of predicted objectives
        avg_fitness = np.zeros(pop_size)
        for obj_name in predictions:
            pred = predictions[obj_name]
            # Normalize to avoid one objective dominating
            if np.max(pred) != np.min(pred):
                norm_pred = (pred - np.min(pred)) / (np.max(pred) - np.min(pred))
            else:
                norm_pred = pred
            avg_fitness += norm_pred
            
        threshold_idx = int(pop_size * self.threshold)
        # Lower is better
        top_indices = np.argsort(avg_fitness)[:threshold_idx]
        top_set = set(top_indices)
        
        # Full evaluation only for top candidates
        F = np.zeros((pop_size, self.problem.n_obj))
        G = np.zeros((pop_size, self.problem.n_constr))
        
        # Evaluate top candidates
        for i in top_indices:
            roads, buildings = decoded[i]
            F[i] = self.problem._calculate_objectives(buildings, roads)
            G[i] = self.problem._calculate_constraints(buildings, roads)
        
        # Use surrogate predictions for rest (or partial eval)
        for i in range(pop_size):
            if i not in top_set:
                roads, buildings = decoded[i]
                
                # Calculate cheap objectives and constraints fully
                # We always calculate constraints to avoid infeasible solutions sneaking in
                G[i] = self.problem._calculate_constraints(buildings, roads)
                
                # For objectives:
                for j, obj_name in enumerate(self.problem.objective_names):
                    if obj_name in predictions:
                        # Use prediction
                        F[i, j] = predictions[obj_name][i]
                    else:
                        # Calculate if not predicted (cheap objectives)
                        # We need a way to calculate single objective.
                        # For now, let's just calculate all if any is missing?
                        # Or better, assume we only predict expensive ones.
                        # But _calculate_objectives returns all.
                        # Let's just calculate all for now to be safe, 
                        # OR implement single objective calculation in problem.
                        # Given the problem structure, _calculate_objectives is monolithic.
                        # So if we don't have predictions for ALL, we might need to run it.
                        # BUT the goal is speed. 
                        # Let's assume we predict 'road_access' and 'walkability'.
                        # 'cost', 'adjacency', 'green_space' are cheap.
                        pass

                # Re-loop to fill missing cheap objectives
                # This is a bit inefficient if we don't have granular calculation.
                # Let's try to calculate cheap ones manually if possible or just accept full eval
                # if we can't separate.
                # Actually, let's look at problem.py. _calculate_objectives calls individual methods.
                # We can call them here.
                
                # Calculate cheap objectives
                if 'cost' in self.problem.objective_names:
                    idx = self.problem.objective_names.index('cost')
                    F[i, idx] = self.problem._calculate_cost_simple(buildings)
                if 'adjacency' in self.problem.objective_names:
                    idx = self.problem.objective_names.index('adjacency')
                    F[i, idx] = self.problem._calculate_adjacency_simple(buildings)
                if 'green_space' in self.problem.objective_names:
                    idx = self.problem.objective_names.index('green_space')
                    F[i, idx] = self.problem._calculate_green_space_simple(buildings)
                
                # Assign predicted values for expensive ones
                for obj_name in predictions:
                    if obj_name in self.problem.objective_names:
                        idx = self.problem.objective_names.index(obj_name)
                        F[i, idx] = predictions[obj_name][i]
        
        return {'F': F, 'G': G}
