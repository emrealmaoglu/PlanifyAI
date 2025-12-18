import * as mapboxgl from 'mapbox-gl';
import React, { useEffect } from 'react';
import { useOptimizationStore } from '../../../store/useOptimizationStore';
import { useMapContext } from '../MapContext';

interface ExistingContextLayersProps {
    geojson: GeoJSON.FeatureCollection | null;
}

export const ExistingContextLayers: React.FC<ExistingContextLayersProps> = ({
    geojson
}) => {
    const { map, isMapLoaded } = useMapContext();
    const {
        clearAllExisting,
        keptBuildingIds,
        hiddenBuildingIds
    } = useOptimizationStore();

    // 1. Initial Rendering
    useEffect(() => {
        if (!map || !isMapLoaded || !geojson) return;

        const srcId = 'existing-context';

        if (map.getSource(srcId)) {
            (map.getSource(srcId) as mapboxgl.GeoJSONSource).setData(geojson);
        } else {
            map.addSource(srcId, { type: 'geojson', data: geojson });

            // 1. Green Areas (Flat)
            if (!map.getLayer('green-areas-flat')) {
                map.addLayer({
                    'id': 'green-areas-flat',
                    'type': 'fill',
                    'source': srcId,
                    'filter': ['match', ['get', 'entity_type'], ['grass', 'sports'], true, false],
                    'paint': {
                        'fill-color': [
                            'match', ['get', 'building_type'],
                            'grass', '#4ade80',
                            'forest', '#166534',
                            'soccer', '#10b981',
                            'basketball', '#f97316',
                            'tennis', '#3b82f6',
                            'pitch', '#22c55e',
                            'stadium', '#22c55e',
                            'sports_centre', '#22c55e',
                            'Sports', '#22c55e',
                            '#4ade80'
                        ],
                        'fill-opacity': 0.5
                    }
                });
            }

            // 2. Trees (Forest)
            if (!map.getLayer('green-areas-trees')) {
                map.addLayer({
                    'id': 'green-areas-trees',
                    'type': 'fill-extrusion',
                    'source': srcId,
                    'filter': ['==', 'entity_type', 'forest'],
                    'paint': {
                        'fill-extrusion-color': '#15803d',
                        'fill-extrusion-height': 6,
                        'fill-extrusion-opacity': 0.8
                    }
                });
            }

            // 3. Boundary
            if (!map.getLayer('campus-boundary')) {
                map.addLayer({
                    'id': 'campus-boundary',
                    'type': 'line',
                    'source': srcId,
                    'filter': ['==', 'layer', 'boundary'],
                    'paint': {
                        'line-color': '#00ffff',
                        'line-width': 3,
                        'line-opacity': 0.8
                    }
                });
            }

            // 4. Buildings
            if (!map.getLayer('existing-buildings')) {
                map.addLayer({
                    'id': 'existing-buildings',
                    'type': 'fill-extrusion',
                    'source': srcId,
                    'filter': ['==', 'layer', 'existing_building'],
                    'paint': {
                        'fill-extrusion-color': [
                            'match', ['get', 'building_type'],
                            'Rectory', '#9333ea',
                            'Faculty', '#3b82f6',
                            'Research', '#ec4899',
                            'Social', '#e11d48',
                            'Dormitory', '#f97316',
                            'Library', '#06b6d4',
                            'Dining', '#f59e0b',
                            'Mosque', '#14b8a6',
                            'Residential', '#64748b',
                            'Context', '#475569',
                            '#374151'
                        ],
                        'fill-extrusion-height': ['get', 'height'],
                        'fill-extrusion-opacity': 0.9
                    }
                });
            }

            // 5. Roads
            if (!map.getLayer('existing-roads')) {
                map.addLayer({
                    'id': 'existing-roads',
                    'type': 'line',
                    'source': srcId,
                    'filter': ['==', 'layer', 'existing_road'],
                    'paint': {
                        'line-color': '#cbd5e1',
                        'line-width': 4
                    }
                });
            }

            // 6. Walkways
            if (!map.getLayer('existing-walkways')) {
                map.addLayer({
                    'id': 'existing-walkways',
                    'type': 'line',
                    'source': srcId,
                    'filter': ['==', 'layer', 'existing_walkway'],
                    'paint': {
                        'line-color': '#d1d5db',
                        'line-width': 2,
                        'line-dasharray': [2, 1]
                    }
                });
            }
        }
    }, [map, isMapLoaded, geojson]);

    // 2. Visibility / Demolition Logic
    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const layersToHide = ['existing-buildings', 'existing-roads', 'existing-walkways', 'green-areas-flat'];
        const natureLayers = ['green-areas-trees'];
        const maskLayerId = 'ground-mask';

        if (clearAllExisting) {
            // Show Ground Mask
            if (!map.getLayer(maskLayerId)) {
                if (map.getSource('existing-context')) {
                    map.addLayer({
                        'id': maskLayerId,
                        'type': 'fill',
                        'source': 'existing-context',
                        'filter': ['==', 'layer', 'boundary'],
                        'paint': {
                            'fill-color': '#ecfccb',
                            'fill-opacity': 0.9
                        }
                    }, 'green-areas-trees');
                }
            } else {
                map.setLayoutProperty(maskLayerId, 'visibility', 'visible');
            }

            // Hide Man-Made
            layersToHide.forEach(layer => {
                if (map.getLayer(layer)) {
                    if (layer === 'existing-buildings' && keptBuildingIds.length > 0) {
                        map.setLayoutProperty(layer, 'visibility', 'visible');
                        map.setFilter(layer, ['in', ['to-string', ['get', 'osm_id']], ['literal', keptBuildingIds]]);
                    } else {
                        map.setLayoutProperty(layer, 'visibility', 'none');
                    }
                }
            });

            // Ensure Nature Visible
            natureLayers.forEach(layer => {
                if (map.getLayer(layer)) {
                    map.setLayoutProperty(layer, 'visibility', 'visible');
                }
            });
        } else {
            // Hide Mask
            if (map.getLayer(maskLayerId)) {
                map.setLayoutProperty(maskLayerId, 'visibility', 'none');
            }

            // Show All
            [...layersToHide, ...natureLayers].forEach(layer => {
                if (map.getLayer(layer)) {
                    map.setLayoutProperty(layer, 'visibility', 'visible');
                    if (layer === 'existing-buildings') {
                        map.setFilter(layer, ['==', 'layer', 'existing_building']);
                    }
                }
            });

            // Handle Single Hidden Buildings
            if (hiddenBuildingIds.length > 0) {
                if (map.getLayer('existing-buildings')) {
                    map.setFilter('existing-buildings', [
                        'all',
                        ['==', 'layer', 'existing_building'],
                        ['!', ['in', ['to-string', ['get', 'osm_id']], ['literal', hiddenBuildingIds]]]
                    ]);
                }
            }
        }
    }, [map, isMapLoaded, clearAllExisting, keptBuildingIds, hiddenBuildingIds]);

    return null;
};
