"""
Pymoo Problem definition for integrated co-optimization.
"""

from pymoo.core.problem import Problem
import numpy as np
from shapely.geometry import Polygon
from typing import List, Dict, Any

from .composite_genotype import CompositeGenotype

class IntegratedCampusProblem(Problem):
    """
    Multi-objective optimization problem for co-designing roads and buildings.
    
    This is the "fitness function" that NSGA-III will optimize.
    """
    
    def __init__(
        self,
        boundary: Polygon,
        n_grids: int = 3,
        n_radials: int = 2,
        n_buildings: int = 50,
        objectives: list = None,
        enable_adaptive_roads: bool = True,
        enable_turkish_standards: bool = True,
        use_smart_init: bool = True,
        use_adaptive_constraints: bool = True
    ):
        """
        Initialize problem.
        
        Args:
            boundary: Campus boundary polygon
            n_grids: Number of grid tensor fields
            n_radials: Number of radial tensor fields
            n_buildings: Number of buildings to place
            objectives: List of objective names to optimize
            enable_adaptive_roads: Whether to adapt roads to buildings
            enable_turkish_standards: Enable Turkish Standards validation
            use_smart_init: Use heuristic initialization
            use_adaptive_constraints: Use epsilon-constraint handling
        """
        self.boundary = boundary
        self.n_grids = n_grids
        self.n_radials = n_radials
        self.n_buildings = n_buildings
        self.enable_adaptive_roads = enable_adaptive_roads
        self.use_smart_init = use_smart_init
        self.use_adaptive_constraints = use_adaptive_constraints
        
        if enable_adaptive_roads:
            from .adaptive_field import AdaptiveTensorFieldGenerator
            self.adaptive_generator = AdaptiveTensorFieldGenerator(
                n_radial_fields=n_radials
            )
            
        self.enable_turkish_standards = enable_turkish_standards
        if enable_turkish_standards:
            from .constraints import TurkishStandardsValidator
            self.standards_validator = TurkishStandardsValidator(boundary)
            n_constr = 5  # green, density, spacing, boundary, road_overlap
        else:
            n_constr = 1
            
        if use_adaptive_constraints:
            from .adaptive_constraints import AdaptiveConstraintHandler
            self.constraint_handler = AdaptiveConstraintHandler()
        
        # Default objectives (MVP - simplified)
        if objectives is None:
            objectives = ['cost', 'adjacency', 'green_space', 'road_access']
        if objectives is None:
            objectives = ['cost', 'adjacency', 'green_space', 'road_access']
        self.objective_names = objectives
        
        self.parallel_evaluator = None  # For parallel execution
        
        # Calculate chromosome length
        n_vars = (
            n_grids * 2 +      # grid centers (x, y)
            n_grids +          # grid orientations
            n_grids +          # grid decay radii
            n_radials * 2 +    # radial centers
            n_radials +        # radial decay radii
            n_buildings * 2 +  # building positions
            n_buildings +      # building types
            n_buildings        # building orientations
        )
        
        # Define bounds
        bounds = boundary.bounds
        xl = []  # Lower bounds
        xu = []  # Upper bounds
        
        # Grid field bounds
        for _ in range(n_grids):
            xl.extend([bounds[0], bounds[1]])  # center x, y
            xu.extend([bounds[2], bounds[3]])
        xl.extend([0] * n_grids)              # orientations
        xu.extend([2*np.pi] * n_grids)
        xl.extend([50] * n_grids)             # decay radii (min)
        xu.extend([300] * n_grids)            # decay radii (max)
        
        # Radial field bounds
        for _ in range(n_radials):
            xl.extend([bounds[0], bounds[1]])
            xu.extend([bounds[2], bounds[3]])
        xl.extend([50] * n_radials)
        xu.extend([200] * n_radials)
        
        # Building bounds
        for _ in range(n_buildings):
            xl.extend([bounds[0], bounds[1]])
            xu.extend([bounds[2], bounds[3]])
        xl.extend([0] * n_buildings)          # types (0-10)
        xu.extend([10] * n_buildings)
        xl.extend([0] * n_buildings)          # orientations
        xu.extend([2*np.pi] * n_buildings)
        
        # Initialize pymoo Problem
        super().__init__(
            n_var=n_vars,
            n_obj=len(objectives),
            n_constr=n_constr,
            xl=np.array(xl),
            xu=np.array(xu)
        )
    
    def _evaluate(self, X, out, *args, **kwargs):
        """
        Evaluate objective functions for population.
        """
        pop_size = X.shape[0]
        
        # Use parallel evaluator if available
        if self.parallel_evaluator is not None:
            result = self.parallel_evaluator.evaluate(X)
            out["F"] = result['F']
            out["G"] = result['G']
            return

        F = np.zeros((pop_size, self.n_obj))
        G = np.zeros((pop_size, self.n_constr))
        
        for i in range(pop_size):
            genotype = self._decode_individual(X[i])
            roads, buildings = self._resolve_layout(genotype)
            
            F[i] = self._calculate_objectives(buildings, roads)
            G[i] = self._calculate_constraints(buildings, roads)
        
        out["F"] = F
        
        # Apply adaptive penalty if enabled
        if self.use_adaptive_constraints and hasattr(self, 'constraint_handler'):
            for i in range(pop_size):
                for j in range(self.n_constr):
                    G[i, j] = self.constraint_handler.apply_penalty(G[i, j])
                    
        out["G"] = G

    def get_initial_population(self, pop_size=100):
        """Generate smart initial population instead of random."""
        if not self.use_smart_init:
            return None
            
        from .initialization import SmartInitializer
        
        initializer = SmartInitializer(
            self.boundary, 
            self.n_buildings,
            min_spacing=15.0
        )
        
        X = []
        
        # 50% grid layouts
        for _ in range(pop_size // 2):
            positions, types, orientations = initializer.generate_grid_layout()
            x = self._encode_individual(positions, types, orientations)
            X.append(x)
        
        # 50% clustered layouts  
        for _ in range(pop_size - (pop_size // 2)):
            positions, types, orientations = initializer.generate_clustered_layout()
            x = self._encode_individual(positions, types, orientations)
            X.append(x)
        
        return np.array(X)

    def _encode_individual(self, positions, types, orientations):
        """Encode building layout to chromosome."""
        # Generate random tensor field params
        bounds = self.boundary.bounds
        
        grid_centers = np.random.uniform(
            [bounds[0], bounds[1]],
            [bounds[2], bounds[3]],
            (self.n_grids, 2)
        ).flatten()
        grid_thetas = np.random.uniform(0, 2*np.pi, self.n_grids)
        grid_decays = np.random.uniform(50, 300, self.n_grids)
        
        radial_centers = np.random.uniform(
            [bounds[0], bounds[1]],
            [bounds[2], bounds[3]],
            (self.n_radials, 2)
        ).flatten()
        radial_decays = np.random.uniform(50, 200, self.n_radials)
        
        # Flatten building params
        b_pos = positions.flatten()
        
        # Concatenate all
        return np.concatenate([
            grid_centers, grid_thetas, grid_decays,
            radial_centers, radial_decays,
            b_pos, types, orientations
        ])

    def _decode_individual(self, x):
        from .composite_genotype import CompositeGenotype
        return CompositeGenotype.from_flat_array(x, self.n_grids, self.n_radials, self.n_buildings)

    def _resolve_layout(self, genotype):
        if self.enable_adaptive_roads:
            building_positions = genotype.building_layout.positions
            tensor_field = self.adaptive_generator.generate_from_buildings(
                building_positions, self.boundary
            )
            roads = self._generate_roads_from_field(tensor_field)
            buildings = genotype.building_layout.to_building_list()
        else:
            roads, buildings = genotype.decode(self.boundary)
        return roads, buildings

    def _calculate_objectives(self, buildings, roads):
        objectives = []
        if 'cost' in self.objective_names:
            objectives.append(self._calculate_cost_simple(buildings))
        if 'adjacency' in self.objective_names:
            objectives.append(self._calculate_adjacency_simple(buildings))
        if 'green_space' in self.objective_names:
            objectives.append(self._calculate_green_space_simple(buildings))
        if 'road_access' in self.objective_names:
            from .objectives import calculate_road_accessibility
            objectives.append(calculate_road_accessibility(buildings, roads))
        if 'road_coverage' in self.objective_names:
            from .objectives import calculate_road_coverage
            objectives.append(calculate_road_coverage(buildings, roads))
        if 'walkability' in self.objective_names:
            from .objectives import calculate_walkability_score
            objectives.append(calculate_walkability_score(buildings, roads))
        if 'solar_exposure' in self.objective_names:
            from .objectives import calculate_solar_exposure
            objectives.append(calculate_solar_exposure(buildings))
        return np.array(objectives)

    def _calculate_constraints(self, buildings, roads):
        if self.enable_turkish_standards:
            # Pass None for roads to skip slow overlap check in validator
            _, details = self.standards_validator.calculate_constraint_violations(buildings, None)
            
            # Calculate road overlap using Spatial Index
            if roads:
                from .spatial_index import SpatialRoadIndex
                road_index = SpatialRoadIndex(roads)
                building_positions = np.array([b['position'] for b in buildings])
                _, _, violation = road_index.query_nearest(
                    building_positions,
                    min_clearance=10.0
                )
                details['road_overlap'] = violation
            else:
                details['road_overlap'] = 0.0

            return np.array([details['green_space'], details['density'], 
                            details['spacing'], details['boundary'], details['road_overlap']])
        else:
            return np.array([self._check_overlaps(buildings)])

    def _generate_roads_from_field(self, tensor_field) -> List[np.ndarray]:
        """Helper to generate roads from tensor field."""
        from ..spatial import StreamlineIntegrator, RoadNetworkGenerator
        
        # Optimize: coarser integration for speed
        integrator = StreamlineIntegrator(
            tensor_field, 
            self.boundary,
            max_step=15.0,  # Increased from 10.0
            rtol=0.05,      # Looser tolerance
            atol=1e-3
        )
        generator = RoadNetworkGenerator(integrator)
        
        bbox = self.boundary.bounds
        # Optimize: fewer seeds
        seeds = generator.generate_seed_points(
            bbox=bbox, grid_spacing=150, min_anisotropy=0.6
        )
        
        roads = generator.generate_network(seeds, min_road_length=30)
        
        return roads
    
    def _calculate_cost_simple(self, buildings: List[Dict[str, Any]]) -> float:
        """Simplified cost: just count buildings."""
        return len(buildings) * 1000.0  # Placeholder
    
    def _calculate_adjacency_simple(self, buildings: List[Dict[str, Any]]) -> float:
        """Simplified adjacency: pairwise distances."""
        if len(buildings) < 2:
            return 0.0
        
        positions = np.array([b['position'] for b in buildings])
        distances = np.linalg.norm(
            positions[:, None] - positions[None, :],
            axis=2
        )
        return float(np.mean(distances))
    
    def _calculate_green_space_simple(self, buildings: List[Dict[str, Any]]) -> float:
        """Simplified green space: building coverage ratio."""
        # Assume each building is 20x20m
        building_area = len(buildings) * 400.0
        campus_area = self.boundary.area
        if campus_area == 0:
            return 0.0
        coverage = building_area / campus_area
        return coverage  # Minimize (want more green)
    
    def _calculate_road_access_simple(self, buildings: List[Dict[str, Any]], roads: List[np.ndarray]) -> float:
        """
        Simplified road access: Euclidean distance to nearest road.
        
        MVP version - no pathfinding, just straight-line distance.
        """
        if not roads:
            return 1e6  # Penalty if no roads
        
        # Get all road points
        road_points = np.vstack(roads)
        
        # Calculate min distance for each building
        total_distance = 0.0
        for building in buildings:
            pos = building['position']
            distances = np.linalg.norm(road_points - pos, axis=1)
            total_distance += np.min(distances)
        
        return total_distance / len(buildings)  # Average distance
    
    def _check_overlaps(self, buildings: List[Dict[str, Any]]) -> float:
        """Check building overlaps (simplified)."""
        # TODO: Proper overlap detection
        return 0.0  # Placeholder
