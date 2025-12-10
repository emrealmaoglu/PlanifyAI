export interface Point {
    x: number;
    y: number;
}

export interface Building {
    type: string;
    position: Point;
    orientation: number;
    area: number;
}

export interface Road {
    points: Point[];
    width: number;
}

export interface Solution {
    solution_id: string;
    buildings: Building[];
    roads: Road[];
    objectives: Record<string, number>;
    constraints: Record<string, number>;
    rank: number;
    crowding_distance: number;
}

export interface OptimizationRequest {
    boundary: {
        points: Point[];
    };
    building_types?: Array<{
        type_id: string;
        name: string;
        min_area: number;
        max_area: number;
        quantity: number;
    }>;
    objectives?: {
        cost: number;
        walkability: number;
        adjacency: number;
        green_space: number;
    };
    config?: {
        population_size: number;
        n_generations: number;
        enable_turkish_standards: boolean;
        enable_parallel: boolean;
        seed?: number;
    };
}

export interface OptimizationProgress {
    status: 'running' | 'completed' | 'failed';
    generation: number;
    total_generations: number;
    best_objectives?: Record<string, number>;
    message: string;
}

export interface OptimizationResponse {
    request_id: string;
    status: 'success' | 'failed';
    solutions: Solution[];
    computation_time: number;
    metadata: Record<string, unknown>;
}

// --- OSM Context Types (Sprint 1 Faz 1.2) ---

export interface OSMFeatureProperties {
    layer: 'boundary' | 'existing_building' | 'gateway' | 'road' | 'green_area' | 'slope_grid' | 'wind_grid';
    osm_id?: string;
    name?: string;
    building_type?: string;
    entity_type?: string;
    bearing?: number;
    type?: string;
    slope?: number;
    [key: string]: unknown; // Allow additional properties
}

export interface OSMFeature extends GeoJSON.Feature {
    properties: OSMFeatureProperties;
}

export interface Gateway {
    id: string;
    location: [number, number]; // [lat, lng]
    bearing?: number;
    type?: string;
}

export interface BoundaryGeoJSON extends GeoJSON.FeatureCollection {
    features: GeoJSON.Feature[];
}

// --- Building List Item (for UI) ---
export interface ExistingBuilding {
    id: string;
    name: string;
    type?: string;
}
