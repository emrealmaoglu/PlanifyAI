# Tensor Field Theory Notes (for Day 2)

## Key Concepts

### 1. Tensor Field Basics

**Tensor:** 2x2 symmetric matrix at each grid point

```
T = [a  b]
    [b  c]
```

- **Eigenvectors:** Major (θ₁) and Minor (θ₂) directions
  - Major: Preferred road direction
  - Minor: Perpendicular constraint

- **Eigenvalues:** Anisotropy measure
  - λ₁ > λ₂: Strong directional preference
  - λ₁ ≈ λ₂: Isotropic (no preference)

### 2. Semantic Extension (Patent-Pending)

Building-type weights influence tensor field:

- **Health:** ω = 2.5 (highest priority)
- **Commercial:** ω = 2.0
- **Educational:** ω = 1.5
- **Administrative:** ω = 1.3
- **Social:** ω = 1.2
- **Recreational:** ω = 1.1
- **Residential:** ω = 1.0

**Novel Contribution:** Building types create semantic clusters that guide road network topology, not just geometric proximity.

### 3. RK4 Integration

4-stage Runge-Kutta for streamline tracing:

```
k₁ = f(tₙ, yₙ)
k₂ = f(tₙ + h/2, yₙ + h·k₁/2)
k₃ = f(tₙ + h/2, yₙ + h·k₂/2)
k₄ = f(tₙ + h, yₙ + h·k₃)

yₙ₊₁ = yₙ + h/6 · (k₁ + 2k₂ + 2k₃ + k₄)
```

Benefits:
- Smooth curves (4th order accuracy)
- No oscillations
- Adapts to tensor field topology

### 4. Singularity Detection

**Critical Points:** Where tensor eigenvalues are zero

Types:
- **Saddle points:** Road intersections
- **Sources/Sinks:** Building entrances
- **Vortices:** Roundabouts

Detection method:
1. Compute eigenvalues at each grid point
2. Find near-zero eigenvalues
3. Classify singularity type
4. Generate roads to/from singularities

## Implementation Plan (Tomorrow)

### Phase 1: Tensor Field Generation
1. Grid-based tensor field generation
2. Building influence computation
3. Distance-based weighting
4. Semantic type weighting (patent-pending)

### Phase 2: Analysis
1. Eigenvector decomposition
2. Singularity detection (critical points)
3. Field visualization

### Phase 3: Road Generation
1. RK4 streamline integration
2. Seed point selection
3. Streamline tracing
4. Network topology generation

## References

- Chen et al. (2008). "Tensor field design for architectural layouts."
- Li et al. (2025). "Semantic tensor fields for urban planning."

## Code Structure (Day 2)

```python
# src/algorithms/semantic_tensor.py
class SemanticTensorField:
    def generate(...)  # Phase 1
    def compute_singularities(...)  # Phase 2
    def trace_streamlines(...)  # Phase 3 (via RK4)

# src/algorithms/road_generator.py
class RoadGenerator:
    def __init__(self, tensor_field)
    def rk4_integrate(...)  # RK4 implementation
    def generate_network(...)  # Full network
```

---

**Status:** Ready for Day 2 implementation 🚀

