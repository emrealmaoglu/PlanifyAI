"""
Objective Profile Configuration System
=======================================

Provides pre-configured objective profiles for different spatial planning scenarios.

Profiles:
    - Standard: Basic objectives (cost, walking, adjacency)
    - Research-Enhanced: All enhanced objectives with diversity
    - 15-Minute City: Accessibility-focused for urban planning
    - Campus Planning: Adjacency-focused for educational facilities

Created: 2026-01-03
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from .objectives_enhanced import WALKING_SPEED_ELDERLY, WALKING_SPEED_HEALTHY


class ProfileType(Enum):
    """Predefined objective profile types."""

    STANDARD = "standard"
    RESEARCH_ENHANCED = "research_enhanced"
    FIFTEEN_MINUTE_CITY = "15_minute_city"
    CAMPUS_PLANNING = "campus_planning"
    CUSTOM = "custom"


@dataclass
class ObjectiveProfile:
    """
    Configuration for objective evaluation.

    Attributes:
        name: Profile name
        use_enhanced: Use research-based enhanced objectives
        weights: Objective weights dict
        walking_speed_kmh: Walking speed for accessibility
        description: Profile description
    """

    name: str
    use_enhanced: bool
    weights: Dict[str, float]
    walking_speed_kmh: float = WALKING_SPEED_HEALTHY
    description: str = ""

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum:.4f}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "use_enhanced": self.use_enhanced,
            "weights": self.weights,
            "walking_speed_kmh": self.walking_speed_kmh,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ObjectiveProfile":
        """Create from dictionary."""
        return cls(**data)


# =============================================================================
# PREDEFINED PROFILES
# =============================================================================


def get_standard_profile() -> ObjectiveProfile:
    """
    Standard profile with basic objectives.

    Objectives:
        - cost (33%): Construction cost minimization
        - walking (34%): Walking distance satisfaction
        - adjacency (33%): Building adjacency satisfaction

    Use Case: General-purpose optimization with balanced objectives
    """
    return ObjectiveProfile(
        name="Standard",
        use_enhanced=False,
        weights={"cost": 0.33, "walking": 0.34, "adjacency": 0.33},
        walking_speed_kmh=WALKING_SPEED_HEALTHY,
        description="Balanced multi-objective optimization with standard metrics",
    )


def get_research_enhanced_profile() -> ObjectiveProfile:
    """
    Research-enhanced profile with all advanced objectives.

    Objectives:
        - cost (25%): Construction cost minimization
        - walking (25%): Enhanced walking accessibility (gravity model)
        - adjacency (25%): Research-based adjacency matrix
        - diversity (25%): Shannon entropy service diversity

    Features:
        - Gravity model with distance decay functions
        - Building type adjacency optimization (QAP)
        - Shannon entropy for service diversity
        - Tobler's hiking function for slope-adjusted walking

    Use Case: Research-grade optimization with all enhanced metrics
    """
    return ObjectiveProfile(
        name="Research-Enhanced",
        use_enhanced=True,
        weights={"cost": 0.25, "walking": 0.25, "adjacency": 0.25, "diversity": 0.25},
        walking_speed_kmh=WALKING_SPEED_HEALTHY,
        description="All research-based enhanced objectives with diversity",
    )


def get_fifteen_minute_city_profile() -> ObjectiveProfile:
    """
    15-Minute City profile focused on accessibility.

    Objectives:
        - cost (15%): Construction cost (lower priority)
        - walking (50%): Enhanced walking accessibility (PRIMARY)
        - adjacency (20%): Building adjacency
        - diversity (15%): Service diversity

    Features:
        - Optimized for elderly walking speed (3.0 km/h)
        - 50% weight on walking accessibility
        - Ensures all services within 15-minute walk
        - Turkish network detour index (1.324)

    Use Case: Age-friendly urban planning, accessibility optimization
    """
    return ObjectiveProfile(
        name="15-Minute City",
        use_enhanced=True,
        weights={"cost": 0.15, "walking": 0.50, "adjacency": 0.20, "diversity": 0.15},
        walking_speed_kmh=WALKING_SPEED_ELDERLY,
        description="Accessibility-focused for 15-minute city planning (elderly-optimized)",
    )


def get_campus_planning_profile() -> ObjectiveProfile:
    """
    Campus planning profile focused on building relationships.

    Objectives:
        - cost (20%): Construction cost
        - walking (20%): Walking accessibility
        - adjacency (50%): Building adjacency (PRIMARY)
        - diversity (10%): Service diversity

    Features:
        - 50% weight on building adjacency
        - Optimizes for educational facility relationships
        - Healthy walking speed (5.0 km/h) for students
        - QAP-based adjacency matrix

    Use Case: University campus planning, educational facility layout
    """
    return ObjectiveProfile(
        name="Campus Planning",
        use_enhanced=True,
        weights={"cost": 0.20, "walking": 0.20, "adjacency": 0.50, "diversity": 0.10},
        walking_speed_kmh=WALKING_SPEED_HEALTHY,
        description="Adjacency-focused for campus and educational facility planning",
    )


# =============================================================================
# PROFILE REGISTRY
# =============================================================================

PROFILE_REGISTRY: Dict[ProfileType, ObjectiveProfile] = {
    ProfileType.STANDARD: get_standard_profile(),
    ProfileType.RESEARCH_ENHANCED: get_research_enhanced_profile(),
    ProfileType.FIFTEEN_MINUTE_CITY: get_fifteen_minute_city_profile(),
    ProfileType.CAMPUS_PLANNING: get_campus_planning_profile(),
}


def get_profile(profile_type: ProfileType) -> ObjectiveProfile:
    """
    Get predefined objective profile.

    Args:
        profile_type: Profile type enum

    Returns:
        ObjectiveProfile instance

    Raises:
        ValueError: If profile type is CUSTOM (use create_custom_profile instead)

    Example:
        >>> profile = get_profile(ProfileType.FIFTEEN_MINUTE_CITY)
        >>> print(profile.weights)
        {'cost': 0.15, 'walking': 0.50, 'adjacency': 0.20, 'diversity': 0.15}
    """
    if profile_type == ProfileType.CUSTOM:
        raise ValueError("Use create_custom_profile() to create custom profiles")

    return PROFILE_REGISTRY[profile_type]


def create_custom_profile(
    name: str,
    use_enhanced: bool,
    weights: Dict[str, float],
    walking_speed_kmh: float = WALKING_SPEED_HEALTHY,
    description: str = "",
) -> ObjectiveProfile:
    """
    Create custom objective profile.

    Args:
        name: Profile name
        use_enhanced: Use research-based enhanced objectives
        weights: Objective weights (must sum to 1.0)
        walking_speed_kmh: Walking speed for accessibility
        description: Optional description

    Returns:
        Custom ObjectiveProfile instance

    Raises:
        ValueError: If weights don't sum to 1.0

    Example:
        >>> profile = create_custom_profile(
        ...     name="Custom Balanced",
        ...     use_enhanced=True,
        ...     weights={"cost": 0.25, "walking": 0.25, "adjacency": 0.25, "diversity": 0.25},
        ...     walking_speed_kmh=4.0,
        ...     description="Custom profile for specific needs"
        ... )
    """
    return ObjectiveProfile(
        name=name,
        use_enhanced=use_enhanced,
        weights=weights,
        walking_speed_kmh=walking_speed_kmh,
        description=description,
    )


def list_available_profiles() -> Dict[str, str]:
    """
    List all available predefined profiles.

    Returns:
        Dict mapping profile names to descriptions

    Example:
        >>> profiles = list_available_profiles()
        >>> for name, desc in profiles.items():
        ...     print(f"{name}: {desc}")
    """
    return {
        profile.name: profile.description
        for profile_type, profile in PROFILE_REGISTRY.items()
        if profile_type != ProfileType.CUSTOM
    }
