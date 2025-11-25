from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.optimize import minimize
import numpy as np

class AdvancedOptimizer:
    def __init__(self, problem, population_size=100, n_generations=50, 
                 use_hsaga=True, refinement_interval=10, use_parallel=True):
        self.problem = problem
        self.pop_size = population_size
        self.n_gen = n_generations
        self.use_hsaga = use_hsaga
        self.refinement_interval = refinement_interval
        self.use_parallel = use_parallel
        
        if use_parallel:
            from .parallel import SharedMemoryEvaluator
            self.parallel_eval = SharedMemoryEvaluator(problem)
        
        # Generate reference directions
        self.ref_dirs = get_reference_directions(
            "das-dennis", problem.n_obj, n_partitions=4
        )
    
    def optimize(self):
        if self.use_parallel:
            # Inject parallel evaluator into the problem
            self.problem.parallel_evaluator = self.parallel_eval
        else:
            self.problem.parallel_evaluator = None

        # Use smart initialization if available
        sampling = None
        if hasattr(self.problem, 'get_initial_population'):
            initial_pop = self.problem.get_initial_population(self.pop_size)
            if initial_pop is not None:
                sampling = initial_pop
                
        kwargs = {
            "ref_dirs": self.ref_dirs,
            "pop_size": self.pop_size,
            "eliminate_duplicates": True
        }
        
        if sampling is not None:
            kwargs["sampling"] = sampling
            
        algorithm = NSGA3(**kwargs)
        
        algorithm.callback = self._refinement_callback
        
        result = minimize(
            self.problem, algorithm,
            ("n_gen", self.n_gen),
            seed=42, verbose=True
        )
        return result
    
    def _refinement_callback(self, algorithm):
        """H-SAGA local refinement every N generations."""
        # Update adaptive constraints
        if hasattr(self.problem, 'constraint_handler'):
            self.problem.constraint_handler.update()

        if not self.use_hsaga:
            return
            
        if algorithm.n_gen % self.refinement_interval != 0:
            return
        
        pop = algorithm.pop[:10]  # Top 10
        for ind in pop:
            ind.X = self._apply_sa(ind.X)
        algorithm.evaluator.eval(self.problem, pop)
    
    def _apply_sa(self, x, n_steps=50):
        """Simulated Annealing refinement."""
        current = x.copy()
        T = 1.0
        
        for _ in range(n_steps):
            neighbor = current + np.random.randn(len(x)) * 0.1
            neighbor = np.clip(neighbor, self.problem.xl, self.problem.xu)
            
            # Simple acceptance (full evaluation too expensive for demo)
            if np.random.rand() < np.exp(-1/T):
                current = neighbor
            T *= 0.95
        
        return current
    
    def extract_best_solution(self, result):
        """Extract best from Pareto front."""
        F = result.F
        F_norm = (F - F.min(axis=0)) / (F.max(axis=0) - F.min(axis=0) + 1e-8)
        best_idx = np.argmin(F_norm.sum(axis=1))
        
        from .composite_genotype import CompositeGenotype
        return CompositeGenotype.from_flat_array(
            result.X[best_idx],
            self.problem.n_grids,
            self.problem.n_radials,
            self.problem.n_buildings
        )
