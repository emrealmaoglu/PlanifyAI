import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import * as mapboxgl from 'mapbox-gl';
import { useEffect, useRef, useState } from 'react';

// CSS imports are handled in index.css

interface UseMapInitializationProps {
    mapContainer: React.RefObject<HTMLDivElement | null>;
    mapboxToken: string;
    initialCenter: [number, number];
    initialZoom: number;
    onGeocoderResult?: (e: any) => void;
}

interface UseMapInitializationResult {
    map: mapboxgl.Map | null;
    isMapLoaded: boolean;
}

export const useMapInitialization = ({
    mapContainer,
    mapboxToken,
    initialCenter,
    initialZoom,
    onGeocoderResult
}: UseMapInitializationProps): UseMapInitializationResult => {
    const map = useRef<mapboxgl.Map | null>(null);
    const [isMapLoaded, setIsMapLoaded] = useState(false);

    useEffect(() => {
        if (map.current || !mapContainer.current) return;

        console.log("Initializing Mapbox map...");

        // Handle "import * as" behavior compatibility
        const mb = (mapboxgl as any).default || mapboxgl;
        mb.accessToken = mapboxToken;

        try {
            // 1. Initialize Map
            const mapInstance = new mb.Map({
                container: mapContainer.current,
                style: 'mapbox://styles/mapbox/navigation-night-v1',
                center: initialCenter,
                zoom: initialZoom,
                pitch: 55,
                bearing: -10,
                projection: { name: 'globe' } as any // Optional: for nicer globe view at low zoom
            });
            map.current = mapInstance;

            // Error Handling
            mapInstance.on('error', (e: any) => {
                // Suppress 403/404 for tiles
                if (e.error?.message?.includes('403') || e.error?.message?.includes('404')) {
                    return;
                }
                if (e.sourceId) {
                    console.warn('Map source error:', e.sourceId, e.error);
                }
            });

            mapInstance.on('load', () => {
                console.log("Map loaded, initializing plugins...");

                // 2. Geocoder
                try {
                    if (MapboxGeocoder) {
                        const geocoder = new MapboxGeocoder({
                            accessToken: mapboxToken,
                            mapboxgl: mb as any,
                            countries: 'tr',
                            language: 'tr',
                            types: 'poi,address,place,locality',
                            proximity: { longitude: 33.7715, latitude: 41.4245 }, // Default bias
                            placeholder: 'Kampüs içinde ara (Örn: Rektörlük)',
                            marker: false
                        });
                        mapInstance.addControl(geocoder, 'top-left');

                        if (onGeocoderResult) {
                            geocoder.on('result', onGeocoderResult);
                        }
                    }
                } catch (err) {
                    console.error("Error initializing MapboxGeocoder:", err);
                }

                // 3. Terrain & Atmosphere
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

                // Initial Camera Ease
                mapInstance.easeTo({ pitch: 60, bearing: -15, duration: 2000 });

                setIsMapLoaded(true);
            });

        } catch (err) {
            console.error("Critical Error initializing Mapbox:", err);
        }

        return () => {
            console.log("Cleaning up Mapbox instance...");
            if (map.current) {
                map.current.remove();
                map.current = null;
            }
            setIsMapLoaded(false);
        };
    }, [mapContainer, mapboxToken]); // initCenter/Zoom are initial only, shouldn't trigger re-init

    return { map: map.current, isMapLoaded };
};
