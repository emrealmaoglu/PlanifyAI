# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Phase 1 - Turkish Standards Engine)

- Turkish building classification system (Yapı Sınıfları I-A to V-C)
- 2025 construction cost calculator with location and quality factors
- İmar Kanunu (Zoning Law) compliance checker
  - FAR (Emsal) validation
  - Setback requirements checking
  - Parking ratio compliance
  - Green space standards (15 m²/person)
- Comprehensive test suite (147 tests, 97% coverage)
- Performance benchmarks (all targets met)
- Complete API documentation with Turkish/English examples

### Performance

- Building classification: <1ms per call
- Cost calculation: <5ms per call
- Compliance check: <10ms full check
- Memory usage: <10MB total

### Documentation

- Module-level API documentation
- Usage examples (Turkish and English)
- Complete type hints and docstrings

### Added (Phase 1 - Integration)

- **Building Type Mapper:** Maps H-SAGA building types to Turkish classifications
  - 16+ building type mappings
  - Automatic Turkish class assignment
  - Cost per m² lookup

- **Integrated Cost Objective:** Updated cost minimization to use Turkish 2025 rates
  - TurkishCostCalculator integration
  - Location factor support (6 location types)
  - Quality factor support (3 quality levels)
  - Detailed cost breakdown by type and class
  - Fallback mechanism for robustness

- **Turkish Compliance Constraints:** İmar Kanunu compliance checking
  - FAR (Emsal) validation
  - Setback requirements
  - Parking ratio compliance
  - Green space standards
  - Physical constraint validation (overlaps, boundaries)

- **Integration Tests:** Comprehensive end-to-end testing
  - 16+ integration tests
  - Mapper, objectives, constraints coverage
  - Complete pipeline validation

- **Demo Script:** Working integration demonstration
  - 7-building campus example
  - Full cost calculation
  - Compliance checking
  - Turkish classifications

### Changed

- `objectives.py`: Updated to use TurkishCostCalculator
- Optimization module now fully integrated with Turkish Standards

### Performance

- Building mapping: <1ms per building
- Cost calculation: Maintained <5ms with Turkish integration
- Constraint checking: <10ms including compliance

### Documentation

- Integration examples and usage guide
- Complete docstrings for new modules
- Demo script with detailed output

---

**Integration Complete:** Turkish Standards + H-SAGA fully connected and tested.

