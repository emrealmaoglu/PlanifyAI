import * as mapboxgl from 'mapbox-gl';
import React, { useEffect } from 'react';
import type { Gateway } from '../../../types';
import { useMapContext } from '../MapContext';

interface GatewayLayerProps {
    gateways: Gateway[];
}

export const GatewayLayer: React.FC<GatewayLayerProps> = ({ gateways }) => {
    const { map, isMapLoaded } = useMapContext();

    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const srcId = 'gateways-source';
        const layerId = 'gateways-layer';

        const features = gateways.map(g => ({
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [g.location[1], g.location[0]] // [lon, lat]
            },
            properties: {
                type: g.type,
                bearing: g.bearing
            }
        }));

        const geojson = { type: 'FeatureCollection', features } as any;

        if (map.getSource(srcId)) {
            (map.getSource(srcId) as mapboxgl.GeoJSONSource).setData(geojson);
        } else {
            map.addSource(srcId, { type: 'geojson', data: geojson });

            map.addLayer({
                'id': layerId,
                'type': 'circle',
                'source': srcId,
                'paint': {
                    'circle-radius': 6,
                    'circle-color': '#06b6d4', // Cyan
                    'circle-stroke-width': 2,
                    'circle-stroke-color': '#ffffff'
                }
            });
        }
    }, [map, isMapLoaded, gateways]);

    return null;
};
