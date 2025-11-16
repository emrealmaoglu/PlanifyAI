"""
Turkish Urban Planning Standards Data

Based on 2025 official regulations and Ministry data
"""

from typing import Dict, Any

# Building Classifications (Yapı Sınıfları)
# Source: Turkish Ministry of Environment, Urbanization and Climate Change

BUILDING_CLASSES: Dict[str, Dict[str, Any]] = {
    "I-A": {
        "name_tr": "Basit tarımsal ve temel yapılar",
        "name_en": "Simple agricultural and basic structures",
        "description": "Single story basic structures",
        "examples": ["Muhtarlık", "Güvenlik kulübesi", "Küçük büfeler"],
        "cost_per_sqm_tl": 800,
        "max_floors": 1,
        "max_height_m": 4.5,
    },
    "II-B": {
        "name_tr": "Tek katlı ofisler, dükkan ve basit atölyeler",
        "name_en": "Single-story offices, shops, simple workshops",
        "description": "Basic commercial structures",
        "examples": ["Küçük ofisler", "Perakende dükkanlar", "Atölyeler"],
        "cost_per_sqm_tl": 1200,
        "max_floors": 1,
        "max_height_m": 5.0,
    },
    "III-A": {
        "name_tr": "Konutlar (4 kata kadar - asansörsüz, kalorifersiz)",
        "name_en": "Residences (up to 4 floors - no elevator/heating)",
        "description": "Low-rise residential buildings",
        "examples": ["Apartmanlar", "Konut blokları"],
        "cost_per_sqm_tl": 1500,
        "max_floors": 4,
        "max_height_m": 12.5,
    },
    "III-B": {
        "name_tr": "Kreş, gündüz bakımevleri, sağlık ocakları",
        "name_en": "Daycare, health centers",
        "description": "Public service buildings",
        "examples": ["Kreşler", "Sağlık ocakları", "Aile sağlığı merkezleri"],
        "cost_per_sqm_tl": 1800,
        "max_floors": 3,
        "max_height_m": 12.0,
    },
    "IV-A": {
        "name_tr": "Ticari bürolar (3 kata kadar)",
        "name_en": "Commercial offices (up to 3 floors)",
        "description": "Mid-rise commercial buildings",
        "examples": ["Ofis binaları", "Alışveriş merkezleri"],
        "cost_per_sqm_tl": 2000,
        "max_floors": 3,
        "max_height_m": 12.5,
    },
    "IV-B": {
        "name_tr": "Asansörlü ve kaloriferli konutlar",
        "name_en": "Residential with elevator and heating",
        "description": "Mid-rise residential with services",
        "examples": ["Modern apartmanlar", "Rezidanslar"],
        "cost_per_sqm_tl": 1800,
        "max_floors": 8,
        "max_height_m": 25.0,
    },
    "V-A": {
        "name_tr": "Eğitim yapıları (okul, fakülte)",
        "name_en": "Educational facilities (schools, universities)",
        "description": "Educational buildings",
        "examples": ["Okullar", "Fakülteler", "Kütüphaneler"],
        "cost_per_sqm_tl": 2000,
        "max_floors": 5,
        "max_height_m": 20.0,
    },
    "V-B": {
        "name_tr": "Hastaneler ve sağlık tesisleri",
        "name_en": "Hospitals and healthcare facilities",
        "description": "Complex healthcare buildings",
        "examples": ["Hastaneler", "Poliklinikler"],
        "cost_per_sqm_tl": 2500,
        "max_floors": 6,
        "max_height_m": 25.0,
    },
    "V-C": {
        "name_tr": "Özel yapılar (müze, tiyatro)",
        "name_en": "Special structures (museums, theaters)",
        "description": "Special purpose buildings",
        "examples": ["Müzeler", "Tiyatrolar", "Spor salonları"],
        "cost_per_sqm_tl": 2200,
        "max_floors": 4,
        "max_height_m": 18.0,
    },
}

# Building Type to Class Mapping
BUILDING_TYPE_TO_CLASS: Dict[str, str] = {
    # Residential
    "residential_low": "III-A",
    "residential_mid": "IV-B",
    "residential_high": "IV-B",
    # Commercial
    "commercial_retail": "II-B",
    "commercial_mall": "IV-A",
    "commercial_office": "IV-A",
    # Educational
    "educational_school": "V-A",
    "educational_university": "V-A",
    "educational_library": "V-A",
    # Healthcare
    "health_clinic": "III-B",
    "health_hospital": "V-B",
    # Social/Cultural
    "social_sports": "V-C",
    "social_cultural": "V-C",
    "social_recreation": "V-C",
    # Administrative
    "administrative_office": "IV-A",
    "administrative_municipal": "II-B",
}

# İmar Kanunu (Zoning Law) Rules
ZONING_RULES: Dict[str, Any] = {
    "far_limits": {  # Emsal (Floor Area Ratio)
        "residential": 1.5,
        "commercial": 2.0,
        "educational": 1.2,
        "mixed_use": 1.8,
        "industrial": 1.0,
    },
    "setbacks_m": {  # İnşaat yaklaşma mesafeleri (meters)
        "front": 5.0,  # Önden (from road)
        "side": 3.0,  # Yandan (from neighbor)
        "rear": 5.0,  # Arkadan (from back boundary)
    },
    "parking_ratio": {  # Otopark ihtiyacı (per 100 m² building area)
        "residential": 1.0,  # 1 space per 100m²
        "commercial": 2.0,  # 2 spaces per 100m²
        "educational": 0.5,  # 0.5 spaces per 100m²
        "office": 1.5,  # 1.5 spaces per 100m²
        "health": 1.2,  # 1.2 spaces per 100m²
    },
    "green_space": {  # Yeşil alan standartları
        "min_per_person_sqm": 15.0,  # m² per person (aspirational)
        "min_percentage": 0.30,  # 30% of total area
    },
    "building_height_limits_floors": {
        "low_density": 4,
        "medium_density": 8,
        "high_density": 15,
    },
}

# 2025 Cost Adjustment Factors
COST_FACTORS: Dict[str, Dict[str, float]] = {
    "location": {
        "istanbul": 1.3,
        "ankara": 1.2,
        "izmir": 1.15,
        "other_metropolitan": 1.1,
        "provincial": 1.0,
        "rural": 0.9,
    },
    "quality": {
        "luxury": 1.5,
        "standard": 1.0,
        "economy": 0.8,
    },
}
