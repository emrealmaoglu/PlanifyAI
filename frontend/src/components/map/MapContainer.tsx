import React, { useMemo, useRef } from 'react';
import { useMapInitialization } from '../../hooks/useMapInitialization';
import type { MapContextValue } from './MapContext';
import { MapProvider } from './MapContext';

interface MapContainerProps {
    mapboxToken: string;
    initialCenter: [number, number];
    initialZoom: number;
    onGeocoderResult?: (e: any) => void;
    children?: React.ReactNode;
}

export const MapContainer: React.FC<MapContainerProps> = ({
    mapboxToken,
    initialCenter,
    initialZoom,
    onGeocoderResult,
    children
}) => {
    const mapContainerRef = useRef<HTMLDivElement | null>(null);

    const { map, isMapLoaded } = useMapInitialization({
        mapContainer: mapContainerRef,
        mapboxToken,
        initialCenter,
        initialZoom,
        onGeocoderResult
    });

    const contextValue = useMemo<MapContextValue>(
        () => ({ map, isMapLoaded }),
        [map, isMapLoaded]
    );

    return (
        <div className="flex-1 relative">
            <div ref={mapContainerRef} className="h-full w-full" />
            <MapProvider value={contextValue}>
                {children}
            </MapProvider>
        </div>
    );
};
