"""
Building Data Structures
========================

Core data structures for representing buildings in spatial planning.

Classes:
    BuildingType: Enumeration of building types
    Building: Building entity with properties and constraints

Created: 2025-11-03
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict
from enum import Enum
import numpy as np


class BuildingType(Enum):
    """
    Building type classification
    
    Used for:
    - Tensor field generation (different patterns)
    - Adjacency scoring (compatibility matrix)
    - Constraint application
    """
    RESIDENTIAL = "residential"
    EDUCATIONAL = "educational"
    COMMERCIAL = "commercial"
    HEALTH = "health"
    SOCIAL = "social"
    ADMINISTRATIVE = "administrative"
    SPORTS = "sports"
    LIBRARY = "library"
    DINING = "dining"
    
    def __str__(self) -> str:
        return self.value


@dataclass
class Building:
    """
    Building entity with semantic properties
    
    Attributes:
        id: Unique identifier (e.g., "B001", "library_main")
        type: Building type classification
        area: Total floor area in square meters
        floors: Number of floors/stories
        position: Optional (x, y) coordinates in meters
        constraints: Building-specific constraints
        
    Properties:
        footprint: Ground floor area (computed from total area / floors)
        importance: Importance weight for tensor field (computed)
        
    Example:
        >>> building = Building(
        ...     id="library_01",
        ...     type=BuildingType.LIBRARY,
        ...     area=5000,  # 5000 m²
        ...     floors=3
        ... )
        >>> building.footprint
        1666.67
        >>> building.importance
        70.71
    """
    
    id: str
    type: BuildingType
    area: float  # m²
    floors: int
    position: Optional[Tuple[float, float]] = None
    constraints: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate building parameters"""
        if self.area <= 0:
            raise ValueError(f"Building area must be positive, got {self.area}")
        
        if self.floors <= 0:
            raise ValueError(f"Building floors must be positive, got {self.floors}")
        
        if self.position is not None:
            if len(self.position) != 2:
                raise ValueError(f"Position must be (x, y) tuple, got {self.position}")
    
    @property
    def footprint(self) -> float:
        """
        Calculate building footprint (ground floor area)
        
        Returns:
            Ground floor area in m²
        """
        return self.area / self.floors
    
    @property
    def radius(self) -> float:
        """
        Approximate building radius (for circular footprint approximation)
        
        Returns:
            Radius in meters
        """
        return np.sqrt(self.footprint / np.pi)
    
    @property
    def importance(self) -> float:
        """
        Calculate importance weight for tensor field generation
        
        Higher importance = stronger attraction field
        
        Weights:
            - Health facilities: 2.5 (highest priority)
            - Libraries: 2.2
            - Commercial: 2.0
            - Dining: 1.8
            - Educational: 1.5
            - Sports: 1.3
            - Social: 1.2
            - Administrative: 1.1
            - Residential: 1.0 (baseline)
        
        Formula: weight * sqrt(area)
        
        Returns:
            Importance score (dimensionless)
        """
        weights = {
            BuildingType.HEALTH: 2.5,
            BuildingType.LIBRARY: 2.2,
            BuildingType.COMMERCIAL: 2.0,
            BuildingType.DINING: 1.8,
            BuildingType.EDUCATIONAL: 1.5,
            BuildingType.SPORTS: 1.3,
            BuildingType.SOCIAL: 1.2,
            BuildingType.ADMINISTRATIVE: 1.1,
            BuildingType.RESIDENTIAL: 1.0
        }
        
        weight = weights.get(self.type, 1.0)
        return weight * np.sqrt(self.area)
    
    def distance_to(self, other: 'Building') -> float:
        """
        Calculate Euclidean distance to another building
        
        Args:
            other: Another Building instance
            
        Returns:
            Distance in meters
            
        Raises:
            ValueError: If either building doesn't have position set
        """
        if self.position is None:
            raise ValueError(f"Building {self.id} doesn't have position set")
        
        if other.position is None:
            raise ValueError(f"Building {other.id} doesn't have position set")
        
        return np.linalg.norm(
            np.array(self.position) - np.array(other.position)
        )
    
    def overlaps_with(self, other: 'Building', safety_margin: float = 5.0) -> bool:
        """
        Check if this building overlaps with another
        
        Args:
            other: Another Building instance
            safety_margin: Additional clearance in meters (default: 5m)
            
        Returns:
            True if buildings overlap (including safety margin)
        """
        if self.position is None or other.position is None:
            return False
        
        distance = self.distance_to(other)
        min_distance = self.radius + other.radius + safety_margin
        
        return distance < min_distance
    
    def __repr__(self) -> str:
        """String representation"""
        pos_str = f"at {self.position}" if self.position else "unplaced"
        return (
            f"Building(id='{self.id}', type={self.type.value}, "
            f"area={self.area}m², floors={self.floors}, {pos_str})"
        )
    
    def __eq__(self, other) -> bool:
        """Equality based on ID"""
        if not isinstance(other, Building):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID"""
        return hash(self.id)


# Utility functions

def create_sample_campus() -> list[Building]:
    """
    Create a sample campus for testing
    
    Returns:
        List of 10 buildings with typical campus mix
    """
    return [
        Building("lib_main", BuildingType.LIBRARY, 5000, 3),
        Building("dorm_a", BuildingType.RESIDENTIAL, 8000, 5),
        Building("dorm_b", BuildingType.RESIDENTIAL, 8000, 5),
        Building("eng_building", BuildingType.EDUCATIONAL, 6000, 4),
        Building("business_school", BuildingType.EDUCATIONAL, 5500, 3),
        Building("cafeteria", BuildingType.DINING, 2000, 2),
        Building("health_center", BuildingType.HEALTH, 3000, 2),
        Building("admin", BuildingType.ADMINISTRATIVE, 4000, 3),
        Building("gym", BuildingType.SPORTS, 3500, 2),
        Building("student_center", BuildingType.SOCIAL, 2500, 2),
    ]
