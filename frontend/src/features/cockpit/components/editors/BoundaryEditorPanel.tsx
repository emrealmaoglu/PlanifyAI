/**
 * BoundaryEditorPanel Component
 *
 * Handles project boundary editing interface.
 * Extracted from PrepTab to follow Single Responsibility Principle.
 *
 * Responsibilities:
 * - Toggle boundary editing mode
 * - Display editing instructions
 * - Direct store updates via useOptimizationStore
 *
 * Dependencies: None (uses store directly)
 */

import React from 'react';
import { MapPin } from 'lucide-react';
import { useOptimizationStore } from '../../../../store/useOptimizationStore';

export const BoundaryEditorPanel: React.FC = React.memo(() => {
    const { isBoundaryEditing, setBoundaryEditing } = useOptimizationStore();

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                <MapPin className="w-5 h-5 text-orange-600" />
                Saha Sınırları
            </h3>

            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <p className="text-sm text-slate-600 mb-3">
                    Proje sınırlarını düzenlemek için aşağıdaki butonu kullanın.
                </p>

                <button
                    onClick={() => setBoundaryEditing(!isBoundaryEditing)}
                    className={`w-full py-2 px-4 rounded-md font-medium transition-all flex items-center justify-center gap-2 ${
                        isBoundaryEditing
                            ? 'bg-orange-600 text-white shadow-lg shadow-orange-900/20'
                            : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                    }`}
                >
                    <MapPin size={18} />
                    {isBoundaryEditing ? 'Düzenlemeyi Tamamla' : 'Sınırları Düzenle'}
                </button>

                {isBoundaryEditing && (
                    <div className="mt-3 text-xs text-orange-600 bg-orange-50 p-2 rounded border border-orange-100">
                        <strong>Nasıl Kullanılır:</strong>
                        <ul className="list-disc list-inside mt-1 space-y-1">
                            <li>Alanı taşımak için içine tıklayıp sürükleyin.</li>
                            <li>Köşeleri değiştirmek için beyaz noktaları sürükleyin.</li>
                            <li>
                                Yeni köşe eklemek için noktalar arasındaki silik tutamaçları
                                sürükleyin.
                            </li>
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
});

BoundaryEditorPanel.displayName = 'BoundaryEditorPanel';
