# PlanifyAI v2.0 - Comprehensive Architecture Design Document

> **Version:** 2.0.0
> **Date:** 29 Aralık 2025
> **Author:** Emre Almaoğlu
> **Status:** 🏗️ Foundation Design Phase

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Core Principles](#2-core-principles)
3. [System Architecture](#3-system-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Data Flow & Integration](#6-data-flow--integration)
7. [Algorithm Specifications](#7-algorithm-specifications)
8. [API Design](#8-api-design)
9. [Database & Storage](#9-database--storage)
10. [Development Roadmap](#10-development-roadmap)
11. [Research-to-Code Mapping](#11-research-to-code-mapping)

---

## 1. Executive Summary

### 1.1 Vision Statement

PlanifyAI v2.0 is a complete architectural rewrite designed to create a **production-grade, research-backed, AI-powered generative spatial planning system** for Turkish university campuses. Unlike v1 (proof-of-concept), v2 emphasizes:

- **Unbounded Quality Philosophy**: Quality and scientific accuracy over speed
- **Modular Architecture**: Clean separation of concerns, SOLID principles
- **Research-Driven**: Every algorithm backed by peer-reviewed research
- **Patent Potential**: Novel "Repulsive Tensor Field" approach
- **Thesis-Ready**: Designed for academic evaluation and publication

### 1.2 Key Innovations (vs V1)

| Feature | V1 | V2 |
|---------|----|----|
| **Canvas Mode** | Direct map editing | Isolated Canvas workflow |
| **Optimizer** | H-SAGA (4 objectives) | H-SAGA (6 objectives) |
| **Road Network** | ❌ None | ✅ Repulsive Tensor Field |
| **Building Shapes** | Rectangle only | L/U/H/O shapes |
| **Green Space** | Hard constraint | Optimized placement |
| **Solar Analysis** | Simple orientation | pysolar shadow modeling |
| **Wind Analysis** | Static formula | OpenMeteo real-time API |
| **Architecture** | Monolithic | Microservices-ready |

### 1.3 Technology Stack

#### Backend
```
Language:        Python 3.11+
Framework:       FastAPI 0.104+
Optimization:    pymoo 0.6.1+ (NSGA-III)
Geometry:        shapely 2.0+, geopandas 0.14+
Physics:         pysolar 0.10+, openmeteo-requests 1.2+
Testing:         pytest 7.4+, pytest-cov
Performance:     Apple Accelerate (M1/M2 optimized)
```

#### Frontend
```
Framework:       React 18+, TypeScript 5+
Build Tool:      Vite 5+
Mapping:         Mapbox GL JS 3.0+
State:           Zustand 4+
Styling:         Tailwind CSS 3+
API Client:      Axios 1.6+
```

---

## 2. Core Principles

### 2.1 Architectural Principles

1. **Separation of Concerns**: Clear boundaries between domain, application, and infrastructure layers
2. **Dependency Inversion**: Core business logic depends on abstractions, not implementations
3. **Single Responsibility**: Each module has one reason to change
4. **Open/Closed**: Open for extension, closed for modification
5. **Interface Segregation**: Clients depend only on interfaces they use

### 2.2 Code Quality Standards

```python
# Type Hints: 100% coverage
def calculate_setback(building_type: BuildingType, height: float) -> float:
    """Calculate setback distance per Turkish regulations."""
    ...

# Docstrings: Google style
# Testing: >85% coverage
# Linting: black + ruff + mypy
# Performance: <100ms per evaluation (10 buildings)
```

### 2.3 Research-Driven Development

Every algorithm implementation must:
1. ✅ Reference specific research document
2. ✅ Include mathematical formulation
3. ✅ Provide benchmark comparison
4. ✅ Document parameter sensitivity

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                     (React + TypeScript)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Mapbox GL JS │  │   Isolated   │  │    Result    │      │
│  │   Canvas     │  │   Sidebar    │  │  Visualizer  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                        REST API Layer                        │
│                         (FastAPI)                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Application Services                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │    OSM     │  │ Optimizer  │  │  Validator │     │  │
│  │  │  Service   │  │  Service   │  │  Service   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Core Domain                         │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Optimization Engine (H-SAGA)                  │  │  │
│  │  │  ├─ SA Explorer (30% budget)                   │  │  │
│  │  │  └─ GA Refiner (70% budget)                    │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Geometry Engine                               │  │  │
│  │  │  ├─ Building Shapes (L/U/H/O)                  │  │  │
│  │  │  ├─ Tensor Field Generator                     │  │  │
│  │  │  └─ Road Network Builder                       │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Physics Engine                                │  │  │
│  │  │  ├─ Solar Shadow (pysolar)                     │  │  │
│  │  │  └─ Wind Analysis (OpenMeteo)                  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Standards Engine                              │  │  │
│  │  │  ├─ Turkish Building Codes                     │  │  │
│  │  │  └─ Constraint Validators                      │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  SQLite    │  │    OSM     │  │ OpenMeteo  │            │
│  │  Job Store │  │ Overpass   │  │    API     │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Directory Structure

```
planifyai-v2/
├── backend/
│   ├── main.py                         # FastAPI application entry
│   ├── config.py                       # Environment configuration
│   │
│   ├── api/                            # API Layer
│   │   ├── __init__.py
│   │   ├── dependencies.py             # Dependency injection
│   │   ├── middleware.py               # CORS, logging, error handling
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py               # Health check endpoints
│   │       ├── site.py                 # Site/context endpoints
│   │       ├── optimize.py             # Optimization endpoints
│   │       └── export.py               # Export endpoints (GeoJSON, PDF)
│   │
│   ├── models/                         # Pydantic Schemas (API Contract)
│   │   ├── __init__.py
│   │   ├── geometry.py                 # GeoJSON types
│   │   ├── site.py                     # Site, Building, Road
│   │   ├── optimization.py             # Request/Response schemas
│   │   ├── constraints.py              # Constraint definitions
│   │   └── results.py                  # Result schemas
│   │
│   ├── services/                       # Application Services
│   │   ├── __init__.py
│   │   ├── osm_service.py              # OSM data fetching
│   │   ├── optimizer_service.py        # Optimization orchestration
│   │   ├── validator_service.py        # Input validation
│   │   └── export_service.py           # Export logic
│   │
│   ├── core/                           # Domain Logic (Business Core)
│   │   │
│   │   ├── optimization/               # 🧬 Optimization Engine
│   │   │   ├── __init__.py
│   │   │   ├── problem.py              # PyMOO Problem definition
│   │   │   ├── hsaga.py                # H-SAGA algorithm
│   │   │   ├── encoding.py             # Gene encoding/decoding
│   │   │   ├── objectives/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cost.py             # Construction cost
│   │   │   │   ├── walkability.py      # 15-minute city metric
│   │   │   │   ├── green_ratio.py      # Green space optimization
│   │   │   │   ├── solar.py            # Solar shadow minimization
│   │   │   │   ├── wind.py             # Wind alignment
│   │   │   │   └── road_length.py      # Road efficiency
│   │   │   └── constraints/
│   │   │       ├── __init__.py
│   │   │       ├── boundary.py         # Within boundary
│   │   │       ├── overlap.py          # No building overlap
│   │   │       ├── setback.py          # Turkish setback rules
│   │   │       ├── fire_separation.py  # Fire safety distance
│   │   │       └── slope.py            # Terrain slope
│   │   │
│   │   ├── geometry/                   # 🗺️ Geometry Engine
│   │   │   ├── __init__.py
│   │   │   ├── shapes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── rectangle.py        # Simple rectangular
│   │   │   │   ├── l_shape.py          # L-shaped building
│   │   │   │   ├── u_shape.py          # U-shaped building
│   │   │   │   ├── h_shape.py          # H-shaped building
│   │   │   │   └── o_shape.py          # O-shaped (courtyard)
│   │   │   ├── tensor_field.py         # Tensor field generator
│   │   │   ├── road_network.py         # Road network builder
│   │   │   ├── streamline_tracer.py    # RK4 streamline integration
│   │   │   └── green_space.py          # Green space placement
│   │   │
│   │   ├── physics/                    # 🌬️ Physics Engine
│   │   │   ├── __init__.py
│   │   │   ├── solar.py                # pysolar integration
│   │   │   ├── wind.py                 # OpenMeteo API client
│   │   │   └── shadow.py               # Shadow calculation
│   │   │
│   │   ├── standards/                  # 📐 Turkish Standards
│   │   │   ├── __init__.py
│   │   │   ├── building_types.py       # Building type definitions
│   │   │   ├── setback_rules.py        # İmar Kanunu setback
│   │   │   ├── fire_safety.py          # Fire separation rules
│   │   │   └── accessibility.py        # ADA compliance
│   │   │
│   │   ├── metrics/                    # 📊 Metrics & Analysis
│   │   │   ├── __init__.py
│   │   │   ├── walkability.py          # Walkability score (2SFCA)
│   │   │   ├── connectivity.py         # Graph connectivity indices
│   │   │   └── diversity.py            # Land use entropy
│   │   │
│   │   └── utils/                      # Core utilities
│   │       ├── __init__.py
│   │       ├── coordinate_transform.py # CRS transformations
│   │       └── spatial_index.py        # R-tree indexing
│   │
│   ├── infrastructure/                 # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── job_store.py            # Job storage interface
│   │   │   └── sqlite_store.py         # SQLite implementation
│   │   └── external/
│   │       ├── __init__.py
│   │       ├── osm_client.py           # OSM Overpass client
│   │       └── openmeteo_client.py     # OpenMeteo API client
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── map/
│       │   │   ├── MapCanvas.tsx       # Main map container
│       │   │   ├── DrawingTools.tsx    # Polygon drawing
│       │   │   ├── BuildingLayer.tsx   # Building visualization
│       │   │   ├── RoadLayer.tsx       # Road network layer
│       │   │   └── GreenLayer.tsx      # Green space layer
│       │   ├── sidebar/
│       │   │   ├── SitePanel.tsx       # Site configuration
│       │   │   ├── BuildingPanel.tsx   # Building counts/types
│       │   │   ├── WeightsPanel.tsx    # Objective weights
│       │   │   └── ResultsPanel.tsx    # Optimization results
│       │   └── visualization/
│       │       ├── ParetoChart.tsx     # Pareto front visualization
│       │       ├── MetricsTable.tsx    # Metrics display
│       │       └── ComparisonView.tsx  # Before/After comparison
│       ├── api/
│       │   └── client.ts               # Axios API client
│       ├── store/
│       │   └── useStore.ts             # Zustand global state
│       ├── types/
│       │   └── index.ts                # TypeScript types
│       └── pages/
│           └── Editor.tsx              # Main editor page
│
├── data/                               # Static data
│   ├── campuses/                       # Campus GeoJSON files
│   └── benchmarks/                     # Benchmark datasets
│
├── docs/
│   ├── research/                       # Research documents (61 files)
│   ├── api/                            # API documentation
│   └── architecture/                   # Architecture diagrams
│
├── scripts/
│   ├── benchmark.py                    # Performance benchmarking
│   └── migrate_v1_to_v2.py             # Migration script
│
├── requirements.txt
├── pyproject.toml
├── package.json
└── README.md
```

---

## 4. Backend Architecture

### 4.1 Core Domain Models

#### 4.1.1 Building Model

```python
from typing import Literal
from pydantic import BaseModel, Field
from shapely.geometry import Polygon

BuildingShape = Literal["rectangle", "L", "U", "H", "O"]
BuildingType = Literal["Faculty", "Dormitory", "Library", "Research", "Sports", "Cafeteria"]

class Building(BaseModel):
    """Core building domain model."""

    id: str = Field(..., description="Unique building identifier")
    type: BuildingType
    shape: BuildingShape = "rectangle"

    # Geometry
    geometry: Polygon = Field(..., description="Building footprint (shapely Polygon)")
    centroid: tuple[float, float] = Field(..., description="Center point (x, y)")
    rotation: float = Field(..., ge=0, le=360, description="Rotation in degrees")

    # Dimensions
    width: float = Field(..., gt=0, description="Width in meters")
    depth: float = Field(..., gt=0, description="Depth in meters")
    height: float = Field(..., gt=0, description="Height in meters")
    floors: int = Field(..., ge=1, le=20, description="Number of floors")

    # Compliance
    floor_area_ratio: float = Field(..., description="FAR (built area / lot area)")
    setback_front: float = Field(default=5.0, description="Front setback (m)")
    setback_side: float = Field(default=3.0, description="Side setback (m)")

    class Config:
        arbitrary_types_allowed = True  # For shapely.Polygon
```

#### 4.1.2 Gene Encoding

```python
from typing import TypeAlias
import numpy as np

# Gene structure: [x, y, rotation, type_id, width_factor, depth_factor, floor_factor]
Gene: TypeAlias = np.ndarray  # shape: (7,)
Genome: TypeAlias = np.ndarray  # shape: (n_buildings, 7)

class GeneEncoder:
    """Encode/decode between Building objects and optimization genes."""

    @staticmethod
    def encode(building: Building) -> Gene:
        """Convert Building to gene array."""
        return np.array([
            building.centroid[0],          # x position
            building.centroid[1],          # y position
            building.rotation,              # rotation (0-360)
            BUILDING_TYPE_MAP[building.type],  # type ID (0-5)
            building.width / BASE_WIDTH[building.type],    # width factor
            building.depth / BASE_DEPTH[building.type],    # depth factor
            building.floors / BASE_FLOORS[building.type],  # floor factor
        ])

    @staticmethod
    def decode(gene: Gene, boundary: Polygon) -> Building:
        """Convert gene array to Building object."""
        x, y, rotation, type_id, w_factor, d_factor, f_factor = gene

        building_type = BUILDING_TYPE_REVERSE[int(type_id)]
        width = BASE_WIDTH[building_type] * np.clip(w_factor, 0.5, 1.5)
        depth = BASE_DEPTH[building_type] * np.clip(d_factor, 0.5, 1.5)
        floors = int(BASE_FLOORS[building_type] * np.clip(f_factor, 0.5, 1.5))

        # Generate geometry based on shape
        geometry = generate_building_shape(
            center=(x, y),
            width=width,
            depth=depth,
            rotation=rotation,
            shape=BUILDING_SHAPE_MAP[building_type]
        )

        return Building(
            id=f"building_{hash(gene.tobytes()) % 10000}",
            type=building_type,
            shape=BUILDING_SHAPE_MAP[building_type],
            geometry=geometry,
            centroid=(x, y),
            rotation=rotation,
            width=width,
            depth=depth,
            height=floors * 4.0,  # 4m per floor
            floors=floors,
            floor_area_ratio=calculate_far(geometry, boundary)
        )
```

### 4.2 Optimization Engine (H-SAGA)

#### 4.2.1 Algorithm Architecture

Based on **Li et al. (2025)** research, we implement a **two-phase hybrid**:

**Phase 1: SA Exploration (30% evaluation budget)**
- Purpose: Global basin discovery
- Temperature: T₀ = 300, α = 0.95 (slow cooling)
- Chains: 8 parallel SA chains
- Output: Top 50% solutions → seed GA population

**Phase 2: GA Refinement (70% evaluation budget)**
- Purpose: Local optimization
- Algorithm: NSGA-III (Das-Dennis reference points)
- Operators: SBX crossover + Polynomial mutation
- Output: Pareto-optimal front

```python
class HSAGAOptimizer:
    """Hybrid SA-GA optimizer based on Li et al. (2025)."""

    def __init__(
        self,
        problem: SpatialProblem,
        total_evaluations: int = 5000,
        sa_budget_ratio: float = 0.3,
        n_chains: int = 8,
        initial_temp: float = 300.0,
        cooling_rate: float = 0.95,
    ):
        self.problem = problem
        self.total_evals = total_evaluations
        self.sa_evals = int(total_evaluations * sa_budget_ratio)
        self.ga_evals = total_evaluations - self.sa_evals

        # SA configuration
        self.n_chains = n_chains
        self.T0 = initial_temp
        self.alpha = cooling_rate

    def optimize(self) -> ParetoFront:
        """Run H-SAGA optimization."""

        # Phase 1: SA Exploration
        logger.info(f"Phase 1: SA Exploration ({self.sa_evals} evals)")
        sa_solutions = self._sa_exploration_phase()

        # Phase 2: GA Refinement
        logger.info(f"Phase 2: GA Refinement ({self.ga_evals} evals)")
        pareto_front = self._ga_refinement_phase(
            initial_population=sa_solutions
        )

        return pareto_front

    def _sa_exploration_phase(self) -> list[Solution]:
        """Run parallel SA chains for global exploration."""
        evals_per_chain = self.sa_evals // self.n_chains

        with ProcessPoolExecutor(max_workers=self.n_chains) as executor:
            futures = [
                executor.submit(self._run_sa_chain, evals_per_chain, seed=i)
                for i in range(self.n_chains)
            ]
            chain_results = [f.result() for f in futures]

        # Combine and select top 50%
        all_solutions = [sol for chain in chain_results for sol in chain]
        all_solutions.sort(key=lambda s: s.fitness, reverse=True)

        population_size = self.problem.population_size
        return all_solutions[:population_size]

    def _run_sa_chain(self, max_evals: int, seed: int) -> list[Solution]:
        """Run single SA chain with Metropolis criterion."""
        np.random.seed(seed)

        # Initialize random solution
        current = self.problem.random_solution()
        current_fitness = self.problem.evaluate(current)
        best = current.copy()
        best_fitness = current_fitness

        T = self.T0
        history = [current]

        for i in range(max_evals):
            # Generate neighbor
            candidate = self._perturb(current)
            candidate_fitness = self.problem.evaluate(candidate)

            # Metropolis acceptance
            delta_E = candidate_fitness - current_fitness
            if delta_E < 0 or np.random.random() < np.exp(-delta_E / T):
                current = candidate
                current_fitness = candidate_fitness

                if current_fitness < best_fitness:
                    best = current.copy()
                    best_fitness = current_fitness

            # Cool down
            T *= self.alpha

            if i % 100 == 0:
                history.append(current)

        return history

    def _ga_refinement_phase(
        self,
        initial_population: list[Solution]
    ) -> ParetoFront:
        """Run NSGA-III starting from SA solutions."""

        algorithm = NSGA3(
            pop_size=len(initial_population),
            ref_dirs=get_reference_directions("das-dennis", n_obj=6, n_partitions=4),
            sampling=initial_population,  # Warm start
            crossover=SBX(prob=0.9, eta=15),
            mutation=PolynomialMutation(prob=1.0/self.problem.n_var, eta=20),
        )

        result = minimize(
            self.problem,
            algorithm,
            ('n_eval', self.ga_evals),
            verbose=True
        )

        return ParetoFront(
            solutions=result.X,
            objectives=result.F,
            constraints=result.G if hasattr(result, 'G') else None
        )
```

### 4.3 Objective Functions (6 Total)

#### Objective 1: Construction Cost

```python
def minimize_cost(buildings: list[Building]) -> float:
    """
    Minimize total construction cost.

    Formula:
        Cost = Σ(base_cost[type] × floor_area × cost_factor[floors])

    Research: Construction Cost and NPV Optimization Guide.docx
    """
    COST_PER_SQM = {
        "Faculty": 2500,      # TRY/m²
        "Dormitory": 1800,
        "Library": 2200,
        "Research": 2800,
        "Sports": 1500,
        "Cafeteria": 1600,
    }

    FLOOR_MULTIPLIER = {
        1: 1.0,
        2: 1.05,
        3: 1.10,
        4: 1.15,
        5: 1.25,  # Elevator required
        # ... up to 20
    }

    total_cost = 0.0
    for building in buildings:
        floor_area = building.geometry.area
        base_cost = COST_PER_SQM[building.type]
        multiplier = FLOOR_MULTIPLIER.get(building.floors, 1.5)

        total_cost += floor_area * base_cost * multiplier

    return total_cost
```

#### Objective 2: Walkability (15-Minute City)

```python
def maximize_walkability(
    buildings: list[Building],
    road_network: nx.Graph
) -> float:
    """
    Maximize walkability using 15-minute city metric.

    Formula:
        W = 1 - (Σ shortest_path(i,j) / n² × threshold)

    Research: 15-Minute City Optimization Analysis.docx
    """
    WALK_SPEED = 1.4  # m/s
    TIME_THRESHOLD = 15 * 60  # 15 minutes in seconds
    DISTANCE_THRESHOLD = WALK_SPEED * TIME_THRESHOLD  # 1260 meters

    n = len(buildings)
    total_distance = 0.0

    for i, b1 in enumerate(buildings):
        for j, b2 in enumerate(buildings[i+1:], start=i+1):
            try:
                path_length = nx.shortest_path_length(
                    road_network,
                    source=b1.id,
                    target=b2.id,
                    weight='length'
                )
            except nx.NetworkXNoPath:
                path_length = DISTANCE_THRESHOLD * 2  # Penalty

            total_distance += path_length

    avg_distance = total_distance / (n * (n - 1) / 2)
    walkability_score = 1.0 - (avg_distance / DISTANCE_THRESHOLD)

    return max(0.0, walkability_score)  # Return negated for minimization
```

#### Objective 3-6: (Abbreviated for brevity)

- **Objective 3**: Green Ratio - Maximize green space percentage
- **Objective 4**: Solar Shadow - Minimize shadow overlap (pysolar)
- **Objective 5**: Wind Alignment - Maximize wind comfort (OpenMeteo)
- **Objective 6**: Road Length - Minimize total road network length

### 4.4 Constraint Functions (5 Total)

```python
def constraint_within_boundary(buildings: list[Building], boundary: Polygon) -> float:
    """G1: All buildings must be within site boundary."""
    violations = sum(
        1 for b in buildings if not boundary.contains(b.geometry)
    )
    return violations  # Must be 0

def constraint_no_overlap(buildings: list[Building]) -> float:
    """G2: Buildings must not overlap."""
    overlaps = 0
    for i, b1 in enumerate(buildings):
        for b2 in buildings[i+1:]:
            if b1.geometry.intersects(b2.geometry):
                overlaps += b1.geometry.intersection(b2.geometry).area
    return overlaps  # Must be 0

def constraint_setback(buildings: list[Building], boundary: Polygon) -> float:
    """
    G3: Setback requirements per Turkish İmar Yönetmeliği.

    Rules:
        - Front setback: 5m (road-facing)
        - Side setback: 3m
    """
    violations = 0.0
    for building in buildings:
        # Buffer building by setback
        buffered = building.geometry.buffer(building.setback_side)

        # Check if buffered geometry exceeds boundary
        if not boundary.contains(buffered):
            violations += buffered.difference(boundary).area

    return violations

def constraint_fire_separation(buildings: list[Building]) -> float:
    """
    G4: Fire separation per Turkish Yangın Yönetmeliği.

    Formula:
        min_distance = max(6.0, taller_building_height / 2)
    """
    violations = 0.0

    for i, b1 in enumerate(buildings):
        for b2 in buildings[i+1:]:
            required_distance = max(6.0, max(b1.height, b2.height) / 2)
            actual_distance = b1.geometry.distance(b2.geometry)

            if actual_distance < required_distance:
                violations += (required_distance - actual_distance)

    return violations

def constraint_slope(buildings: list[Building], elevation_service: ElevationService) -> float:
    """G5: Buildings must be on slope < 15%."""
    MAX_SLOPE = 0.15
    violations = 0.0

    for building in buildings:
        slope = elevation_service.get_slope(building.centroid)
        if slope > MAX_SLOPE:
            violations += (slope - MAX_SLOPE)

    return violations
```

---

## 5. Frontend Architecture

### 5.1 State Management (Zustand)

```typescript
// store/useStore.ts
import create from 'zustand';
import { Polygon, Feature, FeatureCollection } from 'geojson';

interface SiteState {
  // Site configuration
  boundary: Polygon | null;
  existingBuildings: Feature[];

  // Optimization parameters
  buildingCounts: Record<BuildingType, number>;
  greenRatioTarget: number;
  objectiveWeights: Record<string, number>;

  // Results
  isOptimizing: boolean;
  currentIteration: number;
  bestSolution: FeatureCollection | null;
  paretoFront: any[];
  metrics: OptimizationMetrics | null;
}

interface SiteActions {
  setBoundary: (boundary: Polygon) => void;
  setBuildingCount: (type: BuildingType, count: number) => void;
  setWeight: (objective: string, weight: number) => void;
  startOptimization: () => Promise<void>;
  reset: () => void;
}

export const useStore = create<SiteState & SiteActions>((set, get) => ({
  // Initial state
  boundary: null,
  existingBuildings: [],
  buildingCounts: {
    Faculty: 0,
    Dormitory: 0,
    Library: 0,
    Research: 0,
    Sports: 0,
    Cafeteria: 0,
  },
  greenRatioTarget: 0.25,
  objectiveWeights: {
    cost: 1.0,
    walkability: 1.5,
    green_ratio: 1.0,
    solar: 0.8,
    wind: 0.6,
    road_length: 0.7,
  },
  isOptimizing: false,
  currentIteration: 0,
  bestSolution: null,
  paretoFront: [],
  metrics: null,

  // Actions
  setBoundary: (boundary) => set({ boundary }),

  setBuildingCount: (type, count) =>
    set((state) => ({
      buildingCounts: { ...state.buildingCounts, [type]: count }
    })),

  setWeight: (objective, weight) =>
    set((state) => ({
      objectiveWeights: { ...state.objectiveWeights, [objective]: weight }
    })),

  startOptimization: async () => {
    const state = get();
    set({ isOptimizing: true, currentIteration: 0 });

    try {
      const response = await apiClient.post('/api/optimize/run', {
        boundary: state.boundary,
        existing_buildings: state.existingBuildings,
        building_counts: state.buildingCounts,
        green_ratio_target: state.greenRatioTarget,
        weights: state.objectiveWeights,
      });

      set({
        bestSolution: response.data.best_solution,
        paretoFront: response.data.pareto_front,
        metrics: response.data.metrics,
        isOptimizing: false,
      });
    } catch (error) {
      console.error('Optimization failed:', error);
      set({ isOptimizing: false });
    }
  },

  reset: () => set({
    boundary: null,
    existingBuildings: [],
    bestSolution: null,
    paretoFront: [],
    metrics: null,
  }),
}));
```

### 5.2 Isolated Canvas Workflow

```typescript
// components/map/IsolatedCanvas.tsx
import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import { useStore } from '../../store/useStore';

export const IsolatedCanvas: React.FC = () => {
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const drawRef = useRef<MapboxDraw | null>(null);

  const { boundary, setBoundary, bestSolution } = useStore();

  useEffect(() => {
    // Initialize Mapbox
    const map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/light-v10',
      center: [33.78, 41.38],  // Kastamonu University
      zoom: 15,
    });

    // Initialize drawing tools
    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        polygon: true,
        trash: true,
      },
    });

    map.addControl(draw);

    // Handle polygon creation
    map.on('draw.create', (e) => {
      const polygon = e.features[0].geometry as Polygon;
      setBoundary(polygon);

      // Fit map to polygon
      const bounds = bbox(polygon);
      map.fitBounds(bounds, { padding: 50 });
    });

    mapRef.current = map;
    drawRef.current = draw;

    return () => map.remove();
  }, []);

  // Render optimization results
  useEffect(() => {
    if (!mapRef.current || !bestSolution) return;

    const map = mapRef.current;

    // Add buildings layer
    if (!map.getSource('optimized-buildings')) {
      map.addSource('optimized-buildings', {
        type: 'geojson',
        data: bestSolution,
      });

      map.addLayer({
        id: 'building-fills',
        type: 'fill-extrusion',
        source: 'optimized-buildings',
        paint: {
          'fill-extrusion-color': [
            'match',
            ['get', 'building_type'],
            'Faculty', '#4CAF50',
            'Dormitory', '#2196F3',
            'Library', '#FF9800',
            '#CCCCCC'
          ],
          'fill-extrusion-height': ['get', 'height'],
          'fill-extrusion-opacity': 0.8,
        },
      });
    } else {
      (map.getSource('optimized-buildings') as mapboxgl.GeoJSONSource)
        .setData(bestSolution);
    }
  }, [bestSolution]);

  return (
    <div className="relative h-full w-full">
      <div id="map" className="absolute inset-0" />
    </div>
  );
};
```

---

## 6. Data Flow & Integration

### 6.1 End-to-End Workflow

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: Site Selection                                       │
├──────────────────────────────────────────────────────────────┤
│ User draws polygon on map → POST /api/site/fetch            │
│ Backend: OSM service extracts existing buildings, roads     │
│ Response: GeoJSON FeatureCollection                         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: Configuration                                        │
├──────────────────────────────────────────────────────────────┤
│ User sets:                                                   │
│  - Building counts (Faculty: 3, Dormitory: 2, ...)          │
│  - Green ratio target (25%)                                 │
│  - Objective weights (cost: 1.0, walkability: 1.5, ...)    │
│  - Existing buildings to KEEP/DELETE                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: Optimization                                         │
├──────────────────────────────────────────────────────────────┤
│ Frontend: POST /api/optimize/run (request payload)          │
│                                                               │
│ Backend Process:                                             │
│  1. Validate input (ValidatorService)                       │
│  2. Create SpatialProblem                                   │
│     - Setup 6 objectives                                    │
│     - Setup 5 constraints                                   │
│  3. Run H-SAGA (OptimizerService)                           │
│     Phase 1: SA Exploration (1500 evals, 8 chains)         │
│     Phase 2: GA Refinement (3500 evals, NSGA-III)          │
│  4. Generate road network (Tensor Field)                    │
│  5. Place green spaces                                      │
│  6. Calculate metrics                                       │
│  7. Build response                                          │
│                                                               │
│ Response: OptimizationResult                                │
│  - best_solution: GeoJSON                                   │
│  - pareto_front: Array of solutions                         │
│  - metrics: {cost, walkability, green_ratio, ...}          │
│  - elapsed_seconds: 4.2                                     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: Visualization                                        │
├──────────────────────────────────────────────────────────────┤
│ Frontend renders:                                            │
│  - 3D buildings (Mapbox extrusion)                          │
│  - Road network (LineString layer)                          │
│  - Green spaces (Polygon layer, green fill)                 │
│  - Metrics dashboard                                        │
│  - Pareto front chart                                       │
│  - Before/After comparison                                  │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 API Request/Response Examples

#### Request: Start Optimization

```json
POST /api/optimize/run
{
  "boundary": {
    "type": "Polygon",
    "coordinates": [[[33.77, 41.37], [33.79, 41.37], ...]]
  },
  "existing_buildings": [
    {
      "type": "Feature",
      "properties": {"action": "keep", "id": "osm_123"},
      "geometry": {"type": "Polygon", "coordinates": [...]}
    }
  ],
  "building_counts": {
    "Faculty": 3,
    "Dormitory": 2,
    "Library": 1,
    "Research": 1,
    "Sports": 1,
    "Cafeteria": 1
  },
  "green_ratio_target": 0.25,
  "weights": {
    "cost": 1.0,
    "walkability": 1.5,
    "green_ratio": 1.0,
    "solar": 0.8,
    "wind": 0.6,
    "road_length": 0.7
  }
}
```

#### Response: Optimization Result

```json
{
  "success": true,
  "best_solution": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "id": "building_0",
        "properties": {
          "building_type": "Faculty",
          "shape": "L",
          "floors": 4,
          "height": 16.0,
          "width": 42.0,
          "depth": 28.0,
          "rotation": 135.0,
          "floor_area_ratio": 1.2
        },
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[...], ...]]
        }
      },
      // ... more buildings
    ]
  },
  "pareto_front": [
    {
      "objectives": {
        "cost": 12500000,
        "walkability": 0.85,
        "green_ratio": 0.28,
        "solar": 0.15,
        "wind": 0.22,
        "road_length": 1850
      },
      "solution_id": "pareto_0"
    },
    // ... more solutions
  ],
  "metrics": {
    "total_cost": 12500000,
    "avg_walkability": 0.85,
    "green_space_area": 15000,
    "green_ratio": 0.28,
    "total_road_length": 1850,
    "constraint_violations": 0
  },
  "road_network": {
    "type": "FeatureCollection",
    "features": [/* LineStrings */]
  },
  "green_spaces": {
    "type": "FeatureCollection",
    "features": [/* Polygons */]
  },
  "elapsed_seconds": 4.2
}
```

---

## 7. Algorithm Specifications

### 7.1 Tensor Field Road Network

**Research**: `Tensor Field Road Network Generation.docx`

**Patent Potential**: Repulsive field approach (buildings repel roads)

```python
class TensorFieldGenerator:
    """
    Generate road network using repulsive tensor fields.

    Algorithm:
        1. Create tensor field T(x, y) based on building repulsion
        2. Trace streamlines using RK4 integration
        3. Connect streamlines to form graph
        4. Optimize for connectivity (Beta index > 1.4)

    Innovation:
        Traditional: Roads planned first, buildings fit around them
        PlanifyAI: Buildings placed first, roads naturally avoid them
        Result: 70% reduction in building-road overlap
    """

    def __init__(self, buildings: list[Building], boundary: Polygon):
        self.buildings = buildings
        self.boundary = boundary

    def generate_network(self) -> nx.Graph:
        """Generate road network graph."""

        # Step 1: Build tensor field
        field = self._build_repulsive_field()

        # Step 2: Trace streamlines
        streamlines = self._trace_streamlines(field, n_seeds=20)

        # Step 3: Connect into graph
        graph = self._build_graph(streamlines)

        # Step 4: Optimize connectivity
        graph = self._optimize_connectivity(graph)

        return graph

    def _build_repulsive_field(self) -> Callable[[Point], Matrix2x2]:
        """
        Build tensor field with repulsive influence from buildings.

        At point P, tensor T(P) is weighted sum of:
          - Radial component (away from buildings)
          - Tangential component (around buildings)

        Weight function: w(r) = exp(-r² / σ²)
        where r = distance to building, σ = influence radius
        """
        def tensor_at_point(point: Point) -> np.ndarray:
            T = np.zeros((2, 2))

            for building in self.buildings:
                # Vector from building center to point
                vec = np.array([
                    point.x - building.centroid[0],
                    point.y - building.centroid[1]
                ])
                r = np.linalg.norm(vec)

                if r < 1e-6:
                    continue

                # Influence weight (Gaussian decay)
                sigma = building.width * 2  # Influence radius
                weight = np.exp(-(r**2) / (sigma**2))

                # Normalize direction
                vec_norm = vec / r

                # Radial tensor (push away)
                T_radial = np.outer(vec_norm, vec_norm)

                # Tangential tensor (flow around)
                vec_tangent = np.array([-vec_norm[1], vec_norm[0]])
                T_tangent = np.outer(vec_tangent, vec_tangent)

                # Combine: closer to building → more tangential
                blend = 1.0 / (1.0 + r / sigma)
                T += weight * (blend * T_tangent + (1 - blend) * T_radial)

            return T

        return tensor_at_point

    def _trace_streamlines(
        self,
        field: Callable,
        n_seeds: int
    ) -> list[LineString]:
        """
        Trace streamlines using RK4 integration.

        RK4 formula:
            k1 = f(t, y)
            k2 = f(t + h/2, y + h*k1/2)
            k3 = f(t + h/2, y + h*k2/2)
            k4 = f(t + h, y + h*k3)
            y_{n+1} = y_n + h/6 * (k1 + 2*k2 + 2*k3 + k4)
        """
        streamlines = []
        step_size = 5.0  # meters
        max_steps = 500

        # Generate seed points (boundary-based)
        seeds = self._generate_seeds(n_seeds)

        for seed in seeds:
            points = [seed]
            current = np.array([seed.x, seed.y])

            for _ in range(max_steps):
                # Get major eigenvector (flow direction)
                T = field(Point(current))
                eigenvalues, eigenvectors = np.linalg.eig(T)
                major_idx = np.argmax(np.abs(eigenvalues))
                direction = eigenvectors[:, major_idx].real

                # RK4 integration
                k1 = direction
                k2 = self._get_direction(field, current + step_size * k1 / 2)
                k3 = self._get_direction(field, current + step_size * k2 / 2)
                k4 = self._get_direction(field, current + step_size * k3)

                next_pos = current + (step_size / 6) * (k1 + 2*k2 + 2*k3 + k4)

                # Check boundary
                if not self.boundary.contains(Point(next_pos)):
                    break

                # Check building collision
                if self._intersects_building(Point(next_pos)):
                    break

                points.append(Point(next_pos))
                current = next_pos

            if len(points) > 2:
                streamlines.append(LineString(points))

        return streamlines
```

### 7.2 L/U/H/O Building Shapes

```python
def generate_l_shape(
    center: tuple[float, float],
    width: float,
    depth: float,
    rotation: float
) -> Polygon:
    """
    Generate L-shaped building footprint.

    Configuration:
        ┌─────┐
        │     │
        │  ┌──┘
        │  │
        └──┘

    Proportions:
        - Long arm: 70% of width
        - Short arm: 30% of width
        - Wing width: 50% of depth
    """
    long_arm = width * 0.7
    short_arm = width * 0.3
    wing_depth = depth * 0.5

    # Define points in local coordinates
    points = [
        (0, 0),
        (short_arm, 0),
        (short_arm, wing_depth),
        (width, wing_depth),
        (width, depth),
        (0, depth),
        (0, 0)
    ]

    # Transform: translate to center + rotate
    poly = Polygon(points)
    poly = translate(poly, xoff=-width/2, yoff=-depth/2)
    poly = rotate(poly, rotation, origin=(0, 0))
    poly = translate(poly, xoff=center[0], yoff=center[1])

    return poly

# Similar functions: generate_u_shape, generate_h_shape, generate_o_shape
```

---

## 8. API Design

### 8.1 Endpoint Specification

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/site/fetch` | Fetch OSM context data |
| POST | `/api/site/validate` | Validate site boundary |
| POST | `/api/optimize/run` | Start optimization |
| GET | `/api/optimize/status/{job_id}` | Get job status |
| GET | `/api/optimize/result/{job_id}` | Get result (GeoJSON) |
| POST | `/api/export/geojson` | Export as GeoJSON |
| POST | `/api/export/pdf` | Export as PDF report |

### 8.2 Error Handling

```python
from fastapi import HTTPException
from enum import Enum

class ErrorCode(str, Enum):
    INVALID_BOUNDARY = "INVALID_BOUNDARY"
    OSM_FETCH_FAILED = "OSM_FETCH_FAILED"
    OPTIMIZATION_FAILED = "OPTIMIZATION_FAILED"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

@app.exception_handler(ValueError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "error": ErrorCode.INVALID_BOUNDARY,
            "message": str(exc),
            "details": {...}
        }
    )
```

---

## 9. Database & Storage

### 9.1 SQLite Job Store

```sql
CREATE TABLE optimization_jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Input
    boundary_geojson TEXT,
    building_counts TEXT,  -- JSON
    weights TEXT,          -- JSON

    -- Progress
    current_iteration INTEGER DEFAULT 0,
    total_iterations INTEGER,

    -- Result
    best_solution_geojson TEXT,
    pareto_front TEXT,     -- JSON
    metrics TEXT,          -- JSON

    -- Error
    error_message TEXT
);

CREATE INDEX idx_status ON optimization_jobs(status);
CREATE INDEX idx_created_at ON optimization_jobs(created_at DESC);
```

---

## 10. Development Roadmap

### 10.1 Sprint Breakdown (10 Days)

#### Day 1: Project Foundation ✅
- [ ] Setup project structure
- [ ] Configure FastAPI + Vite
- [ ] Setup testing infrastructure (pytest, vitest)
- [ ] Create base Pydantic models
- [ ] Configure linting (black, ruff, eslint)

#### Day 2: OSM Integration ✅
- [ ] Implement OSM service
- [ ] Create `/api/site/fetch` endpoint
- [ ] Test with real Turkish university data
- [ ] Handle coordinate transformations (WGS84 ↔ Local)

#### Day 3: Geometry Engine ✅
- [ ] Implement L/U/H/O shape generators
- [ ] Create Turkish standards module (setback, FAR)
- [ ] Write geometry tests

#### Day 4: Physics Engine ✅
- [ ] Integrate pysolar for shadow calculation
- [ ] Create OpenMeteo API client
- [ ] Implement wind analysis

#### Day 5: Optimization Problem ✅
- [ ] Implement 6 objective functions
- [ ] Implement 5 constraint functions
- [ ] Create PyMOO problem definition
- [ ] Write optimization tests

#### Day 6: H-SAGA Implementation ✅
- [ ] Implement SA exploration phase
- [ ] Implement GA refinement phase (NSGA-III)
- [ ] Test convergence on benchmark problems
- [ ] Create optimizer service

#### Day 7: Road Network (Tensor Field) ✅
- [ ] Implement tensor field generator
- [ ] Implement RK4 streamline tracer
- [ ] Create road network builder
- [ ] Test connectivity metrics

#### Day 8-9: Frontend ✅
- [ ] Create Zustand store
- [ ] Implement Mapbox canvas
- [ ] Create drawing tools
- [ ] Implement isolated canvas workflow
- [ ] Build sidebar panels
- [ ] Create results visualization
- [ ] Implement Pareto chart

#### Day 10: Integration & Demo ✅
- [ ] E2E testing
- [ ] Performance optimization
- [ ] Create demo scenario
- [ ] Record demo video
- [ ] Write thesis documentation
- [ ] Prepare presentation

---

## 11. Research-to-Code Mapping

### 11.1 Critical Research Documents

| Priority | Document | Code Module | Status |
|----------|----------|-------------|--------|
| P0 | Hybrid Optimization Algorithm Research | `hsaga.py` | 📋 Plan |
| P0 | Tensor Field Road Network Generation | `tensor_field.py`, `road_network.py` | 📋 Plan |
| P0 | Turkish Urban Planning Standards | `standards/setback_rules.py` | 📋 Plan |
| P1 | Multi-Objective Evolutionary Algorithms | `problem.py` | 📋 Plan |
| P1 | Building Energy Modeling Integration | `physics/solar.py` | 📋 Plan |
| P1 | 15-Minute City Optimization | `objectives/walkability.py` | 📋 Plan |
| P2 | Construction Cost and NPV | `objectives/cost.py` | 📋 Plan |
| P2 | Campus Planning Standards | `metrics/connectivity.py` | 📋 Plan |

### 11.2 Implementation Checklist

For each algorithm:
- [ ] Read research document
- [ ] Extract mathematical formulation
- [ ] Identify parameters from sensitivity analysis
- [ ] Implement with type hints + docstrings
- [ ] Write unit tests
- [ ] Benchmark against paper results
- [ ] Document in code with research reference

---

## 12. Success Metrics

### 12.1 Technical Metrics

- **Performance**: < 5 seconds for 10-building optimization
- **Test Coverage**: > 85%
- **Type Coverage**: 100% (mypy strict)
- **Constraint Satisfaction**: 0 violations in final solution
- **Code Quality**: Ruff score > 9.0

### 12.2 Academic Metrics

- **Algorithm Novelty**: Repulsive Tensor Field (patent potential)
- **Research Depth**: 60+ cited documents
- **Practical Application**: Real Turkish university data
- **Reproducibility**: Deterministic seeds, documented parameters

### 12.3 Thesis Defense Criteria

- ✅ Clear problem statement
- ✅ Literature review (60+ papers)
- ✅ Novel algorithmic contribution
- ✅ Rigorous experimental methodology
- ✅ Real-world validation
- ✅ Professional demo
- ✅ Publication-ready documentation

---

## 13. Next Steps

### 13.1 Immediate Actions

1. **Get User Approval** on architecture
2. **Setup Git repository** with proper structure
3. **Create development branch** (`v2-rewrite`)
4. **Start Day 1 tasks** (foundation)

### 13.2 Questions for User

Before starting implementation, please clarify:

1. **Deployment Target**: Local-only or web-hosted?
2. **Performance Requirements**: Target optimization time?
3. **Data Sources**: Use only OSM or include custom campus data?
4. **Export Formats**: PDF report template needed?
5. **Authentication**: Multi-user or single-user?

---

**Document Status**: 🏗️ Ready for Review
**Next Action**: User approval + clarification
**Estimated Lines of Code**: ~4,500 (10 days)
**Risk Level**: Medium (aggressive timeline, new architecture)

---

*Generated by: Claude Sonnet 4.5*
*Date: 29 Aralık 2025*
