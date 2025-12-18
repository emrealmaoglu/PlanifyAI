# Road Network Generation API

## Overview

Complete system for generating realistic road networks for campus planning.

## Components

### 1. Streamline Tracer (`streamline_tracer.py`)

Adaptive RK45 integration for major roads.

**Key Functions:**

- `trace_streamline_rk45(field, seed, config)`: Trace single streamline
- `trace_bidirectional_streamline(field, seed, config)`: Bidirectional tracing

**Usage:**

```python
from src.spatial.streamline_tracer import trace_streamline_rk45

result = trace_streamline_rk45(tensor_field, [100, 100])
print(f"Road length: {result.total_length}m")
```

### 2. Road Agents (`road_agents.py`)

Turtle-based agents for minor roads.

**Key Classes:**

- `RoadAgent`: Single agent with position, direction, path
- `RoadAgentSystem`: Multi-agent manager

**Usage:**

```python
from src.spatial.road_agents import RoadAgentSystem

system = RoadAgentSystem()
system.create_agent([50, 50], [1, 0])
roads = system.run_simulation(tensor_field)
```

### 3. Road Network Generator (`road_network.py`)

High-level API combining all components.

**Usage:**

```python
from src.spatial.road_network import RoadNetworkGenerator

gen = RoadNetworkGenerator(bounds=(0, 0, 1000, 1000))
major_roads, minor_roads = gen.generate(buildings)
```

## Performance

- Single streamline: <100ms
- 10 buildings + roads: <5s
- Memory: ~20MB for typical campus

## Next Steps

- Intersection snapping
- Road simplification
- Traffic simulation integration
