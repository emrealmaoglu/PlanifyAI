import { useEffect, useRef, useState } from 'react';
import * as mapboxgl from 'mapbox-gl';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import MapboxDraw from '@mapbox/mapbox-gl-draw';

interface UseMapInitializationProps {
    mapContainerRef: React.RefObject<HTMLDivElement>;
    mapboxToken: string;
    initialCenter: [number, number];
    initialZoom: number;
    onMapLoaded?: () => void;
    onSearchResult?: (lat: number, lng: number) => void;
    onBoundaryUpdate?: (e: any) => void;
}

interface UseMapInitializationReturn {
    map: mapboxgl.Map | null;
    draw: MapboxDraw | null;
    isMapLoaded: boolean;
}

/**
 * useMapInitialization - Mapbox harita başlatma hook'u
 * 
 * OptimizationResults.tsx'den çıkarıldı (Faz 1.1.3)
 * Sorumluluklar:
 * - Mapbox map instance oluşturma
 * - Geocoder ekleme
 * - Terrain/Atmosphere ayarları
 * - MapboxDraw kontrolü
 */
export function useMapInitialization({
    mapContainerRef,
    mapboxToken,
    initialCenter,
    initialZoom,
    onMapLoaded,
    onSearchResult,
    onBoundaryUpdate
}: UseMapInitializationProps): UseMapInitializationReturn {
    const mapRef = useRef<mapboxgl.Map | null>(null);
    const drawRef = useRef<MapboxDraw | null>(null);
    const [isMapLoaded, setIsMapLoaded] = useState(false);

    useEffect(() => {
        if (mapRef.current || !mapContainerRef.current) return;

        // Handle "import * as" behavior
        const mb = (mapboxgl as any).default || mapboxgl;
        mb.accessToken = mapboxToken;

        // 1. MAP SETTINGS
        const mapInstance = new mb.Map({
            container: mapContainerRef.current,
            style: 'mapbox://styles/mapbox/navigation-night-v1',
            center: initialCenter,
            zoom: initialZoom,
            pitch: 55,
            bearing: -10
        });
        mapRef.current = mapInstance;

        mapInstance.on('load', () => {
            console.log("Harita yüklendi, eklentiler başlatılıyor...");
            setIsMapLoaded(true);
            onMapLoaded?.();

            // 2. SEARCH ENGINE (Geocoder)
            try {
                if (MapboxGeocoder) {
                    const geocoder = new MapboxGeocoder({
                        accessToken: mapboxToken,
                        mapboxgl: mb as any,
                        countries: 'tr',
                        language: 'tr',
                        types: 'poi,address,place,locality',
                        proximity: { longitude: 33.7715, latitude: 41.4245 },
                        placeholder: 'Kampüs içinde ara (Örn: Rektörlük)',
                        marker: false
                    });
                    mapInstance.addControl(geocoder, 'top-left');

                    geocoder.on('result', (e: any) => {
                        const { center } = e.result;
                        onSearchResult?.(center[1], center[0]);
                    });
                }
            } catch (err) {
                console.error("Error initializing MapboxGeocoder:", err);
            }

            // 3. TERRAIN & ATMOSPHERE
            try {
                mapInstance.addSource('mapbox-dem', {
                    'type': 'raster-dem',
                    'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
                    'tileSize': 512,
                    'maxzoom': 14
                });
                mapInstance.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });

                mapInstance.addLayer({
                    'id': 'sky',
                    'type': 'sky',
                    'paint': {
                        'sky-type': 'atmosphere',
                        'sky-atmosphere-sun': [0.0, 0.0],
                        'sky-atmosphere-sun-intensity': 15
                    }
                });
            } catch (e) {
                console.warn("Terrain/Sky failed to load:", e);
            }

            // Initial Camera Move
            mapInstance.easeTo({ pitch: 60, bearing: -15, duration: 2000 });

            // 4. DRAWING TOOLS (MapboxDraw)
            try {
                if (MapboxDraw) {
                    drawRef.current = new MapboxDraw({
                        displayControlsDefault: false,
                        controls: { polygon: true, trash: true },
                        userProperties: true
                    });
                    mapInstance.addControl(drawRef.current, 'top-right');

                    // Draw Update Listeners
                    if (onBoundaryUpdate) {
                        mapInstance.on('draw.update', onBoundaryUpdate);
                        mapInstance.on('draw.create', onBoundaryUpdate);
                        mapInstance.on('draw.delete', onBoundaryUpdate);
                    }
                }
            } catch (err) {
                console.error("Error initializing MapboxDraw:", err);
            }
        });

        // Cleanup
        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, [mapContainerRef, mapboxToken, initialCenter, initialZoom]);

    return {
        map: mapRef.current,
        draw: drawRef.current,
        isMapLoaded
    };
}

export default useMapInitialization;
