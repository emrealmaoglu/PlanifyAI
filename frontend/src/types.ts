import type { FeatureCollection } from 'geojson';

export interface Gateway {
    id: string;
    location: [number, number]; // [lat, lon]
    bearing: number; // radians
    type: 'primary' | 'secondary';
}

export type BoundaryGeoJSON = FeatureCollection;
