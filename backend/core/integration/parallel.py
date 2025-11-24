import numpy as np
from multiprocessing import Pool, cpu_count
from functools import partial

class ParallelEvaluator:
    def __init__(self, problem, n_workers=None):
        self.problem = problem
        self.n_workers = n_workers or max(1, cpu_count() - 1)
    
    def evaluate(self, X):
        """Parallel evaluation of population X."""
        pop_size = X.shape[0]
        
        # Split population into chunks
        chunk_size = max(1, pop_size // self.n_workers)
        chunks = [X[i:i+chunk_size] for i in range(0, pop_size, chunk_size)]
        
        # Parallel evaluation
        # We need to use a helper function that can be pickled or is available in global scope
        # Since _evaluate_chunk is an instance method, it might be tricky with multiprocessing if the object isn't picklable.
        # However, typically if the class is defined in a module it works. 
        # But to be safe and avoid pickling the whole problem object repeatedly if it's large, 
        # we might want to be careful. 
        # For now, following the user's design.
        
        with Pool(self.n_workers) as pool:
            results = pool.map(self._evaluate_chunk, chunks)
        
        # Combine results
        F = np.vstack([r['F'] for r in results])
        G = np.vstack([r['G'] for r in results])
        
        return {'F': F, 'G': G}
    
    def _evaluate_chunk(self, X_chunk):
        """Evaluate one chunk (runs in subprocess)."""
        n = X_chunk.shape[0]
        F = np.zeros((n, self.problem.n_obj))
        G = np.zeros((n, self.problem.n_constr))
        
        for i, x in enumerate(X_chunk):
            # Decode and evaluate (existing logic)
            genotype = self.problem._decode_individual(x)
            roads, buildings = self.problem._resolve_layout(genotype)
            
            # Calculate objectives
            F[i] = self.problem._calculate_objectives(buildings, roads)
            G[i] = self.problem._calculate_constraints(buildings, roads)
        
        return {'F': F, 'G': G}
