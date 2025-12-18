"""
AI Package.

This package contains AI-powered components for the PlanifyAI system,
including the layout critique system using Ollama.
"""

from backend.core.ai.critique import (
    AICritic,
    CritiqueConfig,
    CritiqueResult,
    LayoutAnalyzer,
    LayoutMetrics,
    quick_critique,
    critique_solution
)

__all__ = [
    "AICritic",
    "CritiqueConfig",
    "CritiqueResult",
    "LayoutAnalyzer",
    "LayoutMetrics",
    "quick_critique",
    "critique_solution"
]
