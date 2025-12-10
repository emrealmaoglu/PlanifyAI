# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [10.2.1] - 2025-12-10

### Added
- **Process-Based Parallelism**: Implemented `ProcessPoolExecutor` for the Simulated Annealing phase (H-SAGA) to bypass Python GIL.
- **Benchmarks**: New `scripts/test_parallel_speedup.py` for verifying multi-core scaling.
- **P0 Optimization**: Achieved ~2x speedup on 8-core M1/M2 chips for >2000 evaluations.
- **Architecture**: Documented parallel model in `SYSTEM_ARCHITECTURE_AND_ROADMAP.md`.

### Fixed
- **Serialization**: Added `__getstate__`/`__setstate__` to `SpatialOptimizationProblem` for pickle-safe multiprocessing.
- **Dependencies**: Updated `pillow` and `tenacity` versions.

## [0.1.0] - 2025-11-10

### Added - Week 1 MVP

#### Core Algorithm
- H-SAGA hybrid optimizer (Simulated çççAnnealing + Genetic Algorithm)
- Multi-objective optimization (cost, walking distance, adjacency)
- Research-based objective functions
- Fitness evaluator with weighted combination
- Solution representation and management

#### Geospatial Integration
- CampusData dataclass with boundary, constraints, metadata
- CampusDataParser for GeoJSON/Shapefile/dict parsing
- 5 Turkish university campus data files
- Data validation and serialization support

#### Spatial Constraints
- SetbackConstraint (minimum distance from boundary)
- CoverageRatioConstraint (maximum building coverage ratio)
- FloorAreaRatioConstraint (maximum floor area ratio)
- GreenSpaceConstraint (minimum green space ratio)
- ConstraintManager for multi-constraint handling
- Constraint penalties integrated into fitness evaluation

#### Visualization & Export
- CampusPlotter for solution/convergence/objectives visualization
- ResultExporter for GeoJSON/CSV/JSON/Markdown export
- Interactive plots with matplotlib
- Export functionality with download support

#### User Interface
- Streamlit web application
- Campus selection interface
- Building configuration with type distribution
- Algorithm parameter tuning (SA/GA)
- Constraints configuration interface
- Optimization execution with progress tracking
- Results visualization (metrics, charts, plots)
- Solution comparison (history, side-by-side)
- Export functionality (GeoJSON, CSV, Report)

#### Testing
- 196+ tests (unit, integration, edge cases, stress tests)
- 84% code coverage
- Comprehensive test suite with pytest
- Performance benchmarks

#### Documentation
- Comprehensive README
- Architecture documentation
- User guide with examples
- Daily logs for each day
- Week 1 final report (10,000+ words)
- Demo script (5-10 minute flow)
- API documentation

#### Performance
- 10 buildings: <1.2s (30x faster than target)
- 20 buildings: <5s
- 50 buildings: <120s
- Sub-linear scaling
- Memory efficient (<500MB)

### Changed
- None (initial release)

### Deprecated
- None

### Removed
- None

### Fixed
- None (initial release)

### Security
- None (initial release)

---

## [Unreleased]

### Added
- Professional repository structure with phase-based organization
- Git workflow with main/develop/feature branches
- CI/CD pipeline with GitHub Actions
- Comprehensive testing framework (pytest, coverage)
- Code quality tools (black, flake8, mypy)

### Planned for Phase 1
- Semantic tensor fields for road network generation
- Multi-objective Pareto optimization
- Advanced visualization
- Thesis writing
- Patent preparation

---

## [0.0.1] - 2025-11-15

### Added
- **Research Foundation:** 26+ comprehensive research documents
  - Turkish Urban Planning Standards (1,120 lines)
  - Geospatial Data Pipeline Design (1,694 lines)
  - UI/UX & Frontend Stack Analysis (1,403 lines)
  - Campus Planning Metrics & Regulations
  - Competitive Analysis (Autodesk Forma, TestFit)

- **Core Algorithm Prototypes:**
  - H-SAGA hybrid optimization (Simulated Annealing → Genetic Algorithm)
  - Semantic tensor field generation system
  - RK45 streamline integration for road networks
  - Turtle agent pathfinding system
  - ~1000+ lines of working Python code

- **Technology Stack Selection:**
  - Backend: FastAPI + PostGIS
  - Frontend: React + Vite + MapLibre GL
  - Optimization: H-SAGA + NSGA-III (pymoo)
  - Geospatial: OSMnx, Shapely, GeoPandas
  - M1 Optimization: NumPy with Apple Accelerate

- **Academic Planning:**
  - 6-week MVP roadmap
  - Thesis structure outline (60-80 pages, Turkish)
  - Success criteria definition
  - Patent opportunity identification

### Performance
- 50 buildings optimization: <2 minutes target
- Single streamline generation: <100ms target
- Optimized for Apple M1 architecture

### Documentation
- Comprehensive research inventory
- Executive summary
- Gap analysis and future research prompts
- Phase-based development roadmap

---

**Note:** Phase 0 establishes the foundation. Phase 1 will deliver production-ready core engine.

[0.1.0]: https://github.com/emrealmaoglu/planifyai/releases/tag/v0.1.0-week1
