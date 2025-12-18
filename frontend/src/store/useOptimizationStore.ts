import { create } from 'zustand';
import { BUILDING_TYPES } from '../config/buildingConfig';
import type { Gateway, BoundaryGeoJSON } from '../types';

// --- Types ---
interface ProjectInfo {
    name: string;
    description: string;
}

interface SiteParameters {
    setback_front: number;
    setback_side: number;
    setback_rear: number;
}

interface OptimizationGoals {
    COMPACTNESS: number;
    SOLAR_GAIN: number;
    WIND_COMFORT: number;
    ADJACENCY: number;
}

interface AnalysisFlags {
    solar: boolean;
    wind: boolean;
    walkability: boolean;
}

// GeoJSON Feature Collection from OSM Context API
interface GeoContextFull {
    type: 'FeatureCollection';
    features: GeoJSON.Feature[];
    center?: { lat: number; lng: number };
    name?: string;
}

// Simple boundary point
interface Point {
    x: number;
    y: number;
}

interface OptimizationState {
    // --- Data (The Payload) ---
    projectInfo: ProjectInfo;
    geoContext: { latitude: number; longitude: number; radius: number };
    siteParameters: SiteParameters;
    optimizationGoals: OptimizationGoals;
    buildingCounts: Record<string, number>;
    analysisFlags: AnalysisFlags;

    // --- Preview/Search Context (GeoJSON from API) ---
    previewContext: GeoContextFull | null;
    setPreviewContext: (ctx: GeoContextFull | null) => void;

    // --- Boundary Points (for polygon drawing) ---
    boundary: Point[];
    setBoundary: (points: Point[]) => void;

    // --- Interactive Site Prep State ---
    customBoundary: BoundaryGeoJSON | null;
    hiddenBuildingIds: string[];
    keptBuildingIds: string[];
    gateways: Gateway[];
    isBoundaryEditing: boolean;
    isDemolitionMode: boolean;

    // --- UI State ---
    activeDrawMode: 'exclusion' | 'preservation' | 'boundary' | null;
    activeTab: 'prep' | 'design';

    // --- Actions ---
    setProjectInfo: (info: Partial<ProjectInfo>) => void;
    setGeoContext: (ctx: Partial<{ latitude: number; longitude: number; radius: number }>) => void;

    setSiteParameter: (key: keyof SiteParameters, value: number) => void;
    setOptimizationGoal: (key: keyof OptimizationGoals, value: number) => void;

    incrementBuilding: (id: string) => void;
    decrementBuilding: (id: string) => void;

    setDrawMode: (mode: 'exclusion' | 'preservation' | 'boundary' | null) => void;
    setActiveTab: (tab: 'prep' | 'design') => void;
    toggleAnalysis: (key: keyof AnalysisFlags) => void;

    // --- Site Prep Actions ---
    setCustomBoundary: (geojson: BoundaryGeoJSON | null) => void;
    setGateways: (list: Gateway[]) => void;
    toggleHiddenBuilding: (id: string) => void;
    toggleKeptBuilding: (id: string) => void;
    setBoundaryEditing: (isEditing: boolean) => void;
    setDemolitionMode: (isDemolition: boolean) => void;

    clearAllExisting: boolean;
    setClearAllExisting: (clear: boolean) => void;

    existingBuildings: any[]; // Using any[] for now to avoid circular dependency with types, or define a simple type
    setExistingBuildings: (buildings: any[]) => void;
    updateBuilding: (id: string, updates: { name?: string; type?: string }) => void;
}

// --- Initial State ---
const initialCounts: Record<string, number> = {};
Object.values(BUILDING_TYPES).forEach(type => {
    initialCounts[type.id] = type.defaultCount;
});

export const useOptimizationStore = create<OptimizationState>((set) => ({
    // Initial Data
    projectInfo: {
        name: "Yeni Kampüs Projesi",
        description: ""
    },
    geoContext: {
        latitude: 0,
        longitude: 0,
        radius: 500
    },
    siteParameters: {
        setback_front: 5.0,
        setback_side: 3.0,
        setback_rear: 3.0
    },
    optimizationGoals: {
        COMPACTNESS: 0.5,
        SOLAR_GAIN: 0.0,
        WIND_COMFORT: 0.0,
        ADJACENCY: 0.5
    },
    buildingCounts: initialCounts,
    analysisFlags: {
        solar: false,
        wind: false,
        walkability: false
    },

    // Preview/Search Context (GeoJSON from API)
    previewContext: null,
    setPreviewContext: (ctx) => set({ previewContext: ctx }),

    // Boundary Points
    boundary: [],
    setBoundary: (points) => set({ boundary: points }),

    // Initial UI State
    activeDrawMode: null,
    activeTab: 'prep',

    // Site Prep Initial State
    customBoundary: null,
    hiddenBuildingIds: [],
    keptBuildingIds: [], // New: Buildings to preserve during Clear All
    existingBuildings: [], // New: Store fetched buildings for the list UI
    gateways: [],
    isBoundaryEditing: false,
    isDemolitionMode: false,

    // --- Actions ---
    setProjectInfo: (info) => set((state) => ({
        projectInfo: { ...state.projectInfo, ...info }
    })),

    setGeoContext: (ctx) => set((state) => ({
        geoContext: { ...state.geoContext, ...ctx }
    })),

    setSiteParameter: (key, value) => set((state) => ({
        siteParameters: { ...state.siteParameters, [key]: value }
    })),

    setOptimizationGoal: (key, value) => set((state) => ({
        optimizationGoals: { ...state.optimizationGoals, [key]: value }
    })),

    incrementBuilding: (id) => set((state) => {
        const current = state.buildingCounts[id] || 0;
        const typeConfig = Object.values(BUILDING_TYPES).find(t => t.id === id);
        const limit = typeConfig?.limit;

        if (limit !== null && limit !== undefined && current >= limit) {
            return state;
        }
        return { buildingCounts: { ...state.buildingCounts, [id]: current + 1 } };
    }),

    decrementBuilding: (id) => set((state) => {
        const current = state.buildingCounts[id] || 0;
        if (current <= 0) return state;
        return { buildingCounts: { ...state.buildingCounts, [id]: current - 1 } };
    }),

    setDrawMode: (mode) => set({ activeDrawMode: mode }),

    setActiveTab: (tab) => set({ activeTab: tab }),

    toggleAnalysis: (key) => set((state) => ({
        analysisFlags: {
            ...state.analysisFlags,
            [key]: !state.analysisFlags[key]
        }
    })),

    // --- Site Prep Actions Implementation ---
    setCustomBoundary: (geojson) => set({ customBoundary: geojson }),

    setGateways: (list) => set({ gateways: list }),

    toggleHiddenBuilding: (id) => set((state) => {
        const exists = state.hiddenBuildingIds.includes(id);
        if (exists) {
            return { hiddenBuildingIds: state.hiddenBuildingIds.filter(hid => hid !== id) };
        } else {
            // If hiding, remove from kept list if present
            return {
                hiddenBuildingIds: [...state.hiddenBuildingIds, id],
                keptBuildingIds: state.keptBuildingIds.filter(kid => kid !== id)
            };
        }
    }),

    toggleKeptBuilding: (id) => set((state) => {
        const exists = state.keptBuildingIds.includes(id);
        if (exists) {
            return { keptBuildingIds: state.keptBuildingIds.filter(kid => kid !== id) };
        } else {
            // If keeping, remove from hidden list if present
            return {
                keptBuildingIds: [...state.keptBuildingIds, id],
                hiddenBuildingIds: state.hiddenBuildingIds.filter(hid => hid !== id)
            };
        }
    }),

    setBoundaryEditing: (isEditing) => set({ isBoundaryEditing: isEditing }),

    setDemolitionMode: (isDemolition) => set({ isDemolitionMode: isDemolition }),

    clearAllExisting: false,
    setClearAllExisting: (clear) => set({ clearAllExisting: clear }),

    setExistingBuildings: (buildings) => set({ existingBuildings: buildings }),

    updateBuilding: (id, updates) => set((state) => ({
        existingBuildings: state.existingBuildings.map((b) =>
            String(b.id) === id ? { ...b, ...updates } : b
        )
    }))
}));
