import { useEffect } from 'react';

interface ViolationOverlayProps {
    map: any; // mapboxgl.Map
    isMapLoaded: boolean;
    optimizedSourceId?: string;
}

// Building type color mapping
const BUILDING_TYPE_COLORS: Record<string, string> = {
    Faculty: '#3b82f6',
    Dormitory: '#f97316',
    Library: '#06b6d4',
    Dining: '#f59e0b',
    Research: '#ec4899',
    Sports: '#22c55e',
    Rectory: '#9333ea',
    Social: '#e11d48'
};

/**
 * ViolationOverlay - Constraint ihlal gösterimi
 * 
 * OptimizationResults.tsx'den çıkarıldı (Faz 1.1.6)
 * Sorumluluklar:
 * - Kırmızı outline ekleme (ihlalli binalar)
 * - Bina renklerini ihlal durumuna göre güncelleme
 */
export function ViolationOverlay({
    map,
    isMapLoaded,
    optimizedSourceId = 'optimization-results'
}: ViolationOverlayProps) {
    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const optimizedLayerId = 'optimized-buildings';
        const violationLayerId = 'violation-outlines';

        // Check for optimized buildings source
        if (!map.getSource(optimizedSourceId)) return;

        // Add violation outline layer if not exists
        if (!map.getLayer(violationLayerId)) {
            map.addLayer({
                'id': violationLayerId,
                'type': 'line',
                'source': optimizedSourceId,
                'filter': ['has', 'violations'],
                'paint': {
                    'line-color': '#ef4444',  // Red
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

        // Update building colors for violations
        if (map.getLayer(optimizedLayerId)) {
            const colorExpression: mapboxgl.Expression = [
                'case',
                ['has', 'violations'],
                '#fca5a5',  // Light red for violation buildings
                [
                    'match', ['get', 'building_type'],
                    ...Object.entries(BUILDING_TYPE_COLORS).flat(),
                    '#6b7280'  // Default gray
                ]
            ];

            map.setPaintProperty(optimizedLayerId, 'fill-extrusion-color', colorExpression);
        }
    }, [map, isMapLoaded, optimizedSourceId]);

    return null;
}

export default ViolationOverlay;
