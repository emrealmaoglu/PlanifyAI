# ROADMAP_MASTER_V3

> **Version:** 3.0.0 (The "Professional" Release Plan)
> **Status:** Draft / Active
> **Last Updated:** 2025-12-10
> **Authors:** Emre Almaoglu, Antigravity Agent
> **Basis:** `MASTER REVIEW` + `docs/research/RESEARCH_KNOWLEDGE_BASE.md`

This document serves as the **Single Source of Truth** for the engineering and research roadmap of PlanifyAI. It bridges the gap between the "Academic Prototype" (Current State) and the "Scientific Spatial Intelligence Platform" (Target State).

---

## 🏛️ Strategic Directives (The 5 Perspectives)

1.  **Architect (P0):** "Stability before Features." No more God Components. True CPU parallelism is non-negotiable.
2.  **Scientist (P1):** "Theory into Code." If `RESEARCH_KNOWLEDGE_BASE` says SAEA/Tensor Fields, the code must have it. No more "paperware".
3.  **User (UX):** "Don't make me think." The UI must be broken down: Wizard -> Studio -> Dashboard.
4.  **Academic (QA):** "Rigorous Validation." Every algorithm needs a benchmark script (SPOP Suite).
5.  **Product Owner (Risk):** "Liability Shield." Compliance checks (Turkish Standards) must be auditable.

---

## 🗺️ Domain Map & Tracks

| Track ID | Track Name | Focus Area |
| :--- | :--- | :--- |
| **TRK-01** | **BE-Core Optimization** | H-SAGA, Parallelism, Job Orchestration, Tensor Fields |
| **TRK-02** | **BE-Research Integration** | SAEA (Surrogates), Compliance (RASE), UHI/Flood, Financials |
| **TRK-03** | **FE-UX & Visualization** | Architecture Refactor, 3D Studio, Dashboard, XAI |
| **TRK-04** | **Infrastructure & DevOps** | Persistence, Rate Limiting, Testing, Geo-Data pipelines |
| **TRK-05** | **Product & Sector Alignment** | Municipal/Uni Use Cases, Reporting, Export |

---

# 🛤️ Track 01: BE-Core Optimization

### 🚀 Epic: BE-OPT-001 – H-SAGA Parallelization & Runtime Hardening
**Goal:** Fix the "Fake Parallelism" bug and ensure the optimization engine uses 100% of available hardware (Apple Silicon).

*   **Work Package: BE-OPT-001-A – True CPU Parallelism for SA Chains**
    *   **ID:** `BE-OPT-001-A`
    *   **Priority:** **[Done]** (Implemented via `ProcessPoolExecutor`)
    *   **Type:** `BE`
    *   **Scope:** Replace `ThreadPoolExecutor` with `ProcessPoolExecutor` or `joblib` to bypass Python GIL. Geometric operations are CPU-bound.
    *   **Status Note:** True parallelism active. ~1.93x speedup verified on 8-core benchmark with 2000 evals. Overhead dominates for <1000 evals.
    *   **Target Pillars:** Pillar 7.4 (H-SAGA), Pillar 11 (Hardware Opt)
    *   **Related Files:** `backend/core/optimization/hsaga_runner.py`, `backend/core/optimization/spatial_problem.py`
    *   **Risks:** Pickling errors with complex objects (Shapely geometries). Need to ensure `SpatialProblem` is pickleable.
    *   **Acceptance Criteria:**
        *   `hsaga_runner.py` runs N chains on N cores.
        *   Terminal shows 100% CPU usage on all cores during SA phase.
        *   Runtime for 50 buildings / 1000 evals drops by ~6x (on 8-core machine).
    *   **Tasks:**
        *   `[TASK]` Benchmark current serialized runtime (Baseline). (Effort: S)
        *   `[TASK]` Implement `ProcessPoolExecutor` in `SAExplorer.run`. (Effort: M)
        *   `[TASK]` Fix serialization (Pickle) issues for Shapely/R-tree objects. (Effort: M)
        *   `[TASK]` Verify speedup with `scripts/test_parallel_speedup.py`. (Effort: S)

*   **Work Package: BE-OPT-001-B – Fitness Function Vectorization**
    *   **ID:** `BE-OPT-001-B`
    *   **Priority:** **[P1]** (Core Research Alignment)
    *   **Type:** `BE/Research`
    *   **Scope:** Move from scalar penalty (`_scalarize`) to proper Pareto-dominance handling in SA acceptance or Archive maintenance.
    *   **Target Pillars:** Pillar 1 (Fitness Vector), Pillar 29 (MOO)
    *   **Related Files:** `backend/core/optimization/hsaga_runner.py`, `backend/core/optimization/physics_objectives.py`
    *   **Risks:** SA convergence might slow down without scalar pressure.
    *   **Tasks:**
        *   `[TASK]` Implement `DominanceComparator` class. (Effort: S)
        *   `[TASK]` Update `SAExplorer` to use Archive-based acceptance (optional) or scalarize with dynamic weights. (Effort: M)

---

### 🚀 Epic: BE-OPT-002 – Tensor Field Road Generation
**Goal:** Implement the "Pillar 2" core promise: Organic, physics-based road networks instead of random grids.

*   **Work Package: BE-OPT-002-A – Tensor Field Math Core**
    *   **ID:** `BE-OPT-002-A`
    *   **Priority:** **[P1]** (Research Gap - Missing Feature)
    *   **Type:** `BE/Math`
    *   **Scope:** Implement 2D Tensor Field class, Eigen-decomposition, and Regular Grid Interpolation.
    *   **Target Pillars:** Pillar 2 (Tensor Fields), Pillar 2.1, 2.3
    *   **Related Files:** `backend/core/domain/geometry/tensor_field.py` (New), `docs/research/RESEARCH_KNOWLEDGE_BASE.md` (Section 2.1)
    *   **Acceptance Criteria:**
        *   Unit tests verify Major/Minor eigenvector extraction.
        *   Can visualize the field (quiver plot).
    *   **Tasks:**
        *   `[TASK]` Create `TensorField` class with `$T(x,y)$` generation. (Effort: M)
        *   `[TASK]` Implement Eigen-decomposition logic. (Effort: S)

*   **Work Package: BE-OPT-002-B – RK45 Streamline Tracing**
    *   **ID:** `BE-OPT-002-B`
    *   **Priority:** **[P2]** (Advanced)
    *   **Type:** `BE/Algo`
    *   **Scope:** Implement Adaptive Runge-Kutta integrator for tracing roads along eigenvectors.
    *   **Target Pillars:** Pillar 2.2 (Adaptive RK4)
    *   **Related Files:** `backend/core/pipeline/road_generator.py`
    *   **Risks:** Evaluation time. Tracing is slow in Python. May need Numba.
    *   **Tasks:**
        *   `[TASK]` Implement `trace_streamline` using `scipy.integrate.RK45`. (Effort: M)
        *   `[TASK]` Implement stopping criteria (Boundary, Singularity, Proximity). (Effort: L)

---

# 🛤️ Track 02: BE-Research Integration

### 🚀 Epic: BE-RES-001 – Surrogate-Assisted Optimization (SAEA)
**Goal:** Reduce optimization time from Minutes to Seconds using ML Surrogates (The "Killer App" of Pillar 7).

*   **Work Package: BE-RES-001-A – Surrogate Model Integration**
    *   **ID:** `BE-RES-001-A`
    *   **Priority:** **[P0]** (Critical for Usability/Scale)
    *   **Type:** `ML/BE`
    *   **Scope:** Connect `train_surrogates.py` logic to `hsaga_runner.py`. Use surrogate for 90% of evaluations (pre-screening).
    *   **Target Pillars:** Pillar 7.6 (SAEA), Pillar 19 (UHI Surrogate)
    *   **Related Files:** `backend/core/optimization/hsaga_runner.py`, `backend/core/ai/surrogate_model.py` (New)
    *   **Risks:** Model accuracy. Poor surrogate = Bad optimization.
    *   **Acceptance Criteria:**
        *   `HSAGARunner` accepts a trained `model.pkl`.
        *   Optimization loop uses `model.predict()` for pre-screening offspring.
        *   Total runtime decreases >5x.
    *   **Tasks:**
        *   `[TASK]` Create `SurrogateModel` wrapper class (load/predict). (Effort: S)
        *   `[TASK]` Modify `HSAGARunner` to include `surrogate_screening` step in GA loop. (Effort: L)
        *   `[TASK]` Train a baseline Random Forest model on synthetic data. (Effort: M)

---

### 🚀 Epic: BE-RES-002 – Turkish Compliance Engine (RASE)
**Goal:** Make the tool legally relevant in Turkey.

*   **Work Package: BE-RES-002-A – Dynamic Setback & Class Checking**
    *   **ID:** `BE-RES-002-A`
    *   **Priority:** **[P1]** (Market Fit)
    *   **Type:** `BE`
    *   **Scope:** Implement "Planlı Alanlar İmar Yönetmeliği" rules (Height-dependent setbacks).
    *   **Target Pillars:** Pillar 4 (Regulatory), Pillar 20.1 (Dynamic Setbacks)
    *   **Related Files:** `backend/core/turkish_standards/compliance.py`
    *   **Tasks:**
        *   `[TASK]` Implement `calculate_required_setback(h)`. (Effort: S)
        *   `[TASK]` Implement `validate_building_class(type)`. (Effort: S)

---

# 🛤️ Track 03: FE-UX & Visualization

### 🚀 Epic: FE-UX-001 – "God Component" Decomposition
**Goal:** Make the Frontend maintainable.

*   **Work Package: FE-UX-001-A – OptimizationResults Refactor**
    *   **ID:** `FE-UX-001-A`
    *   **Priority:** **[P0]** (Technical Debt Blocker)
    *   **Type:** `FE`
    *   **Scope:** Split `OptimizationResults.tsx` into 5+ sub-components/hooks.
    *   **Targets:** Architecture Hygiene
    *   **Related Files:** `frontend/src/components/OptimizationResults.tsx`, `frontend/src/hooks/useMapInitialization.ts`, `frontend/src/layers/*`
    *   **Tasks:**
        *   `[TASK]` Extract `useMapInitialization` hook. (Effort: S)
        *   `[TASK]` Extract `useBuildingInteraction` hook. (Effort: M)
        *   `[TASK]` Extract `WindOverlay` / `SolarOverlay` completely to `components/layers/`. (Effort: S)
        *   `[TASK]` Create `MapContainer` component. (Effort: M)

*   **Work Package: FE-UX-001-B – Type Safety & Strict Mode**
    *   **ID:** `FE-UX-001-B`
    *   **Priority:** **[P1]** (Quality)
    *   **Type:** `FE`
    *   **Scope:** Eliminate `any` in critical paths (GeoContext, Mapbox Events).
    *   **Related Files:** `frontend/src/types.ts`, `frontend/src/store/useOptimizationStore.ts`
    *   **Tasks:**
        *   `[TASK]` Define `GeoContext` interface to match backend response. (Effort: S)
        *   `[TASK]` Add proper types to Zustand store actions. (Effort: M)

---

# 🛤️ Track 04: Infrastructure & DevOps

### 🚀 Epic: INFRA-001 – Production Hardening
**Goal:** Prepare for "Real User" load.

*   **Work Package: INFRA-001-A – Job Persistence & Scaling**
    *   **ID:** `INFRA-001-A`
    *   **Priority:** **[P0]** (Reliability)
    *   **Type:** `Infra`
    *   **Scope:** Ensure `SQLiteJobStore` handles concurrency correctly or migrate to Redis if needed for multi-worker.
    *   **Related Files:** `backend/api/routers/optimize.py`, `backend/core/storage/sqlite_store.py`
    *   **Tasks:**
        *   `[TASK]` Verify SQLite WAL mode for concurrency. (Effort: S)
        *   `[TASK]` Implement Rate Limiting (`slowapi`) on `/optimize/start`. (Effort: M)

---

# 🛤️ Track 05: Product & Sector Alignment

### 🚀 Epic: PROD-001 – Municipality Pilot Pack
**Goal:** Minimum viable feature set for a University or Municipality demo.

*   **Work Package: PROD-001-A – Reporting & Export**
    *   **ID:** `PROD-001-A`
    *   **Priority:** **[P2]** (User Value)
    *   **Type:** `Product`
    *   **Scope:** Allow users to download results.
    *   **Tasks:**
        *   `[TASK]` Add "Download GeoJSON" button. (Effort: S)
        *   `[TASK]` Add "Download PDF Summary" (Mockup first). (Effort: M)

---

## 📈 Success Metrics (KPIs)
- **Performance:** Optimization < 30 seconds (via SAEA).
- **Architecture:** `OptimizationResults.tsx` < 250 LOC.
- **Utilization:** 100% CPU Load on Apple Silicon (Parallel SA).
- **Compliance:** 100% of generated buildings respect Turkish Setback rules.
