import React, { useEffect, useRef, useState } from 'react';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';
import { config } from '../config';


// Constraint type colors
const CONSTRAINT_COLORS: Record<string, string> = {
    exclusion: '#FF4444',
    preferred: '#44FF44',
    green_space: '#228B22',
    parking: '#888888',
    utility: '#FFA500',
    fixed_building: '#4444FF'
};

interface DrawingToolsProps {
    map: mapboxgl.Map | null;
    sessionId: string;
    onConstraintAdded?: (constraint: any) => void;
    onConstraintRemoved?: (id: string) => void;
}

export const DrawingTools: React.FC<DrawingToolsProps> = ({
    map,
    sessionId,
    onConstraintAdded,
    onConstraintRemoved
}) => {
    const draw = useRef<MapboxDraw | null>(null);
    const [activeMode, setActiveMode] = useState<string>('simple_select');
    const [constraintType, setConstraintType] = useState<string>('exclusion');

    // Initialize drawing tools
    useEffect(() => {
        if (!map) return;

        // Check if control already exists
        if (draw.current) return;

        draw.current = new MapboxDraw({
            displayControlsDefault: false,
            controls: {
                polygon: true,
                trash: true
            },
            styles: [
                // Polygon fill
                {
                    id: 'gl-draw-polygon-fill',
                    type: 'fill',
                    filter: ['==', '$type', 'Polygon'],
                    paint: {
                        'fill-color': ['coalesce', ['get', 'user_color'], '#3bb2d0'],
                        'fill-opacity': 0.3
                    }
                },
                // Polygon outline
                {
                    id: 'gl-draw-polygon-stroke',
                    type: 'line',
                    filter: ['==', '$type', 'Polygon'],
                    paint: {
                        'line-color': ['coalesce', ['get', 'user_color'], '#3bb2d0'],
                        'line-width': 2
                    }
                },
                // Vertex points
                {
                    id: 'gl-draw-polygon-and-line-vertex-active',
                    type: 'circle',
                    filter: ['==', 'meta', 'vertex'],
                    paint: {
                        'circle-radius': 6,
                        'circle-color': '#fff',
                        'circle-stroke-color': '#3bb2d0',
                        'circle-stroke-width': 2
                    }
                }
            ]
        });

        map.addControl(draw.current, 'top-right');

        // Handle draw events
        map.on('draw.create', handleDrawCreate);
        map.on('draw.delete', handleDrawDelete);
        map.on('draw.update', handleDrawUpdate);

        return () => {
            if (draw.current && map) {
                try {
                    map.removeControl(draw.current);
                } catch (e) {
                    // Ignore if map is already removed
                }
            }
        };
    }, [map]);

    // Handle polygon creation
    const handleDrawCreate = async (e: any) => {
        const feature = e.features[0];
        if (!feature) return;

        const coordinates = feature.geometry.coordinates[0];

        try {
            const response = await fetch(`${config.apiBaseUrl}/api/constraints/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    constraint_type: constraintType,
                    coordinates: coordinates,
                    name: `${constraintType}_${Date.now()}`
                })
            });

            const result = await response.json();

            // Update feature with server ID and color
            if (draw.current) {
                draw.current.setFeatureProperty(
                    feature.id,
                    'constraint_id',
                    result.constraint_id
                );
                draw.current.setFeatureProperty(
                    feature.id,
                    'user_color',
                    CONSTRAINT_COLORS[constraintType]
                );
                // Force redraw to apply styles
                const f = draw.current.get(feature.id);
                if (f) {
                    draw.current.add(f);
                }
            }

            if (onConstraintAdded) {
                onConstraintAdded(result);
            }
        } catch (error) {
            console.error('Failed to save constraint:', error);
        }
    };

    // Handle polygon deletion
    const handleDrawDelete = async (e: any) => {
        for (const feature of e.features) {
            const constraintId = feature.properties?.constraint_id;
            if (constraintId) {
                try {
                    await fetch(`${config.apiBaseUrl}/api/constraints/remove/${sessionId}/${constraintId}`, {
                        method: 'DELETE'
                    });

                    if (onConstraintRemoved) {
                        onConstraintRemoved(constraintId);
                    }
                } catch (error) {
                    console.error('Failed to delete constraint:', error);
                }
            }
        }
    };

    // Handle polygon update (drag/reshape)
    const handleDrawUpdate = async (e: any) => {
        // Could implement update logic here
        console.log('Constraint updated:', e.features);
    };

    // Start drawing a new constraint
    const startDrawing = (type: string) => {
        setConstraintType(type);
        if (draw.current) {
            draw.current.changeMode('draw_polygon');
            setActiveMode('draw_polygon');
        }
    };

    return (
        <div className="drawing-tools" style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            zIndex: 1,
            backgroundColor: 'white',
            padding: '10px',
            borderRadius: '4px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
            <div className="tool-header" style={{ marginBottom: '10px' }}>
                <h3 style={{ margin: 0 }}>🎨 God Mode</h3>
                <p style={{ margin: 0, fontSize: '0.8em', color: '#666' }}>Draw zones on the map</p>
            </div>

            <div className="tool-buttons" style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {Object.entries(CONSTRAINT_COLORS).map(([type, color]) => (
                    <button
                        key={type}
                        className={`tool-btn ${type} ${constraintType === type ? 'active' : ''}`}
                        onClick={() => startDrawing(type)}
                        style={{
                            borderColor: color,
                            borderLeft: `4px solid ${color}`,
                            padding: '5px 10px',
                            backgroundColor: constraintType === type ? '#f0f0f0' : 'white',
                            cursor: 'pointer',
                            textAlign: 'left'
                        }}
                    >
                        {type === 'exclusion' && '🚫 Exclusion'}
                        {type === 'preferred' && '✅ Preferred'}
                        {type === 'green_space' && '🌳 Green Space'}
                        {type === 'parking' && '🅿️ Parking'}
                        {type === 'utility' && '⚡ Utility'}
                        {type === 'fixed_building' && '🏢 Fixed Bldg'}
                    </button>
                ))}
            </div>

            <div className="tool-info" style={{ marginTop: '10px', fontSize: '0.8em', color: '#666' }}>
                <small>
                    {activeMode === 'draw_polygon'
                        ? 'Click to add points, double-click to finish'
                        : 'Select a zone type to start drawing'}
                </small>
            </div>
        </div>
    );
};

export default DrawingTools;
