"""
Spatial tensor field module for semantic road network generation.

This module provides:
- Basis fields (GridField, RadialField)
- TensorField class for combining fields
- Factory functions for campus-specific fields
- Road network generation (streamlines + agents)
"""

from .basis_fields import GridField, RadialField
from .road_agents import (
    AgentConfig,
    AgentState,
    RoadAgent,
    RoadAgentSystem,
    create_agents_from_buildings,
)
from .road_network import RoadNetworkConfig, RoadNetworkGenerator
from .streamline_tracer import (
    StopReason,
    StreamlineConfig,
    StreamlineResult,
    resample_path,
    smooth_path,
    trace_bidirectional_streamline,
    trace_streamline_rk45,
)
from .tensor_field import TensorField, create_campus_tensor_field

__all__ = [
    # Tensor fields
    "GridField",
    "RadialField",
    "TensorField",
    "create_campus_tensor_field",
    # Road generation
    "trace_streamline_rk45",
    "trace_bidirectional_streamline",
    "resample_path",
    "smooth_path",
    "StreamlineConfig",
    "StreamlineResult",
    "StopReason",
    "RoadAgent",
    "RoadAgentSystem",
    "AgentConfig",
    "AgentState",
    "create_agents_from_buildings",
    "RoadNetworkGenerator",
    "RoadNetworkConfig",
]
