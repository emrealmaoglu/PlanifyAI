import { buildingsToGeoJSON, roadsToGeoJSON } from '../utils/geoJsonConverter';
import type { Building, Road } from '../types/optimization';
import { describe, test, expect } from 'vitest';

describe('geoJsonConverter', () => {
    test('buildingsToGeoJSON creates valid FeatureCollection', () => {
        const buildings: Building[] = [{
            id: 1,
            building_type: 'academic',
            shape_type: 'h_shape',
            floors: 4,
            height: 14,
            area: 1200,
            centroid: { x: 100, y: 100 },
            orientation: 0,
            geometry: {
                type: 'Polygon',
                coordinates: [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
            }
        }];

        const result = buildingsToGeoJSON(buildings);

        expect(result.type).toBe('FeatureCollection');
        expect(result.features).toHaveLength(1);
        expect(result.features[0].properties?.color).toBe('#3A7BC8');
        expect(result.features[0].properties?.height).toBe(14);
    });

    test('roadsToGeoJSON creates valid FeatureCollection', () => {
        const roads: Road[] = [{
            id: 1,
            width: 6,
            geometry: {
                type: 'LineString',
                coordinates: [[0, 0], [100, 0]]
            }
        }];

        const result = roadsToGeoJSON(roads);

        expect(result.type).toBe('FeatureCollection');
        expect(result.features).toHaveLength(1);
        expect(result.features[0].geometry.type).toBe('LineString');
    });
});
