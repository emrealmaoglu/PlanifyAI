import MapboxDraw from '@mapbox/mapbox-gl-draw';
import * as mapboxgl from 'mapbox-gl';
import { useEffect, useRef } from 'react';
import { useMapContext } from '../components/map/MapContext';
import { useOptimizationStore } from '../store/useOptimizationStore';
import type { BoundaryGeoJSON } from '../types';

// Artık parametre yok, map & isMapLoaded context'ten geliyor
export const useBoundaryEditor = () => {
    const { map, isMapLoaded } = useMapContext();
    const draw = useRef<MapboxDraw | null>(null);

    // Store access
    const {
        customBoundary,
        isBoundaryEditing,
        setCustomBoundary
    } = useOptimizationStore();

    // 1. Initialize Draw Plugin
    useEffect(() => {
        if (!map || !isMapLoaded || draw.current) return;

        try {
            if (MapboxDraw) {
                console.log("Initializing MapboxDraw...");
                const drawInstance = new MapboxDraw({
                    displayControlsDefault: false,
                    controls: { polygon: true, trash: true },
                    userProperties: true
                });
                draw.current = drawInstance;
                map.addControl(drawInstance, 'top-right');

                // Draw Event Listeners
                const updateBoundary = (e: any) => {
                    const data = drawInstance.getAll();
                    console.log("Draw Update:", e.type, data);
                    if (data && data.features.length > 0) {
                        setCustomBoundary(data as BoundaryGeoJSON);
                    } else if (e.type === 'draw.delete') {
                        // Boundary tamamen silindi, store'u temizle
                        setCustomBoundary(null);
                        console.log("Custom Boundary cleared from store");
                    }
                };

                map.on('draw.update', updateBoundary);
                map.on('draw.create', updateBoundary);
                map.on('draw.delete', updateBoundary);
            }
        } catch (err) {
            console.error("Error initializing MapboxDraw:", err);
        }

        // We do typically NOT remove the control on unmount because map instance might persist.
        // But if map changes, we should ensure we don't duplicate controls.
        // Step 1 logic didn't clean it up, so we'll keep it simple.

    }, [map, isMapLoaded, setCustomBoundary]);

    // 2. Handle Edit Mode Toggle
    useEffect(() => {
        if (!map || !draw.current || !isMapLoaded) return;

        if (isBoundaryEditing) {
            // --- ENTER EDIT MODE ---

            // Lock Camera
            map.dragRotate.disable();
            map.touchZoomRotate.disableRotation();

            // Load Data into Draw
            // Only if Draw is empty (to avoid overwriting work in progress if store updates)
            if (draw.current.getAll().features.length === 0) {
                let boundaryToLoad: GeoJSON.FeatureCollection | null = null;

                if (customBoundary) {
                    // Önce store'daki custom boundary'yi kullan
                    boundaryToLoad = customBoundary;
                } else {
                    // Store'da yoksa, haritadaki existing-context source'undan boundary'yi al
                    try {
                        const source = map.getSource('existing-context') as mapboxgl.GeoJSONSource;
                        if (source && typeof (source as any)._data !== 'undefined') {
                            const data = (source as any)._data as GeoJSON.FeatureCollection;
                            if (data && data.features) {
                                const boundaryFeatures = data.features.filter(
                                    (f: any) => f.properties?.layer === 'boundary'
                                );
                                if (boundaryFeatures.length > 0) {
                                    boundaryToLoad = {
                                        type: 'FeatureCollection',
                                        features: boundaryFeatures
                                    };
                                    console.log("Loading boundary from existing-context source:", boundaryToLoad);
                                }
                            }
                        }
                    } catch (e) {
                        console.warn("Could not load boundary from existing-context:", e);
                    }
                }

                if (boundaryToLoad) {
                    draw.current.set(boundaryToLoad);

                    // Auto-select for UX
                    const features = draw.current.getAll().features;
                    if (features.length > 0) {
                        const id = features[0].id as string;
                        draw.current.changeMode('simple_select', { featureIds: [id] });
                    }
                }
            }

            // Hide Static Layer
            if (map.getLayer('campus-boundary')) {
                map.setLayoutProperty('campus-boundary', 'visibility', 'none');
            }

        } else {
            // --- EXIT EDIT MODE ---

            // Save final state before clearing
            const editedData = draw.current.getAll();
            const boundarySourceId = 'custom-boundary-source';
            const boundaryLayerId = 'custom-boundary-layer';

            if (editedData && editedData.features.length > 0) {
                setCustomBoundary(editedData as BoundaryGeoJSON);

                // Sync to Map Source (Static View)
                try {
                    // Note: map.getSource returns undefined if not found
                    if (map.getSource(boundarySourceId)) {
                        (map.getSource(boundarySourceId) as mapboxgl.GeoJSONSource).setData(editedData as any);
                    } else {
                        // Create Source & Layer
                        map.addSource(boundarySourceId, {
                            type: 'geojson',
                            data: editedData as any
                        });
                        map.addLayer({
                            id: boundaryLayerId,
                            type: 'line',
                            source: boundarySourceId,
                            paint: {
                                'line-color': '#00ff88',
                                'line-width': 4,
                                'line-opacity': 0.9
                            }
                        });
                    }
                } catch (e) {
                    console.warn("Error syncing custom boundary source:", e);
                }
            } else {
                // Boundary tamamen silindi
                setCustomBoundary(null);
                console.log("Custom Boundary cleared - no features left");

                // Haritadan custom boundary layer ve source'u kaldır
                try {
                    if (map.getLayer(boundaryLayerId)) {
                        map.removeLayer(boundaryLayerId);
                    }
                    if (map.getSource(boundarySourceId)) {
                        map.removeSource(boundarySourceId);
                    }
                } catch (e) {
                    console.warn("Error removing custom boundary source/layer:", e);
                }
            }

            // Unlock Camera
            map.dragRotate.enable();
            map.touchZoomRotate.enableRotation();

            // Show Static Layer only if custom boundary was deleted
            // If custom boundary exists, keep campus-boundary hidden
            if (map.getLayer('campus-boundary')) {
                if (editedData && editedData.features.length > 0) {
                    // Custom boundary var, eski sınırı gizli tut
                    map.setLayoutProperty('campus-boundary', 'visibility', 'none');
                } else {
                    // Custom boundary silindi, eski sınırı göster
                    map.setLayoutProperty('campus-boundary', 'visibility', 'visible');
                }
            }

            // Clear Draw
            draw.current.deleteAll();
        }
    }, [isBoundaryEditing, map, isMapLoaded, customBoundary, setCustomBoundary]);

    return { draw: draw.current };
};
