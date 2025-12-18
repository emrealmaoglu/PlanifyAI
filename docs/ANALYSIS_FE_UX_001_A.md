# FE-UX-001-A: OptimizationResults Refactor Plan

**Status**: Planning
**Author**: Senior Frontend Architect
**Target Branch**: `feature/fe-ux-001-a-optimization-results-refactor`

---

## 1. High-Level Analysis

The file `frontend/src/components/OptimizationResults.tsx` (~800 lines) has become a classic **God Component**. It violates the Single Responsibility Principle by managing:

### 1.1 Current Responsibilities
1.  **Map Lifecycle Management**: Initialization, styling, camera ease-to, cleanup (`useEffect` L65-253).
2.  **Context Fetching**: API calls to `fetchContext`, data processing, error handling (L278-354).
3.  **Visualization Logic (Layers)**:
    -   Static context (Green areas, buildings, roads) (L356-466).
    -   Gateways (L631-668).
    -   Violations (L675-725).
    -   *Note*: Wind/Slope are already partially extracted but instantiated here.
4.  **Interaction Handling**:
    -   Hover cursors (L237).
    -   Popups with "Keep/Delete" buttons using raw DOM manipulation (L170-235).
5.  **Edit Mode Logic**: MapboxDraw integration, boundary editing state sync, saving draw results store (L468-537).
6.  **Simulation Control**: Handling the "Start Simulation" payload construction (L728-772).
7.  **Simulation Panel Rendering**: Hosting the `SidebarLayout` and `SimulationPanel` (L778-798).

### 1.2 Identified Split Blocks

| Block | Current State | Target Destination |
| :--- | :--- | :--- |
| **Map Initialization** | `useEffect(..., [])` huge block | `hooks/useMapInitialization.ts` |
| **Context API** | `fetchContext` function | `hooks/useContextFetch.ts` (or `store` action) |
| **Existing Layers** | `renderContextLayers` function | `components/layers/ExistingContextLayer.tsx` |
| **Interaction** | `click` listener & Popups | `hooks/useBuildingInteraction.ts` |
| **Boundary Editor** | Draw `useEffect` block | `hooks/useBoundaryEditor.ts` |
| **Gateways** | Gateway `useEffect` | `components/layers/GatewayLayer.tsx` |

### 1.3 State Management Leakage
-   **Global**: `useOptimizationStore` is doing heavy lifting.
-   **Local**: `map`, `draw` refs are local but needed everywhere.
-   **Leak**: Popup logic directly manipulates DOM buttons (`btn-keep-${osmId}`) which call store methods. This is fragile outside of React.

---

## 2. Target Architecture

We will move towards a **Composition-based Architecture** where `OptimizationResults` becomes a layout container (Orchestrator).

### 2.1 File Structure

```text
src/
├── components/
│   ├── map/
│   │   ├── MapContainer.tsx         # The map div + init logic
│   │   ├── MapContext.tsx           # Context to pass map instance down
│   │   ├── layers/
│   │   │   ├── ExistingContextLayers.tsx # Roads, buildings, nature
│   │   │   ├── GatewayLayer.tsx     # Entry points
│   │   │   ├── ViolationLayer.tsx   # Red outlines
│   │   │   ├── CustomBoundaryLayer.tsx # Edited boundary line
│   │   └── interactions/
│   │       ├── BuildingPopup.tsx    # (Logic for popup)
│   │       └── useMapInteraction.ts # Click/Hover handlers
├── hooks/
│   ├── useMapInitialization.ts      # Pure mapbox init
│   ├── useBoundaryEditor.ts         # Draw control logic
│   └── useSimulationRunner.ts       # Start simulation API call logic
```

### 2.2 Detailed Specs

#### `hooks/useMapInitialization.ts`
-   **Responsibility**: Load Mapbox GL, add controls (Zoom, Geocoder), set Terrain/Sky, handle `on('load')`.
-   **Returns**: `{ map: mapboxgl.Map, isLoaded: boolean, mapContainerRef }`.
-   **Testing**: Mock `mapbox-gl` and verify `new Map()` is called with correct options.

#### `hooks/useBuildingInteraction.ts`
-   **Responsibility**: Add click listeners to `existing-buildings`. Create/Remove popups.
-   **Props**: `map` instance.
-   **Improvement**: Use a React Portal for Popups if possible, or keep the efficient pure DOM approach but abstract the HTML generation into a helper `createPopupContent(feature)`.

#### `components/map/MapContainer.tsx`
-   **Responsibility**: Render the `div`, call `useMapInitialization`, and wrap children in a `MapContext.Provider`.
-   **Allows**: Children components to simply `useMapContext()` to get the map instance without passing props deep.

---

## 3. Execution Plan

We will perform this "Open Heart Surgery" in 4 steps.

### Step 1: Base Map Extraction (Safe)
-   Create `useMapInitialization`.
-   Create `MapContainer`.
-   Refactor `OptimizationResults` to use these.
-   **Risk**: Geocoder or Draw control initialization order might break.
-   **Verify**: Map loads, Terrain looks 3D, Geocoder appears.

### Step 2: Editor & Interaction Extraction (Medium)
-   Extract `useBoundaryEditor` (Draw logic).
-   Extract `useBuildingInteraction` (Popup logic).
-   **Risk**: `draw.current` ref sharing. We might need to expose `draw` instance from the hook or store it in context.
-   **Verify**: Drawing polygon updates store. Clicking building shows popup. Buttons work.

### Step 3: Layer Componentization (Refactor)
-   Move `renderContextLayers` -> `ExistingContextLayers`.
-   Move Gateway logic -> `GatewayLayer`.
-   Move Violation styling -> `ViolationLayer`.
-   **Risk**: Layer ordering (z-index). "Ground mask" must be below buildings.
-   **Verify**: Green areas, buildings, and red violation outlines appear correctly.

### Step 4: Cleanup & Context Fetch
-   Move `fetchContext` and `handleStartSimulation` to dedicated hooks or keep in parent if mostly API calls.
-   Final polish of `OptimizationResults.tsx`.

---

## 4. Git Integration

### Branches
-   `feature/fe-ux-001-a-optimization-results-refactor` (Main Branch for this work)

### Commits
-   `refactor(fe): extract map initialization hook`
-   `refactor(fe): separate boundary editor logic`
-   `refactor(fe): componentize map layers`
-   `feat(fe): implement map context provider`

### Documentation Updates
-   **SYSTEM_CONSTITUTION V5.0**: Update `2.1 Directory Structure` to reflect new `components/map/` folder.
-   **ROADMAP**: Mark `FE-UX-001-A` as "In Progress".

---

## 5. Quality Bar
-   **DX**: New dev can open `ExistingContextLayers.tsx` to just change building colors without seeing 800 lines of setup code.
-   **Perf**: React re-renders won't re-initialize map (strict dependency arrays).
-   **Testability**: Hooks can be tested in isolation with `renderHook`.
