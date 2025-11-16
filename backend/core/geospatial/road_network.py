"""
Main road network generator combining tensor fields and agents.

Orchestrates the complete road generation pipeline:

1. Create semantic tensor field from building layout
2. Generate major roads via RK45 streamline tracing
3. Generate minor roads via turtle agents
4. Post-process and export

This is the HIGH-LEVEL API that H-SAGA optimizer will call.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.spatial.road_agents import AgentConfig, RoadAgentSystem, create_agents_from_buildings
from src.spatial.streamline_tracer import (
    StreamlineConfig,
    trace_bidirectional_streamline,
    trace_streamline_rk45,
)
from src.spatial.tensor_field import TensorField, create_campus_tensor_field


@dataclass
class RoadNetworkConfig:
    """Configuration for road network generation."""

    # Tensor field
    tensor_resolution: int = 50

    # Major roads (streamlines)
    n_major_roads: int = 4
    major_road_max_length: float = 500.0
    use_bidirectional: bool = True

    # Minor roads (agents)
    n_agents_per_building: int = 2
    agent_max_steps: int = 30
    agent_step_size: float = 10.0

    # Post-processing
    resample_spacing: float = 5.0  # Resample roads to uniform spacing


class RoadNetworkGenerator:
    """
    Main generator for complete road networks.

    Usage:
        >>> generator = RoadNetworkGenerator(bounds=(0, 0, 1000, 1000))
        >>> major, minor = generator.generate(buildings)
    """

    def __init__(
        self,
        bounds: Tuple[float, float, float, float],
        config: Optional[RoadNetworkConfig] = None,
    ):
        """
        Args:
            bounds: (xmin, ymin, xmax, ymax) in meters
            config: RoadNetworkConfig with generation parameters
        """
        self.bounds = bounds
        self.config = config or RoadNetworkConfig()

        # Will be set during generation
        self.tensor_field: Optional[TensorField] = None
        self.major_roads: List[np.ndarray] = []
        self.minor_roads: List[np.ndarray] = []

    def generate(
        self,
        buildings: List,  # List[Building]
        config: Optional[RoadNetworkConfig] = None,
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Generate complete road network for building layout.

        This is the MAIN ENTRY POINT for road generation.

        Args:
            buildings: List of Building objects from H-SAGA optimizer
            config: Optional override of default config

        Returns:
            (major_roads, minor_roads) where each is list of (N, 2) paths

        Example:
            >>> from src.algorithms.building import Building, BuildingType
            >>> buildings = [Building('A', BuildingType.ADMIN, [500, 500], 1000, 3)]
            >>> gen = RoadNetworkGenerator((0, 0, 1000, 1000))
            >>> major, minor = gen.generate(buildings)
            >>> print(f"Generated {len(major)} major + {len(minor)} minor roads")
        """
        if config is not None:
            self.config = config

        # Step 1: Create semantic tensor field
        print("🏗️  Building tensor field...")
        self.tensor_field = self._build_tensor_field(buildings)

        # Step 2: Generate major roads (streamlines)
        print("🛣️  Tracing major roads...")
        self.major_roads = self._generate_major_roads()

        # Step 3: Generate minor roads (agents)
        print("🐢 Generating minor roads...")
        self.minor_roads = self._generate_minor_roads(buildings)

        # Step 4: Post-process
        print("✨ Post-processing...")
        self.major_roads = self._postprocess_roads(self.major_roads)
        self.minor_roads = self._postprocess_roads(self.minor_roads)

        print(f"✅ Generated {len(self.major_roads)} major + {len(self.minor_roads)} minor roads")

        return self.major_roads, self.minor_roads

    def _build_tensor_field(self, buildings: List) -> TensorField:
        """Create semantic tensor field from buildings."""
        field = create_campus_tensor_field(
            buildings,
            bounds=self.bounds,
            resolution=self.config.tensor_resolution,
        )

        return field

    def _generate_major_roads(self) -> List[np.ndarray]:
        """Generate major arterial roads via streamline tracing."""
        if self.tensor_field is None:
            raise ValueError("Tensor field not built yet")

        roads = []

        # Create seed points (e.g., from campus perimeter)
        seeds = self._get_major_road_seeds()

        # Streamline config
        streamline_config = StreamlineConfig(max_length=self.config.major_road_max_length)

        for seed in seeds:
            if self.config.use_bidirectional:
                result = trace_bidirectional_streamline(
                    self.tensor_field,
                    seed,
                    streamline_config,
                    field_type="major",
                )
            else:
                result = trace_streamline_rk45(
                    self.tensor_field,
                    seed,
                    streamline_config,
                    field_type="major",
                )

            if result.success and len(result.path) > 5:
                roads.append(result.path)

        return roads

    def _get_major_road_seeds(self) -> List[np.ndarray]:
        """
        Get seed points for major roads.

        Strategy: Place seeds around campus perimeter
        """
        xmin, ymin, xmax, ymax = self.bounds
        n_seeds = self.config.n_major_roads

        seeds = []

        # Distribute around perimeter
        for i in range(n_seeds):
            # Cycle through: left, top, right, bottom edges
            edge = i % 4

            if edge == 0:  # Left edge
                x = xmin + 50
                y = ymin + (ymax - ymin) * (i // 4 + 0.5) / max(1, n_seeds // 4)
            elif edge == 1:  # Top edge
                x = xmin + (xmax - xmin) * (i // 4 + 0.5) / max(1, n_seeds // 4)
                y = ymax - 50
            elif edge == 2:  # Right edge
                x = xmax - 50
                y = ymin + (ymax - ymin) * (i // 4 + 0.5) / max(1, n_seeds // 4)
            else:  # Bottom edge
                x = xmin + (xmax - xmin) * (i // 4 + 0.5) / max(1, n_seeds // 4)
                y = ymin + 50

            seeds.append(np.array([x, y]))

        return seeds

    def _generate_minor_roads(self, buildings: List) -> List[np.ndarray]:
        """Generate minor roads using agent system."""
        if self.tensor_field is None:
            raise ValueError("Tensor field not built yet")

        # Agent config
        agent_config = AgentConfig(
            step_size=self.config.agent_step_size,
            max_steps=self.config.agent_max_steps,
            tensor_weight=0.3,
            momentum_weight=0.7,
        )

        # Create agents from buildings
        # Use factory function if available, otherwise create manually
        try:
            agent_system = create_agents_from_buildings(buildings, agent_config)
        except Exception:
            # Fallback: create agents manually
            agent_system = RoadAgentSystem(agent_config)

            # Create agents at building entrances
            for building in buildings:
                if building.position is None:
                    continue

                center = np.array(building.position)
                radius = np.sqrt(building.footprint / np.pi)

                for i in range(self.config.n_agents_per_building):
                    angle = (2 * np.pi * i) / self.config.n_agents_per_building
                    offset = radius * 1.5 * np.array([np.cos(angle), np.sin(angle)])
                    position = center + offset
                    direction = offset / np.linalg.norm(offset)

                    agent_system.create_agent(position, direction)

        # Run simulation
        roads = agent_system.run_simulation(
            self.tensor_field,
            max_iterations=1000,
            field_type="minor",
        )

        return roads

    def _postprocess_roads(self, roads: List[np.ndarray]) -> List[np.ndarray]:
        """
        Post-process roads for quality.

        - Resample to uniform spacing
        - Remove very short roads
        - (Future: Intersection snapping, simplification)
        """
        from src.spatial.streamline_tracer import resample_path

        processed = []

        for road in roads:
            # Skip very short roads
            if len(road) < 3:
                continue

            # Resample
            resampled = resample_path(road, target_spacing=self.config.resample_spacing)

            processed.append(resampled)

        return processed

    def get_stats(self) -> Dict:
        """Get statistics about generated network."""
        major_total_length = sum(
            np.sum(np.linalg.norm(np.diff(road, axis=0), axis=1)) for road in self.major_roads
        )

        minor_total_length = sum(
            np.sum(np.linalg.norm(np.diff(road, axis=0), axis=1)) for road in self.minor_roads
        )

        return {
            "n_major_roads": len(self.major_roads),
            "n_minor_roads": len(self.minor_roads),
            "major_total_length_m": major_total_length,
            "minor_total_length_m": minor_total_length,
            "total_length_m": major_total_length + minor_total_length,
        }
