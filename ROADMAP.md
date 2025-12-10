# PlanifyAI Master Roadmap (V2.0.0)
> **Status:** Active / Systemic Overhaul
> **Last Updated:** 2025-12-10
> **Authors:** Emre Almaoglu, Antigravity Agent
> **Motto:** "Reliable, Scientific, Scalable."

---

## 🏛️ Strategic Vision: The "Scientific Studio"
This roadmap transitions PlanifyAI from an **"Academic Prototype"** to a **"Professional Spatial Intelligence Platform"**. It is built on four non-negotiable pillars:

1.  **Architectural Integrity (The Plumbing):** No God Components, strict Type Safety, clear Boundaries.
2.  **Research Fidelity (The Brain):** If it's in `docs/research/`, it must be in the Code. Bridging the "Research-Code Gap".
3.  **Production Hardening (The Muscle):** Redis Job Stores, Rate Limiting, CI/CD, Testing Culture.
4.  **Scientific UX (The Face):** Hybrid "Studio/Notebook" paradigms, deep explainability (XAI), and professional aesthetics.

---

## 🗓️ Phase 10: Architectural Hygiene & Core Stability (Current)
**Goal:** Eliminate "God Components" and establish strict architectural boundaries.
**Timeline:** Sprint 10-11

- [ ] **10.1 Frontend Decoupling (The `OptimizationResults.tsx` Split)**
    - [ ] `hooks/useMapInitialization.ts`: Encapsulate Mapbox setup & terrain.
    - [ ] `hooks/useBuildingInteraction.ts`: Encapsulate click/hover/popup logic.
    - [ ] `layers/WindOverlay.tsx` & `SolarOverlay.tsx`: Isolate physics layers.
    - [ ] `SimulationPanel.tsx`: Isolate sidebar control logic.
    - [ ] `OptimizationResults.tsx`: Reduce from 933 lines to <200 lines (Orchestrator only).

- [ ] **10.2 Backend Service Refactoring**
    - [x] **OSM Service Intelligence:** Restored "Context/Residential" building classification.
    - [ ] `osm_service.py` Split:
        - `osm_fetcher.py`: Pure I/O (OSMnx/API calls).
        - `osm_transformer.py`: CRS & Geometry projections.
        - `osm_classifier.py`: Tag parsing logic (The logic just fixed).

- [ ] **10.3 Type Safety Enforcement**
    - [ ] Fix `GeoContext` Interface: Explicitly define `features: FeatureCollection`.
    - [ ] Add `MapboxEvent` types (remove `any`).
    - [ ] Strict Mode Compliance (frontend).

---

## 🧬 Phase 11: Research Implementation (Bridging the Gap)
**Goal:** Implement the "Missing Pillars" identified in the Evidence-Based Review.
**Timeline:** Sprint 12-13

- [x] **11.1 Research Knowledge Base Synthesis:** Missing docs (Street Gen, SAEA, Scientific UX) added to KB.
- [ ] **11.2 Tensor Field Road Generation (Pillar 2)**
    - [ ] **Core Math:** Implement `TensorField` class (Eigen-decomposition).
    - [ ] **Streamline Tracing:** Implement `RK45` integrator with adaptive steps.
    - [ ] **UI:** Road Generation Tool in the Studio Sidebar.
    - [ ] **Validation:** Compare against existing `Simplified Road Network` (L-System).

- [ ] **11.3 Surrogate-Assisted Optimization (SAEA) (Pillar 7.6)**
    - [ ] **Offline Training:** Create `generate_synthetic_campus_data.py`.
    - [ ] **Surrogate Model:** Implement `GaussianProcessRegressor` (sklearn) for fitness approximation.
    - [ ] **Integration:** Modify `HSAGARunner` to use Surrogate for pre-screening (Infill Criterion).
    - [ ] **Benchmark:** Demonstrate 10x speedup vs physics simulation.

- [ ] **11.4 Explainable AI (XAI) (Pillar 22)**
    - [ ] **Pareto Front Visualization:** Interactive Scatter Plot (Cost vs Quality).
    - [ ] **SHAP Values:** "Why is this building here?" tooltip (Feature Importance).

---

## 🛡️ Phase 12: Production Hardening
**Goal:** Risk mitigation and scalability.
**Timeline:** Sprint 14-15

- [ ] **12.1 Persistence Layer**
    - [ ] **Job Store:** Migrate from In-Memory `_jobs = {}` to `RedisJobStore` (or SQLite for V1).
    - [ ] **Persistence Interface:** Define `JobRepository` Protocol.

- [ ] **12.2 API Security & Stability**
    - [ ] **Rate Limiting:** Implement `slowapi` (10 req/min for optimization).
    - [ ] **Health Checks:** `/health` endpoint (Liveness/Readiness probes).
    - [ ] **Structured Logging:** JSON logs with Correlation IDs.
    - [ ] **Global Error Handler:** Standardized `4xx/5xx` JSON responses.

---

## 🎨 Phase 13: Scientific UX & "God Mode"
**Goal:** A UI that respects the user's intelligence.
**Timeline:** Sprint 16+

- [ ] **13.1 The "Scientific Studio"**
    - [ ] **Notebook View:** Reactive parameter scripting pane.
    - [ ] **Comparative Dashboard:** Side-by-side scenario comparison (Kepler.gl style).
    - [ ] **God Mode Tools:** Manual override of AI decisions (Force/Block/Anchor).

---

## 🧪 Testing & Validation Strategy
**Strict Rule:** No feature is "Done" without proof.

- [ ] **Unit Tests:** `pytest-cov` > 40% Coverage.
- [ ] **Integration Tests:** `HSAGARunner` verified with real constraints.
- [ ] **E2E Tests:** `simulate_user_journey.py` running against local API.
- [ ] **Benchmark:** `SPOP Suite` (Standard Planify Optimization Protocol) run on all algorithms.

---

## 📈 Success Metrics (KPIs)
1.  **Code Maintenance:** `OptimizationResults.tsx` < 250 LOC.
2.  **Performance:** Optimization < 30s (via SAEA).
3.  **Reliability:** Zero "Grey Map" incidents (OSM Service).
4.  **Security:** Zero Hardcoded Secrets/URLs.
