import * as mapboxgl from 'mapbox-gl';
import { useEffect } from 'react';
import { useMapContext } from '../map/MapContext';

interface SlopeOverlayProps {
    slopeEnabled: boolean;
    features: GeoJSON.Feature[];
}

/**
 * SlopeOverlay - Eğim/Walkability heatmap layer'ı
 *
 * OptimizationResults.tsx'den çıkarıldı (Faz 1.1.6)
 * Sorumluluklar:
 * - Slope data visualization
 * - Color interpolation (0-20% slope)
 * - Visibility toggle
 */
export function SlopeOverlay({
    slopeEnabled,
    features
}: SlopeOverlayProps) {
    const { map, isMapLoaded } = useMapContext();

    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const srcId = 'slope-grid-source';
        const layerId = 'slope-heatmap-layer';

        // Filter slope features
        const slopeFeatures = features.filter(
            (f) => f.properties?.layer === 'slope_grid'
        );

        if (slopeFeatures.length === 0) return;

        const slopeGeojson: GeoJSON.FeatureCollection = {
            type: 'FeatureCollection',
            features: slopeFeatures
        };

        if (map.getSource(srcId)) {
            (map.getSource(srcId) as mapboxgl.GeoJSONSource).setData(slopeGeojson);
        } else {
            map.addSource(srcId, { type: 'geojson', data: slopeGeojson });

            map.addLayer({
                'id': layerId,
                'type': 'circle',
                'source': srcId,
                'paint': {
                    'circle-radius': 12,
                    'circle-color': [
                        'interpolate',
                        ['linear'],
                        ['get', 'slope'],
                        0, '#22c55e',      // Green (0%)
                        0.05, '#84cc16',   // Lime (5%)
                        0.10, '#eab308',   // Yellow (10%)
                        0.15, '#f97316',   // Orange (15% - limit)
                        0.20, '#ef4444'    // Red (20%+)
                    ],
                    'circle-opacity': 0.7
                }
            }, 'existing-buildings'); // Below buildings
        }

        // Toggle visibility
        const visibility = slopeEnabled ? 'visible' : 'none';
        if (map.getLayer(layerId)) {
            map.setLayoutProperty(layerId, 'visibility', visibility);
        }
    }, [map, isMapLoaded, slopeEnabled, features]);

    return null;
}

export default SlopeOverlay;
