"""
Spatial Genome Encoding for H-SAGA Optimization.

Defines the genome structure, decoder (array -> polygon), and
smart initializer for generating valid building placements.

Genome Structure (7 genes per building):
    [0] x:          X position (meters, local CRS)
    [1] y:          Y position (meters, local CRS)
    [2] rotation:   Rotation angle (radians, 0 to 2π)
    [3] type_id:    Building type index (0 to N_TYPES-1)
    [4] width_factor:  Width multiplier (0.8 to 1.2)
    [5] depth_factor:  Depth multiplier (0.8 to 1.2)
    [6] floor_factor:  Floor count multiplier (0.5 to 1.5)
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from shapely.geometry import Polygon, Point, box
from shapely.affinity import rotate, translate
from shapely import prepared


# =============================================================================
# BUILDING TYPE REGISTRY
# =============================================================================

@dataclass
class BuildingTypeSpec:
    """Specification for a building type."""
    id: int
    name: str
    base_width: float   # meters
    base_depth: float   # meters
    base_floors: int
    floor_height: float = 3.5  # meters per floor
    color: str = "#666666"
    
    @property
    def base_height(self) -> float:
        return self.base_floors * self.floor_height


# Default Building Types (aligned with Turkish Campus Standards)
BUILDING_TYPES: Dict[str, BuildingTypeSpec] = {
    "Rectory": BuildingTypeSpec(0, "Rectory", 40, 30, 4, color="#9333ea"),
    "Faculty": BuildingTypeSpec(1, "Faculty", 60, 25, 5, color="#3b82f6"),
    "Dormitory": BuildingTypeSpec(2, "Dormitory", 50, 15, 6, color="#f97316"),
    "Dining": BuildingTypeSpec(3, "Dining", 35, 25, 2, color="#f59e0b"),
    "Library": BuildingTypeSpec(4, "Library", 45, 35, 3, color="#06b6d4"),
    "Sports": BuildingTypeSpec(5, "Sports", 60, 40, 1, color="#22c55e"),
    "Research": BuildingTypeSpec(6, "Research", 40, 20, 4, color="#ec4899"),
    "Social": BuildingTypeSpec(7, "Social", 30, 20, 2, color="#e11d48"),
}

TYPE_ID_TO_NAME = {spec.id: name for name, spec in BUILDING_TYPES.items()}
TYPE_NAME_TO_ID = {name: spec.id for name, spec in BUILDING_TYPES.items()}


# =============================================================================
# GENOME STRUCTURE
# =============================================================================

@dataclass
class BuildingGene:
    """Decoded representation of a single building's genome."""
    x: float
    y: float
    rotation: float
    type_id: int
    width_factor: float
    depth_factor: float
    floor_factor: float
    
    @property
    def type_name(self) -> str:
        return TYPE_ID_TO_NAME.get(self.type_id, "Unknown")
    
    @property
    def type_spec(self) -> BuildingTypeSpec:
        return BUILDING_TYPES.get(self.type_name, BUILDING_TYPES["Faculty"])
    
    @property
    def width(self) -> float:
        return self.type_spec.base_width * self.width_factor
    
    @property
    def depth(self) -> float:
        return self.type_spec.base_depth * self.depth_factor
    
    @property
    def floors(self) -> int:
        return max(1, int(self.type_spec.base_floors * self.floor_factor))
    
    @property
    def height(self) -> float:
        return self.floors * self.type_spec.floor_height
    
    @property
    def footprint_area(self) -> float:
        return self.width * self.depth
    
    @property
    def total_floor_area(self) -> float:
        return self.footprint_area * self.floors


GENES_PER_BUILDING = 7


def genome_to_array(genes: List[BuildingGene]) -> np.ndarray:
    """Convert list of BuildingGene to flat numpy array."""
    arr = np.zeros(len(genes) * GENES_PER_BUILDING)
    for i, g in enumerate(genes):
        offset = i * GENES_PER_BUILDING
        arr[offset + 0] = g.x
        arr[offset + 1] = g.y
        arr[offset + 2] = g.rotation
        arr[offset + 3] = g.type_id
        arr[offset + 4] = g.width_factor
        arr[offset + 5] = g.depth_factor
        arr[offset + 6] = g.floor_factor
    return arr


def array_to_genome(arr: np.ndarray, num_buildings: int) -> List[BuildingGene]:
    """Convert flat numpy array to list of BuildingGene."""
    genes = []
    for i in range(num_buildings):
        offset = i * GENES_PER_BUILDING
        genes.append(BuildingGene(
            x=arr[offset + 0],
            y=arr[offset + 1],
            rotation=arr[offset + 2],
            type_id=int(arr[offset + 3]),
            width_factor=arr[offset + 4],
            depth_factor=arr[offset + 5],
            floor_factor=arr[offset + 6]
        ))
    return genes


# =============================================================================
# DECODER: Genome -> Shapely Polygon
# =============================================================================

def decode_to_polygon(gene: BuildingGene) -> Polygon:
    """
    Convert a BuildingGene to a Shapely Polygon.
    
    Creates a rectangle centered at (x, y), rotated by the rotation angle.
    """
    half_w = gene.width / 2
    half_d = gene.depth / 2
    
    # Create rectangle centered at origin
    rect = box(-half_w, -half_d, half_w, half_d)
    
    # Rotate around center
    rect = rotate(rect, gene.rotation, use_radians=True, origin='center')
    
    # Translate to position
    rect = translate(rect, xoff=gene.x, yoff=gene.y)
    
    return rect


def decode_all_to_polygons(genes: List[BuildingGene]) -> List[Polygon]:
    """Decode all genes in a genome to polygons."""
    return [decode_to_polygon(g) for g in genes]


def decode_array_to_polygons(arr: np.ndarray, num_buildings: int) -> List[Polygon]:
    """Direct conversion from flat array to polygons."""
    genes = array_to_genome(arr, num_buildings)
    return decode_all_to_polygons(genes)


# =============================================================================
# SMART INITIALIZER: Generate Valid Random Individuals
# =============================================================================

class SmartInitializer:
    """
    Generates random valid building placements inside the campus boundary.
    
    Uses rejection sampling with spatial acceleration to ensure:
    1. All buildings are inside the boundary
    2. Buildings don't overlap
    3. Type requirements are satisfied
    """
    
    def __init__(
        self,
        boundary: Polygon,
        building_counts: Dict[str, int],
        min_separation: float = 5.0,
        max_attempts: int = 1000
    ):
        """
        Args:
            boundary: Campus boundary polygon (local CRS)
            building_counts: Dict mapping type name to count (e.g., {"Faculty": 2})
            min_separation: Minimum distance between buildings (meters)
            max_attempts: Max placement attempts per building
        """
        self.boundary = boundary
        self.prepared_boundary = prepared.prep(boundary)
        self.building_counts = building_counts
        self.min_separation = min_separation
        self.max_attempts = max_attempts
        
        # Precompute bounds
        self.minx, self.miny, self.maxx, self.maxy = boundary.bounds
        
        # Build type sequence
        self.type_sequence = self._build_type_sequence()
        self.num_buildings = len(self.type_sequence)
        
    def _build_type_sequence(self) -> List[int]:
        """Build ordered list of type IDs based on counts."""
        sequence = []
        for type_name, count in self.building_counts.items():
            if type_name in TYPE_NAME_TO_ID:
                type_id = TYPE_NAME_TO_ID[type_name]
                sequence.extend([type_id] * count)
        return sequence
    
    def generate_individual(self, rng: np.random.Generator = None) -> np.ndarray:
        """
        Generate a single valid individual (flat array).
        
        Uses greedy placement with rejection sampling.
        """
        if rng is None:
            rng = np.random.default_rng()
        
        genes = []
        placed_polygons = []
        
        for type_id in self.type_sequence:
            gene = self._place_building(type_id, placed_polygons, rng)
            genes.append(gene)
            placed_polygons.append(decode_to_polygon(gene))
        
        return genome_to_array(genes)
    
    def _place_building(
        self,
        type_id: int,
        existing_polygons: List[Polygon],
        rng: np.random.Generator
    ) -> BuildingGene:
        """Place a single building avoiding existing ones."""
        
        type_name = TYPE_ID_TO_NAME[type_id]
        spec = BUILDING_TYPES[type_name]
        
        for attempt in range(self.max_attempts):
            # Random position
            x = rng.uniform(self.minx + spec.base_width, self.maxx - spec.base_width)
            y = rng.uniform(self.miny + spec.base_depth, self.maxy - spec.base_depth)
            
            # Random rotation
            rotation = rng.uniform(0, 2 * np.pi)
            
            # Random size factors (slight variation)
            width_factor = rng.uniform(0.9, 1.1)
            depth_factor = rng.uniform(0.9, 1.1)
            floor_factor = rng.uniform(0.8, 1.2)
            
            gene = BuildingGene(
                x=x, y=y, rotation=rotation,
                type_id=type_id,
                width_factor=width_factor,
                depth_factor=depth_factor,
                floor_factor=floor_factor
            )
            
            polygon = decode_to_polygon(gene)
            
            # Check boundary containment
            if not self.prepared_boundary.contains(polygon):
                continue
            
            # Check separation from existing
            is_valid = True
            for existing in existing_polygons:
                if polygon.distance(existing) < self.min_separation:
                    is_valid = False
                    break
            
            if is_valid:
                return gene
        
        # Fallback: return last attempt even if invalid (constraint will penalize)
        return gene
    
    def generate_population(
        self,
        pop_size: int,
        rng: np.random.Generator = None
    ) -> np.ndarray:
        """
        Generate initial population matrix.
        
        Returns:
            2D array of shape (pop_size, num_buildings * GENES_PER_BUILDING)
        """
        if rng is None:
            rng = np.random.default_rng()
        
        population = np.zeros((pop_size, self.num_buildings * GENES_PER_BUILDING))
        
        for i in range(pop_size):
            population[i] = self.generate_individual(rng)
        
        return population


# =============================================================================
# VARIABLE BOUNDS CALCULATOR
# =============================================================================

def calculate_variable_bounds(
    boundary: Polygon,
    num_buildings: int,
    num_types: int = 8
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate lower and upper bounds for decision variables.
    
    Returns:
        Tuple of (lower_bounds, upper_bounds) arrays
    """
    minx, miny, maxx, maxy = boundary.bounds
    
    n_vars = num_buildings * GENES_PER_BUILDING
    xl = np.zeros(n_vars)
    xu = np.zeros(n_vars)
    
    for i in range(num_buildings):
        offset = i * GENES_PER_BUILDING
        
        # x position
        xl[offset + 0] = minx
        xu[offset + 0] = maxx
        
        # y position
        xl[offset + 1] = miny
        xu[offset + 1] = maxy
        
        # rotation (0 to 2π)
        xl[offset + 2] = 0.0
        xu[offset + 2] = 2 * np.pi
        
        # type_id (discrete, but we treat as continuous and round)
        xl[offset + 3] = 0
        xu[offset + 3] = num_types - 1
        
        # width_factor
        xl[offset + 4] = 0.8
        xu[offset + 4] = 1.2
        
        # depth_factor
        xl[offset + 5] = 0.8
        xu[offset + 5] = 1.2
        
        # floor_factor
        xl[offset + 6] = 0.5
        xu[offset + 6] = 1.5
    
    return xl, xu


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_building_centroids(genes: List[BuildingGene]) -> np.ndarray:
    """Get centroids as Nx2 array."""
    return np.array([[g.x, g.y] for g in genes])


def get_type_indices(genes: List[BuildingGene], type_name: str) -> List[int]:
    """Get indices of buildings with given type."""
    target_id = TYPE_NAME_TO_ID.get(type_name, -1)
    return [i for i, g in enumerate(genes) if g.type_id == target_id]


def calculate_pairwise_distances(genes: List[BuildingGene]) -> np.ndarray:
    """Calculate pairwise Euclidean distances between building centroids."""
    centroids = get_building_centroids(genes)
    n = len(centroids)
    distances = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            d = np.sqrt(
                (centroids[i, 0] - centroids[j, 0]) ** 2 +
                (centroids[i, 1] - centroids[j, 1]) ** 2
            )
            distances[i, j] = d
            distances[j, i] = d
    
    return distances
