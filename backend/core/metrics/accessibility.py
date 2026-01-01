"""
Two-Step Floating Catchment Area (2SFCA) Analysis
==================================================

Implements 2SFCA method for measuring spatial accessibility to campus facilities.
Critical metric for evaluating campus layout quality.

2SFCA measures how accessible services (libraries, dining halls, etc.) are to
demand points (dormitories, academic buildings) considering:
1. Distance decay (closer is better)
2. Service capacity (larger facilities serve more people)
3. Competition for services (demand from other buildings)

References:
    - Luo & Wang (2003): Measures of spatial accessibility to health care
    - Wan et al. (2012): A three-step floating catchment area method
    - Research: "Campus Planning Standards" document

Algorithm:
    Step 1: For each service location, compute service-to-population ratio
            within catchment area
    Step 2: For each demand point, sum accessibility ratios from all reachable
            services

Created: 2026-01-01
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


@dataclass
class ServicePoint:
    """
    Service facility (library, dining hall, etc.).

    Attributes:
        id: Unique identifier
        position: (x, y) coordinates in meters
        capacity: Service capacity (seats, beds, etc.)
        type: Service type (library, dining, health, etc.)
    """

    id: str
    position: Tuple[float, float]
    capacity: float
    type: str


@dataclass
class DemandPoint:
    """
    Demand location (dormitory, academic building, etc.).

    Attributes:
        id: Unique identifier
        position: (x, y) coordinates in meters
        population: Number of people (students, staff)
        type: Building type
    """

    id: str
    position: Tuple[float, float]
    population: float
    type: str


class TwoStepFCA:
    """
    Two-Step Floating Catchment Area calculator.

    Usage:
        >>> services = [ServicePoint('LIB1', (500, 500), capacity=200, type='library')]
        >>> demands = [DemandPoint('DORM1', (600, 600), population=400, type='dormitory')]
        >>> fca = TwoStepFCA(catchment_radius=300.0)
        >>> scores = fca.calculate(services, demands)
        >>> print(f"DORM1 accessibility: {scores['DORM1']:.2f}")
    """

    def __init__(
        self,
        catchment_radius: float = 400.0,
        distance_decay_function: str = "gaussian",
        decay_beta: float = 1.0,
    ):
        """
        Initialize 2SFCA calculator.

        Args:
            catchment_radius: Maximum distance to consider (meters, default: 400m = 5min walk)
            distance_decay_function: 'gaussian' or 'linear' or 'step'
            decay_beta: Decay rate for gaussian function (default: 1.0)
        """
        self.catchment_radius = catchment_radius
        self.distance_decay_function = distance_decay_function
        self.decay_beta = decay_beta

    def calculate(
        self,
        services: List[ServicePoint],
        demands: List[DemandPoint],
    ) -> Dict[str, float]:
        """
        Calculate 2SFCA accessibility scores for all demand points.

        Args:
            services: List of service facilities
            demands: List of demand locations

        Returns:
            Dictionary mapping demand_id -> accessibility score
            Higher score = better accessibility

        Example:
            >>> services = [ServicePoint('LIB', (0, 0), 200, 'library')]
            >>> demands = [DemandPoint('DORM', (100, 0), 400, 'dorm')]
            >>> fca = TwoStepFCA(catchment_radius=200)
            >>> scores = fca.calculate(services, demands)
            >>> scores['DORM']  # ~0.5 (capacity/population ratio)
        """
        # Step 1: Calculate service-to-population ratios (R_j)
        service_ratios = self._step1_service_ratios(services, demands)

        # Step 2: Calculate accessibility for each demand point (A_i)
        accessibility_scores = self._step2_accessibility(services, demands, service_ratios)

        return accessibility_scores

    def _step1_service_ratios(
        self,
        services: List[ServicePoint],
        demands: List[DemandPoint],
    ) -> Dict[str, float]:
        """
        Step 1: For each service j, compute R_j = S_j / sum(P_k * W_kj)

        Where:
            S_j = service capacity
            P_k = population at demand point k
            W_kj = distance weight from k to j

        Returns:
            Dictionary mapping service_id -> ratio
        """
        ratios = {}

        for service in services:
            sx, sy = service.position

            # Sum demand within catchment
            weighted_demand = 0.0

            for demand in demands:
                dx, dy = demand.position

                # Calculate distance
                distance = np.sqrt((dx - sx) ** 2 + (dy - sy) ** 2)

                # Check if within catchment
                if distance <= self.catchment_radius:
                    # Apply distance decay weight
                    weight = self._distance_weight(distance)

                    # Add weighted demand
                    weighted_demand += demand.population * weight

            # Calculate ratio (avoid division by zero)
            if weighted_demand > 0:
                ratios[service.id] = service.capacity / weighted_demand
            else:
                ratios[service.id] = 0.0

        return ratios

    def _step2_accessibility(
        self,
        services: List[ServicePoint],
        demands: List[DemandPoint],
        service_ratios: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Step 2: For each demand point i, compute A_i = sum(R_j * W_ij)

        Where:
            R_j = service-to-population ratio from Step 1
            W_ij = distance weight from i to j

        Returns:
            Dictionary mapping demand_id -> accessibility score
        """
        scores = {}

        for demand in demands:
            dx, dy = demand.position

            # Sum accessibility from all reachable services
            accessibility = 0.0

            for service in services:
                sx, sy = service.position

                # Calculate distance
                distance = np.sqrt((dx - sx) ** 2 + (dy - sy) ** 2)

                # Check if within catchment
                if distance <= self.catchment_radius:
                    # Apply distance decay weight
                    weight = self._distance_weight(distance)

                    # Add weighted service ratio
                    accessibility += service_ratios[service.id] * weight

            scores[demand.id] = accessibility

        return scores

    def _distance_weight(self, distance: float) -> float:
        """
        Compute distance decay weight.

        Args:
            distance: Distance in meters

        Returns:
            Weight in [0, 1] where 1 = closest, 0 = at catchment boundary
        """
        if distance > self.catchment_radius:
            return 0.0

        if self.distance_decay_function == "gaussian":
            # Gaussian decay: W = exp(-beta * (d/d0)^2)
            normalized_distance = distance / self.catchment_radius
            weight = np.exp(-self.decay_beta * normalized_distance**2)
            return float(weight)

        elif self.distance_decay_function == "linear":
            # Linear decay: W = 1 - (d/d0)
            weight = 1.0 - (distance / self.catchment_radius)
            return max(0.0, weight)

        elif self.distance_decay_function == "step":
            # Step function: W = 1 if d <= d0, else 0
            return 1.0

        else:
            raise ValueError(f"Unknown decay function: {self.distance_decay_function}")


def calculate_accessibility_scores(
    buildings: List,
    service_types: List[str] = None,
    demand_types: List[str] = None,
    catchment_radius: float = 400.0,
) -> Dict[str, float]:
    """
    High-level function to calculate 2SFCA accessibility for campus buildings.

    Automatically classifies buildings into service/demand based on type.

    Args:
        buildings: List of Building objects from optimizer
        service_types: Building types considered as services (default: library, dining, health)
        demand_types: Building types considered as demand (default: residential, academic)
        catchment_radius: Maximum walkable distance (default: 400m)

    Returns:
        Dictionary mapping building_id -> accessibility score

    Example:
        >>> from backend.core.optimization.building import Building
        >>> buildings = [
        ...     Building('LIB', 'library', 1000, 2),
        ...     Building('DORM', 'residential', 2000, 5)
        ... ]
        >>> buildings[0].position = (0, 0)
        >>> buildings[1].position = (200, 0)
        >>> scores = calculate_accessibility_scores(buildings)
    """
    # Default classification
    if service_types is None:
        service_types = ["library", "dining", "health", "social", "sports"]

    if demand_types is None:
        demand_types = ["residential", "academic", "research"]

    # Build service and demand lists
    services = []
    demands = []

    for building in buildings:
        if not hasattr(building, "position") or building.position is None:
            continue

        if building.type.value in service_types:
            # Service facility
            services.append(
                ServicePoint(
                    id=building.id,
                    position=building.position,
                    capacity=building.area,  # Use area as proxy for capacity
                    type=building.type.value,
                )
            )

        if building.type.value in demand_types:
            # Demand point
            # Estimate population based on area and building type
            if building.type.value == "residential":
                # ~20 m² per student
                population = building.area / 20.0
            elif building.type.value == "academic":
                # ~10 m² per student (higher density)
                population = building.area / 10.0
            else:
                population = building.area / 15.0

            demands.append(
                DemandPoint(
                    id=building.id,
                    position=building.position,
                    population=population,
                    type=building.type.value,
                )
            )

    # Calculate 2SFCA
    if not services or not demands:
        # No services or no demand - return zero scores
        return {b.id: 0.0 for b in buildings}

    fca = TwoStepFCA(catchment_radius=catchment_radius)
    scores = fca.calculate(services, demands)

    # Fill in scores for all buildings (services get 0)
    all_scores = {}
    for building in buildings:
        if building.id in scores:
            all_scores[building.id] = scores[building.id]
        else:
            all_scores[building.id] = 0.0

    return all_scores


def aggregate_accessibility_metric(accessibility_scores: Dict[str, float]) -> float:
    """
    Aggregate individual accessibility scores into single campus-wide metric.

    Uses mean accessibility as the campus-level metric.

    Args:
        accessibility_scores: Dictionary from calculate_accessibility_scores()

    Returns:
        Mean accessibility score (higher is better)
    """
    if not accessibility_scores:
        return 0.0

    scores_list = list(accessibility_scores.values())
    return float(np.mean(scores_list))
