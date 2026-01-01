"""
Tensor Field Road Network Generator
====================================

Complete implementation of road network generation using semantic tensor fields.
This is the HIGH-LEVEL API that H-SAGA optimizer will call.

Pipeline:
1. Create semantic tensor field from building layout
2. Generate major roads via RK45 streamline tracing
3. Generate minor roads connecting buildings
4. Post-process and validate

References:
    - Chen et al. (2008): Interactive Procedural Street Modeling
    - Parish & Müller (2001): Procedural modeling of cities
    - Research: "Tensor Field Road Network Generation"

Created: 2026-01-01
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .streamline_tracer import (
    StreamlineConfig,
    trace_bidirectional_streamline,
    trace_streamline_rk45,
)
from .tensor_field import TensorField, create_campus_tensor_field


@dataclass
class RoadNetworkConfig:
    """Configuration for road network generation."""

    # Tensor field
    tensor_resolution: int = 50  # Grid resolution

    # Major roads (streamlines)
    n_major_roads: int = 4  # Number of major arterial roads
    major_road_max_length: float = 500.0  # Maximum major road length (meters)
    use_bidirectional: bool = True  # Trace in both directions from seed

    # Minor roads (connecting roads)
    generate_minor_roads: bool = True  # Whether to generate minor roads
    minor_road_max_length: float = 200.0  # Maximum minor road length (meters)

    # Post-processing
    resample_spacing: float = 10.0  # Resample roads to uniform spacing (meters)
    min_road_length: float = 20.0  # Filter out very short roads (meters)


class RoadNetworkGenerator:
    """
    Main generator for complete road networks using tensor fields.

    Usage:
        >>> generator = RoadNetworkGenerator(bounds=(0, 0, 1000, 1000))
        >>> major, minor, stats = generator.generate(buildings)
        >>> print(f"Generated {len(major)} major + {len(minor)} minor roads")
    """

    def __init__(
        self,
        bounds: Tuple[float, float, float, float],
        config: Optional[RoadNetworkConfig] = None,
    ):
        """
        Initialize road network generator.

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
        buildings: List,
        config: Optional[RoadNetworkConfig] = None,
    ) -> Tuple[List[np.ndarray], List[np.ndarray], Dict]:
        """
        Generate complete road network for building layout.

        This is the MAIN ENTRY POINT for road generation.

        Args:
            buildings: List of Building objects from H-SAGA optimizer
            config: Optional override of default config

        Returns:
            (major_roads, minor_roads, stats) where:
            - major_roads: List of (N, 2) numpy arrays (arterial roads)
            - minor_roads: List of (N, 2) numpy arrays (connecting roads)
            - stats: Dictionary with network statistics

        Example:
            >>> from backend.core.optimization.building import Building
            >>> buildings = [Building('A', 'administrative', 1000, 3)]
            >>> buildings[0].position = (500, 500)
            >>> gen = RoadNetworkGenerator((0, 0, 1000, 1000))
            >>> major, minor, stats = gen.generate(buildings)
        """
        if config is not None:
            self.config = config

        print("🏗️  Building tensor field...")
        self.tensor_field = self._build_tensor_field(buildings)

        print("🛣️  Tracing major roads...")
        self.major_roads = self._generate_major_roads()

        if self.config.generate_minor_roads:
            print("🔗 Generating minor roads...")
            self.minor_roads = self._generate_minor_roads(buildings)

        print("✨ Post-processing...")
        self.major_roads = self._postprocess_roads(self.major_roads)
        self.minor_roads = self._postprocess_roads(self.minor_roads)

        stats = self._compute_stats()

        print(f"✅ Generated {len(self.major_roads)} major + {len(self.minor_roads)} minor roads")
        print(f"   Total length: {stats['total_length_m']:.0f}m")

        return self.major_roads, self.minor_roads, stats

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

        # Create seed points (strategic locations across campus)
        seeds = self._get_major_road_seeds()

        # Streamline config
        streamline_config = StreamlineConfig(max_length=self.config.major_road_max_length)

        for seed in seeds:
            if self.config.use_bidirectional:
                result = trace_bidirectional_streamline(
                    self.tensor_field,
                    seed,
                    config=streamline_config,
                    field_type="major",
                )
            else:
                result = trace_streamline_rk45(
                    self.tensor_field,
                    seed,
                    config=streamline_config,
                    field_type="major",
                )

            if result.success and len(result.path) > 1:
                roads.append(result.path)

        return roads

    def _generate_minor_roads(self, buildings: List) -> List[np.ndarray]:
        """Generate minor roads connecting buildings."""
        if self.tensor_field is None:
            raise ValueError("Tensor field not built yet")

        roads = []

        # For each building, generate connecting roads using minor eigenvector field
        streamline_config = StreamlineConfig(max_length=self.config.minor_road_max_length)

        for building in buildings:
            if not hasattr(building, "position") or building.position is None:
                continue

            # Create seed points around building perimeter
            seeds = self._get_building_connection_seeds(building)

            for seed in seeds:
                result = trace_streamline_rk45(
                    self.tensor_field,
                    seed,
                    config=streamline_config,
                    field_type="minor",  # Use minor field for cross streets
                )

                if result.success and result.total_length > self.config.min_road_length:
                    roads.append(result.path)

        return roads

    def _get_major_road_seeds(self) -> List[np.ndarray]:
        """
        Generate seed points for major roads.

        Strategy: Place seeds along campus perimeter to create arterial network.
        """
        xmin, ymin, xmax, ymax = self.bounds

        seeds = []

        # Create seeds along each edge
        n_seeds_per_edge = max(1, self.config.n_major_roads // 4)

        # Top edge
        for i in range(n_seeds_per_edge):
            x = xmin + (xmax - xmin) * (i + 1) / (n_seeds_per_edge + 1)
            seeds.append(np.array([x, ymax - 50]))  # 50m from edge

        # Bottom edge
        for i in range(n_seeds_per_edge):
            x = xmin + (xmax - xmin) * (i + 1) / (n_seeds_per_edge + 1)
            seeds.append(np.array([x, ymin + 50]))

        # Left edge
        for i in range(n_seeds_per_edge):
            y = ymin + (ymax - ymin) * (i + 1) / (n_seeds_per_edge + 1)
            seeds.append(np.array([xmin + 50, y]))

        # Right edge
        for i in range(n_seeds_per_edge):
            y = ymin + (ymax - ymin) * (i + 1) / (n_seeds_per_edge + 1)
            seeds.append(np.array([xmax - 50, y]))

        # Limit to requested number
        return seeds[: self.config.n_major_roads]

    def _get_building_connection_seeds(self, building) -> List[np.ndarray]:
        """
        Generate seed points around a building for minor road connections.

        Strategy: Place seeds at cardinal directions from building center.
        """
        if not hasattr(building, "position") or building.position is None:
            return []

        bx, by = building.position
        seeds = []

        # Estimate building radius (assuming square footprint)
        if hasattr(building, "footprint"):
            radius = np.sqrt(building.footprint) / 2
        else:
            radius = 20.0  # Default 20m

        # Offset distance (place seeds outside building)
        offset = radius + 10.0

        # Cardinal directions
        directions = [
            (1, 0),  # East
            (0, 1),  # North
            (-1, 0),  # West
            (0, -1),  # South
        ]

        for dx, dy in directions:
            seed = np.array([bx + dx * offset, by + dy * offset])

            # Check if seed is in bounds
            if self.tensor_field.in_bounds(seed):
                seeds.append(seed)

        return seeds

    def _postprocess_roads(self, roads: List[np.ndarray]) -> List[np.ndarray]:
        """
        Post-process roads: resample, filter short roads.

        Args:
            roads: List of (N, 2) road paths

        Returns:
            Processed roads
        """
        processed = []

        for road in roads:
            # Filter out very short roads
            if len(road) < 2:
                continue

            # Compute road length
            segments = np.diff(road, axis=0)
            segment_lengths = np.linalg.norm(segments, axis=1)
            total_length = float(np.sum(segment_lengths))

            if total_length < self.config.min_road_length:
                continue

            # Resample to uniform spacing
            resampled = self._resample_path(road, self.config.resample_spacing)

            processed.append(resampled)

        return processed

    def _resample_path(self, path: np.ndarray, target_spacing: float) -> np.ndarray:
        """
        Resample path to have approximately uniform spacing.

        Args:
            path: (N, 2) array of [x, y] coordinates
            target_spacing: Desired distance between points (meters)

        Returns:
            (M, 2) array of resampled points
        """
        if len(path) < 2:
            return path

        # Compute cumulative arc length
        segments = np.diff(path, axis=0)
        segment_lengths = np.linalg.norm(segments, axis=1)
        cumulative_length = np.concatenate([[0], np.cumsum(segment_lengths)])

        total_length = cumulative_length[-1]

        # Create uniform arc length samples
        n_samples = max(2, int(total_length / target_spacing) + 1)
        uniform_arc_lengths = np.linspace(0, total_length, n_samples)

        # Interpolate x and y separately
        resampled_x = np.interp(uniform_arc_lengths, cumulative_length, path[:, 0])
        resampled_y = np.interp(uniform_arc_lengths, cumulative_length, path[:, 1])

        resampled_path = np.column_stack([resampled_x, resampled_y])

        return resampled_path

    def _compute_stats(self) -> Dict:
        """Compute network statistics."""
        total_major_length = 0.0
        for road in self.major_roads:
            if len(road) > 1:
                segments = np.diff(road, axis=0)
                total_major_length += float(np.sum(np.linalg.norm(segments, axis=1)))

        total_minor_length = 0.0
        for road in self.minor_roads:
            if len(road) > 1:
                segments = np.diff(road, axis=0)
                total_minor_length += float(np.sum(np.linalg.norm(segments, axis=1)))

        return {
            "n_major_roads": len(self.major_roads),
            "n_minor_roads": len(self.minor_roads),
            "major_length_m": total_major_length,
            "minor_length_m": total_minor_length,
            "total_length_m": total_major_length + total_minor_length,
            "config": {
                "tensor_resolution": self.config.tensor_resolution,
                "n_major_roads_target": self.config.n_major_roads,
                "use_bidirectional": self.config.use_bidirectional,
            },
        }

    def get_geojson(self) -> Dict:
        """
        Export road network as GeoJSON for visualization.

        Returns:
            GeoJSON FeatureCollection with major and minor roads
        """
        features = []

        # Major roads
        for i, road in enumerate(self.major_roads):
            features.append(
                {
                    "type": "Feature",
                    "properties": {"road_type": "major", "road_id": f"major_{i}"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[float(x), float(y)] for x, y in road],
                    },
                }
            )

        # Minor roads
        for i, road in enumerate(self.minor_roads):
            features.append(
                {
                    "type": "Feature",
                    "properties": {"road_type": "minor", "road_id": f"minor_{i}"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[float(x), float(y)] for x, y in road],
                    },
                }
            )

        return {"type": "FeatureCollection", "features": features}
