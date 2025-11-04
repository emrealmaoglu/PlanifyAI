# PlanifyAI Architecture Documentation

**Version:** 1.0.0
**Last Updated:** 2025-11-03
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Modules](#core-modules)
4. [Data Flow](#data-flow)
5. [Algorithm Design](#algorithm-design)
6. [Design Decisions](#design-decisions)
7. [Future Extensions](#future-extensions)

---

## Overview

PlanifyAI is a spatial planning optimization system that uses hybrid metaheuristics (H-SAGA) and tensor fields to generate optimal campus layouts. The system optimizes building placement, road networks, and spatial relationships to minimize cost while maximizing accessibility and adjacency satisfaction.

### Key Principles

- **Modular Design**: Clear separation of concerns (algorithms, spatial, data, UI)
- **Type Safety**: Extensive use of Python type hints and mypy checking
- **Testability**: High test coverage (target: 80%+, current: 96%)
- **Performance**: Optimized for M1 Macs (OpenBLAS/Accelerate)
- **Extensibility**: Abstract base classes for algorithm implementations

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                    (Streamlit Web App)                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Controller │  │  Visualizer  │  │   Exporter   │     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Algorithm Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          H-SAGA Optimizer (Abstract Base)            │  │
│  │  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │ Simulated    │  │   Genetic    │                 │  │
│  │  │ Annealing    │→ │  Algorithm   │                 │  │
│  │  └──────────────┘  └──────────────┘                 │  │
│  │  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │  NSGA-III    │  │  Evaluation  │                 │  │
│  │  │  Selection   │  │   Functions  │                 │  │
│  │  └──────────────┘  └──────────────┘                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Spatial Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Tensor     │  │     Road     │  │  Constraints │     │
│  │   Fields     │→ │  Generation  │  │   Engine     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Building   │  │   Solution   │  │   Dataset    │     │
│  │   Models     │  │   Models     │  │   Loaders    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Modules

### 1. `src/algorithms/` - Optimization Algorithms

**Purpose**: Core optimization logic and algorithm implementations.

#### Files

- **`building.py`**: Building data model
  - `BuildingType` enum: Building categories (LIBRARY, EDUCATIONAL, etc.)
  - `Building` dataclass: Building properties (area, floors, position, constraints)
  - Properties: `footprint`, `radius`, `importance`
  - Methods: `distance_to()`, `overlaps_with()`
  - Factory: `create_sample_campus()`

- **`solution.py`**: Solution representation
  - `Solution` class: Spatial layout configuration
  - Position management: `get_position()`, `set_position()`, `get_all_coordinates()`
  - Geometry: `compute_centroid()`, `compute_bounding_box()`
  - Validity: `is_valid(buildings, bounds)` - checks bounds and overlaps
  - Fitness tracking: `fitness`, `objectives`, `metadata`

- **`base.py`**: Abstract optimizer interface
  - `Optimizer` ABC: Base class for all optimizers
  - Abstract methods: `optimize()`, `evaluate_solution()`
  - Statistics tracking: `stats` dict (iterations, evaluations, convergence)
  - Helper: `_log_iteration()` for progress tracking

**Design Pattern**: Abstract Factory + Strategy Pattern

---

### 2. `src/spatial/` - Spatial Planning

**Purpose**: Tensor field generation, road network creation, spatial analysis.

**Status**: To be implemented (Week 2)

**Planned Components**:
- Tensor field generation (Parish & Müller method)
- Road network generation (RK4 integration)
- Spatial constraints engine
- Adjacency analysis

---

### 3. `src/data/` - Data Processing

**Purpose**: Data loading, preprocessing, and export.

**Status**: To be implemented (Week 3)

**Planned Components**:
- Campus dataset loaders (OSM, GeoJSON)
- Building type mappings
- Constraint definitions
- Export utilities (JSON, GeoJSON, Shapefile)

---

### 4. `src/ui/` - User Interface

**Purpose**: Streamlit web application.

**Status**: To be implemented (Week 4)

**Planned Components**:
- Main dashboard
- Interactive map (Folium)
- Parameter controls
- Results visualization (Plotly)
- TR/EN localization

---

### 5. `src/utils/` - Utilities

**Purpose**: Shared utilities and helpers.

**Status**: To be implemented as needed

**Planned Components**:
- Logging configuration
- Configuration management
- File I/O helpers
- Math utilities

---

## Data Flow

### Optimization Pipeline

```
1. Input Preparation
   └─> Buildings list (from dataset or user input)
   └─> Bounds definition (site boundaries)
   └─> Constraint rules (setbacks, adjacencies)

2. Initial Solution Generation
   └─> Random placement within bounds
   └─> Validity check (no overlaps, within bounds)

3. Optimization Loop (H-SAGA)
   ├─> Phase 1: Simulated Annealing
   │   ├─> Random perturbation
   │   ├─> Acceptance criterion (Metropolis)
   │   └─> Temperature cooling
   │
   └─> Phase 2: Genetic Algorithm
       ├─> Selection (tournament/pareto)
       ├─> Crossover (position swapping)
       ├─> Mutation (small perturbations)
       └─> Elitism (keep best solutions)

4. Multi-Objective Evaluation
   └─> Objective 1: Cost (minimize)
   └─> Objective 2: Accessibility (maximize)
   └─> Objective 3: Adjacency satisfaction (maximize)
   └─> NSGA-III ranking and selection

5. Output Generation
   └─> Best solution(s) (Pareto front)
   └─> Road network (tensor field)
   └─> Visualization data
   └─> Export formats (JSON, GeoJSON)
```

---

## Algorithm Design

### H-SAGA (Hybrid Simulated Annealing - Genetic Algorithm)

**Reference**: Li et al. 2025 (Adapted for spatial planning)

#### Phase 1: Simulated Annealing

```python
def simulated_annealing_phase():
    T = initial_temperature
    current = initial_solution()

    while T > min_temperature:
        for iteration in range(iterations_per_temp):
            neighbor = perturb(current)
            delta = evaluate(neighbor) - evaluate(current)

            if accept(delta, T):  # Metropolis criterion
                current = neighbor
                update_best(current)

        T = cool(T)  # Exponential cooling
        log_progress(current)
```

**Key Parameters**:
- Initial temperature: 1.0
- Cooling rate: 0.95-0.99
- Iterations per temperature: 10-50

#### Phase 2: Genetic Algorithm

```python
def genetic_algorithm_phase(population):
    for generation in range(max_generations):
        # Evaluation
        fitness = [evaluate(sol) for sol in population]

        # Selection (NSGA-III)
        parents = select_parents(population, fitness)

        # Crossover
        offspring = crossover(parents)

        # Mutation
        offspring = mutate(offspring)

        # Elitism
        population = select_elite(population + offspring)

        log_generation(population)
```

**Key Parameters**:
- Population size: 50-100
- Crossover rate: 0.8-0.9
- Mutation rate: 0.1-0.2
- Generations: 50-200

### Multi-Objective Optimization (NSGA-III)

**Objectives**:
1. **Cost** (minimize): Construction + land costs
2. **Accessibility** (maximize): Distance to amenities, road connectivity
3. **Adjacency** (maximize): Preferred building type relationships

**Method**: NSGA-III (Non-dominated Sorting Genetic Algorithm III)
- Reference point-based selection
- Pareto dominance ranking
- Reference point adaptation

---

## Design Decisions

### 1. Why Abstract Base Classes?

**Decision**: Use `ABC` for `Optimizer` base class.

**Rationale**:
- Enforces interface consistency
- Enables algorithm swapping (SA, GA, PSO, etc.)
- Supports future algorithm research
- Clear contract for implementations

### 2. Why Dataclasses?

**Decision**: Use `@dataclass` for `Building` and `Solution`.

**Rationale**:
- Clean, readable code
- Built-in `__repr__`, `__eq__`, `__hash__`
- Type hints support
- Minimal boilerplate

### 3. Why Tuple Positions?

**Decision**: Store positions as `(x, y)` tuples, not NumPy arrays.

**Rationale**:
- Immutable (prevents accidental modification)
- Hashable (for sets/dicts)
- Simple and readable
- Easy conversion to NumPy when needed

### 4. Why Separate Spatial Module?

**Decision**: Separate `spatial/` from `algorithms/`.

**Rationale**:
- Clear separation of concerns
- Tensor fields can be used independently
- Easier testing and maintenance
- Supports future GIS integrations

### 5. Why M1 Optimization?

**Decision**: Target M1 Mac optimization (OpenBLAS/Accelerate).

**Rationale**:
- Development machine is M1 Mac
- 2-5x performance improvement
- Production deployment may also use ARM64
- NumPy auto-detects best BLAS

---

## Future Extensions

### Phase 2 Features

1. **3D Visualization**
   - Three.js integration
   - Building height rendering
   - Shadow analysis

2. **Real Data Integration**
   - OSM data import
   - Turkish campus datasets
   - Building cost databases

3. **Advanced Algorithms**
   - Deep Reinforcement Learning (DRL)
   - Graph Neural Networks (GNN)
   - Surrogate modeling

4. **Simulations**
   - Energy modeling (EnergyPlus)
   - Traffic simulation (SUMO)
   - Environmental analysis (UHI, flooding)

5. **External Integrations**
   - BIM (IFC files via IfcOpenShell)
   - GIS (QGIS, ArcGIS plugins)
   - CAD export (DWG, DXF)

---

## Module Dependencies

```
algorithms/ ──┐
              ├─> utils/
spatial/ ─────┤
              ├─> data/
data/ ────────┤
              └─> ui/
ui/ ──────────┘
```

**No circular dependencies**: Clear top-to-bottom flow.

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test each module independently
- Mock dependencies where needed
- Target: 80%+ coverage ✅ (Current: 96%)

### Integration Tests (`tests/integration/`)
- Test module interactions
- End-to-end optimization pipeline
- Real dataset validation

### Benchmarks (`tests/benchmarks/`)
- Performance profiling
- Scalability testing (10, 50, 100, 500 buildings)
- Memory usage monitoring

---

## Performance Targets

### Current (Day 1)
- ✅ Test coverage: 96% (exceeds 80% target)
- ✅ Code quality: Pylint 10.00/10 (exceeds 8.0+ target)

### MVP (Week 5)
- **Runtime**: 50-100 buildings in <2 minutes
- **Memory**: <2 GB peak usage
- **Test Coverage**: ≥80% (maintained)

### Future (Phase 2)
- **Scalability**: 500+ buildings in <10 minutes
- **Parallelization**: Multi-core SA chains
- **GPU Acceleration**: Tensor field generation

---

## Configuration Management

### Current
- `pytest.ini`: Test configuration
- `.pylintrc`: Linting rules
- `mypy.ini`: Type checking
- `.editorconfig`: Editor consistency
- `.pre-commit-config.yaml`: Git hooks

### Future
- `config/optimizer.yaml`: Algorithm parameters
- `config/constraints.yaml`: Building constraints
- `config/ui.yaml`: Interface settings

---

## Documentation Standards

### Code Documentation
- **Docstrings**: Google style (detailed for public APIs)
- **Type Hints**: Required for all function signatures
- **Comments**: Explain "why", not "what"

### API Documentation
- Generated with mkdocs + mkdocstrings
- Auto-generated from docstrings
- Examples for each module

### User Documentation
- Markdown format
- Turkish and English versions
- Step-by-step tutorials

---

**Last Updated**: 2025-11-03
**Next Review**: Week 3 (after tensor field implementation)
