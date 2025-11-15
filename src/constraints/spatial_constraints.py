"""
Spatial Constraints Module
==========================

Spatial constraint system for campus planning.

Classes:
    SpatialConstraint: Base class for spatial constraints
    SetbackConstraint: Buildings must be X meters from boundary
    CoverageRatioConstraint: Building coverage ≤ max_ratio
    FloorAreaRatioConstraint: Total floor area ≤ FAR × site area
    GreenSpaceConstraint: Minimum green space ratio
    ConstraintManager: Manage and check multiple constraints

Created: 2025-11-09
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from shapely.geometry import Point

from algorithms.building import Building
from algorithms.solution import Solution
from data.campus_data import CampusData


class SpatialConstraint(ABC):
    """
    Base class for spatial constraints.

    All constraints must implement:
    - check(): Boolean check if constraint is satisfied
    - penalty(): Numeric penalty for violation (0.0 = satisfied, 1.0 = max violation)
    - description(): Human-readable description
    """

    @abstractmethod
    def check(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> bool:
        """
        Check if solution satisfies constraint.

        Args:
            solution: Solution to check
            campus: Campus data
            buildings: List of Building objects being optimized

        Returns:
            True if constraint is satisfied, False otherwise
        """
        pass

    @abstractmethod
    def penalty(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> float:
        """
        Calculate penalty for constraint violation.

        Args:
            solution: Solution to check
            campus: Campus data
            buildings: List of Building objects being optimized

        Returns:
            Penalty value: 0.0 = satisfied, 1.0 = maximum violation
        """
        pass

    @abstractmethod
    def description(self) -> str:
        """
        Get human-readable constraint description.

        Returns:
            Description string
        """
        pass


class SetbackConstraint(SpatialConstraint):
    """
    Buildings must be X meters from campus boundary.

    Checks that all buildings in solution maintain minimum distance
    from campus boundary.

    Attributes:
        setback_distance: Minimum distance from boundary in meters

    Example:
        >>> constraint = SetbackConstraint(setback_distance=10.0)
        >>> satisfied = constraint.check(solution, campus)
        >>> penalty = constraint.penalty(solution, campus)
    """

    def __init__(self, setback_distance: float = 10.0):
        """
        Initialize setback constraint.

        Args:
            setback_distance: Minimum distance from boundary in meters
        """
        if setback_distance < 0:
            raise ValueError("setback_distance must be >= 0")
        self.setback_distance = setback_distance

    def check(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> bool:
        """Check if all buildings respect setback distance."""
        # Create buffer polygon (interior of boundary with setback)
        if self.setback_distance == 0:
            # No setback, just check if within boundary
            buffer_polygon = campus.boundary
        else:
            buffer_polygon = campus.boundary.buffer(-self.setback_distance)

        # Create building dict for quick lookup
        building_dict = {b.id: b for b in buildings}

        # Check all buildings are within buffer
        for building_id, position in solution.positions.items():
            point = Point(position[0], position[1])
            # Get building from buildings list (new buildings being optimized)
            building = building_dict.get(building_id)
            if building is None:
                continue

            # Check if building (with radius) is within buffer
            building_buffer = point.buffer(building.radius)
            if not buffer_polygon.contains(building_buffer):
                return False

        return True

    def penalty(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> float:
        """Calculate setback violation penalty."""
        if self.setback_distance == 0:
            return 0.0

        # Create buffer polygon
        buffer_polygon = campus.boundary.buffer(-self.setback_distance)

        # Create building dict for quick lookup
        building_dict = {b.id: b for b in buildings}

        max_violation = 0.0
        total_violations = 0

        # Check each building
        for building_id, position in solution.positions.items():
            point = Point(position[0], position[1])
            building = building_dict.get(building_id)
            if building is None:
                continue

            building_buffer = point.buffer(building.radius)
            if not buffer_polygon.contains(building_buffer):
                total_violations += 1
                # Calculate violation distance
                distance_to_boundary = campus.boundary.exterior.distance(point)
                violation = max(0, self.setback_distance - distance_to_boundary + building.radius)
                # Normalize: max penalty if violation = setback_distance
                normalized_violation = min(1.0, violation / self.setback_distance)
                max_violation = max(max_violation, normalized_violation)

        # Penalty is average violation severity
        if total_violations == 0:
            return 0.0
        return max_violation

    def description(self) -> str:
        """Get constraint description."""
        return f"Setback from boundary: {self.setback_distance}m"


class CoverageRatioConstraint(SpatialConstraint):
    """
    Building coverage must be ≤ max_ratio of total area.

    Coverage ratio = total building footprint area / site area

    Attributes:
        max_coverage_ratio: Maximum allowed coverage ratio (0.0-1.0)

    Example:
        >>> constraint = CoverageRatioConstraint(max_coverage_ratio=0.3)
        >>> satisfied = constraint.check(solution, campus)
    """

    def __init__(self, max_coverage_ratio: float = 0.3):
        """
        Initialize coverage ratio constraint.

        Args:
            max_coverage_ratio: Maximum allowed coverage ratio (0.0-1.0)
        """
        if not 0 < max_coverage_ratio <= 1.0:
            raise ValueError("max_coverage_ratio must be between 0 and 1")
        self.max_coverage_ratio = max_coverage_ratio

    def check(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> bool:
        """Check if coverage ratio is within limit."""
        coverage = self._calculate_coverage(solution, campus, buildings)
        return coverage <= self.max_coverage_ratio

    def penalty(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> float:
        """Calculate coverage violation penalty."""
        coverage = self._calculate_coverage(solution, campus, buildings)
        if coverage <= self.max_coverage_ratio:
            return 0.0

        # Calculate excess coverage
        excess = coverage - self.max_coverage_ratio
        # Normalize: penalty proportional to excess
        # Max penalty (1.0) if coverage is 2x the limit
        max_penalty_coverage = self.max_coverage_ratio * 2.0
        if coverage >= max_penalty_coverage:
            return 1.0

        penalty = excess / self.max_coverage_ratio
        return min(1.0, penalty)

    def _calculate_coverage(
        self, solution: Solution, campus: CampusData, buildings: List[Building]
    ) -> float:
        """Calculate current coverage ratio."""
        site_area = campus.get_total_area()

        # Create building dict for quick lookup
        building_dict = {b.id: b for b in buildings}

        # Calculate total building footprint area
        total_footprint = 0.0
        for building_id in solution.positions.keys():
            building = building_dict.get(building_id)
            if building:
                total_footprint += building.footprint

        return total_footprint / site_area if site_area > 0 else 0.0

    def description(self) -> str:
        """Get constraint description."""
        return f"Coverage ratio ≤ {self.max_coverage_ratio:.0%}"


class FloorAreaRatioConstraint(SpatialConstraint):
    """
    Total floor area ≤ FAR × site area.

    Floor Area Ratio (FAR) = total building area / site area

    Attributes:
        max_far: Maximum allowed Floor Area Ratio

    Example:
        >>> constraint = FloorAreaRatioConstraint(max_far=2.0)
        >>> satisfied = constraint.check(solution, campus)
    """

    def __init__(self, max_far: float = 2.0):
        """
        Initialize FAR constraint.

        Args:
            max_far: Maximum allowed Floor Area Ratio
        """
        if max_far <= 0:
            raise ValueError("max_far must be > 0")
        self.max_far = max_far

    def check(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> bool:
        """Check if FAR is within limit."""
        far = self._calculate_far(solution, campus, buildings)
        return far <= self.max_far

    def penalty(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> float:
        """Calculate FAR violation penalty."""
        far = self._calculate_far(solution, campus, buildings)
        if far <= self.max_far:
            return 0.0

        # Calculate excess FAR
        excess = far - self.max_far
        # Normalize: penalty proportional to excess
        # Max penalty (1.0) if FAR is 2x the limit
        max_penalty_far = self.max_far * 2.0
        if far >= max_penalty_far:
            return 1.0

        penalty = excess / self.max_far
        return min(1.0, penalty)

    def _calculate_far(
        self, solution: Solution, campus: CampusData, buildings: List[Building]
    ) -> float:
        """Calculate current Floor Area Ratio."""
        site_area = campus.get_total_area()

        # Create building dict for quick lookup
        building_dict = {b.id: b for b in buildings}

        # Calculate total building area
        total_area = 0.0
        for building_id in solution.positions.keys():
            building = building_dict.get(building_id)
            if building:
                total_area += building.area

        return total_area / site_area if site_area > 0 else 0.0

    def description(self) -> str:
        """Get constraint description."""
        return f"Floor Area Ratio ≤ {self.max_far}"


class GreenSpaceConstraint(SpatialConstraint):
    """
    Minimum green space ratio.

    Green space ratio = 1 - coverage_ratio

    Attributes:
        min_green_ratio: Minimum required green space ratio (0.0-1.0)

    Example:
        >>> constraint = GreenSpaceConstraint(min_green_ratio=0.4)
        >>> satisfied = constraint.check(solution, campus)
    """

    def __init__(self, min_green_ratio: float = 0.4):
        """
        Initialize green space constraint.

        Args:
            min_green_ratio: Minimum required green space ratio (0.0-1.0)
        """
        if not 0 <= min_green_ratio <= 1.0:
            raise ValueError("min_green_ratio must be between 0 and 1")
        self.min_green_ratio = min_green_ratio

    def check(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> bool:
        """Check if green space ratio meets minimum."""
        # Calculate coverage ratio
        coverage_constraint = CoverageRatioConstraint(max_coverage_ratio=1.0)
        coverage = coverage_constraint._calculate_coverage(solution, campus, buildings)
        green_ratio = 1.0 - coverage
        return green_ratio >= self.min_green_ratio

    def penalty(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> float:
        """Calculate green space violation penalty."""
        # Calculate coverage ratio
        coverage_constraint = CoverageRatioConstraint(max_coverage_ratio=1.0)
        coverage = coverage_constraint._calculate_coverage(solution, campus, buildings)
        green_ratio = 1.0 - coverage

        if green_ratio >= self.min_green_ratio:
            return 0.0

        # Calculate deficiency
        deficiency = self.min_green_ratio - green_ratio
        # Normalize: penalty proportional to deficiency
        # Max penalty if green_ratio = 0
        if green_ratio <= 0:
            return 1.0

        penalty = deficiency / self.min_green_ratio
        return min(1.0, penalty)

    def description(self) -> str:
        """Get constraint description."""
        return f"Green space ratio ≥ {self.min_green_ratio:.0%}"


class ConstraintManager:
    """
    Manage and check multiple constraints.

    Provides methods to add constraints, check all constraints,
    and calculate total penalties.

    Example:
        >>> manager = ConstraintManager()
        >>> manager.add_constraint(SetbackConstraint(10.0))
        >>> manager.add_constraint(CoverageRatioConstraint(0.3))
        >>> satisfied = manager.check_all(solution, campus)
        >>> penalty = manager.total_penalty(solution, campus)
    """

    def __init__(self):
        """Initialize constraint manager."""
        self.constraints: List[SpatialConstraint] = []

    def add_constraint(self, constraint: SpatialConstraint):
        """
        Add a constraint to the manager.

        Args:
            constraint: Constraint to add
        """
        if not isinstance(constraint, SpatialConstraint):
            raise TypeError(f"constraint must be SpatialConstraint, got {type(constraint)}")
        self.constraints.append(constraint)

    def check_all(self, solution: Solution, campus: CampusData, buildings: List[Building]) -> bool:
        """
        Check if solution satisfies all constraints.

        Args:
            solution: Solution to check
            campus: Campus data
            buildings: List of Building objects being optimized

        Returns:
            True if all constraints are satisfied, False otherwise
        """
        return all(c.check(solution, campus, buildings) for c in self.constraints)

    def total_penalty(
        self, solution: Solution, campus: CampusData, buildings: List[Building]
    ) -> float:
        """
        Calculate total penalty for all constraint violations.

        Args:
            solution: Solution to check
            campus: Campus data
            buildings: List of Building objects being optimized

        Returns:
            Total penalty value (sum of all constraint penalties)
        """
        return sum(c.penalty(solution, campus, buildings) for c in self.constraints)

    def violations(
        self, solution: Solution, campus: CampusData, buildings: List[Building]
    ) -> Dict[str, float]:
        """
        Get dictionary of violated constraints with penalties.

        Args:
            solution: Solution to check
            campus: Campus data
            buildings: List of Building objects being optimized

        Returns:
            Dictionary mapping constraint descriptions to penalty values
        """
        violations = {}
        for constraint in self.constraints:
            penalty = constraint.penalty(solution, campus, buildings)
            if penalty > 0.0:
                violations[constraint.description()] = penalty
        return violations

    def __len__(self) -> int:
        """Get number of constraints."""
        return len(self.constraints)

    def __repr__(self) -> str:
        """String representation."""
        return f"ConstraintManager({len(self.constraints)} constraints)"
