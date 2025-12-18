"""
Physics module for solar analysis and other physical simulations.
"""

from .solar import (
    SolarCalculator,
    SunPosition,
    ShadowCalculator,
    SolarPenaltyCalculator,
    create_solar_penalty_calculator,
    quick_shadow_check
)

from .wind import (
    WindData,
    WindDataFetcher,
    WindAlignmentCalculator,
    WindPenaltyCalculator,
    fetch_wind_data,
    quick_wind_score
)

__all__ = [
    'SolarCalculator',
    'SunPosition',
    'ShadowCalculator',
    'SolarPenaltyCalculator',
    'create_solar_penalty_calculator',
    'quick_shadow_check'
]
