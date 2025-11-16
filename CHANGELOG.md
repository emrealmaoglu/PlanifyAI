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

