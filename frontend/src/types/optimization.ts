export interface Coordinate {
    x: number;
    y: number;
}

export interface GeoJSONPolygon {
    type: 'Polygon';
    coordinates: number[][][];
}

export interface GeoJSONLineString {
    type: 'LineString';
    coordinates: number[][];
}

export interface Building {
    id: number;
    building_type: 'academic' | 'dormitory' | 'social' | 'admin';
    shape_type: 'h_shape' | 'u_shape' | 'l_shape' | 'rectangular';
    floors: number;
    height: number;
    area: number;
    centroid: Coordinate;
    orientation: number;
    geometry: GeoJSONPolygon;
}

export interface Road {
    id: number;
    width: number;
    geometry: GeoJSONLineString;
}

export interface Driveway {
    building_id: number;
    geometry: GeoJSONLineString;
}

export interface Solution {
    solution_id: string;
    buildings: Building[];
    roads: Road[];
    driveways: Driveway[];
    objectives: Record<string, number>;
    constraints: Record<string, number>;
    rank: number;
    crowding_distance: number;
}

// Building type → color mapping
export const BUILDING_COLORS: Record<string, string> = {
    academic: '#4A90D9',   // Blue - formal/institutional
    dormitory: '#7CB342',  // Green - residential
    social: '#FFA726',     // Orange - vibrant/social
    admin: '#78909C'       // Gray - administrative
};

// Building type → 3D extrusion color (slightly darker for depth)
export const BUILDING_3D_COLORS: Record<string, string> = {
    academic: '#3A7BC8',
    dormitory: '#6BA32F',
    social: '#E89516',
    admin: '#607D8B'
};
