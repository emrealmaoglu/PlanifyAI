import { useCallback } from 'react';
import { useOptimizationStore } from '../store/useOptimizationStore';
import type { BoundaryGeoJSON, Gateway } from '../types';

interface UseContextFetcherResult {
    fetchContext: (apiBaseUrl: string, lat: number, lon: number) => Promise<void>;
}

export const useContextFetcher = (): UseContextFetcherResult => {
    const {
        setGeoContext,
        setCustomBoundary,
        setExistingBuildings,
        setGateways,
        setPreviewContext
    } = useOptimizationStore();

    const fetchContext = useCallback(
        async (apiBaseUrl: string, lat: number, lon: number) => {
            // 1) Geo context store’a
            setGeoContext({ latitude: lat, longitude: lon });

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);

            try {
                const res = await fetch(
                    `${apiBaseUrl}/api/context/fetch?lat=${lat}&lon=${lon}&radius=2000&t=${Date.now()}`,
                    { signal: controller.signal }
                );
                // clearTimeout handled in finally

                if (!res.ok) {
                    throw new Error(`Context fetch failed with status ${res.status}`);
                }

                const data = await res.json();
                if (!data?.data) return;

                const geojson = data.data as GeoJSON.FeatureCollection;

                // Feature id fix
                geojson.features.forEach((f: any) => {
                    if (f.properties && f.properties.osm_id) {
                        f.id = f.properties.osm_id;
                    }
                });

                // Boundary
                const boundaryFeature = geojson.features.find(
                    (f: any) => f.properties.layer === 'boundary'
                );
                if (boundaryFeature) {
                    setCustomBoundary({
                        type: 'FeatureCollection',
                        features: [boundaryFeature]
                    } as BoundaryGeoJSON);
                }

                // Existing Buildings
                const buildings = geojson.features.filter(
                    (f: any) => f.properties.layer === 'existing_building'
                );
                setExistingBuildings(
                    buildings.map((f: any) => ({
                        id: f.properties.osm_id,
                        name: f.properties.name || 'İsimsiz Bina',
                        type: f.properties.building_type
                    }))
                );

                // Gateways
                const gatewayFeatures = geojson.features.filter(
                    (f: any) => f.properties.layer === 'gateway'
                );
                if (gatewayFeatures.length > 0) {
                    const gwList: Gateway[] = gatewayFeatures.map((f: any) => ({
                        id: f.properties.osm_id || Math.random().toString(),
                        location: [f.geometry.coordinates[1], f.geometry.coordinates[0]],
                        bearing: f.properties.bearing,
                        type: f.properties.type
                    }));
                    setGateways(gwList);
                }

                // Ana context
                setPreviewContext(geojson);
            } finally {
                clearTimeout(timeoutId);
            }
        },
        [setGeoContext, setCustomBoundary, setExistingBuildings, setGateways, setPreviewContext]
    );

    return { fetchContext };
};
