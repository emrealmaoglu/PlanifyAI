"""
Campus Relocation Service

Kampüsü yeni bir alana taşır, gateway pozisyonlarını korur.
"""

from typing import Optional, Tuple
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.affinity import translate
from dataclasses import dataclass
import logging

from backend.core.domain.models.campus import CampusContext, Gateway, ExistingBuilding

logger = logging.getLogger(__name__)


@dataclass
class RelocationResult:
    """Relocation işlemi sonucu."""
    relocated_campus: CampusContext
    topology_preserved: bool
    distance_error: float  # Gateway distances error (%)
    translation_vector: Tuple[float, float]  # (dx, dy)


class CampusRelocator:
    """
    Kampüsü yeni bir alana taşır.

    Özellikler:
    - Boundary'yi yeni konuma taşır
    - Gateway relative pozisyonlarını korur
    - Mevcut binaları korur (opsiyonel)
    - Topology doğrulaması yapar
    """

    def __init__(self, preserve_topology: bool = True):
        """
        Initialize relocator.

        Args:
            preserve_topology: Gateway topology'sini doğrula
        """
        self.preserve_topology = preserve_topology

    def relocate_to_empty_space(
        self,
        campus: CampusContext,
        target_center: Point = Point(0, 0),
        clear_existing_buildings: bool = True
    ) -> RelocationResult:
        """
        Kampüsü target_center'a taşır.

        Args:
            campus: Orijinal kampüs
            target_center: Hedef merkez (default: 0,0)
            clear_existing_buildings: Mevcut binaları temizle (boş alan için)

        Returns:
            RelocationResult with relocated campus

        Example:
            >>> relocator = CampusRelocator()
            >>> campus = CampusContext(boundary=..., gateways=[...])
            >>> result = relocator.relocate_to_empty_space(campus, Point(0, 0))
            >>> print(result.relocated_campus.center)
            POINT (0 0)
        """
        logger.info(f"Relocating campus to {target_center}")

        # 1. Calculate current center
        current_center = campus.center if campus.center else campus.boundary.centroid
        logger.info(f"Current center: {current_center}")

        # 2. Calculate translation vector
        dx = target_center.x - current_center.x
        dy = target_center.y - current_center.y
        logger.info(f"Translation vector: dx={dx:.2f}, dy={dy:.2f}")

        # 3. Translate boundary
        relocated_boundary = translate(campus.boundary, xoff=dx, yoff=dy)

        # 4. Translate gateways
        relocated_gateways = [
            Gateway(
                id=gw.id,
                location=Point(gw.location.x + dx, gw.location.y + dy),
                bearing=gw.bearing,  # Bearing preserved
                type=gw.type,
                name=gw.name
            )
            for gw in campus.gateways
        ]

        # 5. Translate buildings (or clear them)
        if clear_existing_buildings:
            relocated_buildings = []
            logger.info("Cleared existing buildings (empty space mode)")
        else:
            relocated_buildings = [
                ExistingBuilding(
                    id=b.id,
                    geometry=translate(b.geometry, xoff=dx, yoff=dy),
                    building_type=b.building_type,
                    height=b.height,
                    name=b.name,
                    floors=b.floors
                )
                for b in campus.existing_buildings
            ]

        # 6. Translate roads and green areas
        relocated_roads = [translate(road, xoff=dx, yoff=dy) for road in campus.roads]
        relocated_greens = [translate(green, xoff=dx, yoff=dy) for green in campus.green_areas]

        # 7. Create new CampusContext
        relocated_campus = CampusContext(
            boundary=relocated_boundary,
            gateways=relocated_gateways,
            existing_buildings=relocated_buildings,
            roads=relocated_roads,
            green_areas=relocated_greens,
            center=target_center,
            area_m2=relocated_boundary.area,
            name=campus.name
        )

        # 8. Verify topology preservation
        topology_preserved = True
        distance_error = 0.0

        if self.preserve_topology and len(campus.gateways) > 1:
            topology_preserved, distance_error = self._verify_topology(
                campus.gateways,
                relocated_gateways
            )

        logger.info(f"Relocation complete. Topology preserved: {topology_preserved}, Error: {distance_error:.2%}")

        return RelocationResult(
            relocated_campus=relocated_campus,
            topology_preserved=topology_preserved,
            distance_error=distance_error,
            translation_vector=(dx, dy)
        )

    def _verify_topology(
        self,
        original_gateways: list,
        relocated_gateways: list
    ) -> Tuple[bool, float]:
        """
        Gateway topology'sinin korunduğunu doğrula.

        Algoritma:
        1. Her iki gateway set için distance matrix hesapla
        2. Matrix'leri karşılaştır
        3. Error < 0.01 (1%) ise topology preserved

        Args:
            original_gateways: Orijinal gateway'ler
            relocated_gateways: Taşınmış gateway'ler

        Returns:
            (topology_preserved, distance_error_percent)
        """
        if len(original_gateways) != len(relocated_gateways):
            logger.warning("Gateway count mismatch!")
            return False, 1.0

        # Calculate distance matrices
        orig_distances = self._compute_distance_matrix(original_gateways)
        reloc_distances = self._compute_distance_matrix(relocated_gateways)

        # Compare matrices
        # Use relative error: |orig - reloc| / orig
        with np.errstate(divide='ignore', invalid='ignore'):
            relative_errors = np.abs(orig_distances - reloc_distances) / orig_distances
            relative_errors = np.nan_to_num(relative_errors, nan=0.0, posinf=0.0)

        max_error = np.max(relative_errors)
        mean_error = np.mean(relative_errors[relative_errors > 0])  # Ignore diagonal

        logger.debug(f"Topology verification: max_error={max_error:.4f}, mean_error={mean_error:.4f}")

        # Threshold: 1% error is acceptable (due to floating point precision)
        topology_preserved = max_error < 0.01

        return topology_preserved, mean_error

    def _compute_distance_matrix(self, gateways: list) -> np.ndarray:
        """
        Gateway'ler arası mesafe matrix'i hesapla.

        Args:
            gateways: Gateway listesi

        Returns:
            NxN distance matrix
        """
        n = len(gateways)
        distances = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    distances[i, j] = gateways[i].location.distance(
                        gateways[j].location
                    )

        return distances

    def create_empty_boundary(
        self,
        width: float = 1000.0,
        height: float = 800.0,
        center: Point = Point(0, 0)
    ) -> Polygon:
        """
        Boş alan için rectangular boundary oluşturur.

        Args:
            width: Genişlik (metre)
            height: Yükseklik (metre)
            center: Merkez noktası

        Returns:
            Rectangular polygon

        Example:
            >>> relocator = CampusRelocator()
            >>> empty_boundary = relocator.create_empty_boundary(1000, 800)
            >>> print(empty_boundary.area)
            800000.0
        """
        half_w = width / 2
        half_h = height / 2

        coords = [
            (center.x - half_w, center.y - half_h),
            (center.x + half_w, center.y - half_h),
            (center.x + half_w, center.y + half_h),
            (center.x - half_w, center.y + half_h),
            (center.x - half_w, center.y - half_h)  # Close polygon
        ]

        return Polygon(coords)

    def relocate_with_new_boundary(
        self,
        campus: CampusContext,
        new_boundary: Polygon,
        scale_to_fit: bool = True
    ) -> RelocationResult:
        """
        Kampüsü yeni bir boundary içine taşır, gerekirse scale eder.

        Args:
            campus: Orijinal kampüs
            new_boundary: Yeni boundary
            scale_to_fit: True ise kampüsü scale et (yeni boundary'ye sığdır)

        Returns:
            RelocationResult
        """
        # 1. Center to new boundary center
        target_center = new_boundary.centroid

        # 2. Basic relocation
        result = self.relocate_to_empty_space(campus, target_center)

        # 3. Scale if needed
        if scale_to_fit:
            original_area = campus.boundary.area
            new_area = new_boundary.area

            if original_area > new_area:
                scale_factor = np.sqrt(new_area / original_area) * 0.9  # 90% to leave margin
                logger.info(f"Scaling campus by {scale_factor:.2f} to fit new boundary")

                # TODO: Implement scaling
                # This would require scaling boundary, gateways, buildings
                # For now, just log warning
                logger.warning("Scaling not yet implemented!")

        return result


def relocate_campus_to_coordinates(
    campus: CampusContext,
    target_lat: float,
    target_lon: float,
    use_local_coords: bool = True
) -> RelocationResult:
    """
    Convenience function: Kampüsü WGS84 koordinatlara taşı.

    Args:
        campus: Orijinal kampüs (WGS84 koordinatlarında)
        target_lat: Hedef latitude
        target_lon: Hedef longitude
        use_local_coords: True ise önce local metric'e çevir

    Returns:
        RelocationResult

    Example:
        >>> campus_wgs84 = fetch_campus_context(lat=41.42, lon=33.77, radius=500)
        >>> result = relocate_campus_to_coordinates(campus_wgs84, 0.0, 0.0)
        >>> print(result.relocated_campus.center)
        POINT (0 0)
    """
    relocator = CampusRelocator()

    if use_local_coords:
        # Convert to local metric coordinates first
        campus_local = campus.to_local_coordinates(target_center=Point(0, 0))
        target = Point(target_lon, target_lat)  # Already metric if (0,0)
        return relocator.relocate_to_empty_space(campus_local, target)
    else:
        # Direct WGS84 relocation (not recommended - distances will be wrong)
        target = Point(target_lon, target_lat)
        return relocator.relocate_to_empty_space(campus, target)
