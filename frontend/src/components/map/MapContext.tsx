import * as mapboxgl from 'mapbox-gl';
import React, { createContext, useContext } from 'react';

export interface MapContextValue {
    map: mapboxgl.Map | null;
    isMapLoaded: boolean;
}

const MapContext = createContext<MapContextValue | undefined>(undefined);

interface MapProviderProps {
    value: MapContextValue;
    children: React.ReactNode;
}

export const MapProvider: React.FC<MapProviderProps> = ({ value, children }) => {
    return <MapContext.Provider value={value}>{children}</MapContext.Provider>;
};

export const useMapContext = (): MapContextValue => {
    const ctx = useContext(MapContext);
    if (!ctx) {
        throw new Error('useMapContext must be used within a MapProvider');
    }
    return ctx;
};
