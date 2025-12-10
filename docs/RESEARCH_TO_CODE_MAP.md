# Research to Code Implementation Map

This document bridges the gap between the `docs/research/` theories and the `backend/` implementation.
It is populated as the research review progresses.

## 1. Tensor Field Road Network Generation
**Source:** `docs/research/Tensor Field Road Network Generation.docx`
**Status:** 🟡 Not Implemented (Ghost Code)

### Core Concepts
- **Traceless 2D Symmetric Tensor:** 2x2 matrix field defining road directionality.
- **Eigenanalysis:** $e_1$ (major) and $e_2$ (minor) eigenvectors guide streamline tracing.
- **RK4 Integration:** 4th-order Runge-Kutta integration for smooth road curves.
- **Typology-Aware Fields:** Use Land Use weights to blend different basis fields (Grid vs. Organic).

### Implementation Plan
- [ ] **Create Module:** `backend/core/geospatial/tensor_field.py`
- [ ] **Class:** `TensorFieldGenerator`
- [ ] **Key Methods:**
    - `get_tensor(point: Tuple[float, float]) -> Matrix2x2`
    - `trace_streamline(seed: Point, direction: Vector) -> LineString` (RK4)
    - `generate_graph(boundary: Polygon, zoning: ZoningMap) -> NetworkGraph`

---

## 2. Evolutionary Constraint Handling
**Source:** `docs/research/Evolutionary Spatial Planning Constraint Handling.docx`
**Status:** 🟠 Partial / Naive Implementation

### Core Concepts
- **Hybrid CHT:** Recommends "Deb's Feasibility Rules" + "Heuristic Repair".
- **Hard Constraints:**
    - **Seismic Separation:** 6.0m (derived from 3m+3m setbacks).
    - **Accessibility:** 1.5m pathway width.
    - **Green Space:** 30% ratio (National Goal).
- **Repair Heuristic:** "Displacement and Aggregation" operator to fix overlaps.

### Implementation Plan
- [ ] **Refactor:** `backend/core/optimization/spatial_problem.py` (Implement Deb's Rules explicitly).
- [ ] **New Module:** `backend/core/constraints/repair.py`
- [ ] **Logic:** Implement `repair_solution(gene)` using the "Displacement" heuristic described in Section III.D.

---

## 3. Campus Planning Standards (Accessibility & Compliance)
**Source:** `docs/research/Campus Planning Standards and Metrics.docx`
**Status:** 🔴 Missing

### Core Concepts
- **Universal Design:** ADAAG (Slope < 5%, Width > 36in) + EN 17210 (Sensory).
- **Quantifiable Metrics:**
    - **2SFCA:** Two-Step Floating Catchment Area for access equality.
    - **Entropy Index:** For land use diversity mix.
    - **Connectivity Indices:** Beta, Gamma, Alpha indices from graph theory.

### Implementation Plan
- [ ] **New Module:** `backend/core/metrics/accessibility.py` (Implement 2SFCA).
- [ ] **New Module:** `backend/core/metrics/connectivity.py` (Implement Kansky's Indices).
- [ ] **Integration:** Add `is_ada_compliant` boolean flag to `PathwayGene`.

---
