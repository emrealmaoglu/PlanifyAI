# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-10

### Added - Week 1 MVP

#### Core Algorithm
- H-SAGA hybrid optimizer (Simulated Annealing + Genetic Algorithm)
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

### Planned for Week 2
- Semantic tensor fields for road network generation
- Multi-objective Pareto optimization
- Advanced visualization
- Thesis writing
- Patent preparation

---

[0.1.0]: https://github.com/emrealmaoglu/planifyai/releases/tag/v0.1.0-week1
