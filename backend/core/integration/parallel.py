import numpy as np
from multiprocessing import Pool, cpu_count, shared_memory
from functools import partial
import pickle

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
        return {'F': F, 'G': G}

class SharedMemoryEvaluator(ParallelEvaluator):
    """Parallel evaluator using shared memory for problem instance."""
    
    def __init__(self, problem, n_workers=None):
        super().__init__(problem, n_workers)
        
        # Serialize problem to shared memory
        problem_bytes = pickle.dumps(problem)
        self.shm = shared_memory.SharedMemory(
            create=True, 
            size=len(problem_bytes)
        )
        self.shm.buf[:len(problem_bytes)] = problem_bytes
        self.problem_size = len(problem_bytes)
    
    def evaluate(self, X):
        """Evaluate using shared memory."""
        pop_size = X.shape[0]
        chunk_size = max(1, pop_size // self.n_workers)
        chunks = [X[i:i+chunk_size] for i in range(0, pop_size, chunk_size)]
        
        # Pass shared memory name instead of problem
        with Pool(self.n_workers) as pool:
            eval_func = partial(
                self._evaluate_chunk_shm,
                shm_name=self.shm.name,
                problem_size=self.problem_size
            )
            results = pool.map(eval_func, chunks)
        
        # Combine results
        F = np.vstack([r['F'] for r in results])
        G = np.vstack([r['G'] for r in results])
        
        return {'F': F, 'G': G}
    
    @staticmethod
    def _evaluate_chunk_shm(X_chunk, shm_name, problem_size):
        """Deserialize problem from shared memory."""
        shm = shared_memory.SharedMemory(name=shm_name)
        problem = pickle.loads(bytes(shm.buf[:problem_size]))
        
        n = X_chunk.shape[0]
        F = np.zeros((n, problem.n_obj))
        G = np.zeros((n, problem.n_constr))
        
        for i, x in enumerate(X_chunk):
            genotype = problem._decode_individual(x)
            roads, buildings = problem._resolve_layout(genotype)
            F[i] = problem._calculate_objectives(buildings, roads)
            G[i] = problem._calculate_constraints(buildings, roads)
        
        shm.close()
        return {'F': F, 'G': G}
    
    def __del__(self):
        """Cleanup shared memory."""
        if hasattr(self, 'shm'):
            try:
                self.shm.close()
                self.shm.unlink()
            except FileNotFoundError:
                pass
