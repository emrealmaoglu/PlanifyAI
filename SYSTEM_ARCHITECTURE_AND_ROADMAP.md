---
Project Name: PlanifyAI
Version: v10.2.0 (Production Ready)
Architecture Status: ✅ AS-BUILT
Pivot Status: Active (Spatial-First)
Last Update: 2025-12-10 (Sprint 8)
Author: Emre Almaoğlu
---

# SYSTEM CONSTITUTION V5.0 (PRODUCTION READY)

> 📚 **Bu Belge Nedir?**
> Bu belge, PlanifyAI projesinin "anayasası"dır. Tüm mimari kararlar, algoritma detayları, dosya yapısı ve yol haritası burada belgelenir.

---

## 1. PROJECT STATUS DASHBOARD

| Metric | Value |
|--------|-------|
| **Version** | v10.2.0 |
| **Health** | ✅ STABLE |
| **Unit Tests** | **35 PASSED** |
| **Optimization Speed** | 0.29s (7 buildings) |
| **Regulatory Status** | ✅ Turkish Standards Active |
| **Error Handling** | ✅ Toast + ErrorBoundary |

### Phase Completion

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 6 | ✅ | Spatial Optimization Engine |
| Phase 7 | ✅ | Physics (Wind/Solar) |
| Phase 8 | ✅ | Regulatory Compliance |
| Phase 9 | ✅ | XAI Visualization |
| Phase 10 | ✅ | Production Cleanup |
| **Phase 11** | ✅ | **FE Refactor (FE-UX-001-A)** |
| **Sprint 1-8** | ✅ | **Refactor + Tests + Error Handling** |

---

## 2. THE "AS-BUILT" ARCHITECTURE

### 2.1 Directory Structure

```text
PlanifyAI/
├── backend/
│   ├── api/
│   │   ├── routes/              # FastAPI endpoints
│   │   ├── main.py              # App entry point
│   │   └── run.py               # Server runner
│   └── core/
│       ├── domain/geometry/
│       │   └── osm_service.py   [SPATIAL ETL - OSM Fetch]
│       ├── optimization/
│       │   ├── encoding.py      [GENOME: 7 genes/building]
│       │   ├── spatial_problem.py [PROBLEM: 4F, 5G]
│       │   ├── hsaga_runner.py  [ALGORITHM: SA→GA]
│       │   └── physics_objectives.py [PHYSICS: Wind/Solar]
│       ├── terrain/
│       │   └── elevation.py     [DEM: Slope Analysis]
│       ├── visualization/
│       │   └── slope_grid_generator.py [XAI: Heatmaps]
│       ├── schemas/
│       │   └── input.py         [API CONTRACT]
│       ├── turkish_standards/
│       │   ├── compliance.py    [REGULATIONS]
│       │   └── data.py          [BUILDING SPECS]
│       ├── storage/              ← NEW (Sprint 2)
│       │   ├── protocol.py      [JOBSTORE INTERFACE]
│       │   └── sqlite_store.py  [SQLITE IMPL]
│       └── pipeline/
│           └── orchestrator.py  [JOB COORDINATOR]
├── frontend/
│   └── src/
│       ├── features/cockpit/
│       │   ├── SidebarLayout.tsx [MAIN UI + Save/Load]
│       │   └── tabs/
│       │       ├── DesignTab.tsx [ACCORDIONS]
│       │       └── PrepTab.tsx   [SITE PREP]
│       ├── store/
│       │   └── useOptimizationStore.ts [ZUSTAND STATE]
│       ├── hooks/
│       │   └── useMapInitialization.ts [MAP INIT HOOK] ← NEW
│       └── components/
│           ├── SimulationPanel.tsx  [LOADING/STATUS]
│           ├── ErrorBoundary.tsx    [CRASH RECOVERY] ← NEW
│           ├── Toast.tsx            [NOTIFICATIONS] ← NEW
│           ├── DrawingTools.tsx     [GOD MODE DRAWING]
│           ├── OptimizationResults.tsx [XAI LAYERS + MAP]
│           └── layers/              ← NEW
│               ├── WindOverlay.tsx  [WIND ARROWS]
│               └── SlopeOverlay.tsx [SLOPE HEATMAP]
├── tests/
│   ├── unit/                    ← NEW (35 tests)
│   │   ├── test_constraint_calculator.py
│   │   └── test_sqlite_job_store.py
│   ├── api/
│   │   └── test_optimize_endpoints.py
│   ├── simulate_user_journey.py [E2E TEST]
│   └── verify_optimization.py   [UNIT TESTS]
├── docs/                        [RESEARCH PAPERS]
├── data/osm/                    [OSM CACHE]
├── archive/                     [LEGACY FILES]
│   ├── legacy_reports/          [Old MD reports]
│   ├── debug_scripts/           [Debug Python files]
│   └── temp_data/               [JSON responses]
├── scripts/                     [UTILITY SCRIPTS]
├── config/                      [CONFIG FILES]
├── SYSTEM_ARCHITECTURE_AND_ROADMAP.md [THIS FILE]
├── README.md                    [PROJECT OVERVIEW]
├── CHANGELOG.md                 [VERSION HISTORY]
├── requirements.txt             [PYTHON DEPS]
└── setup.py                     [PACKAGE SETUP]
```

### 2.2 Key File Descriptions

| File | Module | Purpose |
|------|--------|---------|
| `osm_service.py` | ETL | Fetches & classifies OSM campus data |
| `encoding.py` | Genome | `[x,y,θ,type,w,d,floors]` per building |
| `spatial_problem.py` | PyMOO | 4 objectives + 5 constraints |
| `hsaga_runner.py` | Optimizer | SA(30%) → NSGA-III(70%) |
| `physics_objectives.py` | Physics | Wind wake, solar shadow |
| `elevation.py` | Terrain | Open-Elevation API + slope |
| `slope_grid_generator.py` | XAI | Heatmap data generation |
| `orchestrator.py` | Pipeline | Job management |

---

## 3. ALGORITHM SPECIFICATIONS

### 3.1 H-SAGA (Hybrid Simulated Annealing → Genetic Algorithm)

```
┌─────────────────────────────────────────────────┐
│                 H-SAGA PIPELINE                 │
├─────────────────────────────────────────────────┤
│  PHASE 1: Simulated Annealing (30% budget)     │
│  ├─ 8 parallel chains                          │
│  ├─ Exponential cooling                        │
│  └─ Basin exploration                          │
├─────────────────────────────────────────────────┤
│  PHASE 2: NSGA-III (70% budget)                │
│  ├─ Initialize with SA survivors               │
│  ├─ Das-Dennis reference directions            │
│  └─ SBX + Polynomial mutation                  │
├─────────────────────────────────────────────────┤
│  OUTPUT: Pareto-optimal layout                 │
└─────────────────────────────────────────────────┘
```

### 3.2 Genome Structure

```python
BuildingGene = [x, y, rotation, type_id, width_factor, depth_factor, floor_factor]
# x, y: Position (meters, local CRS)
# rotation: 0-360 degrees
# type_id: 0=Faculty, 1=Dormitory, 2=Library, etc.
# width_factor: 0.5-1.5 (dimension scaling)
# depth_factor: 0.5-1.5
# floor_factor: 0.5-1.5 (floor count scaling)
```

### 3.3 Objective Functions (Minimize All)

| ID | Objective | Formula | Weight |
|----|-----------|---------|--------|
| F[0] | Compactness | `σ(distances) / mean(distances)` | 0.25 |
| F[1] | Adjacency | `Σ(missing_pairs) / total_pairs` | 0.25 |
| F[2] | Wind Comfort | `Σ(exposed_width + wake_interference)` | 0.25 |
| F[3] | Solar Gain | `Σ(orientation_penalty + shadow_interference)` | 0.25 |

### 3.4 Constraint Functions (All ≤ 0)

| ID | Constraint | Rule | Source |
|----|------------|------|--------|
| G[0] | Boundary | All buildings inside campus | Spatial |
| G[1] | Overlap | No building intersections | Spatial |
| G[2] | Dynamic Setback | Front: 5m, Side: 3m | Turkish Zoning |
| G[3] | Fire Separation | `max(6m, H/2)` | Fire Code |
| G[4] | Slope | ≤ 15% grade | Geospatial |

---

## 4. PHYSICS MODELS

### 4.1 Wind Comfort

```
Wake Zone Length = 3 × Building Width
Exposed Width = W × sin(θ_wind - θ_building)
Blockage Score = Σ(exposed_widths + wake_overlaps)
```

**Reference:** 3D Urban Optimization Research

### 4.2 Solar Gain

```
Shadow Length = Height × cot(solar_altitude)
Orientation Penalty = 1 - cos(θ_facade - θ_optimal)
Optimal Orientation = South (180°) at lat=41°N
```

**Reference:** Building Energy Modeling Standards

### 4.3 Slope Analysis

```
Slope = ΔElevation / Distance × 100%
Max Allowed = 15%
API: Open-Elevation (with offline fallback)
```

---

## 5. REGULATORY COMPLIANCE (Turkish Standards)

### 5.1 Setback Rules (Planlı Alanlar İmar Yönetmeliği)

| Edge Type | Detection Method | Setback |
|-----------|------------------|---------|
| Front | `dot(edge_normal, road_direction) > 0.7` | 5m |
| Side | Otherwise | 3m |

### 5.2 Fire Separation (Derz Boşluğu)

```
Required Distance = max(6.0m, taller_building_height / 2)
```

### 5.3 Building Type Specifications

| Type | Min Width | Max Width | Floors | FAR |
|------|-----------|-----------|--------|-----|
| Faculty | 30m | 60m | 2-5 | 1.5 |
| Dormitory | 15m | 30m | 3-8 | 2.0 |
| Library | 25m | 45m | 2-4 | 1.2 |
| Research | 20m | 40m | 2-4 | 1.0 |
| Sports | 30m | 50m | 1 | 0.5 |
| Dining | 20m | 35m | 1-2 | 0.8 |

---

## 6. XAI VISUALIZATION

### 6.1 Slope Heatmap

```
Grid: 10×10 cells over campus
Colors: Green (0-5%) → Yellow (5-15%) → Red (>15%)
Layer: Mapbox GL circle layer
```

### 6.2 Wind Arrows

```
Grid: 5×5 arrows over campus
Rotation: From wind direction (degrees)
Layer: Mapbox GL symbol layer with canvas icon
```

### 6.3 Violation Styling

```
Violating Buildings: Red outline (4px) + Light red fill
Layer: Mapbox GL line + conditional fill-extrusion-color
```

---

## 7. API CONTRACT

### 7.1 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/context/fetch` | Fetch campus from OSM |
| POST | `/api/optimize/start` | Start optimization job |
| GET | `/api/optimize/status/{id}` | Poll job status |
| GET | `/api/optimize/geojson/{id}` | Get results |

### 7.2 Response Format

```json
{
  "type": "FeatureCollection",
  "properties": {
    "objectives": {
      "compactness": 0.15,
      "adjacency": 0.12,
      "wind_comfort": 0.18,
      "solar_gain": 0.22
    },
    "compliance_score": 0.92,
    "wind_vector": {"direction": 22.5, "speed": 3.5}
  },
  "features": [
    {
      "id": "building_0",
      "properties": {
        "building_type": "Faculty",
        "floors": 4,
        "height": 16.0,
        "violations": [],
        "layer": "optimized_building"
      },
      "geometry": {"type": "Polygon", "coordinates": [...]}
    }
  ],
  "slope_grid": {
    "bounds": [33.77, 41.37, 33.79, 41.39],
    "resolution": 100,
    "cells": [{"center": [33.78, 41.38], "slope": 0.08}, ...]
  }
}
```

---

## 8. PERFORMANCE BENCHMARKS

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| E2E Test (7 buildings) | <5s | **2.64s** | ✅ |
| H-SAGA Optimization | <30s | **0.29s** | ✅ |
| Slope Grid (100 cells) | <1s | **<0.1s** | ✅ |
| Wind Arrows (25) | 60fps | **60fps** | ✅ |
| GeoJSON Size | <500KB | **~50KB** | ✅ |

---

## 9. PHASE 10 CLEANUP LOG

### 9.1 Files Deleted (2025-12-09)

| Category | Files | Size |
|----------|-------|------|
| Legacy Optimization | `hsaga.py`, `problem.py`, `objectives.py`, `constraints.py`, `building_mapper.py` | ~100KB |
| Integration Folder | `integration/*` (16+ files) | ~100KB |
| Spatial Folder | `spatial/*` (tensor fields) | ~50KB |
| Backup Files | `*_Safe.tsx`, `*_Safe.ts` | ~1KB |
| Legacy Tests | `tests/sprint3/*` | ~20KB |
| Debug Scripts | 25+ debug/verify scripts | ~50KB |
| Legacy Reports | 25+ MD report files | ~200KB |

**Total Cleanup:** ~500KB of dead code

### 9.2 Files Organized

| From | To | Count |
|------|----|-------|
| Root MD files | `archive/legacy_reports/` | 25 |
| Root debug scripts | `archive/debug_scripts/` | 20 |
| Root JSON files | `archive/temp_data/` | 15 |
| OSM data files | `data/osm/` | 2 |

---

## 10. UI/UX FEATURES

### 10.1 Sidebar Layout

```
┌─────────────────────────────────────┐
│ [P] PlanifyAI     [📥][📤]         │  ← Save/Load buttons
├─────────────────────────────────────┤
│ [Saha Hazırlığı] [Tasarım]         │  ← Tab navigation
├─────────────────────────────────────┤
│ ▼ Optimizasyon Öncelikleri         │  ← Collapsible accordion
│   ├─ Kompaktlık: ████░░ 50%        │
│   ├─ İlişki Ağı: ████░░ 50%        │
│   ├─ Güneş:      ░░░░░░ 0%         │
│   └─ Rüzgar:     ░░░░░░ 0%         │
├─────────────────────────────────────┤
│ ► Aktif Analizler                  │  ← Collapsed by default
├─────────────────────────────────────┤
│ [▶ SİMÜLASYONU BAŞLAT]             │  ← Action button
└─────────────────────────────────────┘
```

### 10.2 Save/Load Feature

```json
// Export Format: planify_scenario_2025-12-09.json
{
  "version": "1.0",
  "exportedAt": "2025-12-09T11:11:54Z",
  "projectInfo": {"name": "Kampüs Projesi"},
  "buildingCounts": {"Faculty": 2, "Dormitory": 5},
  "siteParameters": {"setback_front": 5.0},
  "optimizationGoals": {"COMPACTNESS": 0.5}
}
```

---

## 11. SCIENTIFIC TRACEABILITY

| Feature | Code Location | Research Source |
|---------|---------------|-----------------|
| H-SAGA | `hsaga_runner.py` | Li et al. 2025, Hybrid Metaheuristics |
| Wind Model | `physics_objectives.py` | 3D Urban Optimization.docx |
| Solar Model | `physics_objectives.py` | Building Energy Modeling |
| Setbacks | `spatial_problem.py` | Turkish Zoning Law |
| Fire Codes | `spatial_problem.py` | Turkish Fire Safety Code |

---

## 12. FUTURE ROADMAP

### Phase 11: Real-time Updates (Planned)
- [ ] WebSocket connection for live progress
- [ ] Feasibility indicator during optimization
- [ ] Pareto front visualization

### Phase 12: Case-Based Reasoning (Planned)
- [ ] Layout templates library
- [ ] Cross-project learning
- [ ] Recommendation engine

### Phase 13: Advanced Features (Future)
- [ ] SAEA (Surrogate-Assisted Optimization)
- [ ] Road network generation
- [ ] Multi-campus comparison

---

## 13. DEVELOPMENT PROTOCOLS

### 13.1 Git Workflow

```bash
# Feature development
git checkout -b feature/phase-11-websocket
# ... make changes ...
git add -A && git commit -m "feat(api): add WebSocket endpoint"
git push origin feature/phase-11-websocket
# Create PR → Review → Merge
```

### 13.2 Testing

```bash
# Unit tests
python3 tests/verify_optimization.py

# E2E test
python3 tests/simulate_user_journey.py

# Frontend type check
cd frontend && npx tsc --noEmit
```

### 13.3 Code Style

- Python: `ruff` + `black`
- TypeScript: `eslint` + `prettier`
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`)

---

> 📋 **Document Version:** 5.0
> 📅 **Last Updated:** 2025-12-09
> ✍️ **Author:** Emre Almaoğlu
