import type { Building, Road, Driveway } from '../types/optimization';
import { BUILDING_3D_COLORS } from '../types/optimization';
import type { FeatureCollection, Feature, Polygon, LineString } from 'geojson';

/**
 * Convert buildings to GeoJSON FeatureCollection for Mapbox.
 * Each feature includes properties for 3D extrusion.
 */
export function buildingsToGeoJSON(buildings: Building[]): FeatureCollection<Polygon> {
    return {
        type: 'FeatureCollection',
        features: buildings.map((building): Feature<Polygon> => ({
            type: 'Feature',
            id: building.id,
            properties: {
                id: building.id,
                building_type: building.building_type,
                shape_type: building.shape_type,
                floors: building.floors,
                height: building.height,
                area: building.area,
                color: BUILDING_3D_COLORS[building.building_type] || '#888888'
            },
            geometry: building.geometry
        }))
    };
}

/**
 * Convert roads to GeoJSON FeatureCollection.
 */
export function roadsToGeoJSON(roads: Road[]): FeatureCollection<LineString> {
    return {
        type: 'FeatureCollection',
        features: roads.map((road): Feature<LineString> => ({
            type: 'Feature',
            id: road.id,
            properties: {
                id: road.id,
                width: road.width
            },
            geometry: road.geometry
        }))
    };
}

/**
 * Convert driveways to GeoJSON FeatureCollection.
 */
export function drivewaysToGeoJSON(driveways: Driveway[]): FeatureCollection<LineString> {
    return {
        type: 'FeatureCollection',
        features: driveways.map((driveway, index): Feature<LineString> => ({
            type: 'Feature',
            id: index,
            properties: {
                building_id: driveway.building_id
            },
            geometry: driveway.geometry
        }))
    };
}
