import React, { useEffect, useRef, useState } from 'react';
import * as mapboxgl from 'mapbox-gl';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import SidebarLayout from '../features/cockpit/SidebarLayout';
import SimulationPanel from './SimulationPanel';
import { WindOverlay, SlopeOverlay } from './layers';
import { useToast } from './Toast';
import { useOptimizationStore } from '../store/useOptimizationStore';
import type { BoundaryGeoJSON, Gateway } from '../types';

// CSS imported in index.css to avoid duplication
// import 'mapbox-gl/dist/mapbox-gl.css';
// import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css';
// import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

interface OptimizationResultsProps {
    mapboxToken: string;
    apiBaseUrl: string;
    initialCenter: [number, number];
    initialZoom: number;
}

const OptimizationResults: React.FC<OptimizationResultsProps> = ({
    mapboxToken,
    apiBaseUrl,
    initialCenter,
    initialZoom
}) => {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<mapboxgl.Map | null>(null);
    const draw = useRef<MapboxDraw | null>(null);

    // Store Connection
    const {
        projectInfo,
        geoContext,
        previewContext, // GeoJSON features from API
        buildingCounts,
        analysisFlags,
        siteParameters,
        optimizationGoals,
        setGeoContext, // This is used in fetchContext, so it should remain.
        // New State & Actions
        customBoundary,
        hiddenBuildingIds,
        gateways,
        isBoundaryEditing,
        // isDemolitionMode, // Accessed via getState()
        setCustomBoundary,
        setGateways,
        clearAllExisting,
        setExistingBuildings,
        // existingBuildings, // Removed logic
        keptBuildingIds
    } = useOptimizationStore();

    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('Hazır');
    const [isMapLoaded, setIsMapLoaded] = useState(false);

    // Toast notifications
    const { success, error: showError } = useToast();

    useEffect(() => {
        if (map.current) return;

        // Handle "import * as" behavior
        const mb = (mapboxgl as any).default || mapboxgl;
        mb.accessToken = mapboxToken;

        // 1. HARİTA AYARLARI
        const mapInstance = new mb.Map({
            container: mapContainer.current!,
            style: 'mapbox://styles/mapbox/navigation-night-v1',
            center: initialCenter,
            zoom: initialZoom,
            pitch: 55,
            bearing: -10
        });
        map.current = mapInstance;

        // Suppress Mapbox tile 404 errors (incidents, etc.)
        mapInstance.on('error', (e: any) => {
            // Only log actual source errors, suppress tile loading errors
            if (e.error?.message?.includes('403') || e.error?.message?.includes('404')) {
                return; // Suppress tile loading errors
            }
            if (e.sourceId) {
                console.warn('Map source error:', e.sourceId, e.error);
            }
        });

        mapInstance.on('load', () => {
            console.log("Harita yüklendi, eklentiler başlatılıyor...");
            setIsMapLoaded(true);

            // 2. ARAMA MOTORU (Moved inside load)
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
                        fetchContext(center[1], center[0]);
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

            // Initial Fetch is now handled by a separate useEffect that depends on isMapLoaded

            // Initialize Draw (Moved inside load)
            try {
                if (MapboxDraw) {
                    draw.current = new MapboxDraw({
                        displayControlsDefault: false,
                        controls: { polygon: true, trash: true },
                        userProperties: true
                    });
                    mapInstance.addControl(draw.current, 'top-right');

                    // Draw Update Listener
                    mapInstance.on('draw.update', updateBoundaryFromDraw);
                    mapInstance.on('draw.create', updateBoundaryFromDraw);
                    mapInstance.on('draw.delete', updateBoundaryFromDraw);
                }
            } catch (err) {
                console.error("Error initializing MapboxDraw:", err);
            }

            // --- INTERACTION HANDLERS ---
            mapInstance.on('click', 'existing-buildings', (e: mapboxgl.MapMouseEvent & { features?: mapboxgl.GeoJSONFeature[] }) => {
                const feature = e.features?.[0];
                if (feature && feature.properties?.osm_id) {
                    const osmId = String(feature.properties.osm_id);
                    const name = feature.properties.name || 'İsimsiz Bina';
                    const type = feature.properties.building_type || 'Bilinmiyor';

                    const currentStore = useOptimizationStore.getState();
                    const isKept = currentStore.keptBuildingIds.includes(osmId);
                    const isHidden = currentStore.hiddenBuildingIds.includes(osmId);

                    // Create Popup Content
                    const popupNode = document.createElement('div');
                    popupNode.className = 'p-2 min-w-[160px]';

                    const keepBtnClass = isKept
                        ? 'bg-green-100 text-green-700 border border-green-200'
                        : 'bg-slate-50 text-slate-600 hover:bg-green-50 hover:text-green-600 border border-slate-200';

                    const deleteBtnClass = isHidden
                        ? 'bg-red-100 text-red-700 border border-red-200'
                        : 'bg-slate-50 text-slate-600 hover:bg-red-50 hover:text-red-600 border border-slate-200';

                    popupNode.innerHTML = `
                        <div class="mb-2">
                            <h3 class="font-bold text-sm text-slate-800 leading-tight">${name}</h3>
                            <p class="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">${type}</p>
                        </div>
                        <div class="flex gap-2">
                            <button id="btn-keep-${osmId}" class="flex-1 px-2 py-1.5 text-xs font-medium rounded transition-all ${keepBtnClass}">
                                ${isKept ? 'Korunuyor' : 'Koru'}
                            </button>
                            <button id="btn-delete-${osmId}" class="flex-1 px-2 py-1.5 text-xs font-medium rounded transition-all ${deleteBtnClass}">
                                ${isHidden ? 'Geri Al' : 'Sil'}
                            </button>
                        </div>
                    `;

                    const btnKeep = popupNode.querySelector(`#btn-keep-${osmId}`);
                    const btnDelete = popupNode.querySelector(`#btn-delete-${osmId}`);

                    if (btnKeep) {
                        btnKeep.addEventListener('click', () => {
                            useOptimizationStore.getState().toggleKeptBuilding(osmId);
                            // Close popup to force user to re-click if they want to change again? 
                            // Or just let the map update visual feedback.
                            // Let's keep popup open but maybe update text? 
                            // Re-rendering popup content is hard without React. 
                            // Simple fix: Close popup on action to show "done".
                            popup.remove();
                        });
                    }

                    if (btnDelete) {
                        btnDelete.addEventListener('click', () => {
                            useOptimizationStore.getState().toggleHiddenBuilding(osmId);
                            popup.remove();
                        });
                    }

                    const popup = new mb.Popup({ closeButton: false, maxWidth: '200px' })
                        .setLngLat(e.lngLat)
                        .setDOMContent(popupNode)
                        .addTo(mapInstance);
                }
            });

            mapInstance.on('mouseenter', 'existing-buildings', () => {
                mapInstance.getCanvas().style.cursor = 'pointer';
            });
            mapInstance.on('mouseleave', 'existing-buildings', () => {
                mapInstance.getCanvas().style.cursor = '';
            });
        });

        // Cleanup function
        return () => {
            console.log("Cleaning up Mapbox instance...");
            mapInstance.remove();
            map.current = null;
            setIsMapLoaded(false);
        };

    }, []);

    // --- INITIAL CONTEXT FETCH ---
    // Separate effect to ensure fetchContext is defined before calling
    useEffect(() => {
        if (!isMapLoaded || !map.current) return;

        const center = map.current.getCenter();
        if (center) {
            console.log("Initial fetch triggered for:", center.lat, center.lng);
            fetchContext(center.lat, center.lng);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isMapLoaded]);

    const updateBoundaryFromDraw = (e: any) => {
        const data = draw.current?.getAll();
        console.log("Draw Update:", e.type, data);
        if (data && data.features.length > 0) {
            setCustomBoundary(data as BoundaryGeoJSON);
            console.log("Custom Boundary Updated in Store:", data);
        }
    };

    // --- 1. DATA SYNC & FETCH ---
    const fetchContext = async (lat: number, lon: number) => {
        setStatus('Bölge taranıyor (OpenStreetMap)...');
        setLoading(true);

        // Update geoContext in store
        setGeoContext({ latitude: lat, longitude: lon });

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

        try {
            const res = await fetch(`${apiBaseUrl}/api/context/fetch?lat=${lat}&lon=${lon}&radius=2000&t=${Date.now()}`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!res.ok) throw new Error("Veri alınamadı");

            const data = await res.json();
            console.log("Context Data:", data);

            if (map.current && data.data) {
                const geojson = data.data as GeoJSON.FeatureCollection;

                // CRITICAL FIX: Assign 'id' to features for setFeatureState to work
                geojson.features.forEach((f: any) => {
                    if (f.properties && f.properties.osm_id) {
                        f.id = f.properties.osm_id;
                    }
                });

                // Extract Boundary & Gateways
                const boundaryFeature = geojson.features.find((f: any) => f.properties.layer === 'boundary');
                const gatewayFeatures = geojson.features.filter((f: any) => f.properties.layer === 'gateway');

                // Sync Store
                if (boundaryFeature) {
                    setCustomBoundary({
                        type: 'FeatureCollection',
                        features: [boundaryFeature]
                    } as BoundaryGeoJSON);
                }

                // NEW: Populate Existing Buildings List
                console.log("GeoJSON Received:", geojson);
                const buildings = geojson.features.filter((f: any) => f.properties.layer === 'existing_building');
                console.log("Filtered Buildings:", buildings);

                setExistingBuildings(buildings.map((f: any) => ({
                    id: f.properties.osm_id,
                    name: f.properties.name || 'İsimsiz Bina',
                    type: f.properties.building_type
                })));

                if (gatewayFeatures.length > 0) {
                    const gwList: Gateway[] = gatewayFeatures.map((f: any) => ({
                        id: f.properties.osm_id || Math.random().toString(),
                        location: [f.geometry.coordinates[1], f.geometry.coordinates[0]], // [lat, lon]
                        bearing: f.properties.bearing,
                        type: f.properties.type
                    }));
                    setGateways(gwList);
                }

                // Render Map Layers
                renderContextLayers(geojson);
                setStatus('Hazır');
                success('Bağlam verileri yüklündi!');
            }
        } catch (err: any) {
            console.error(err);
            setStatus('Hata: Bağlantı kurulamadı.');
            showError('Bağlam verileri yüklenemedi. Lütfen tekrar deneyin.');
        } finally {
            setLoading(false);
        }
    };

    const renderContextLayers = (geojson: GeoJSON.FeatureCollection) => {
        if (!map.current) return;
        const srcId = 'existing-context';

        if (map.current.getSource(srcId)) {
            (map.current.getSource(srcId) as mapboxgl.GeoJSONSource).setData(geojson);
        } else {
            map.current.addSource(srcId, { type: 'geojson', data: geojson });

            // 1. Green Areas (Grass/Flat) - Hidden in Clear All
            map.current.addLayer({
                'id': 'green-areas-flat',
                'type': 'fill',
                'source': srcId,
                'filter': ['match', ['get', 'entity_type'], ['grass', 'sports'], true, false],
                'paint': {
                    'fill-color': [
                        'match', ['get', 'building_type'],
                        'grass', '#4ade80',
                        'forest', '#166534', // Forest ground
                        'soccer', '#10b981',
                        'basketball', '#f97316',
                        'tennis', '#3b82f6',
                        'pitch', '#22c55e',    // Generic pitch
                        'stadium', '#22c55e',  // Stadium
                        'sports_centre', '#22c55e',
                        'Sports', '#22c55e',
                        '#4ade80'
                    ], 'fill-opacity': 0.5
                }
            });

            // 2. Trees (Forest) - KEPT in Clear All
            map.current.addLayer({
                'id': 'green-areas-trees',
                'type': 'fill-extrusion',
                'source': srcId,
                'filter': ['==', 'entity_type', 'forest'],
                'paint': {
                    'fill-extrusion-color': '#15803d',
                    'fill-extrusion-height': 6,
                    'fill-extrusion-opacity': 0.8
                }
            });

            // 3. Boundary (Static Neon Line)
            map.current.addLayer({
                'id': 'campus-boundary',
                'type': 'line',
                'source': srcId,
                'filter': ['==', 'layer', 'boundary'],
                'paint': {
                    'line-color': '#00ffff',
                    'line-width': 3,
                    // 'line-dasharray': [2, 2], // User requested solid line
                    'line-opacity': 0.8
                }
            });

            // 4. Buildings
            map.current.addLayer({
                'id': 'existing-buildings',
                'type': 'fill-extrusion',
                'source': srcId,
                'filter': ['==', 'layer', 'existing_building'],
                'paint': {
                    'fill-extrusion-color': [
                        'match', ['get', 'building_type'],
                        'Rectory', '#9333ea',
                        'Faculty', '#3b82f6',
                        'Research', '#ec4899',
                        'Social', '#e11d48',
                        'Dormitory', '#f97316',
                        'Library', '#06b6d4',
                        'Dining', '#f59e0b',
                        'Mosque', '#14b8a6',
                        'Residential', '#64748b', // Slate 500
                        'Context', '#475569',     // Slate 600
                        '#374151'
                    ],
                    'fill-extrusion-height': ['get', 'height'],
                    'fill-extrusion-opacity': 0.9
                }
            });

            // 5. Roads
            map.current.addLayer({
                'id': 'existing-roads',
                'type': 'line',
                'source': srcId,
                'filter': ['==', 'layer', 'existing_road'],
                'paint': {
                    'line-color': '#cbd5e1',
                    'line-width': 4
                }
            });

            // 6. Walkways
            map.current.addLayer({
                'id': 'existing-walkways',
                'type': 'line',
                'source': srcId,
                'filter': ['==', 'layer', 'existing_walkway'],
                'paint': {
                    'line-color': '#d1d5db',
                    'line-width': 2,
                    'line-dasharray': [2, 1]
                }
            });
        }
    };

    // --- 2. BOUNDARY EDITING LOGIC ---
    useEffect(() => {
        if (!map.current || !draw.current || !isMapLoaded) return;

        if (isBoundaryEditing) {
            // Enter Edit Mode

            // 1. Lock Map Angle (Keep view fixed)
            map.current.dragRotate.disable();
            map.current.touchZoomRotate.disableRotation();

            // 2. Load Data (Only if empty to prevent re-render loop interrupting drag)
            if (draw.current.getAll().features.length === 0 && customBoundary) {
                draw.current.set(customBoundary);

                // Auto-select to show handles
                const features = draw.current.getAll().features;
                if (features.length > 0) {
                    const id = features[0].id as string;
                    draw.current.changeMode('simple_select', { featureIds: [id] });
                }
            }

            // Hide static layer
            if (map.current.getLayer('campus-boundary')) {
                map.current.setLayoutProperty('campus-boundary', 'visibility', 'none');
            }
        } else {
            // Exit Edit Mode

            // IMPORTANT: Save the edited boundary BEFORE clearing
            const editedData = draw.current.getAll();
            if (editedData && editedData.features.length > 0) {
                setCustomBoundary(editedData as BoundaryGeoJSON);
                console.log("Boundary saved on exit:", editedData);

                // UPDATE: Sync the edited boundary to the map source
                const boundarySourceId = 'custom-boundary-source';
                if (map.current.getSource(boundarySourceId)) {
                    (map.current.getSource(boundarySourceId) as mapboxgl.GeoJSONSource).setData(editedData as any);
                } else {
                    // Create a new source for custom boundary
                    map.current.addSource(boundarySourceId, {
                        type: 'geojson',
                        data: editedData as any
                    });
                    // Add a layer for the custom boundary
                    map.current.addLayer({
                        id: 'custom-boundary-layer',
                        type: 'line',
                        source: boundarySourceId,
                        paint: {
                            'line-color': '#00ff88',
                            'line-width': 4,
                            'line-opacity': 0.9
                        }
                    });
                }
            }

            // 1. Unlock Map Angle
            map.current.dragRotate.enable();
            map.current.touchZoomRotate.enableRotation();

            if (map.current.getLayer('campus-boundary')) {
                map.current.setLayoutProperty('campus-boundary', 'visibility', 'visible');
            }
            draw.current.deleteAll();
        }
    }, [isBoundaryEditing, customBoundary, isMapLoaded, setCustomBoundary]); // Depend on customBoundary to load it initially

    // Separate Effect to Render Custom Boundary when NOT editing (if we want to show the edited version)
    // Actually, the easiest way is:
    // 1. Backend provides initial boundary.
    // 2. User edits -> `customBoundary` updates.
    // 3. We should render `customBoundary` INSTEAD of the backend one if it exists.
    // Let's update the 'campus-boundary' filter to HIDE the backend one if we have a custom one?
    // Or just overlay?
    // Let's leave it simple for now: Edit Mode shows Draw. View Mode shows Static (Backend).
    // If user edits, they should probably stay in Edit Mode or we need to update the static view.
    // For this iteration, let's assume "Edit Mode" is the way to see changes.

    // --- 3. DEMOLITION & CLEAR ALL LOGIC (Filter Based - Reverted from Ghosting) ---
    useEffect(() => {
        if (!map.current || !isMapLoaded) return;

        // Layers to hide when "Clear All" is active
        const layersToHide = ['existing-buildings', 'existing-roads', 'existing-walkways', 'green-areas-flat'];
        const natureLayers = ['green-areas-trees'];
        const maskLayerId = 'ground-mask';

        if (clearAllExisting) {
            // 1. Show Ground Mask (Create if not exists)
            if (!map.current.getLayer(maskLayerId)) {
                if (map.current.getSource('existing-context')) {
                    map.current.addLayer({
                        'id': maskLayerId,
                        'type': 'fill',
                        'source': 'existing-context',
                        'filter': ['==', 'layer', 'boundary'],
                        'paint': {
                            'fill-color': '#ecfccb', // Light lime/green (empty land)
                            'fill-opacity': 0.9 // High opacity to cover base map
                        }
                    }, 'green-areas-trees'); // Place BELOW trees
                }
            } else {
                map.current.setLayoutProperty(maskLayerId, 'visibility', 'visible');
            }

            // 2. Hide Man-Made + Grass
            layersToHide.forEach(layer => {
                if (map.current?.getLayer(layer)) {
                    // If layer is buildings, we might need to keep some visible
                    if (layer === 'existing-buildings' && keptBuildingIds.length > 0) {
                        map.current.setLayoutProperty(layer, 'visibility', 'visible');
                        // Filter to show ONLY kept buildings
                        map.current.setFilter(layer, ['in', ['to-string', ['get', 'osm_id']], ['literal', keptBuildingIds]]);
                    } else {
                        map.current.setLayoutProperty(layer, 'visibility', 'none');
                    }
                }
            });

            // 3. Ensure Nature is Visible
            natureLayers.forEach(layer => {
                if (map.current?.getLayer(layer)) {
                    map.current.setLayoutProperty(layer, 'visibility', 'visible');
                }
            });
        } else {
            // Hide Ground Mask
            if (map.current.getLayer(maskLayerId)) {
                map.current.setLayoutProperty(maskLayerId, 'visibility', 'none');
            }

            // Show All
            [...layersToHide, ...natureLayers].forEach(layer => {
                if (map.current?.getLayer(layer)) {
                    map.current.setLayoutProperty(layer, 'visibility', 'visible');
                    // Reset filter for buildings (show all)
                    if (layer === 'existing-buildings') {
                        map.current.setFilter(layer, ['==', 'layer', 'existing_building']);
                    }
                }
            });

            // Handle individual hidden buildings (when NOT in Clear All mode)
            if (hiddenBuildingIds.length > 0) {
                if (map.current.getLayer('existing-buildings')) {
                    // Filter OUT hidden buildings
                    map.current.setFilter('existing-buildings', [
                        'all',
                        ['==', 'layer', 'existing_building'],
                        ['!', ['in', ['to-string', ['get', 'osm_id']], ['literal', hiddenBuildingIds]]]
                    ]);
                }
            }
        }

    }, [clearAllExisting, keptBuildingIds, hiddenBuildingIds, isMapLoaded]);

    // --- 4. GATEWAY VISUALIZATION ---
    useEffect(() => {
        if (!map.current || !isMapLoaded) return;

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

        if (map.current.getSource(srcId)) {
            (map.current.getSource(srcId) as mapboxgl.GeoJSONSource).setData(geojson);
        } else {
            map.current.addSource(srcId, { type: 'geojson', data: geojson });

            map.current.addLayer({
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
    }, [gateways, isMapLoaded]);

    // --- LAYER OVERLAYS ---
    // WindOverlay and SlopeOverlay components handle wind/slope layers
    // See: components/layers/WindOverlay.tsx, SlopeOverlay.tsx

    // --- 7. PHASE 9: VIOLATION STYLING (Red Outline) ---
    useEffect(() => {
        if (!map.current || !isMapLoaded) return;

        const optimizedLayerId = 'optimized-buildings';
        const violationLayerId = 'violation-outlines';
        const srcId = 'optimization-results';

        // Check for optimized buildings source
        if (!map.current.getSource(srcId)) return;

        // Add violation outline layer if not exists
        if (!map.current.getLayer(violationLayerId)) {
            map.current.addLayer({
                'id': violationLayerId,
                'type': 'line',
                'source': srcId,
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

        // Pulse animation for violations (CSS-based, applied via class)
        if (map.current.getLayer(optimizedLayerId)) {
            map.current.setPaintProperty(optimizedLayerId, 'fill-extrusion-color', [
                'case',
                ['has', 'violations'],
                '#fca5a5',  // Light red for violation buildings
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
    }, [previewContext, isMapLoaded]);

    // --- SIMULATION HANDLING ---
    const handleStartSimulation = async () => {
        setLoading(true);
        setStatus("Simülasyon Başlatılıyor...");
        try {
            const payload = {
                project_name: projectInfo.name,
                description: projectInfo.description,
                latitude: geoContext.latitude,
                longitude: geoContext.longitude,
                radius: geoContext.radius,
                building_counts: buildingCounts,

                // NEW: Send User-Defined Constraints & Weights
                site_parameters: siteParameters,
                optimization_goals: optimizationGoals,

                // NEW: Send Edited Boundary & Hidden Buildings
                boundary_geojson: customBoundary,
                hidden_building_ids: hiddenBuildingIds,
                kept_building_ids: keptBuildingIds,
                clear_all_existing: clearAllExisting,

                enable_solar: analysisFlags.solar,
                enable_wind: analysisFlags.wind,
                enable_walkability: analysisFlags.walkability
            };
            console.log("🚀 Sending Payload:", payload);

            const res = await fetch(`${apiBaseUrl}/api/optimize/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Simülasyon başlatılamadı");
            const data = await res.json();
            setStatus(`İşlem Başladı: ${data.job_id}`);
            success(`Simülasyon başlatıldı! (Job: ${data.job_id})`);
        } catch (err) {
            console.error(err);
            setStatus("Hata oluştu");
            showError('Simülasyon başlatılırken bir hata oluştu');
        } finally {
            setLoading(false);
        }
    };

    // Prepare features for layer components
    const features = previewContext?.features || [];

    return (
        <div className="flex h-screen w-full bg-slate-900 overflow-hidden relative">
            <SidebarLayout onStartSimulation={handleStartSimulation} />
            <div className="flex-1 relative">
                <div ref={mapContainer} className="h-full w-full" />
                <SimulationPanel loading={loading} status={status} />

                {/* Layer Overlay Components (side-effect only) */}
                <WindOverlay
                    map={map.current}
                    isMapLoaded={isMapLoaded}
                    windEnabled={analysisFlags.wind}
                    features={features}
                />
                <SlopeOverlay
                    map={map.current}
                    isMapLoaded={isMapLoaded}
                    slopeEnabled={analysisFlags.walkability}
                    features={features}
                />
            </div>
        </div>
    );
};

export default OptimizationResults;
