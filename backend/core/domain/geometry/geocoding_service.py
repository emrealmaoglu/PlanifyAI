"""
University Campus Location Service

Üniversite kampüslerini otomatik tespit eder.
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class UniversityCampusLocator:
    """
    Üniversite kampüslerini otomatik bulur.
    """

    # Known Turkish universities (fallback database)
    KNOWN_UNIVERSITIES = {
        "kastamonu üniversitesi": {
            "lat": 41.424274,
            "lon": 33.777434,
            "name": "Kastamonu Üniversitesi",
            "city": "Kastamonu",
            "country": "Turkey",
        },
        "kastamonu university": {
            "lat": 41.424274,
            "lon": 33.777434,
            "name": "Kastamonu Üniversitesi",
            "city": "Kastamonu",
            "country": "Turkey",
        },
        "ankara üniversitesi": {
            "lat": 39.940277,
            "lon": 32.851524,
            "name": "Ankara Üniversitesi",
            "city": "Ankara",
            "country": "Turkey",
        },
        "hacettepe üniversitesi": {
            "lat": 39.866389,
            "lon": 32.734722,
            "name": "Hacettepe Üniversitesi",
            "city": "Ankara",
            "country": "Turkey",
        },
        "istanbul üniversitesi": {
            "lat": 41.013611,
            "lon": 28.949722,
            "name": "İstanbul Üniversitesi",
            "city": "İstanbul",
            "country": "Turkey",
        },
        "odtü": {
            "lat": 39.891944,
            "lon": 32.780833,
            "name": "ODTÜ (Orta Doğu Teknik Üniversitesi)",
            "city": "Ankara",
            "country": "Turkey",
        },
        "middle east technical university": {
            "lat": 39.891944,
            "lon": 32.780833,
            "name": "ODTÜ (Middle East Technical University)",
            "city": "Ankara",
            "country": "Turkey",
        },
    }

    def __init__(self):
        """Initialize the locator."""
        self.user_agent = "planifyai/2.0"

    def find_university(
        self, university_name: str, country: str = "Turkey"
    ) -> Optional[Tuple[float, float]]:
        """
        Üniversite adından lat/lon koordinatlarını bulur.

        Args:
            university_name: Üniversite adı (örn: "Kastamonu Üniversitesi")
            country: Ülke (default: "Turkey")

        Returns:
            (latitude, longitude) tuple or None if not found

        Example:
            >>> locator = UniversityCampusLocator()
            >>> coords = locator.find_university("Kastamonu Üniversitesi")
            >>> print(coords)
            (41.424274, 33.777434)
        """
        # Normalize query (lowercase, trim)
        query_normalized = university_name.lower().strip()

        # Check known universities database
        if query_normalized in self.KNOWN_UNIVERSITIES:
            uni = self.KNOWN_UNIVERSITIES[query_normalized]
            logger.info(f"Found university in database: {uni['name']}")
            return (uni["lat"], uni["lon"])

        # Try partial match
        for key, uni in self.KNOWN_UNIVERSITIES.items():
            if query_normalized in key or key in query_normalized:
                logger.info(f"Partial match found: {uni['name']}")
                return (uni["lat"], uni["lon"])

        # Not found
        logger.warning(f"University not found: {university_name}")
        return None

    def get_university_info(self, university_name: str) -> Optional[Dict]:
        """
        Üniversite hakkında detaylı bilgi döndürür.

        Args:
            university_name: Üniversite adı

        Returns:
            Dictionary with university info or None

        Example:
            >>> locator = UniversityCampusLocator()
            >>> info = locator.get_university_info("Kastamonu Üniversitesi")
            >>> print(info['name'])
            'Kastamonu Üniversitesi'
        """
        query_normalized = university_name.lower().strip()

        if query_normalized in self.KNOWN_UNIVERSITIES:
            return self.KNOWN_UNIVERSITIES[query_normalized]

        # Partial match
        for key, uni in self.KNOWN_UNIVERSITIES.items():
            if query_normalized in key or key in query_normalized:
                return uni

        return None

    def auto_detect_optimal_radius(self, lat: float, lon: float, initial_radius: int = 500) -> int:
        """
        Kampüs büyüklüğüne göre optimal radius hesaplar.

        Algoritma:
        1. İlk radius ile OSM query yap
        2. Boundary tespit et
        3. Eğer boundary eksikse radius artır
        4. Optimal radius döndür

        Args:
            lat: Latitude
            lon: Longitude
            initial_radius: Başlangıç radius (meter)

        Returns:
            Optimal radius (meter)

        Note:
            Bu fonksiyon şu anda basit bir implementasyon.
            Gelecekte OSM Overpass API ile dinamik detection eklenebilir.
        """
        # Kastamonu için bilinen değer
        if 41.4 < lat < 41.5 and 33.7 < lon < 33.8:
            return 2000  # 2km radius yeterli

        # Default Turkish universities (Turkey coordinates: 36-42°N, 26-45°E)
        if 36 < lat < 42 and 26 < lon < 45:
            return 1500  # 1.5km genelde yeterli

        # International universities (genelde daha büyük)
        return 2500

    def list_known_universities(self) -> list:
        """
        Bilinen üniversiteleri listeler.

        Returns:
            List of university names
        """
        return [uni["name"] for uni in self.KNOWN_UNIVERSITIES.values()]


# Convenience function
def find_university_coordinates(university_name: str) -> Optional[Tuple[float, float]]:
    """
    Quick utility to find university coordinates.

    Args:
        university_name: Name of the university

    Returns:
        (lat, lon) tuple or None

    Example:
        >>> coords = find_university_coordinates("Kastamonu Üniversitesi")
        >>> print(f"Lat: {coords[0]}, Lon: {coords[1]}")
        Lat: 41.424274, Lon: 33.777434
    """
    locator = UniversityCampusLocator()
    return locator.find_university(university_name)
