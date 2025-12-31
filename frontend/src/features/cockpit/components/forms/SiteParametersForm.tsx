/**
 * SiteParametersForm Component
 *
 * Handles site parameter input (setbacks, regulatory constraints).
 * Extracted from PrepTab to follow Single Responsibility Principle.
 *
 * Responsibilities:
 * - Setback inputs (front, side, rear)
 * - PAİY (Turkish building code) compliance
 * - Direct store updates via useOptimizationStore
 *
 * Dependencies: None (uses store directly)
 */

import React from 'react';
import { Ruler } from 'lucide-react';
import { useOptimizationStore } from '../../../../store/useOptimizationStore';

export const SiteParametersForm: React.FC = React.memo(() => {
    const { siteParameters, setSiteParameter } = useOptimizationStore();

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                <Ruler className="w-5 h-5 text-emerald-600" />
                Çekme Mesafeleri (Setbacks)
            </h3>
            <p className="text-xs text-slate-500">
                Planlı Alanlar İmar Yönetmeliği standartlarına göre yapı yaklaşma mesafeleri.
            </p>

            <div className="grid grid-cols-3 gap-3">
                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                        Ön Bahçe
                    </label>
                    <div className="relative">
                        <input
                            type="number"
                            step="0.1"
                            min="0"
                            value={siteParameters.setback_front}
                            onChange={(e) =>
                                setSiteParameter('setback_front', parseFloat(e.target.value) || 0)
                            }
                            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-emerald-500 focus:border-emerald-500"
                        />
                        <span className="absolute right-2 top-2 text-xs text-slate-400">m</span>
                    </div>
                </div>

                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                        Yan Bahçe
                    </label>
                    <div className="relative">
                        <input
                            type="number"
                            step="0.1"
                            min="0"
                            value={siteParameters.setback_side}
                            onChange={(e) =>
                                setSiteParameter('setback_side', parseFloat(e.target.value) || 0)
                            }
                            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-emerald-500 focus:border-emerald-500"
                        />
                        <span className="absolute right-2 top-2 text-xs text-slate-400">m</span>
                    </div>
                </div>

                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                        Arka Bahçe
                    </label>
                    <div className="relative">
                        <input
                            type="number"
                            step="0.1"
                            min="0"
                            value={siteParameters.setback_rear}
                            onChange={(e) =>
                                setSiteParameter('setback_rear', parseFloat(e.target.value) || 0)
                            }
                            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-emerald-500 focus:border-emerald-500"
                        />
                        <span className="absolute right-2 top-2 text-xs text-slate-400">m</span>
                    </div>
                </div>
            </div>
        </div>
    );
});

SiteParametersForm.displayName = 'SiteParametersForm';
