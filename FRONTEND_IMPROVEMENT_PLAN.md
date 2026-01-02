# Frontend Architecture Improvement Plan

**Date:** 2025-12-31  
**Context:** Post-Sprint 3 frontend optimization and React best practices

---

## 📊 Current Frontend Architecture

### Technology Stack ✅
```json
{
  "framework": "React 19.2.0",
  "build": "Vite 7.2.4",
  "styling": "Tailwind CSS 4.1.17",
  "state": "Zustand 5.0.8",
  "maps": "Mapbox GL 3.16.0",
  "http": "Axios 1.13.2 + TanStack Query 5.90.10"
}
```

### Directory Structure
```
frontend/src/
├── components/
│   ├── map/               # Map-related components
│   │   ├── MapContainer.tsx
│   │   ├── MapContext.tsx ✅ (Clean context pattern)
│   │   ├── InitialContextFetcher.tsx
│   │   └── layers/
│   │       ├── ExistingContextLayers.tsx
│   │       └── GatewayLayer.tsx  # Sprint 3 addition
│   ├── layers/            # Overlay components
│   ├── SimulationPanel.tsx
│   ├── OptimizationResults.tsx
│   └── ...
├── features/
│   └── cockpit/
│       ├── tabs/
│       └── SidebarLayout.tsx
├── hooks/                 # Custom React hooks
│   ├── useContextFetcher.ts
│   ├── useSimulationRunner.ts
│   └── useBoundaryEditing.ts
├── store/                 # Zustand state management
├── types/                 # TypeScript definitions
└── utils/
```

---

## 🎯 Identified Improvements

### 1. Map Logic Refactoring (Sprint 3 Done ✅)
**Status:** COMPLETE  
**Achievement:** Refactored map logic into MapContext and hooks

**Before (v10.2.1):**
```tsx
// All logic in MapContainer (500+ lines)
<MapContainer>
  {/* Everything mixed together */}
</MapContainer>
```

**After (v10.2.2):**
```tsx
// Clean separation
<MapProvider value={{ map, isMapLoaded }}>
  <MapContainer />
  <InitialContextFetcher />
  <GatewayLayer />
</MapProvider>
```

**Benefits:**
- ✅ Reduced MapContainer from 500+ to ~200 lines
- ✅ Reusable hooks (useContextFetcher, useBoundaryEditing)
- ✅ Better testability
- ✅ Gateway layer isolated

### 2. Performance Optimization 🎯

#### 2.1 Code Splitting (Needed)
**Problem:** Large bundle size affects initial load

**Solution:**
```tsx
// Lazy load heavy components
const OptimizationResults = lazy(() =>
  import('./components/OptimizationResults')
);
const SimulationPanel = lazy(() =>
  import('./components/SimulationPanel')
);

// Route-based splitting
const routes = [
  {
    path: '/',
    component: lazy(() => import('./pages/Home'))
  }
];
```

**Expected Impact:**
- Initial bundle: -40%
- Time to interactive: -30%
- First contentful paint: -25%

#### 2.2 Memoization (Partial)
**Current:**
```tsx
// Re-renders on every parent update
function GatewayLayer({ gateways }) {
  return gateways.map(g => <Marker key={g.id} />);
}
```

**Improved:**
```tsx
const GatewayLayer = memo(({ gateways }) => {
  return gateways.map(g => <Marker key={g.id} />);
}, (prev, next) =>
  prev.gateways.length === next.gateways.length
);
```

#### 2.3 Virtual Scrolling (Future)
For large building lists (100+ buildings):
```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

// Only render visible items
const virtualizer = useVirtualizer({
  count: buildings.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50
});
```

### 3. TypeScript Coverage 📝

#### 3.1 Current Status
**Good:**
- ✅ types/optimization.ts (comprehensive)
- ✅ MapContext.tsx (fully typed)
- ✅ hooks/*.ts (typed hooks)

**Needs Improvement:**
```tsx
// ❌ Implicit any
function handleClick(e) {  // e: any
  // ...
}

// ✅ Should be
function handleClick(e: React.MouseEvent<HTMLButtonElement>) {
  // ...
}
```

#### 3.2 Strict Mode Enablement
**Goal:** Enable strict TypeScript checks

`tsconfig.json`:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true
  }
}
```

### 4. State Management Optimization 🔄

#### 4.1 Zustand Store Structure
**Current:** Single store (good for small apps)

**Future (if needed):**
```tsx
// Slice-based stores
export const useMapStore = create<MapState>((set) => ({
  // Map-specific state
}));

export const useOptimizationStore = create<OptState>((set) => ({
  // Optimization-specific state
}));

// Combine when needed
const map = useMapStore();
const opt = useOptimizationStore();
```

#### 4.2 React Query Integration ✅
**Status:** Already using TanStack Query

**Enhancement:** Add mutation hooks
```tsx
const { mutate: optimizeCampus } = useMutation({
  mutationFn: (request: OptimizationRequest) =>
    axios.post('/api/optimize/start', request),
  onSuccess: (data) => {
    // Invalidate related queries
    queryClient.invalidateQueries(['optimization', data.job_id]);
  }
});
```

### 5. Component Architecture 🏗️

#### 5.1 Atomic Design Pattern (Partial)
**Current:** Mixed component sizes

**Proposal:**
```
components/
├── atoms/        # Buttons, Icons, Labels
├── molecules/    # SearchBar, Toast, DrawingTools
├── organisms/    # MapContainer, SimulationPanel
└── templates/    # Full page layouts
```

#### 5.2 Composition over Props Drilling
**Before:**
```tsx
<GrandParent settings={settings}>
  <Parent settings={settings}>
    <Child settings={settings} />
  </Parent>
</GrandParent>
```

**After:**
```tsx
<SettingsProvider value={settings}>
  <GrandParent>
    <Parent>
      <Child />
    </Parent>
  </GrandParent>
</SettingsProvider>
```

---

## 🚀 Implementation Roadmap

### Phase 1: Quick Wins (1-2 days)
1. ✅ MapContext refactoring (DONE in v10.2.2)
2. Add React.memo to expensive components
3. Enable TypeScript strict mode
4. Add missing type annotations

### Phase 2: Performance (3-5 days)
1. Implement code splitting
2. Lazy load heavy components
3. Bundle size analysis with vite-bundle-visualizer
4. Optimize re-renders with React DevTools Profiler

### Phase 3: Architecture (1 week)
1. Refactor to Atomic Design
2. Create design system documentation
3. Component library setup
4. Storybook integration (optional)

### Phase 4: Testing (Ongoing)
1. Add Vitest unit tests (currently 1 test)
2. React Testing Library for components
3. E2E tests with Playwright
4. Visual regression tests

---

## 📈 Success Metrics

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Bundle size (gzip) | ~800KB | <500KB | Phase 2 |
| Initial load time | ~2.5s | <1.5s | Phase 2 |
| TypeScript coverage | ~70% | >95% | Phase 1 |
| Component tests | 1 | 50+ | Phase 4 |
| Lighthouse score | ~75 | >90 | Phase 2-3 |

---

## 🛠️ Immediate Actions (Current Session)

### Action 1: Add React.memo to GatewayLayer
```tsx
// frontend/src/components/map/layers/GatewayLayer.tsx
import { memo } from 'react';

export const GatewayLayer = memo(({ gateways, map }) => {
  // Component logic
}, (prev, next) => {
  return prev.gateways === next.gateways && prev.map === next.map;
});
```

### Action 2: Create Bundle Analysis Script
```json
// package.json
{
  "scripts": {
    "analyze": "vite-bundle-visualizer"
  }
}
```

### Action 3: TypeScript Strict Mode (Gradual)
1. Enable strict in tsconfig
2. Fix errors file by file
3. Add type coverage tool

---

## 🔗 Integration with Research Roadmap

### Sprint A1: Turkish Building Codes
**Frontend Impact:**
- Add building code compliance indicators
- Visual feedback for violations
- Regulation tooltips on hover

### Sprint A2: 15-Minute City
**Frontend Impact:**
- Accessibility heatmap layer
- Walking distance visualizations
- Isochrone overlays

### Sprint B2: Tensor Field Roads
**Frontend Impact:**
- Streamline visualization layer
- Interactive tensor field controls
- Real-time singularity detection display

---

## 📝 Documentation Needs

1. **Component API Documentation**
   - Props and types
   - Usage examples
   - Best practices

2. **State Management Guide**
   - Zustand store structure
   - When to use context vs store
   - Data flow diagrams

3. **Performance Guidelines**
   - Bundle optimization checklist
   - Re-render debugging guide
   - Profiling workflow

---

## 🎓 Key Takeaways

**Strengths:**
- ✅ Modern React 19 with concurrent features
- ✅ Vite for fast builds
- ✅ TanStack Query for server state
- ✅ MapContext pattern (post-v10.2.2)

**Focus Areas:**
- 🎯 Code splitting and lazy loading
- 🎯 TypeScript strict mode
- 🎯 Component memoization
- 🎯 Test coverage

**Strategic:**
- Frontend improvements should align with research integration
- Incremental refactoring alongside backend sprints
- Performance monitoring from day 1
