# Backend Refactoring Plan

**Goal**: Eliminate god classes and improve backend modularity

**Date**: December 31, 2025

## Current State Analysis

### God Classes Identified

| File | Lines | Issues | Priority |
|------|-------|--------|----------|
| hsaga.py | 1,351 | Monolithic algorithm, multiple responsibilities | P0 |
| orchestrator.py | 899 | Complex pipeline logic, mixed concerns | P1 |
| osm_service.py | 829 | Heavy OSM integration, no separation | P1 |
| spatial_problem.py | 791 | Large problem definition, constraint mixing | P2 |
| critique.py | 666 | AI critique logic, too many methods | P2 |

### Python Module Size Guidelines

- ✅ **Good**: < 300 lines
- ⚠️ **Warning**: 300-500 lines
- ❌ **God Class**: > 500 lines

## Issues with Current Architecture

### 1. hsaga.py (1,351 lines) - CRITICAL

**Current Structure**:
```
hsaga.py
├── HSAGA class (main algorithm)
├── Dominance checking
├── Crowding distance
├── Tournament selection
├── Crossover operations
├── Mutation operations
├── Archive management
├── Diversity maintenance
└── Statistics tracking
```

**Problems**:
- Violates Single Responsibility Principle
- Hard to test individual components
- Difficult to swap algorithm variants
- No clear separation of concerns

**Target Structure**:
```
algorithms/
├── hsaga.py (< 200 lines) - Main orchestrator
├── selection/
│   ├── tournament.py (< 150 lines)
│   └── dominance.py (< 150 lines)
├── operators/
│   ├── crossover.py (< 200 lines)
│   └── mutation.py (< 200 lines)
├── diversity/
│   ├── crowding.py (< 150 lines)
│   └── archive.py (< 200 lines)
└── metrics/
    └── statistics.py (< 150 lines)
```

**Benefits**:
- Each module has single responsibility
- Easy to test in isolation
- Can swap components (e.g., different crossover)
- Clear API boundaries

### 2. orchestrator.py (899 lines) - HIGH PRIORITY

**Current Structure**:
```
orchestrator.py
├── Pipeline initialization
├── Context fetching
├── Road generation
├── Building placement
├── Optimization loop
├── Result validation
├── Export formatting
└── Error handling
```

**Problems**:
- Pipeline and business logic mixed
- Hard to add new pipeline stages
- Complex error handling scattered
- Difficult to test stages independently

**Target Structure**:
```
pipeline/
├── orchestrator.py (< 150 lines) - Composition only
├── stages/
│   ├── context_stage.py (< 150 lines)
│   ├── road_stage.py (< 150 lines)
│   ├── building_stage.py (< 150 lines)
│   ├── optimization_stage.py (< 200 lines)
│   └── export_stage.py (< 150 lines)
├── validators/
│   └── result_validator.py (< 150 lines)
└── pipeline_runner.py (< 200 lines)
```

### 3. osm_service.py (829 lines)

**Current Issues**:
- OSM API calls mixed with data processing
- Feature extraction logic embedded
- No caching strategy
- Heavy geometry operations

**Target**:
```
geometry/
├── osm_service.py (< 200 lines) - API client only
├── osm_parser.py (< 250 lines) - Data parsing
├── osm_cache.py (< 150 lines) - Caching layer
└── feature_extractor.py (< 250 lines) - Feature processing
```

## Refactoring Strategy

### Phase 1: Extract Algorithm Components from hsaga.py (Week 1)

**Step 1: Extract Selection Operators**
```python
# Before: In hsaga.py
def tournament_selection(population, tournament_size):
    # 50 lines of selection logic
    pass

# After: selection/tournament.py
class TournamentSelector:
    def __init__(self, tournament_size: int = 2):
        self.tournament_size = tournament_size

    def select(self, population: List[Individual]) -> Individual:
        """Select individual via tournament."""
        # Clean, testable implementation
        pass
```

**Step 2: Extract Genetic Operators**
```python
# Before: In hsaga.py
def sbx_crossover(parent1, parent2, eta=15):
    # 80 lines of crossover logic
    pass

# After: operators/crossover.py
class SBXCrossover:
    """Simulated Binary Crossover operator."""

    def __init__(self, eta: float = 15.0):
        self.eta = eta

    def cross(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Apply SBX crossover."""
        pass
```

**Expected Outcome**: hsaga.py reduced to ~200 lines (just composition)

### Phase 2: Extract Pipeline Stages from orchestrator.py (Week 2)

**Pipeline Stage Pattern**:
```python
# pipeline/stages/base.py
from abc import ABC, abstractmethod

class PipelineStage(ABC):
    """Base class for pipeline stages."""

    @abstractmethod
    def execute(self, context: dict) -> dict:
        """Execute stage and return updated context."""
        pass

    @abstractmethod
    def validate(self, context: dict) -> bool:
        """Validate stage prerequisites."""
        pass

# pipeline/stages/context_stage.py
class ContextFetchStage(PipelineStage):
    def execute(self, context: dict) -> dict:
        """Fetch OSM context data."""
        # Clean implementation
        return context

    def validate(self, context: dict) -> bool:
        return 'latitude' in context and 'longitude' in context
```

**New Orchestrator**:
```python
# pipeline/orchestrator.py (< 150 lines)
class PipelineOrchestrator:
    def __init__(self):
        self.stages = [
            ContextFetchStage(),
            RoadGenerationStage(),
            BuildingPlacementStage(),
            OptimizationStage(),
            ExportStage()
        ]

    def run(self, initial_context: dict) -> dict:
        """Run all pipeline stages."""
        context = initial_context

        for stage in self.stages:
            if not stage.validate(context):
                raise PipelineError(f"{stage.__class__.__name__} validation failed")

            context = stage.execute(context)

        return context
```

### Phase 3: Split OSM Service (Week 3)

**Separation of Concerns**:
```python
# geometry/osm_client.py
class OSMClient:
    """HTTP client for OSM Overpass API."""

    def fetch_features(self, bbox: BoundingBox) -> str:
        """Fetch raw OSM data."""
        pass

# geometry/osm_parser.py
class OSMParser:
    """Parse OSM JSON to GeoJSON features."""

    def parse(self, osm_data: str) -> FeatureCollection:
        """Parse OSM data to structured features."""
        pass

# geometry/osm_cache.py
class OSMCache:
    """Cache OSM responses to avoid repeated API calls."""

    def get(self, key: str) -> Optional[str]:
        pass

    def set(self, key: str, value: str, ttl: int = 3600):
        pass

# geometry/osm_service.py (orchestrator)
class OSMService:
    """High-level OSM service (< 200 lines)."""

    def __init__(self):
        self.client = OSMClient()
        self.parser = OSMParser()
        self.cache = OSMCache()

    def get_context(self, lat: float, lon: float, radius: int) -> FeatureCollection:
        """Get campus context with caching."""
        cache_key = f"{lat}_{lon}_{radius}"

        cached = self.cache.get(cache_key)
        if cached:
            return self.parser.parse(cached)

        data = self.client.fetch_features(...)
        self.cache.set(cache_key, data)

        return self.parser.parse(data)
```

## Design Patterns to Apply

### 1. Strategy Pattern for Algorithms

Replace monolithic algorithm with swappable strategies:

```python
# algorithms/base.py
class OptimizationAlgorithm(ABC):
    @abstractmethod
    def optimize(self, problem: Problem) -> Solution:
        pass

# algorithms/hsaga.py
class HSAGA(OptimizationAlgorithm):
    def __init__(self, selector: Selector, crossover: Crossover, mutation: Mutation):
        self.selector = selector
        self.crossover = crossover
        self.mutation = mutation

    def optimize(self, problem: Problem) -> Solution:
        # Clean orchestration logic
        pass

# algorithms/nsga3.py
class NSGA3(OptimizationAlgorithm):
    # Alternative algorithm with same interface
    pass
```

**Usage**:
```python
# Easy to swap algorithms
algorithm = HSAGA(
    selector=TournamentSelector(size=2),
    crossover=SBXCrossover(eta=15),
    mutation=PolynomialMutation(eta=20)
)

result = algorithm.optimize(problem)
```

### 2. Pipeline Pattern for Orchestration

```python
# Pipeline with clear stages
pipeline = Pipeline([
    ContextFetchStage(),
    RoadGenerationStage(),
    OptimizationStage()
])

result = pipeline.run(initial_context)
```

### 3. Repository Pattern for Data Access

```python
# Instead of direct OSM API calls everywhere
class BuildingRepository:
    def __init__(self, osm_service: OSMService):
        self.osm_service = osm_service

    def get_existing_buildings(self, bbox: BoundingBox) -> List[Building]:
        """Get buildings with business logic abstraction."""
        features = self.osm_service.get_context(...)
        return [self._to_building(f) for f in features if f.type == 'building']
```

### 4. Dependency Injection

```python
# Instead of hardcoded dependencies
class OptimizationService:
    def __init__(
        self,
        algorithm: OptimizationAlgorithm,
        validator: ResultValidator,
        exporter: ResultExporter
    ):
        self.algorithm = algorithm
        self.validator = validator
        self.exporter = exporter
```

## Testing Strategy

### Before Refactor
```python
# Hard to test: Need to mock entire 1,351-line class
def test_hsaga():
    hsaga = HSAGA(...)
    # How do we test just crossover?
    # How do we test just selection?
    # Everything is coupled!
```

### After Refactor
```python
# Easy to test: Each component in isolation
def test_sbx_crossover():
    crossover = SBXCrossover(eta=15)
    parent1 = Individual([1, 2, 3])
    parent2 = Individual([4, 5, 6])

    child1, child2 = crossover.cross(parent1, parent2)

    assert child1.genes != parent1.genes  # Offspring differs
    assert len(child1.genes) == len(parent1.genes)  # Same length

def test_tournament_selector():
    selector = TournamentSelector(size=2)
    population = [Individual(...) for _ in range(10)]

    selected = selector.select(population)

    assert selected in population
    # Test tournament logic in isolation
```

## Performance Improvements

### 1. Lazy Loading
```python
# Before: Load everything upfront
class HSAGA:
    def __init__(self):
        self.all_operators = [...]  # Heavy initialization

# After: Load on demand
class HSAGA:
    def __init__(self):
        self._operators = None

    @property
    def operators(self):
        if self._operators is None:
            self._operators = self._load_operators()
        return self._operators
```

### 2. Caching
```python
# Add caching to expensive operations
class OSMService:
    @lru_cache(maxsize=128)
    def get_context(self, lat: float, lon: float, radius: int):
        # Cached responses
        pass
```

### 3. Async I/O
```python
# For API calls and I/O operations
class OSMClient:
    async def fetch_features_async(self, bbox: BoundingBox):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()
```

## Migration Plan

### Week 1: HSAGA Decomposition
- **Day 1-2**: Extract selection operators
- **Day 3-4**: Extract genetic operators
- **Day 5**: Extract diversity components
- **Result**: hsaga.py < 300 lines

### Week 2: Pipeline Refactoring
- **Day 1-2**: Create stage base class and interfaces
- **Day 3-4**: Extract individual stages
- **Day 5**: Update orchestrator to use stages
- **Result**: orchestrator.py < 200 lines

### Week 3: OSM Service Split
- **Day 1**: Create OSM client
- **Day 2**: Create parser
- **Day 3**: Add caching layer
- **Day 4**: Update service orchestrator
- **Day 5**: Testing and validation
- **Result**: osm_service.py < 250 lines

### Week 4: Testing and Cleanup
- **Day 1-2**: Write unit tests for new components
- **Day 3**: Integration tests for refactored pipeline
- **Day 4**: Performance benchmarks
- **Day 5**: Documentation updates

## Success Metrics

### Code Quality
- ✅ No Python module > 500 lines
- ✅ Average module size < 250 lines
- ✅ Test coverage > 80%
- ✅ Cyclomatic complexity < 10 per function

### Developer Experience
- ✅ Easier to understand individual components
- ✅ Faster to add new algorithm variants
- ✅ Clear separation of concerns
- ✅ Better error messages

### Performance
- ✅ No performance regression
- ✅ Better caching (less API calls)
- ✅ Parallel stage execution potential

## File Structure (After Refactor)

```
backend/core/
├── algorithms/
│   ├── base.py (< 100 lines) - Abstract base
│   ├── hsaga.py (< 200 lines) - Main algorithm orchestrator
│   ├── nsga3.py (< 200 lines) - Alternative algorithm
│   ├── selection/
│   │   ├── tournament.py (< 150 lines)
│   │   └── dominance.py (< 150 lines)
│   ├── operators/
│   │   ├── crossover.py (< 200 lines)
│   │   └── mutation.py (< 200 lines)
│   ├── diversity/
│   │   ├── crowding.py (< 150 lines)
│   │   └── archive.py (< 200 lines)
│   └── metrics/
│       └── statistics.py (< 150 lines)
│
├── pipeline/
│   ├── orchestrator.py (< 150 lines) - Composition only
│   ├── base_stage.py (< 100 lines) - Stage interface
│   ├── stages/
│   │   ├── context_stage.py (< 150 lines)
│   │   ├── road_stage.py (< 150 lines)
│   │   ├── building_stage.py (< 150 lines)
│   │   ├── optimization_stage.py (< 200 lines)
│   │   └── export_stage.py (< 150 lines)
│   ├── validators/
│   │   └── result_validator.py (< 150 lines)
│   └── runner.py (< 200 lines)
│
└── geometry/
    ├── osm/
    │   ├── client.py (< 150 lines) - API client
    │   ├── parser.py (< 250 lines) - Data parsing
    │   ├── cache.py (< 150 lines) - Caching layer
    │   └── service.py (< 200 lines) - High-level orchestrator
    └── repositories/
        ├── building_repo.py (< 150 lines)
        └── road_repo.py (< 150 lines)
```

## Backward Compatibility

### API Stability
All refactoring is internal - public API remains stable:

```python
# External API unchanged
from backend.core.optimization.hsaga import HSAGA

hsaga = HSAGA(...)
result = hsaga.optimize(problem)
```

### Gradual Migration
Each refactoring is independent:
- Week 1: HSAGA (algorithm still works)
- Week 2: Pipeline (API unchanged)
- Week 3: OSM Service (same interface)

## Next Steps

1. ✅ Create this document
2. ⏭️ Extract TournamentSelector from hsaga.py
3. ⏭️ Extract SBXCrossover from hsaga.py
4. ⏭️ Test in isolation
5. ⏭️ Update HSAGA to use new components

---

**Status**: Planning complete, ready for implementation
**Estimated Effort**: 4 weeks
**Impact**: Very High - Cleaner code, better tests, easier maintenance
