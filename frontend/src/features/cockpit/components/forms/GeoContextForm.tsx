/**
 * GeoContextForm Component
 *
 * Handles geographic context input (latitude, longitude, radius).
 * Extracted from PrepTab to follow Single Responsibility Principle.
 *
 * Responsibilities:
 * - Latitude/Longitude input
 * - Analysis radius slider
 * - Direct store updates
 *
 * Dependencies: None (uses store directly)
 */

import React from 'react';
import { MapPin } from 'lucide-react';
import { useOptimizationStore } from '../../../../store/useOptimizationStore';

export const GeoContextForm: React.FC = React.memo(() => {
    const { geoContext, setGeoContext } = useOptimizationStore();

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                <MapPin className="w-5 h-5 text-purple-600" />
                Konum ve Kapsam
            </h3>

            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                        Enlem
                    </label>
                    <input
                        type="number"
                        step="0.000001"
                        value={geoContext.latitude}
                        onChange={(e) =>
                            setGeoContext({ latitude: parseFloat(e.target.value) || 0 })
                        }
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-md text-sm"
                    />
                </div>
                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                        Boylam
                    </label>
                    <input
                        type="number"
                        step="0.000001"
                        value={geoContext.longitude}
                        onChange={(e) =>
                            setGeoContext({ longitude: parseFloat(e.target.value) || 0 })
                        }
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-md text-sm"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-slate-700 mb-1 flex justify-between">
                    <span>Analiz Yarıçapı</span>
                    <span className="text-slate-500">{geoContext.radius}m</span>
                </label>
                <input
                    type="range"
                    min="100"
                    max="2000"
                    step="50"
                    value={geoContext.radius}
                    onChange={(e) =>
                        setGeoContext({ radius: parseInt(e.target.value) })
                    }
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                />
                <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span>100m</span>
                    <span>2000m</span>
                </div>
            </div>
        </div>
    );
});

GeoContextForm.displayName = 'GeoContextForm';
