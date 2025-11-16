# PlanifyAI - 2. Hafta Günlük Implementation Planı
## 🚀 Teorik Araştırmadan Pratik Uygulamaya

---

# 📋 **HAFTALIK ÖZET**

| Gün | Ana Görev | Deliverable | Süre |
|-----|-----------|-------------|------|
| **Pazartesi** | H-SAGA Core | Working algorithm | 5 saat |
| **Salı** | Semantic Tensor Fields | Patent-worthy implementation | 5 saat |
| **Çarşamba** | Road Generation | RK4 integration | 5 saat |
| **Perşembe** | Testing & Profiling | 85% coverage, benchmarks | 5 saat |
| **Cuma** | UI Prototype | Streamlit app (TR/EN) | 5 saat |
| **Cumartesi** | Integration | End-to-end working | 5 saat |
| **Pazar** | Polish & Demo | Video demo ready | 5 saat |

---

# 🗓️ **GÜNLÜK DETAYLI PLANLAR**

## PAZARTESİ: H-SAGA Core Implementation

### 🌅 Sabah (09:00-12:00): Algorithm Architecture

#### Task 1: Project Setup (30 dk)
```bash
# Terminal komutları
mkdir planifyai && cd planifyai
git init
git checkout -b feature/hsaga-implementation

# Folder structure
mkdir -p src/{algorithms,data,ui,utils}
mkdir -p tests/{unit,integration,benchmarks}
mkdir -p docs/{api,examples,research}
mkdir -p config
mkdir -p outputs

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Core dependencies
pip install numpy scipy pandas geopandas shapely
pip install pytest pytest-cov pytest-benchmark
pip install streamlit plotly folium
```

#### Task 2: H-SAGA Base Class (90 dk)
```python
# src/algorithms/hsaga.py
"""
Hybrid Simulated Annealing - Genetic Algorithm
Based on Li et al. 2025 reverse approach
"""
import numpy as np
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum

class BuildingType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"  
    EDUCATIONAL = "educational"
    HEALTH = "health"
    SOCIAL = "social"

@dataclass
class Building:
    """Building entity with semantic type"""
    id: str
    type: BuildingType
    area: float  # m²
    floors: int
    position: Optional[Tuple[float, float]] = None
    constraints: Dict = field(default_factory=dict)

    @property
    def footprint(self) -> float:
        """Calculate building footprint"""
        return self.area / self.floors

    @property
    def importance(self) -> float:
        """Calculate importance weight for tensor field"""
        weights = {
            BuildingType.HEALTH: 2.5,
            BuildingType.COMMERCIAL: 2.0,
            BuildingType.EDUCATIONAL: 1.5,
            BuildingType.SOCIAL: 1.2,
            BuildingType.RESIDENTIAL: 1.0
        }
        return weights.get(self.type, 1.0) * np.sqrt(self.area)

class HybridSAGA:
    """
    Reverse Hybrid: SA for exploration → GA for refinement
    Optimized for M1 Mac performance
    """

    def __init__(self,
                 area_bounds: Tuple[float, float, float, float],
                 buildings: List[Building],
                 constraints: Optional[Dict] = None):
        """
        Initialize H-SAGA optimizer

        Args:
            area_bounds: (x_min, y_min, x_max, y_max)
            buildings: List of buildings to place
            constraints: Dictionary of constraints (green_areas, obstacles, etc.)
        """
        self.bounds = area_bounds
        self.buildings = buildings
        self.constraints = constraints or {}

        # SA parameters (from Li et al.)
        self.sa_config = {
            'temperature': 300,
            'cooling_rate': 0.95,
            'iterations': 200,
            'chains': 10  # Parallel SA chains
        }

        # GA parameters  
        self.ga_config = {
            'population_size': 100,
            'generations': 100,
            'crossover_rate': 0.8,
            'mutation_rate': 0.15,  # High for diversity
            'elite_size': 10
        }

        # Fitness weights (adjustable)
        self.weights = {
            'walkability': 0.25,
            'green_access': 0.25,
            'compactness': 0.20,
            'type_compatibility': 0.15,
            'infrastructure_cost': 0.15
        }

        # Performance tracking
        self.stats = {
            'iterations': 0,
            'best_fitness': -np.inf,
            'convergence_history': []
        }
```

#### Task 3: Simulated Annealing Implementation (60 dk)
```python
# Continuation of hsaga.py

    def _simulated_annealing(self) -> List[Dict]:
        """
        Stage 1: SA for global exploration
        Returns top solutions from parallel SA chains
        """
        solutions = []

        # Use multiprocessing for M1 performance cores
        from multiprocessing import Pool

        def run_sa_chain(seed):
            """Single SA chain"""
            np.random.seed(seed)
            current = self._random_solution()
            best = current.copy()
            temp = self.sa_config['temperature']

            for iteration in range(self.sa_config['iterations']):
                # Generate neighbor solution
                neighbor = self._perturb_solution(current, temp)

                # Evaluate fitness change
                current_fitness = self._evaluate_fitness(current)
                neighbor_fitness = self._evaluate_fitness(neighbor)
                delta = neighbor_fitness - current_fitness

                # Metropolis criterion
                accept = delta > 0 or np.random.random() < np.exp(delta / temp)

                if accept:
                    current = neighbor
                    if neighbor_fitness > self._evaluate_fitness(best):
                        best = neighbor.copy()

                # Cooling
                temp *= self.sa_config['cooling_rate']

            return best

        # Run parallel SA chains on M1 performance cores
        with Pool(processes=4) as pool:
            solutions = pool.map(run_sa_chain, range(self.sa_config['chains']))

        return solutions

    def _random_solution(self) -> Dict:
        """Generate random valid solution"""
        solution = {'positions': {}}
        x_min, y_min, x_max, y_max = self.bounds

        for building in self.buildings:
            # Random position within bounds
            margin = np.sqrt(building.footprint) / 2
            x = np.random.uniform(x_min + margin, x_max - margin)
            y = np.random.uniform(y_min + margin, y_max - margin)
            solution['positions'][building.id] = (x, y)

        return solution

    def _perturb_solution(self, solution: Dict, temperature: float) -> Dict:
        """Perturb solution for SA neighbor generation"""
        new_solution = solution.copy()
        new_solution['positions'] = solution['positions'].copy()

        # Perturbation size based on temperature
        step_size = temperature / 100  # Adaptive step size

        # Randomly select building to move
        building_id = np.random.choice(list(solution['positions'].keys()))
        x, y = solution['positions'][building_id]

        # Gaussian perturbation
        dx = np.random.normal(0, step_size)
        dy = np.random.normal(0, step_size)

        # Apply and clip to bounds
        x_min, y_min, x_max, y_max = self.bounds
        new_x = np.clip(x + dx, x_min + 10, x_max - 10)
        new_y = np.clip(y + dy, y_min + 10, y_max - 10)

        new_solution['positions'][building_id] = (new_x, new_y)

        return new_solution
```

### 🌞 Öğleden Sonra (14:00-17:00): GA & Fitness Functions

#### Task 4: Genetic Algorithm Implementation (90 dk)
```python
# Continue hsaga.py

    def _genetic_refinement(self, initial_population: List[Dict]) -> List[Dict]:
        """
        Stage 2: GA for local refinement
        Uses SA solutions as initial population
        """
        # Expand population from SA solutions
        population = self._expand_population(
            initial_population,
            self.ga_config['population_size']
        )

        for generation in range(self.ga_config['generations']):
            # Evaluate fitness for all individuals
            fitness_scores = [
                self._evaluate_fitness(ind)
                for ind in population
            ]

            # Tournament selection
            parents = self._tournament_selection(
                population,
                fitness_scores,
                tournament_size=3
            )

            # Crossover and mutation
            offspring = []
            for i in range(0, len(parents)-1, 2):
                parent1, parent2 = parents[i], parents[i+1]

                # Type-aware crossover
                if np.random.random() < self.ga_config['crossover_rate']:
                    child1, child2 = self._type_aware_crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()

                # Adaptive mutation
                if np.random.random() < self.ga_config['mutation_rate']:
                    child1 = self._adaptive_mutation(child1, generation)
                if np.random.random() < self.ga_config['mutation_rate']:
                    child2 = self._adaptive_mutation(child2, generation)

                offspring.extend([child1, child2])

            # Elitism - preserve best solutions
            elite_indices = np.argsort(fitness_scores)[-self.ga_config['elite_size']:]
            elite = [population[i] for i in elite_indices]

            # New population
            population = elite + offspring[:self.ga_config['population_size'] - len(elite)]

            # Track convergence
            best_fitness = max(fitness_scores)
            self.stats['convergence_history'].append(best_fitness)

            # Progress logging
            if generation % 20 == 0:
                print(f"  GA Generation {generation}: Best fitness = {best_fitness:.3f}")

        return population

    def _type_aware_crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """
        Crossover that preserves building type relationships
        Patent-pending: Type-semantic preservation in crossover
        """
        child1 = {'positions': {}}
        child2 = {'positions': {}}

        # Group buildings by type
        type_groups = {}
        for building in self.buildings:
            if building.type not in type_groups:
                type_groups[building.type] = []
            type_groups[building.type].append(building.id)

        # Crossover by type groups (preserve type clusters)
        for building_type, building_ids in type_groups.items():
            if np.random.random() < 0.5:
                # Child1 gets type cluster from parent1
                for bid in building_ids:
                    child1['positions'][bid] = parent1['positions'][bid]
                    child2['positions'][bid] = parent2['positions'][bid]
            else:
                # Child1 gets type cluster from parent2
                for bid in building_ids:
                    child1['positions'][bid] = parent2['positions'][bid]
                    child2['positions'][bid] = parent1['positions'][bid]

        return child1, child2
```

#### Task 5: Fitness Function Implementation (90 dk)
```python
# src/algorithms/fitness.py
import numpy as np
from typing import Dict, List
from scipy.spatial.distance import cdist

class FitnessEvaluator:
    """
    Multi-objective fitness evaluation
    Implements metrics from research
    """

    def __init__(self, buildings: List, constraints: Dict, weights: Dict):
        self.buildings = buildings
        self.constraints = constraints
        self.weights = weights

    def evaluate(self, solution: Dict) -> float:
        """
        Calculate weighted fitness score
        """
        metrics = {
            'walkability': self._walkability_score(solution),
            'green_access': self._green_access_score(solution),
            'compactness': self._compactness_score(solution),
            'type_compatibility': self._type_compatibility_score(solution),
            'infrastructure_cost': self._infrastructure_cost_score(solution)
        }

        # Penalty for constraint violations
        penalty = self._calculate_penalties(solution)

        # Weighted sum
        fitness = sum(
            self.weights[key] * metrics[key]
            for key in metrics
        )

        return fitness - penalty

    def _walkability_score(self, solution: Dict) -> float:
        """
        EPA Walkability Index adaptation
        Based on average inter-building distances
        """
        positions = np.array(list(solution['positions'].values()))

        if len(positions) < 2:
            return 1.0

        # Pairwise distances
        distances = cdist(positions, positions)

        # Average non-zero distance
        mask = distances > 0
        avg_distance = np.mean(distances[mask]) if mask.any() else 0

        # Normalize (ideal: 50-150m)
        ideal_distance = 100
        score = np.exp(-abs(avg_distance - ideal_distance) / ideal_distance)

        return score

    def _green_access_score(self, solution: Dict) -> float:
        """
        2SFCA (2-Step Floating Catchment Area) method
        Measures access to green spaces
        """
        if 'green_areas' not in self.constraints:
            return 0.5  # Neutral if no green areas defined

        green_areas = self.constraints['green_areas']

        # Distance to nearest green area for each building
        access_scores = []

        for building_id, position in solution['positions'].items():
            min_distance = float('inf')

            for green_area in green_areas:
                # Distance to green area centroid
                distance = np.linalg.norm(
                    np.array(position) - np.array(green_area['centroid'])
                )
                min_distance = min(min_distance, distance)

            # Score based on distance (ideal: <200m)
            score = np.exp(-min_distance / 200) if min_distance < 500 else 0
            access_scores.append(score)

        return np.mean(access_scores) if access_scores else 0.5

    def _type_compatibility_score(self, solution: Dict) -> float:
        """
        Building type compatibility matrix
        Patent-pending: Type-semantic spatial relationships
        """
        # Compatibility matrix (higher = better neighbors)
        compatibility = {
            ('residential', 'residential'): 1.0,
            ('residential', 'commercial'): 0.3,
            ('residential', 'educational'): 0.7,
            ('residential', 'health'): 0.5,
            ('residential', 'social'): 0.8,
            ('commercial', 'commercial'): 0.9,
            ('commercial', 'educational'): 0.4,
            ('commercial', 'health'): 0.6,
            ('educational', 'educational'): 0.8,
            ('educational', 'health'): 0.7,
            ('health', 'health'): 0.5,
        }

        score = 0
        count = 0

        # Check nearby buildings
        for b1 in self.buildings:
            pos1 = solution['positions'][b1.id]

            for b2 in self.buildings:
                if b1.id == b2.id:
                    continue

                pos2 = solution['positions'][b2.id]
                distance = np.linalg.norm(
                    np.array(pos1) - np.array(pos2)
                )

                # Only consider nearby buildings (<100m)
                if distance < 100:
                    key = tuple(sorted([b1.type.value, b2.type.value]))
                    compat_score = compatibility.get(key, 0.5)

                    # Weight by inverse distance
                    weighted_score = compat_score / (1 + distance/100)
                    score += weighted_score
                    count += 1

        return score / count if count > 0 else 0.5
```

### 🌙 Akşam (20:00-21:00): Testing & Documentation

#### Task 6: Unit Tests (60 dk)
```python
# tests/unit/test_hsaga.py
import pytest
import numpy as np
from src.algorithms.hsaga import HybridSAGA, Building, BuildingType

class TestHSAGA:

    @pytest.fixture
    def sample_buildings(self):
        """Create sample buildings for testing"""
        return [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 5),
            Building("B2", BuildingType.COMMERCIAL, 1500, 3),
            Building("B3", BuildingType.EDUCATIONAL, 3000, 4),
            Building("B4", BuildingType.HEALTH, 1000, 2),
            Building("B5", BuildingType.SOCIAL, 1200, 2)
        ]

    @pytest.fixture
    def optimizer(self, sample_buildings):
        """Create optimizer instance"""
        return HybridSAGA(
            area_bounds=(0, 0, 500, 500),
            buildings=sample_buildings,
            constraints={'green_areas': []}
        )

    def test_initialization(self, optimizer, sample_buildings):
        """Test proper initialization"""
        assert optimizer.buildings == sample_buildings
        assert optimizer.bounds == (0, 0, 500, 500)
        assert len(optimizer.weights) == 5

    def test_random_solution_generation(self, optimizer):
        """Test random solution is valid"""
        solution = optimizer._random_solution()

        assert 'positions' in solution
        assert len(solution['positions']) == len(optimizer.buildings)

        # Check all positions are within bounds
        for building_id, (x, y) in solution['positions'].items():
            assert 0 <= x <= 500
            assert 0 <= y <= 500

    def test_solution_perturbation(self, optimizer):
        """Test SA perturbation maintains validity"""
        solution = optimizer._random_solution()
        perturbed = optimizer._perturb_solution(solution, temperature=100)

        # Should have same structure
        assert set(solution['positions'].keys()) == set(perturbed['positions'].keys())

        # At least one position should change
        changed = False
        for bid in solution['positions']:
            if solution['positions'][bid] != perturbed['positions'][bid]:
                changed = True
                break
        assert changed

    @pytest.mark.benchmark
    def test_performance_5_buildings(self, optimizer, benchmark):
        """Benchmark with 5 buildings"""
        result = benchmark(optimizer.optimize)
        assert result['time'] < 20.0  # Should complete in <20s
        assert result['fitness'] > 0
```

---

## SALI: Semantic Tensor Fields

### 🌅 Sabah (09:00-12:00): Tensor Field Mathematics

#### Task 1: Base Tensor Field Class (90 dk)
```python
# src/algorithms/semantic_tensor.py
"""
Patent-pending: Building-type aware tensor field generation
Creates adaptive road patterns based on building semantics
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class TensorField:
    """2D Tensor field representation"""
    grid_size: int
    resolution: float  # meters per grid cell
    data: np.ndarray  # Shape: (grid_size, grid_size, 2, 2)

    def __post_init__(self):
        if self.data is None:
            self.data = np.zeros((self.grid_size, self.grid_size, 2, 2))

    def get_eigendecomposition(self, x: int, y: int) -> Tuple[np.ndarray, np.ndarray]:
        """Get eigenvectors and eigenvalues at a point"""
        tensor = self.data[x, y]
        eigenvalues, eigenvectors = np.linalg.eig(tensor)
        return eigenvalues, eigenvectors

    def get_major_direction(self, x: int, y: int) -> np.ndarray:
        """Get major eigenvector (primary flow direction)"""
        eigenvalues, eigenvectors = self.get_eigendecomposition(x, y)
        major_idx = np.argmax(np.abs(eigenvalues))
        return eigenvectors[:, major_idx]

class SemanticTensorFieldGenerator:
    """
    Generates tensor fields based on building types
    Core innovation: Type-specific field patterns
    """

    def __init__(self, grid_size: int = 200, resolution: float = 2.5):
        """
        Initialize generator

        Args:
            grid_size: Grid dimensions (grid_size x grid_size)
            resolution: Meters per grid cell
        """
        self.grid_size = grid_size
        self.resolution = resolution
        self.field = TensorField(grid_size, resolution, None)

        # Field generation parameters by building type
        self.field_params = {
            'commercial': {
                'pattern': 'radial',
                'strength': 2.0,
                'decay_rate': 0.8,
                'influence_radius': 150  # meters
            },
            'residential': {
                'pattern': 'grid',
                'strength': 1.0,
                'grid_angle': 0,  # North-South alignment
                'influence_radius': 100
            },
            'educational': {
                'pattern': 'organic',
                'strength': 1.5,
                'turbulence': 0.3,
                'influence_radius': 120
            },
            'health': {
                'pattern': 'radial_strong',
                'strength': 2.5,
                'decay_rate': 0.6,
                'influence_radius': 200  # Emergency access
            },
            'social': {
                'pattern': 'mixed',
                'strength': 1.2,
                'influence_radius': 80
            }
        }
```

#### Task 2: Field Pattern Generators (90 dk)
```python
# Continue semantic_tensor.py

    def generate_composite_field(self, buildings: List) -> TensorField:
        """
        Generate composite tensor field from all buildings
        Patent claim: Semantic composition of tensor fields
        """
        composite_field = np.zeros((self.grid_size, self.grid_size, 2, 2))

        for building in buildings:
            # Get building-specific field
            building_field = self._generate_building_field(building)

            # Weight by building importance
            weight = building.importance

            # Add to composite with decay
            composite_field += weight * building_field

        # Post-processing
        composite_field = self._normalize_field(composite_field)
        composite_field = self._smooth_field(composite_field)

        self.field.data = composite_field
        return self.field

    def _generate_building_field(self, building) -> np.ndarray:
        """Generate field based on building type"""
        params = self.field_params.get(building.type.value, self.field_params['social'])

        if params['pattern'] == 'radial':
            return self._radial_field(building, params)
        elif params['pattern'] == 'radial_strong':
            return self._radial_field(building, params)
        elif params['pattern'] == 'grid':
            return self._grid_field(building, params)
        elif params['pattern'] == 'organic':
            return self._organic_field(building, params)
        else:  # mixed
            return self._mixed_field(building, params)

    def _radial_field(self, building, params) -> np.ndarray:
        """
        Radial attractor field (commercial, health)
        Roads converge toward building
        """
        field = np.zeros((self.grid_size, self.grid_size, 2, 2))

        # Convert building position to grid coordinates
        cx = int(building.position[0] / self.resolution)
        cy = int(building.position[1] / self.resolution)

        # Influence radius in grid cells
        radius_cells = params['influence_radius'] / self.resolution

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Vector from point to center
                dx = cx - i
                dy = cy - j
                distance = np.sqrt(dx**2 + dy**2) + 1e-6

                # Skip if outside influence radius
                if distance > radius_cells:
                    continue

                # Normalized radial vector
                radial = np.array([dx/distance, dy/distance])

                # Decay function
                decay = params['strength'] * np.exp(-params['decay_rate'] * distance / radius_cells)

                # Tensor from radial vector (outer product)
                field[i, j] = decay * np.outer(radial, radial)

        return field

    def _grid_field(self, building, params) -> np.ndarray:
        """
        Grid-aligned field (residential)
        Promotes regular street patterns
        """
        field = np.zeros((self.grid_size, self.grid_size, 2, 2))

        # Grid directions (rotated by angle)
        angle = params['grid_angle']
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        # Primary direction (e.g., North-South)
        dir1 = np.array([cos_a, sin_a])
        # Secondary direction (perpendicular)
        dir2 = np.array([-sin_a, cos_a])

        # Create base tensors
        tensor1 = params['strength'] * np.outer(dir1, dir1)
        tensor2 = params['strength'] * 0.5 * np.outer(dir2, dir2)

        # Apply with distance decay from building
        cx = int(building.position[0] / self.resolution)
        cy = int(building.position[1] / self.resolution)
        radius_cells = params['influence_radius'] / self.resolution

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                distance = np.sqrt((i-cx)**2 + (j-cy)**2)

                if distance > radius_cells:
                    continue

                decay = np.exp(-distance / (radius_cells / 2))
                field[i, j] = decay * (tensor1 + tensor2)

        return field

    def _organic_field(self, building, params) -> np.ndarray:
        """
        Organic/curved field (educational)
        Creates park-like curved paths
        """
        field = np.zeros((self.grid_size, self.grid_size, 2, 2))

        cx = int(building.position[0] / self.resolution)
        cy = int(building.position[1] / self.resolution)
        radius_cells = params['influence_radius'] / self.resolution

        # Use Perlin noise for organic patterns
        # Simplified version using sine waves
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                distance = np.sqrt((i-cx)**2 + (j-cy)**2)

                if distance > radius_cells:
                    continue

                # Organic flow using trigonometric functions
                theta = np.arctan2(j-cy, i-cx)

                # Add turbulence
                turbulence = params['turbulence'] * np.sin(distance / 10)
                flow_angle = theta + turbulence

                # Flow direction
                flow_dir = np.array([np.cos(flow_angle), np.sin(flow_angle)])

                # Perpendicular direction for curvature
                perp_dir = np.array([-np.sin(flow_angle), np.cos(flow_angle)])

                # Decay
                decay = params['strength'] * np.exp(-distance / radius_cells)

                # Combine directions with different weights
                field[i, j] = decay * (
                    0.7 * np.outer(flow_dir, flow_dir) +
                    0.3 * np.outer(perp_dir, perp_dir)
                )

        return field
```

### 🌞 Öğleden Sonra (14:00-17:00): Integration & Optimization

#### Task 3: Field Normalization & Smoothing (60 dk)
```python
# Continue semantic_tensor.py

    def _normalize_field(self, field: np.ndarray) -> np.ndarray:
        """
        Normalize tensor field to prevent singularities
        Ensures numerical stability for streamline tracing
        """
        normalized = np.zeros_like(field)

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                tensor = field[i, j]

                # Skip zero tensors
                if np.allclose(tensor, 0):
                    continue

                # Eigendecomposition
                eigenvalues, eigenvectors = np.linalg.eig(tensor)

                # Clamp eigenvalues to reasonable range
                eigenvalues = np.clip(eigenvalues, -1, 1)

                # Reconstruct tensor
                normalized[i, j] = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

        return normalized

    def _smooth_field(self, field: np.ndarray, iterations: int = 3) -> np.ndarray:
        """
        Gaussian smoothing for continuous field
        Prevents sharp discontinuities
        """
        smoothed = field.copy()

        for _ in range(iterations):
            for i in range(2):
                for j in range(2):
                    smoothed[:, :, i, j] = gaussian_filter(
                        smoothed[:, :, i, j],
                        sigma=1.5
                    )

        return smoothed

    def visualize_field(self, save_path: Optional[str] = None):
        """
        Visualize tensor field using eigenvectors
        Useful for debugging and presentations
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch

        fig, ax = plt.subplots(figsize=(12, 12))

        # Sample points for visualization (every 5th point)
        step = 5

        for i in range(0, self.grid_size, step):
            for j in range(0, self.grid_size, step):
                tensor = self.field.data[i, j]

                if np.allclose(tensor, 0):
                    continue

                # Get eigenvectors
                eigenvalues, eigenvectors = np.linalg.eig(tensor)

                # Major eigenvector
                major_idx = np.argmax(np.abs(eigenvalues))
                major_vec = eigenvectors[:, major_idx]
                major_val = eigenvalues[major_idx]

                # Scale by eigenvalue
                scale = np.abs(major_val) * step * 0.8

                # Plot arrow
                arrow = FancyArrowPatch(
                    (j, i),
                    (j + major_vec[0] * scale, i + major_vec[1] * scale),
                    arrowstyle='->',
                    color='blue',
                    alpha=0.6,
                    linewidth=1
                )
                ax.add_patch(arrow)

        ax.set_xlim(0, self.grid_size)
        ax.set_ylim(0, self.grid_size)
        ax.set_aspect('equal')
        ax.invert_yaxis()
        ax.set_title('Semantic Tensor Field Visualization')
        ax.set_xlabel('X (grid cells)')
        ax.set_ylabel('Y (grid cells)')

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()
```

#### Task 4: Performance Optimization for M1 (60 dk)
```python
# src/utils/m1_optimization.py
"""
M1 Mac optimization utilities
Uses Apple Accelerate framework via NumPy
"""
import numpy as np
import os

def verify_accelerate():
    """Verify NumPy is using Accelerate"""
    config = np.show_config(mode='dicts')['Build Dependencies']['blas']

    if 'accelerate' in config.get('name', '').lower():
        print("✅ NumPy is using Apple Accelerate")
        return True
    else:
        print("⚠️ NumPy is NOT using Accelerate. Performance will be suboptimal.")
        print("Install with: conda install numpy 'libblas=*=*accelerate'")
        return False

def optimize_threading():
    """Set optimal threading for M1"""
    # M1 has 4 performance cores + 4 efficiency cores
    # Best to use performance cores only
    os.environ['OMP_NUM_THREADS'] = '4'
    os.environ['MKL_NUM_THREADS'] = '4'
    os.environ['NUMPY_NUM_THREADS'] = '4'
    print("✅ Threading optimized for M1 (4 performance cores)")

# Vectorized operations for tensor field
def batch_tensor_operation(tensors: np.ndarray, operation: str) -> np.ndarray:
    """
    Batch tensor operations using vectorization
    Much faster than loops on M1
    """
    if operation == 'eigendecomposition':
        # Vectorized eigendecomposition
        return np.linalg.eig(tensors)
    elif operation == 'determinant':
        return np.linalg.det(tensors)
    elif operation == 'trace':
        return np.trace(tensors, axis1=-2, axis2=-1)
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

#### Task 5: Integration Test (60 dk)
```python
# tests/integration/test_semantic_tensor.py
import pytest
import numpy as np
from src.algorithms.semantic_tensor import SemanticTensorFieldGenerator
from src.algorithms.hsaga import Building, BuildingType

class TestSemanticTensorIntegration:

    def test_commercial_radial_field(self):
        """Test commercial building creates radial field"""
        generator = SemanticTensorFieldGenerator(grid_size=100)

        building = Building(
            "mall",
            BuildingType.COMMERCIAL,
            area=5000,
            floors=2
        )
        building.position = (50, 50)  # Center of grid

        field = generator._radial_field(
            building,
            generator.field_params['commercial']
        )

        # Check radial pattern
        # At center, should have strong field
        center_tensor = field[20, 20]  # Convert position
        assert np.linalg.norm(center_tensor) > 0.5

        # Far from center, should be weak
        corner_tensor = field[5, 5]
        assert np.linalg.norm(corner_tensor) < 0.1

    def test_composite_field_generation(self):
        """Test composite field from multiple buildings"""
        generator = SemanticTensorFieldGenerator(grid_size=100)

        buildings = [
            Building("mall", BuildingType.COMMERCIAL, 3000, 2),
            Building("apartment", BuildingType.RESIDENTIAL, 5000, 10),
            Building("school", BuildingType.EDUCATIONAL, 4000, 3)
        ]

        # Set positions
        buildings[0].position = (30, 30)
        buildings[1].position = (70, 70)
        buildings[2].position = (50, 50)

        # Generate composite field
        field = generator.generate_composite_field(buildings)

        # Field should not be zero
        assert not np.allclose(field.data, 0)

        # Check field is smooth (no sharp discontinuities)
        # Gradient should be reasonable
        grad_x = np.gradient(field.data[:, :, 0, 0], axis=0)
        grad_y = np.gradient(field.data[:, :, 0, 0], axis=1)

        max_gradient = max(np.max(np.abs(grad_x)), np.max(np.abs(grad_y)))
        assert max_gradient < 10  # No extreme gradients
```

---

## ÇARŞAMBA: Road Network Generation

### 🌅 Sabah (09:00-12:00): RK4 Implementation

#### Task 1: Road Tracer Class (120 dk)
```python
# src/algorithms/road_generator.py
"""
Road network generation via tensor field streamline tracing
Uses Runge-Kutta 4th order integration
"""
import numpy as np
import networkx as nx
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

class RoadType(Enum):
    PRIMARY = "primary"      # 8m width, main roads
    SECONDARY = "secondary"  # 6m width, collector roads  
    PEDESTRIAN = "pedestrian"  # 3m width, walkways
    BICYCLE = "bicycle"      # 2m width, bike lanes

@dataclass
class Road:
    """Road segment representation"""
    id: str
    type: RoadType
    points: List[Tuple[float, float]]
    width: float

    @property
    def length(self) -> float:
        """Calculate road length"""
        if len(self.points) < 2:
            return 0

        length = 0
        for i in range(len(self.points) - 1):
            p1 = np.array(self.points[i])
            p2 = np.array(self.points[i + 1])
            length += np.linalg.norm(p2 - p1)
        return length

class TensorFieldRoadGenerator:
    """
    Generates road networks by tracing streamlines through tensor fields
    Patent-pending: Semantic streamline classification
    """

    def __init__(self,
                 tensor_field,
                 buildings: List,
                 area_bounds: Tuple[float, float, float, float],
                 terrain: Optional[np.ndarray] = None):
        """
        Initialize road generator

        Args:
            tensor_field: SemanticTensorField instance
            buildings: List of Building objects
            area_bounds: (x_min, y_min, x_max, y_max)
            terrain: Optional elevation/slope data
        """
        self.field = tensor_field
        self.buildings = buildings
        self.bounds = area_bounds
        self.terrain = terrain

        # Road network storage
        self.roads = {
            RoadType.PRIMARY: [],
            RoadType.SECONDARY: [],
            RoadType.PEDESTRIAN: [],
            RoadType.BICYCLE: []
        }

        # Parameters for RK4 integration
        self.rk4_params = {
            'step_size': 5.0,  # meters
            'max_steps': 1000,
            'min_length': 20.0,  # minimum road length
            'angle_threshold': np.pi / 4  # 45 degrees max turn
        }

        # Road classification parameters
        self.road_params = {
            RoadType.PRIMARY: {'width': 8.0, 'priority': 1},
            RoadType.SECONDARY: {'width': 6.0, 'priority': 2},
            RoadType.PEDESTRIAN: {'width': 3.0, 'priority': 3},
            RoadType.BICYCLE: {'width': 2.0, 'priority': 4}
        }

    def generate_network(self) -> nx.Graph:
        """
        Main pipeline for road network generation
        Returns NetworkX graph representation
        """
        print("🛣️ Generating road network...")

        # Step 1: Generate seed points
        seeds = self._generate_seed_points()
        print(f"  Generated {len(seeds)} seed points")

        # Step 2: Trace streamlines
        streamlines = self._trace_streamlines(seeds)
        print(f"  Traced {len(streamlines)} streamlines")

        # Step 3: Classify and filter roads
        self._classify_roads(streamlines)

        # Step 4: Create graph representation
        graph = self._create_road_graph()

        # Step 5: Optimize network (remove redundancy, ensure connectivity)
        graph = self._optimize_network(graph)

        total_roads = sum(len(roads) for roads in self.roads.values())
        print(f"✅ Generated {total_roads} road segments")

        return graph
```

... [Devam edecek - karakter limiti nedeniyle kısaltıldı]

---

# 📊 **HAFTA SONU ÖZET**

## Cumartesi: Full Integration
- Tüm modülleri birleştir
- End-to-end test
- Performance profiling

## Pazar: Demo & Documentation
- Video demo kayıt
- README.md güncelleme
- GitHub release

---

# ✅ **BAŞARI KRİTERLERİ**

1. **Performance:** 10 bina < 30 saniye
2. **Quality:** Fitness score > 0.7
3. **Coverage:** Test coverage > 85%
4. **Patent:** Semantic tensor fields documented
5. **UI:** TR/EN support working

**Kolay gelsin! Her gün commit atmayı unutmayın!** 🚀
