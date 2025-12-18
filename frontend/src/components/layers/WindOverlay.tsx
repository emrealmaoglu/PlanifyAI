import * as mapboxgl from 'mapbox-gl';
import { useEffect } from 'react';
import { useMapContext } from '../map/MapContext';

interface WindOverlayProps {
    windEnabled: boolean;
    features: GeoJSON.Feature[];
}

/**
 * WindOverlay - Rüzgar yönü ok layer'ı
 *
 * OptimizationResults.tsx'den çıkarıldı (Faz 1.1.6)
 * Sorumluluklar:
 * - Wind arrow icon oluşturma
 * - Wind layer yönetimi
 * - Visibility toggle
 */
export function WindOverlay({
    windEnabled,
    features
}: WindOverlayProps) {
    const { map, isMapLoaded } = useMapContext();

    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const srcId = 'wind-arrows-source';
        const layerId = 'wind-arrows-layer';

        // Filter wind features
        const windFeatures = features.filter(
            (f) => f.properties?.layer === 'wind_grid'
        );

        if (windFeatures.length === 0) return;

        const windGeojson: GeoJSON.FeatureCollection = {
            type: 'FeatureCollection',
            features: windFeatures
        };

        if (map.getSource(srcId)) {
            (map.getSource(srcId) as mapboxgl.GeoJSONSource).setData(windGeojson);
        } else {
            map.addSource(srcId, { type: 'geojson', data: windGeojson });

            // Load arrow icon if not loaded
            if (!map.hasImage('wind-arrow')) {
                const size = 24;
                const canvas = document.createElement('canvas');
                canvas.width = size;
                canvas.height = size;
                const ctx = canvas.getContext('2d')!;

                ctx.fillStyle = '#3b82f6';
                ctx.beginPath();
                ctx.moveTo(size / 2, 0);
                ctx.lineTo(size, size);
                ctx.lineTo(size / 2, size * 0.7);
                ctx.lineTo(0, size);
                ctx.closePath();
                ctx.fill();

                map.addImage('wind-arrow', {
                    width: size,
                    height: size,
                    data: ctx.getImageData(0, 0, size, size).data
                });
            }

            map.addLayer({
                'id': layerId,
                'type': 'symbol',
                'source': srcId,
                'layout': {
                    'icon-image': 'wind-arrow',
                    'icon-size': 0.8,
                    'icon-rotate': ['get', 'rotation'],
                    'icon-rotation-alignment': 'map',
                    'icon-allow-overlap': true
                },
                'paint': {
                    'icon-opacity': 0.8
                }
            });
        }

        // Toggle visibility
        const visibility = windEnabled ? 'visible' : 'none';
        if (map.getLayer(layerId)) {
            map.setLayoutProperty(layerId, 'visibility', visibility);
        }
    }, [map, isMapLoaded, windEnabled, features]);

    return null; // This is a side-effect only component
}

export default WindOverlay;
