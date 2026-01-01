"""
Campus Planning Objective Functions
====================================

Multi-objective optimization objectives for campus spatial planning.

Modules:
    - accessibility: 2SFCA spatial accessibility
    - adjacency_qap: QAP-based building adjacency with explainability
    - connectivity: Kansky network connectivity
    - gateway_connectivity: Gateway access optimization
"""

from .accessibility import maximize_accessibility
from .adjacency_qap import (
    calculate_qap_cost,
    get_adjacency_report,
    get_adjacency_weight,
    maximize_adjacency_satisfaction,
)
from .connectivity import maximize_connectivity

__all__ = [
    # Accessibility
    "maximize_accessibility",
    # Adjacency (QAP-based)
    "maximize_adjacency_satisfaction",
    "calculate_qap_cost",
    "get_adjacency_weight",
    "get_adjacency_report",
    # Connectivity
    "maximize_connectivity",
]
