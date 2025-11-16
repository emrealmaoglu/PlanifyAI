"""
Turtle-based agent system for minor road generation.

Implements discrete agents that sample tensor fields for directional hints
but apply planning rules for realistic campus road layouts.

Key Features:
- Turtle agents with position, direction, path history
- Tensor field guidance (soft constraint)
- Planning rules (hard constraints): spacing, intersection detection
- Priority queue for agent management

References:
- Parish & Müller (2001): L-system-inspired road generation
- Research: "Simplified Road Network Generation Research"
"""

import heapq
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from typing import List, Optional, Set, Tuple

import numpy as np

from src.spatial.tensor_field import TensorField


class AgentState(Enum):
    """Agent lifecycle states."""

    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    INTERSECTED = "intersected"


@dataclass
class AgentConfig:
    """Configuration for road agents."""

    step_size: float = 10.0  # Distance per step (meters)
    max_steps: int = 50  # Maximum steps before termination
    tensor_weight: float = 0.3  # How much to follow tensor field (0-1)
    momentum_weight: float = 0.7  # How much to continue current direction
    intersection_snap_distance: float = 15.0  # Snap to nearby intersections (meters)
    min_road_spacing: float = 30.0  # Minimum distance between parallel roads
    turn_angle_limit: float = 45.0  # Maximum turn per step (degrees)


@dataclass
class RoadAgent:
    """
    Turtle agent for procedural road generation.

    Agents move through space, building roads as they go.
    Movement is guided by:
    1. Tensor field (global aesthetic)
    2. Momentum (smooth curves)
    3. Planning rules (spacing, intersections)

    Attributes:
        position: Current [x, y] position
        direction: Current unit direction vector
        path: List of positions visited
        state: Current agent state
        priority: Priority for processing (higher = process first)
    """

    agent_id: str
    position: np.ndarray
    direction: np.ndarray
    path: List[np.ndarray] = dataclass_field(default_factory=list)
    state: AgentState = AgentState.ACTIVE
    priority: float = 1.0
    n_steps: int = 0
    parent_id: Optional[str] = None  # For branching agents

    def __post_init__(self):
        """Initialize path with starting position."""
        # Convert position and direction to numpy arrays if they're lists
        self.position = np.asarray(self.position)
        self.direction = np.asarray(self.direction)

        if len(self.path) == 0:
            self.path.append(self.position.copy())

        # Normalize direction
        norm = np.linalg.norm(self.direction)
        if norm > 1e-10:
            self.direction = self.direction / norm

    def __lt__(self, other):
        """For priority queue ordering (higher priority first)."""
        return self.priority > other.priority


class RoadAgentSystem:
    """
    Manager for multiple road agents.

    Handles:
    - Agent creation and lifecycle
    - Collision detection
    - Intersection snapping
    - Priority queue management
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Args:
            config: AgentConfig with agent parameters
        """
        self.config = config or AgentConfig()

        # Active agents (priority queue)
        self.agent_queue: List[RoadAgent] = []

        # Completed roads (list of paths)
        self.completed_roads: List[np.ndarray] = []

        # All generated points (for spatial queries)
        self.all_points: List[np.ndarray] = []

        # Agent ID counter
        self.next_agent_id = 0

    def create_agent(
        self,
        position: np.ndarray,
        direction: Optional[np.ndarray] = None,
        priority: float = 1.0,
    ) -> RoadAgent:
        """
        Create and add new agent to system.

        Args:
            position: Starting [x, y] position
            direction: Initial direction (if None, random)
            priority: Agent priority (higher processed first)

        Returns:
            Created RoadAgent
        """
        if direction is None:
            # Random direction
            angle = np.random.uniform(0, 2 * np.pi)
            direction = np.array([np.cos(angle), np.sin(angle)])

        agent = RoadAgent(
            agent_id=f"agent_{self.next_agent_id}",
            position=position.copy(),
            direction=direction.copy(),
            priority=priority,
        )

        self.next_agent_id += 1

        # Add to queue
        heapq.heappush(self.agent_queue, agent)

        return agent

    def step_agent(
        self,
        agent: RoadAgent,
        tensor_field: TensorField,
        field_type: str = "minor",
    ) -> bool:
        """
        Execute one step for an agent.

        Args:
            agent: RoadAgent to step
            tensor_field: TensorField for guidance
            field_type: 'major' or 'minor'

        Returns:
            True if agent should continue, False if terminated
        """
        # Check if agent exceeded max steps
        if agent.n_steps >= self.config.max_steps:
            agent.state = AgentState.COMPLETED
            return False

        # 1. Sample tensor field for direction hint
        point = agent.position.reshape(1, -1)
        tensor_hint = tensor_field.get_eigenvectors(point, field_type=field_type)
        tensor_hint = tensor_hint.flatten()

        # 2. Blend tensor hint with momentum
        w_tensor = self.config.tensor_weight
        w_momentum = self.config.momentum_weight

        new_direction = w_tensor * tensor_hint + w_momentum * agent.direction

        # Normalize
        norm = np.linalg.norm(new_direction)
        if norm > 1e-10:
            new_direction = new_direction / norm
        else:
            # Fallback to current direction
            new_direction = agent.direction

        # 3. Apply turn angle limit
        current_angle = np.arctan2(agent.direction[1], agent.direction[0])
        new_angle = np.arctan2(new_direction[1], new_direction[0])

        angle_diff = new_angle - current_angle
        # Wrap to [-pi, pi]
        angle_diff = (angle_diff + np.pi) % (2 * np.pi) - np.pi

        max_turn_rad = np.radians(self.config.turn_angle_limit)
        if np.abs(angle_diff) > max_turn_rad:
            # Clamp turn
            clamped_angle = current_angle + np.sign(angle_diff) * max_turn_rad
            new_direction = np.array([np.cos(clamped_angle), np.sin(clamped_angle)])

        # 4. Compute new position
        new_position = agent.position + self.config.step_size * new_direction

        # 5. Check if new position valid (boundary, spacing)
        if not tensor_field.in_bounds(new_position):
            agent.state = AgentState.TERMINATED
            return False

        # Check minimum road spacing (exclude agent's own path)
        # Only check against other agents' paths, not the current agent's path
        if self._violates_spacing(new_position, exclude_path=agent.path):
            agent.state = AgentState.TERMINATED
            return False

        # 6. Update agent
        agent.position = new_position
        agent.direction = new_direction
        agent.path.append(new_position.copy())
        agent.n_steps += 1

        # Store point
        self.all_points.append(new_position.copy())

        return True

    def _violates_spacing(
        self, position: np.ndarray, exclude_path: Optional[List[np.ndarray]] = None
    ) -> bool:
        """
        Check if position is too close to existing roads.

        Args:
            position: [x, y] position to check
            exclude_path: Optional path to exclude from spacing check (agent's own path)

        Returns:
            True if violates minimum spacing
        """
        if len(self.all_points) == 0:
            return False

        # Compute distances to all existing points
        points_array = np.array(self.all_points)

        # Exclude points from the agent's own path if provided
        if exclude_path is not None and len(exclude_path) > 0:
            exclude_array = np.array(exclude_path)
            # Remove points that are in the exclude_path
            # Use a small tolerance for comparison
            distances_to_exclude = np.linalg.norm(
                points_array[:, None, :] - exclude_array[None, :, :], axis=2
            )
            mask = np.all(distances_to_exclude > 1e-6, axis=1)  # Points not in exclude_path
            points_array = points_array[mask]

            if len(points_array) == 0:
                return False

        distances = np.linalg.norm(points_array - position, axis=1)
        min_distance = np.min(distances)

        return min_distance < self.config.min_road_spacing

    def run_simulation(
        self,
        tensor_field: TensorField,
        max_iterations: int = 1000,
        field_type: str = "minor",
    ) -> List[np.ndarray]:
        """
        Run agent simulation until completion.

        Args:
            tensor_field: TensorField for guidance
            max_iterations: Safety limit on iterations
            field_type: 'major' or 'minor' eigenvector field

        Returns:
            List of completed road paths (each is (N, 2) array)
        """
        iteration = 0

        while len(self.agent_queue) > 0 and iteration < max_iterations:
            iteration += 1

            # Pop highest priority agent
            agent = heapq.heappop(self.agent_queue)

            # Skip if not active
            if agent.state != AgentState.ACTIVE:
                continue

            # Step agent
            should_continue = self.step_agent(agent, tensor_field, field_type)

            if should_continue:
                # Re-add to queue (might have lower priority now)
                agent.priority *= 0.99  # Slight decay to avoid starvation
                heapq.heappush(self.agent_queue, agent)
            else:
                # Agent completed/terminated
                # Save road if it has at least 2 points (start + at least 1 step)
                if len(agent.path) >= 2:
                    road_path = np.array(agent.path)
                    self.completed_roads.append(road_path)

        return self.completed_roads


def create_agents_from_buildings(
    buildings: List,  # List[Building]
    config: Optional[AgentConfig] = None,
) -> RoadAgentSystem:
    """
    Factory function to create agents at building entrances.

    Strategy:
    - Place agents at building perimeters
    - Direction points away from building center
    - Priority based on building importance

    Args:
        buildings: List of Building objects
        config: AgentConfig for agents

    Returns:
        RoadAgentSystem with agents created
    """
    system = RoadAgentSystem(config)

    for building in buildings:
        # Get building position and footprint
        if building.position is None:
            continue

        center = np.array(building.position)
        radius = np.sqrt(building.footprint / np.pi)  # Approximate radius

        # Create 2-4 agents around building perimeter
        n_agents = 2 if building.footprint < 1000 else 4

        for i in range(n_agents):
            angle = (2 * np.pi * i) / n_agents

            # Position at perimeter
            offset = radius * 1.5 * np.array([np.cos(angle), np.sin(angle)])
            position = center + offset

            # Direction points away from center
            direction = offset / np.linalg.norm(offset)

            # Priority based on building type
            IMPORTANT_TYPES = ["administrative", "library", "dining"]
            priority = 2.0 if building.type.value in IMPORTANT_TYPES else 1.0

            system.create_agent(position, direction, priority)

    return system
