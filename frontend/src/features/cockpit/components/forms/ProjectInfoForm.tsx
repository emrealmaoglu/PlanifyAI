/**
 * ProjectInfoForm Component
 *
 * Handles project metadata input (name, description).
 * Extracted from PrepTab to follow Single Responsibility Principle.
 *
 * Responsibilities:
 * - Project name input
 * - Project description textarea
 * - Direct store updates via useOptimizationStore
 *
 * Dependencies: None (uses store directly)
 */

import React from 'react';
import { Home } from 'lucide-react';
import { useOptimizationStore } from '../../../../store/useOptimizationStore';

export const ProjectInfoForm: React.FC = React.memo(() => {
    const { projectInfo, setProjectInfo } = useOptimizationStore();

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                <Home className="w-5 h-5 text-blue-600" />
                Proje Bilgileri
            </h3>

            <div className="space-y-3">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Proje Adı
                    </label>
                    <input
                        type="text"
                        value={projectInfo.name}
                        onChange={(e) => setProjectInfo({ name: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                        placeholder="Örn: Kastamonu Kampüs Yenileme"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Açıklama
                    </label>
                    <textarea
                        value={projectInfo.description}
                        onChange={(e) => setProjectInfo({ description: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors h-24 resize-none"
                        placeholder="Proje hedefleri ve notlar..."
                    />
                </div>
            </div>
        </div>
    );
});

ProjectInfoForm.displayName = 'ProjectInfoForm';
