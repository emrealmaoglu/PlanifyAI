"""
Unit tests for road agent system.

Tests verify:
1. Agent creation and initialization
2. Single agent stepping
3. Multi-agent simulation
4. Collision detection
5. Priority queue management
"""

import numpy as np
import pytest

from src.spatial.road_agents import (
    AgentConfig,
    AgentState,
    RoadAgent,
    RoadAgentSystem,
    create_agents_from_buildings,
)
from src.spatial.tensor_field import TensorField


class TestRoadAgentBasics:
    """Test fundamental agent operations."""

    def test_agent_initialization(self):
        """Test agent creates with correct attributes."""
        position = np.array([50, 50])
        direction = np.array([1, 0])

        agent = RoadAgent(agent_id="test_0", position=position, direction=direction)

        assert agent.agent_id == "test_0"
        assert np.array_equal(agent.position, position)
        assert np.allclose(agent.direction, [1, 0])
        assert agent.state == AgentState.ACTIVE
        assert len(agent.path) == 1  # Initial position
        assert agent.n_steps == 0

    def test_agent_direction_normalization(self):
        """Test agent normalizes direction vector."""
        agent = RoadAgent(
            agent_id="test_0",
            position=np.array([0, 0]),
            direction=np.array([3, 4]),  # Not unit length
        )

        # Should be normalized to unit length
        assert np.allclose(np.linalg.norm(agent.direction), 1.0)
        assert np.allclose(agent.direction, [0.6, 0.8])


class TestRoadAgentSystem:
    """Test agent system management."""

    def test_system_initialization(self):
        """Test agent system creates empty."""
        system = RoadAgentSystem()

        assert len(system.agent_queue) == 0
        assert len(system.completed_roads) == 0
        assert system.next_agent_id == 0

    def test_create_agent(self):
        """Test agent creation adds to queue."""
        system = RoadAgentSystem()

        agent = system.create_agent(position=np.array([50, 50]), direction=np.array([1, 0]))

        assert len(system.agent_queue) == 1
        assert agent.agent_id == "agent_0"

        # Create another
        agent2 = system.create_agent(position=np.array([60, 60]), direction=np.array([0, 1]))

        assert len(system.agent_queue) == 2
        assert agent2.agent_id == "agent_1"

    def test_priority_queue_ordering(self):
        """Test higher priority agents processed first."""
        system = RoadAgentSystem()

        # Create agents with different priorities
        low_priority = system.create_agent([10, 10], [1, 0], priority=1.0)
        high_priority = system.create_agent([20, 20], [1, 0], priority=10.0)

        # Pop from queue
        first_agent = system.agent_queue[0]  # Peek without popping

        # Should be high priority agent
        assert first_agent.agent_id == high_priority.agent_id


class TestAgentStepping:
    """Test agent movement and decision making."""

    def test_single_agent_step(self):
        """Test agent takes one step successfully."""
        system = RoadAgentSystem()
        agent = system.create_agent([50, 50], [1, 0])

        # Create tensor field
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)  # North

        # Step agent
        should_continue = system.step_agent(agent, field)

        assert should_continue
        assert agent.n_steps == 1
        assert len(agent.path) == 2

        # Position should have moved
        assert not np.array_equal(agent.position, agent.path[0])

    def test_agent_follows_tensor_field(self):
        """Test agent direction influenced by tensor field."""
        config = AgentConfig(
            tensor_weight=0.8,  # High tensor influence
            momentum_weight=0.2,
            step_size=10.0,
        )
        system = RoadAgentSystem(config)

        # Agent starts pointing east
        agent = system.create_agent([50, 50], [1, 0])

        # Field points north
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(angle_degrees=0, strength=1.0)

        # Step several times
        for _ in range(5):
            system.step_agent(agent, field, field_type="major")

        # Direction should have turned northward
        # (not fully north due to momentum, but trending)
        assert agent.direction[0] < 0.9  # Less eastward

    def test_agent_boundary_termination(self):
        """Test agent terminates at field boundary."""
        system = RoadAgentSystem()

        # Start near edge, pointing outward
        agent = system.create_agent([95, 50], [1, 0])

        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        # Step until boundary
        max_steps = 10
        for _ in range(max_steps):
            should_continue = system.step_agent(agent, field)
            if not should_continue:
                break

        # Should have terminated
        assert agent.state == AgentState.TERMINATED

    def test_agent_max_steps_limit(self):
        """Test agent terminates after max steps."""
        config = AgentConfig(max_steps=5)
        system = RoadAgentSystem(config)

        agent = system.create_agent([50, 50], [1, 0])

        field = TensorField(bounds=(0, 0, 1000, 1000), resolution=30)
        field.add_grid_field(0, 1.0)

        # Step beyond max
        for _ in range(10):
            should_continue = system.step_agent(agent, field)
            if not should_continue:
                break

        # Should have stopped at max_steps
        assert agent.n_steps <= config.max_steps
        assert agent.state == AgentState.COMPLETED


class TestSimulation:
    """Test full multi-agent simulation."""

    def test_empty_simulation(self):
        """Test simulation with no agents."""
        system = RoadAgentSystem()
        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        roads = system.run_simulation(field)

        assert len(roads) == 0

    def test_single_agent_simulation(self):
        """Test simulation with one agent."""
        config = AgentConfig(max_steps=20, step_size=5.0)
        system = RoadAgentSystem(config)

        system.create_agent([50, 50], [1, 0])

        field = TensorField(bounds=(0, 0, 200, 200), resolution=30)
        field.add_grid_field(0, 1.0)

        roads = system.run_simulation(field, max_iterations=100)

        # Should have one road
        assert len(roads) >= 1

        # Road should have multiple points
        assert len(roads[0]) > 2

    def test_multiple_agents_simulation(self):
        """Test simulation with multiple agents."""
        system = RoadAgentSystem()

        # Create 5 agents at different positions
        for i in range(5):
            pos = np.array([20 + i * 30, 50])
            direction = np.array([0, 1])  # All point north
            system.create_agent(pos, direction, priority=1.0)

        field = TensorField(bounds=(0, 0, 200, 200), resolution=30)
        field.add_grid_field(0, 1.0)

        roads = system.run_simulation(field)

        # Should have generated roads
        assert len(roads) > 0

    def test_simulation_max_iterations_safety(self):
        """Test simulation respects max_iterations limit."""
        config = AgentConfig(max_steps=1000)  # Very high
        system = RoadAgentSystem(config)

        system.create_agent([50, 50], [1, 0])

        field = TensorField(bounds=(0, 0, 100, 100), resolution=20)
        field.add_grid_field(0, 1.0)

        # Low max_iterations
        roads = system.run_simulation(field, max_iterations=10)

        # Should have stopped early
        # (agent not necessarily completed)
        assert len(system.agent_queue) <= 1  # May have 1 left


class TestCollisionDetection:
    """Test road spacing and collision avoidance."""

    def test_spacing_violation_detection(self):
        """Test system detects when roads too close."""
        config = AgentConfig(min_road_spacing=20.0)
        system = RoadAgentSystem(config)

        # Add some existing points
        system.all_points = [np.array([50, 50]), np.array([60, 60])]

        # Check violation
        # Close point (should violate)
        close_point = np.array([55, 55])
        assert system._violates_spacing(close_point)

        # Far point (should not violate)
        far_point = np.array([100, 100])
        assert not system._violates_spacing(far_point)


@pytest.mark.skip(reason="Requires Building class")
class TestBuildingIntegration:
    """Test integration with building layouts."""

    def test_create_agents_from_buildings(self):
        """Test factory creates agents at building entrances."""
        from src.algorithms.building import Building, BuildingType

        buildings = [
            Building("ADM-01", BuildingType.ADMINISTRATIVE, 1000, 3, position=(500, 500)),
            Building("RES-01", BuildingType.RESIDENTIAL, 800, 5, position=(300, 300)),
        ]

        system = create_agents_from_buildings(buildings)

        # Should have created agents (2-4 per building)
        assert len(system.agent_queue) >= 4  # At least 2 * 2

        # Agents should be near buildings
        # (Not exactly at center - at perimeter)
