import * as mapboxgl from 'mapbox-gl';
import { useEffect } from 'react';
import { useOptimizationStore } from '../../store/useOptimizationStore';
import { useMapContext } from '../map/MapContext';

/**
 * ViolationStyling
 * - optimization-results source'u için ihlal (violations) outline'ı ekler
 * - optimized-buildings layer'ındaki binaların rengini violations'a göre günceller
 */
export const ViolationStyling: React.FC = () => {
    const { map, isMapLoaded } = useMapContext();
    const { previewContext } = useOptimizationStore();

    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const optimizedLayerId = 'optimized-buildings';
        const violationLayerId = 'violation-outlines';
        const srcId = 'optimization-results';

        // optimized results source yoksa çık
        const src = map.getSource(srcId) as mapboxgl.GeoJSONSource | undefined;
        if (!src) return;

        // Violation outline layer yoksa ekle
        if (!map.getLayer(violationLayerId)) {
            map.addLayer({
                'id': violationLayerId,
                'type': 'line',
                'source': srcId,
                'filter': ['has', 'violations'],
                'paint': {
                    'line-color': '#ef4444',
                    'line-width': 4,
                    'line-opacity': [
                        'case',
                        ['>', ['length', ['get', 'violations']], 0],
                        1.0,
                        0
                    ]
                }
            });
        }

        // optimized-buildings layer'ında violation bazlı renklendirme
        if (map.getLayer(optimizedLayerId)) {
            map.setPaintProperty(optimizedLayerId, 'fill-extrusion-color', [
                'case',
                ['has', 'violations'],
                '#fca5a5', // ihlalli binalar için açık kırmızı
                [
                    'match', ['get', 'building_type'],
                    'Faculty', '#3b82f6',
                    'Dormitory', '#f97316',
                    'Library', '#06b6d4',
                    'Dining', '#f59e0b',
                    'Research', '#ec4899',
                    'Sports', '#22c55e',
                    'Rectory', '#9333ea',
                    'Social', '#e11d48',
                    '#6b7280'
                ]
            ]);
        }
    }, [map, isMapLoaded, previewContext]);

    return null;
};

export default ViolationStyling;
