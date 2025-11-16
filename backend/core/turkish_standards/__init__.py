"""
Turkish Urban Planning Standards Module
========================================

This module provides Turkish-specific urban planning tools including:
- Building classification (Yapı Sınıfları)
- Construction cost calculation (2025 rates)
- Zoning law compliance (İmar Kanunu)

Usage:
------
>>> from backend.core.turkish_standards import (
...     TurkishBuildingClassifier,
...     TurkishCostCalculator,
...     TurkishComplianceChecker,
...     BuildingClass
... )

>>> # Example: Classify and cost a university building
>>> classifier = TurkishBuildingClassifier()
>>> building_class = classifier.classify("educational_university", 5000, 4)

>>> calculator = TurkishCostCalculator()
>>> cost = calculator.calculate_total_cost(
...     building_class.value,
...     5000,
...     4,
...     location="ankara"
... )
>>> print(f"Cost: {cost.total_tl:,.0f} TL")
Cost: 12,000,000 TL
"""

__version__ = "0.1.0"
__author__ = "PlanifyAI Team"

from .classification import (
    BuildingClass,
    BuildingClassInfo,
    TurkishBuildingClassifier,
)

from .costs import (
    ConstructionCost,
    TurkishCostCalculator,
)

from .compliance import (
    ComplianceViolation,
    ComplianceReport,
    TurkishComplianceChecker,
)

__all__ = [
    "BuildingClass",
    "BuildingClassInfo",
    "TurkishBuildingClassifier",
    "ConstructionCost",
    "TurkishCostCalculator",
    "ComplianceViolation",
    "ComplianceReport",
    "TurkishComplianceChecker",
]
