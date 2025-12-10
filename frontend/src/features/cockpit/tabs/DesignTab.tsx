
import React from 'react';
import { useOptimizationStore } from "../../../store/useOptimizationStore";
import { BUILDING_TYPES } from "../../../config/buildingConfig";
import { Sliders, Wind, Sun, LayoutGrid, Network, ChevronDown, Plus, Minus, Building2 } from 'lucide-react';

// Accordion component using native HTML details/summary
const Accordion: React.FC<{ title: string; icon: React.ReactNode; defaultOpen?: boolean; children: React.ReactNode }> = ({
    title, icon, defaultOpen = false, children
}) => (
    <details className="group" open={defaultOpen}>
        <summary className="flex items-center justify-between cursor-pointer p-3 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors list-none">
            <span className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                {icon}
                {title}
            </span>
            <ChevronDown className="w-4 h-4 text-slate-400 transition-transform group-open:rotate-180" />
        </summary>
        <div className="pt-3 pb-1">
            {children}
        </div>
    </details>
);

// Building Count Grid Component
const BuildingCountGrid: React.FC = () => {
    const { buildingCounts, incrementBuilding, decrementBuilding } = useOptimizationStore();

    const totalBuildings = Object.values(buildingCounts).reduce((sum, count) => sum + count, 0);

    return (
        <div className="space-y-3">
            {Object.values(BUILDING_TYPES).map((type) => {
                const count = buildingCounts[type.id] || 0;
                const atLimit = type.limit !== null && count >= type.limit;

                return (
                    <div
                        key={type.id}
                        className="flex items-center justify-between p-2 rounded-lg bg-slate-800/30 hover:bg-slate-700/30 transition-colors"
                    >
                        <div className="flex items-center gap-2">
                            <span className="text-lg">{type.icon}</span>
                            <div>
                                <span className="text-sm font-medium text-slate-200">{type.label}</span>
                                {type.limit && (
                                    <span className="text-[10px] text-slate-500 ml-1">(max: {type.limit})</span>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => decrementBuilding(type.id)}
                                disabled={count <= 0}
                                className={`w-7 h-7 rounded-md flex items-center justify-center transition-colors ${count > 0
                                    ? 'bg-slate-700 hover:bg-red-600 text-slate-300 hover:text-white'
                                    : 'bg-slate-800 text-slate-600 cursor-not-allowed'
                                    }`}
                            >
                                <Minus size={14} />
                            </button>

                            <span
                                className="w-8 text-center font-bold text-lg"
                                style={{ color: count > 0 ? type.color : '#64748b' }}
                            >
                                {count}
                            </span>

                            <button
                                onClick={() => incrementBuilding(type.id)}
                                disabled={atLimit}
                                data-testid={`increment-${type.id}`}
                                className={`w-7 h-7 rounded-md flex items-center justify-center transition-colors ${!atLimit
                                    ? 'bg-slate-700 hover:bg-green-600 text-slate-300 hover:text-white'
                                    : 'bg-slate-800 text-slate-600 cursor-not-allowed'
                                    }`}
                            >
                                <Plus size={14} />
                            </button>
                        </div>
                    </div>
                );
            })}

            {/* Total Summary */}
            <div className="mt-4 pt-3 border-t border-slate-700 flex items-center justify-between">
                <span className="text-sm font-medium text-slate-400">Toplam Bina</span>
                <span className={`text-xl font-bold ${totalBuildings > 0 ? 'text-blue-400' : 'text-slate-500'}`}>
                    {totalBuildings}
                </span>
            </div>

            {totalBuildings === 0 && (
                <div className="bg-amber-900/30 border border-amber-600/50 rounded-lg p-2 text-amber-300 text-xs text-center">
                    ⚠️ En az 1 bina seçin
                </div>
            )}
        </div>
    );
};

export const DesignTab: React.FC = () => {
    const {
        optimizationGoals, setOptimizationGoal,
        analysisFlags, toggleAnalysis
    } = useOptimizationStore();

    return (
        <div className="space-y-4 p-4">
            {/* Building Selection - PROMINENT */}
            <Accordion
                title="Bina Seçimi"
                icon={<Building2 className="w-4 h-4 text-blue-400" />}
                defaultOpen={true}
            >
                <p className="text-xs text-slate-500 mb-3">
                    Kampüse yerleştirilecek binaları seçin.
                </p>
                <BuildingCountGrid />
            </Accordion>

            {/* Optimization Priorities Accordion */}
            <Accordion
                title="Optimizasyon Öncelikleri"
                icon={<Sliders className="w-4 h-4 text-indigo-400" />}
                defaultOpen={false}
            >
                <p className="text-xs text-slate-500 mb-4">
                    Algoritmanın hedef ağırlıklarını belirleyin.
                </p>

                <div className="space-y-4">
                    {/* Compactness */}
                    <div>
                        <div className="flex justify-between mb-1">
                            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                                <LayoutGrid className="w-3.5 h-3.5 text-slate-400" />
                                Kompaktlık
                            </label>
                            <span className="text-xs font-bold text-indigo-400">
                                {Math.round(optimizationGoals.COMPACTNESS * 100)}%
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0" max="1" step="0.1"
                            value={optimizationGoals.COMPACTNESS}
                            onChange={(e) => setOptimizationGoal('COMPACTNESS', parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                        />
                    </div>

                    {/* Adjacency */}
                    <div>
                        <div className="flex justify-between mb-1">
                            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                                <Network className="w-3.5 h-3.5 text-slate-400" />
                                İlişki Ağı
                            </label>
                            <span className="text-xs font-bold text-indigo-400">
                                {Math.round(optimizationGoals.ADJACENCY * 100)}%
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0" max="1" step="0.1"
                            value={optimizationGoals.ADJACENCY}
                            onChange={(e) => setOptimizationGoal('ADJACENCY', parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                        />
                    </div>

                    {/* Solar */}
                    <div>
                        <div className="flex justify-between mb-1">
                            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                                <Sun className="w-3.5 h-3.5 text-amber-400" />
                                Güneş Kazanımı
                            </label>
                            <span className="text-xs font-bold text-amber-400">
                                {Math.round(optimizationGoals.SOLAR_GAIN * 100)}%
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0" max="1" step="0.1"
                            value={optimizationGoals.SOLAR_GAIN}
                            onChange={(e) => setOptimizationGoal('SOLAR_GAIN', parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
                        />
                    </div>

                    {/* Wind */}
                    <div>
                        <div className="flex justify-between mb-1">
                            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                                <Wind className="w-3.5 h-3.5 text-sky-400" />
                                Rüzgar Konforu
                            </label>
                            <span className="text-xs font-bold text-sky-400">
                                {Math.round(optimizationGoals.WIND_COMFORT * 100)}%
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0" max="1" step="0.1"
                            value={optimizationGoals.WIND_COMFORT}
                            onChange={(e) => setOptimizationGoal('WIND_COMFORT', parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-500"
                        />
                    </div>
                </div>
            </Accordion>

            {/* Analysis Flags Accordion */}
            <Accordion
                title="Görsel Analizler"
                icon={<span className="text-sm">📊</span>}
                defaultOpen={false}
            >
                <p className="text-xs text-slate-500 mb-3">
                    Haritada gösterilecek analiz katmanları.
                </p>
                <div className="flex gap-2 flex-wrap">
                    <button
                        onClick={() => toggleAnalysis('solar')}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${analysisFlags.solar
                            ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                            : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                            }`}
                    >
                        ☀️ Güneş
                    </button>
                    <button
                        onClick={() => toggleAnalysis('wind')}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${analysisFlags.wind
                            ? 'bg-sky-500/20 border-sky-500/50 text-sky-300'
                            : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                            }`}
                    >
                        💨 Rüzgar
                    </button>
                    <button
                        onClick={() => toggleAnalysis('walkability')}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${analysisFlags.walkability
                            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
                            : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                            }`}
                    >
                        📐 Eğim
                    </button>
                </div>
            </Accordion>
        </div>
    );
};
