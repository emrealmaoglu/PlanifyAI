"""
Gateway Connectivity Objective

Binaların gateway'lere erişimini optimize eder.
"""

from typing import List
import numpy as np
from shapely.geometry import Point, Polygon

from backend.core.domain.models.campus import Gateway


class GatewayConnectivityObjective:
    """
    Optimize edilmiş binaların gateway'lere erişimini maksimize eder.

    Formula:
        score = 1 / (1 + average_gateway_distance / max_campus_dimension)

    Score range: [0, 1]
    - 1.0 = Tüm binalar gateway'lerin hemen yanında
    - 0.0 = Tüm binalar gateway'lerden çok uzak

    Improvements (from SPRINT_3_IMPROVEMENTS.md):
    - Boundary-based normalization (not building-based)
    - Pre-calculated max_dimension for performance
    - Consistent scoring across all generations
    """

    def __init__(self, gateways: List[Gateway], boundary: Polygon, weight: float = 1.0):
        """
        Initialize gateway connectivity objective.

        Args:
            gateways: Kampüsteki gateway listesi
            boundary: Kampüs sınırı (normalize için gerekli)
            weight: Objective weight (default: 1.0)

        Note:
            Boundary is required for consistent normalization across
            optimization generations. Using building bounds would cause
            early generation bias.
        """
        self.gateways = gateways
        self.boundary = boundary
        self.weight = weight

        # Pre-calculate campus dimension (immutable across generations)
        minx, miny, maxx, maxy = boundary.bounds
        self.max_dimension = max(maxx - minx, maxy - miny)

        if self.max_dimension == 0:
            raise ValueError("Campus boundary has zero dimension")

    def calculate(self, buildings: List[Polygon]) -> float:
        """
        Her binanın en yakın gateway'e olan mesafesini hesapla.

        Args:
            buildings: Optimize edilmiş binalar

        Returns:
            Normalized score (0-1)

        Algorithm:
            1. For each building, find minimum distance to any gateway
            2. Calculate average of all minimum distances
            3. Normalize using campus max_dimension
            4. Return inverse score (closer = better)

        Example:
            >>> gateways = [Gateway(...), Gateway(...)]
            >>> boundary = Polygon([...])
            >>> objective = GatewayConnectivityObjective(gateways, boundary)
            >>> buildings = [Polygon(...), Polygon(...)]
            >>> score = objective.calculate(buildings)
            >>> print(score)  # 0.75 (closer to gateways)
        """
        if not buildings or not self.gateways:
            return 0.0

        total_min_distance = 0.0

        for building in buildings:
            building_centroid = building.centroid

            # En yakın gateway'i bul
            min_distance = min(
                building_centroid.distance(gw.location)
                for gw in self.gateways
            )

            total_min_distance += min_distance

        # Ortalama mesafe
        avg_distance = total_min_distance / len(buildings)

        # Normalize using campus boundary dimension (✓ consistent across generations)
        normalized_distance = avg_distance / self.max_dimension

        # Score: Mesafe azaldıkça score artar
        # Formula: 1 / (1 + x)
        # x=0 → score=1.0 (perfect)
        # x=1 → score=0.5 (average)
        # x=∞ → score=0.0 (worst)
        score = 1.0 / (1.0 + normalized_distance)

        return score * self.weight

    def get_closest_gateway_for_building(self, building: Polygon) -> Gateway:
        """
        Bir bina için en yakın gateway'i döndür.

        Args:
            building: Bina polygonu

        Returns:
            En yakın gateway

        Note:
            Bu fonksiyon road network generation için kullanışlı olabilir.
        """
        if not self.gateways:
            return None

        building_centroid = building.centroid

        closest_gateway = min(
            self.gateways,
            key=lambda gw: building_centroid.distance(gw.location)
        )

        return closest_gateway

    def get_gateway_distribution(self, buildings: List[Polygon]) -> dict:
        """
        Her gateway'e kaç binanın en yakın olduğunu hesapla.

        Args:
            buildings: Optimize edilmiş binalar

        Returns:
            Dictionary: {gateway_id: building_count}

        Example:
            >>> distribution = objective.get_gateway_distribution(buildings)
            >>> print(distribution)
            {'gateway_1': 5, 'gateway_2': 3, 'gateway_3': 7}
        """
        distribution = {gw.id: 0 for gw in self.gateways}

        for building in buildings:
            closest = self.get_closest_gateway_for_building(building)
            if closest:
                distribution[closest.id] += 1

        return distribution

    def __repr__(self):
        return (f"GatewayConnectivityObjective("
                f"gateways={len(self.gateways)}, "
                f"max_dimension={self.max_dimension:.1f}, "
                f"weight={self.weight})")
