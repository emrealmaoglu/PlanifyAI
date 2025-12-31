# PlanifyAI Architecture Analysis & Improvement Plan

**Date:** 2025-12-31  
**Context:** Post-Sprint 3 architecture review and incremental improvements

---

## 🔍 Current Architecture Issues

### 1. Duplicate Module Structure ❌
**Problem:** Both `src/` and `backend/core/` contain similar modules

```
src/
├── algorithms/     # Duplicate with backend/core/optimization/
├── constraints/    # Duplicate with backend/core/optimization/constraints/
├── data/          # Duplicate with backend/core/schemas/
└── spatial/       # Duplicate with backend/core/domain/geometry/

backend/core/
├── optimization/   # Modern, tested, Sprint 3 integrated
├── schemas/       # Pydantic models
└── domain/        # DDD architecture
```

**Impact:**
- Confusion about which module to import
- Maintenance burden (update in 2 places)
- Test coverage diluted (0% on src/)

**Solution:**
- **Phase 1:** Deprecate `src/` directory
- **Phase 2:** Migrate any unique logic to `backend/core/`
- **Phase 3:** Update all imports to `backend.core.*`

### 2. Duplicate Files Within Modules ❌
**Problem:** Duplicate files with "2" suffix

```
backend/core/
├── optimization/
│   ├── fitness.py
│   ├── fitness 2.py      # Duplicate! ❌
│   ├── solution.py
│   └── solution 2.py     # Duplicate! ❌
└── __init__ 2.py          # Duplicate! ❌
```

**Solution:**
- Delete all `*2.py` files after verification
- Review for unique logic before deletion

### 3. Test Directory Fragmentation
**Problem:** Tests scattered across multiple locations

```
tests/          # Integration & E2E
backend/tests/  # Isolated backend tests (redundant)
src/            # No tests (0% coverage)
```

**Solution:**
- Consolidate all tests under `tests/`
- Remove `backend/tests/`
- Add `tests/unit/backend/` subdirectory

---

## ✅ Architecture Strengths

### 1. Domain-Driven Design (DDD) ✅
```
backend/core/domain/
├── models/        # Domain entities (Campus, Gateway)
└── geometry/      # Geometry services
```

**Rationale:** Clean separation of business logic from infrastructure

### 2. Clear API Layer ✅
```
backend/api/routers/
├── optimize.py    # Optimization endpoints
├── campus.py      # Campus detection
└── ...
```

**Rationale:** FastAPI routers with clear responsibilities

### 3. Pipeline Architecture ✅
```
backend/core/pipeline/
└── orchestrator.py  # Central coordination point
```

**Rationale:** Single entry point for complex workflows

---

## 🎯 Improvement Roadmap

### Phase 1: Cleanup (Current Session)
**Goal:** Remove redundancy, improve clarity

1. ✅ Delete duplicate `*2.py` files
2. ✅ Analyze `src/` vs `backend/core/` overlap
3. ✅ Create deprecation plan for `src/`
4. ✅ Consolidate test directories

### Phase 2: Frontend Optimization (Next)
**Goal:** Improve React architecture

1. Analyze component structure
2. Identify performance bottlenecks
3. Add missing TypeScript types
4. Implement code splitting

### Phase 3: Backend Refactoring (Ongoing)
**Goal:** Apply research insights incrementally

1. Sprint A1: Turkish building codes integration
2. Surrogate model infrastructure
3. NSGA-III migration preparation

---

## 📊 Metrics Tracking

| Metric | Before | Target | Current |
|--------|--------|--------|---------|
| Duplicate files | 5+ | 0 | 3 (`*2.py`) |
| Test coverage (backend) | 85% | 90% | 85% |
| Test coverage (src) | 0% | N/A (deprecate) | 0% |
| Import clarity | Mixed | 100% backend.core | ~60% |
| Frontend bundle size | ? | <500KB | TBD |

---

## 🛠️ Immediate Actions

### Action 1: Delete Duplicate Files
```bash
# Verify no unique logic
diff backend/core/optimization/fitness.py backend/core/optimization/fitness\ 2.py
diff backend/core/optimization/solution.py backend/core/optimization/solution\ 2.py

# Delete duplicates
rm "backend/core/optimization/fitness 2.py"
rm "backend/core/optimization/solution 2.py"
rm "backend/core/__init__ 2.py"
```

### Action 2: Analyze src/ Directory
Create migration plan for any critical src/ code.

### Action 3: Frontend Audit
Analyze React component structure and identify improvements.

---

## 📝 Next Steps

1. Execute Phase 1 cleanup
2. Commit incremental improvements
3. Document architectural decisions
4. Proceed with Research Integration (Phase Alpha)
