# FE-UX-002-A: MapContext & MapContainer Refactor

**Goal:** Eliminate prop drilling of `map` and `isMapLoaded` by introducing a React Context-based architecture.

## Checklist

- [x] **Step 1: Context Definition** <!-- id: 1 -->
    - [x] Create `MapContext.tsx` (Minimal API: map + isMapLoaded) <!-- id: 2 -->
    - [x] Verify build passes (passive code) <!-- id: 3 -->

- [x] **Step 2: MapContainer Implementation** <!-- id: 4 -->
    - [x] Create `MapContainer.tsx` (Wraps `useMapInitialization` and `MapProvider`) <!-- id: 5 -->
    - [x] Replace `useMapInitialization` in `OptimizationResults.tsx` with `MapContainer` <!-- id: 6 -->

- [x] **Step 3: Hook Migration** <!-- id: 7 -->
    - [x] Refactor `useBoundaryEditor` to use `useMapContext` <!-- id: 8 -->
    - [x] Refactor `useBuildingInteraction` to use `useMapContext` <!-- id: 9 -->
    - [x] Update usages in `OptimizationResults.tsx` <!-- id: 10 -->

- [x] **Step 4: Layer Component Migration** <!-- id: 11 -->
    - [x] Refactor `ExistingContextLayers` to use `useMapContext` <!-- id: 12 -->
    - [x] Refactor `GatewayLayer` to use `useMapContext` <!-- id: 13 -->
    - [x] Refactor `WindOverlay` / `SlopeOverlay` to use `useMapContext` (if applicable) <!-- id: 14 -->
    - [x] Cleanup `OptimizationResults.tsx` props <!-- id: 15 -->

- [x] **Step 5: Verification** <!-- id: 16 -->
    - [x] Manual Smoke Test (Map loads, Layers render, Tools work) <!-- id: 17 -->
    - [x] `npm run build` passes <!-- id: 18 -->
