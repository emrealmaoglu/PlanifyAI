# Component Refactoring Plan

**Goal**: Eliminate god components and improve modularity

**Date**: December 31, 2025

## Current State Analysis

### God Components Identified

| Component | Lines | Issues | Priority |
|-----------|-------|--------|----------|
| PrepTab.tsx | 409 | Multiple responsibilities, too many state variables | P0 |
| SidebarLayout.tsx | 281 | Complex layout logic, mixed concerns | P1 |
| DesignTab.tsx | 258 | Heavy UI logic, no separation | P1 |
| DrawingTools.tsx | 236 | Map interaction tightly coupled | P2 |

### Component Size Guidelines

- ✅ **Good**: < 150 lines
- ⚠️ **Warning**: 150-200 lines
- ❌ **God Component**: > 200 lines

## Refactoring Strategy

### Phase 1: PrepTab Decomposition (P0)

**Current Structure** (409 lines):
```
PrepTab
├── Project Info Section (60 lines)
├── Geo Context Section (80 lines)
├── Site Parameters Section (100 lines)
├── Boundary Editor Section (50 lines)
├── Existing Buildings Section (80 lines)
└── Building Edit Logic (40 lines)
```

**Target Structure**:
```
PrepTab (< 100 lines) - Composition only
├── ProjectInfoForm (< 80 lines)
├── GeoContextForm (< 100 lines)
├── SiteParametersForm (< 120 lines)
├── BoundaryEditorPanel (< 60 lines)
└── ExistingBuildingsManager (< 100 lines)
    ├── BuildingList (< 60 lines)
    └── BuildingEditor (< 50 lines)
```

**Benefits**:
- Each component has single responsibility
- Easier testing (unit test each form)
- Better reusability
- Clearer code organization

### Phase 2: SidebarLayout Refactoring (P1)

**Current Issues**:
- Tab management mixed with layout
- Simulation controls embedded
- No clear separation of concerns

**Target**:
```
SidebarLayout (< 80 lines)
├── TabNavigator (< 60 lines)
├── TabPanel (< 40 lines)
└── SimulationControls (< 60 lines)
```

### Phase 3: DesignTab Refactoring (P1)

**Current Issues**:
- Building type configuration
- Optimization goals
- All in one component

**Target**:
```
DesignTab (< 80 lines)
├── BuildingTypesConfig (< 100 lines)
│   ├── BuildingTypeCard (< 50 lines)
│   └── BuildingTypeForm (< 60 lines)
└── OptimizationGoalsPanel (< 100 lines)
    ├── GoalsList (< 60 lines)
    └── GoalEditor (< 50 lines)
```

### Phase 4: DrawingTools Refactoring (P2)

**Current Issues**:
- Map interaction logic
- Drawing state management
- UI rendering

**Target**:
```
DrawingTools (< 80 lines)
├── DrawingToolbar (< 60 lines)
├── DrawingModeSelector (< 50 lines)
└── useDrawing hook (extracted logic)
```

## Implementation Plan

### Step 1: Extract Forms from PrepTab

**Week 1**:
1. Create `features/cockpit/components/forms/` directory
2. Extract `ProjectInfoForm.tsx` (60 lines)
3. Extract `GeoContextForm.tsx` (100 lines)
4. Extract `SiteParametersForm.tsx` (120 lines)
5. Update PrepTab to use new components

**Expected Outcome**: PrepTab reduced to ~150 lines

### Step 2: Extract Building Management

**Week 1**:
1. Create `features/cockpit/components/buildings/` directory
2. Extract `BoundaryEditorPanel.tsx` (60 lines)
3. Extract `ExistingBuildingsManager.tsx` (100 lines)
   - Internal: `BuildingList.tsx` (60 lines)
   - Internal: `BuildingEditor.tsx` (50 lines)
4. Update PrepTab to use new components

**Expected Outcome**: PrepTab reduced to ~80 lines (just composition)

### Step 3: Refactor SidebarLayout

**Week 2**:
1. Extract `TabNavigator.tsx` (60 lines)
2. Extract `TabPanel.tsx` (40 lines)
3. Extract `SimulationControls.tsx` (60 lines)
4. Update SidebarLayout

**Expected Outcome**: SidebarLayout reduced to ~80 lines

### Step 4: Refactor DesignTab

**Week 2**:
1. Create `features/cockpit/components/design/` directory
2. Extract `BuildingTypesConfig.tsx` (100 lines)
   - Internal: `BuildingTypeCard.tsx` (50 lines)
   - Internal: `BuildingTypeForm.tsx` (60 lines)
3. Extract `OptimizationGoalsPanel.tsx` (100 lines)
   - Internal: `GoalsList.tsx` (60 lines)
   - Internal: `GoalEditor.tsx` (50 lines)
4. Update DesignTab

**Expected Outcome**: DesignTab reduced to ~80 lines

### Step 5: Refactor DrawingTools

**Week 3**:
1. Create `hooks/useDrawing.ts` - Extract drawing logic
2. Extract `DrawingToolbar.tsx` (60 lines)
3. Extract `DrawingModeSelector.tsx` (50 lines)
4. Update DrawingTools

**Expected Outcome**: DrawingTools reduced to ~80 lines

## Design Principles

### 1. Single Responsibility Principle (SRP)
Each component should have ONE reason to change:
- ✅ `ProjectInfoForm` - Only project metadata
- ✅ `GeoContextForm` - Only location settings
- ❌ `PrepTab` - Everything (before refactor)

### 2. Composition Over Inheritance
Build complex UIs from small, reusable pieces:
```tsx
// Good: Composition
<PrepTab>
  <ProjectInfoForm />
  <GeoContextForm />
  <SiteParametersForm />
</PrepTab>

// Bad: Monolithic
<PrepTab>
  {/* 400 lines of mixed logic */}
</PrepTab>
```

### 3. Prop Drilling vs Context
- **Shallow props** (1-2 levels): Use props
- **Deep props** (3+ levels): Use context or state management
- **Example**: Store access via hooks, not prop drilling

### 4. Custom Hooks for Logic
Extract complex logic into hooks:
```tsx
// Before: Logic in component
const PrepTab = () => {
  const [editing, setEditing] = useState(false);
  const handleEdit = () => { /* complex logic */ };
  // ... 100 more lines
};

// After: Logic in hook
const useBuilding Editor = () => {
  const [editing, setEditing] = useState(false);
  const handleEdit = () => { /* complex logic */ };
  return { editing, handleEdit };
};
```

## File Structure (After Refactor)

```
frontend/src/
├── features/
│   └── cockpit/
│       ├── tabs/
│       │   ├── PrepTab.tsx (< 80 lines) ✅
│       │   └── DesignTab.tsx (< 80 lines) ✅
│       ├── components/
│       │   ├── forms/
│       │   │   ├── ProjectInfoForm.tsx (60 lines)
│       │   │   ├── GeoContextForm.tsx (100 lines)
│       │   │   └── SiteParametersForm.tsx (120 lines)
│       │   ├── buildings/
│       │   │   ├── BoundaryEditorPanel.tsx (60 lines)
│       │   │   ├── ExistingBuildingsManager.tsx (100 lines)
│       │   │   ├── BuildingList.tsx (60 lines)
│       │   │   └── BuildingEditor.tsx (50 lines)
│       │   ├── design/
│       │   │   ├── BuildingTypesConfig.tsx (100 lines)
│       │   │   ├── BuildingTypeCard.tsx (50 lines)
│       │   │   ├── BuildingTypeForm.tsx (60 lines)
│       │   │   ├── OptimizationGoalsPanel.tsx (100 lines)
│       │   │   ├── GoalsList.tsx (60 lines)
│       │   │   └── GoalEditor.tsx (50 lines)
│       │   └── navigation/
│       │       ├── TabNavigator.tsx (60 lines)
│       │       ├── TabPanel.tsx (40 lines)
│       │       └── SimulationControls.tsx (60 lines)
│       └── SidebarLayout.tsx (< 80 lines) ✅
```

## Testing Strategy

### Before Refactor
- Hard to test: 1 test per 409-line component
- Low coverage due to complexity

### After Refactor
- Easy to test: 1 test per small component
- Each form can be tested in isolation
- Mock store easily with hooks

**Example Test**:
```tsx
// Before: Complex test setup
test('PrepTab handles project name change', () => {
  // Need to mock entire component
  // Need to find nested input
  // Hard to isolate behavior
});

// After: Simple test
test('ProjectInfoForm updates name', () => {
  render(<ProjectInfoForm />);
  const input = screen.getByLabelText('Proje Adı');
  fireEvent.change(input, { target: { value: 'New Name' } });
  expect(mockSetProjectInfo).toHaveBeenCalledWith({ name: 'New Name' });
});
```

## Performance Improvements

### 1. React.memo() on Forms
Prevent unnecessary re-renders:
```tsx
export const ProjectInfoForm = React.memo(() => {
  // Only re-renders when props change
});
```

### 2. useCallback for Handlers
Stable references for child components:
```tsx
const handleChange = useCallback((value: string) => {
  setProjectInfo({ name: value });
}, [setProjectInfo]);
```

### 3. Code Splitting
Lazy load heavy forms:
```tsx
const SiteParametersForm = lazy(() => import('./forms/SiteParametersForm'));
```

## Success Metrics

### Code Quality
- ✅ No component > 200 lines
- ✅ Average component size < 100 lines
- ✅ Test coverage > 80%

### Developer Experience
- ✅ Easier to find code
- ✅ Faster to make changes
- ✅ Less merge conflicts

### Performance
- ✅ Reduced re-renders
- ✅ Better code splitting
- ✅ Faster build times

## Migration Path

### Backward Compatibility
All changes are internal - no API changes:
```tsx
// App.tsx - NO CHANGES NEEDED
<OptimizationResults {...props} />
```

### Gradual Migration
1. Week 1: PrepTab refactor
2. Week 2: SidebarLayout + DesignTab
3. Week 3: DrawingTools
4. Week 4: Testing + cleanup

### Rollback Strategy
Each refactor is a separate commit:
- Easy to revert if issues
- Can cherry-pick specific changes
- No big-bang deployment

## Next Steps

1. ✅ Create this document
2. ⏭️ Start with ProjectInfoForm extraction
3. ⏭️ Test in isolation
4. ⏭️ Update PrepTab to use it
5. ⏭️ Repeat for other forms

---

**Status**: Planning complete, ready for implementation
**Estimated Effort**: 3-4 weeks
**Impact**: High - Better maintainability, testability, performance
