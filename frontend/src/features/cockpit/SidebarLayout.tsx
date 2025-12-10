import React, { useRef, useMemo } from 'react';
import { useOptimizationStore } from '../../store/useOptimizationStore';
import { PrepTab } from './tabs/PrepTab';
import { DesignTab } from './tabs/DesignTab';
import { Play, MapPin, Trash2, PenTool, Rocket, Download, Upload, Check, AlertCircle } from 'lucide-react';

interface SidebarLayoutProps {
    onStartSimulation: () => void;
}

// Step configuration
const STEPS = [
    { id: 'scope', label: 'Kapsam', icon: MapPin, description: 'Konum ve sınırları belirle' },
    { id: 'clean', label: 'Temizlik', icon: Trash2, description: 'Mevcut yapıları düzenle' },
    { id: 'design', label: 'Tasarım', icon: PenTool, description: 'Bina ve hedefleri ayarla' },
    { id: 'simulate', label: 'Simülasyon', icon: Rocket, description: 'Optimizasyonu çalıştır' }
] as const;

type StepId = typeof STEPS[number]['id'];

const SidebarLayout: React.FC<SidebarLayoutProps> = ({ onStartSimulation }) => {
    const {
        buildingCounts,
        customBoundary,
        geoContext
    } = useOptimizationStore();

    const fileInputRef = useRef<HTMLInputElement>(null);
    const [currentStep, setCurrentStep] = React.useState<StepId>('scope');

    // Calculate total buildings
    const totalBuildings = useMemo(() =>
        Object.values(buildingCounts).reduce((sum, count) => sum + count, 0),
        [buildingCounts]
    );

    // Step validation
    const stepValidation = useMemo(() => ({
        scope: geoContext.latitude !== 0 && geoContext.longitude !== 0,
        clean: true, // Always valid, optional step
        design: totalBuildings > 0,
        simulate: totalBuildings > 0 && (geoContext.latitude !== 0 || customBoundary !== null)
    }), [geoContext, customBoundary, totalBuildings]);

    // Can proceed to next step?
    const canProceed = (stepId: StepId): boolean => {
        const stepIndex = STEPS.findIndex(s => s.id === stepId);
        const currentIndex = STEPS.findIndex(s => s.id === currentStep);

        // Can always go back
        if (stepIndex <= currentIndex) return true;

        // Check all previous steps are valid
        for (let i = 0; i < stepIndex; i++) {
            if (!stepValidation[STEPS[i].id]) return false;
        }
        return true;
    };

    // Go to step
    const goToStep = (stepId: StepId) => {
        if (canProceed(stepId)) {
            setCurrentStep(stepId);
        }
    };

    // Export scenario
    const handleExport = () => {
        const state = useOptimizationStore.getState();
        const scenario = {
            version: "1.0",
            exportedAt: new Date().toISOString(),
            projectInfo: state.projectInfo,
            buildingCounts: state.buildingCounts,
            siteParameters: state.siteParameters,
            optimizationGoals: state.optimizationGoals,
            analysisFlags: state.analysisFlags,
            geoContext: state.geoContext
        };

        const blob = new Blob([JSON.stringify(scenario, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `planify_scenario_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    // Import scenario
    const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const scenario = JSON.parse(e.target?.result as string);
                const store = useOptimizationStore.getState();

                if (scenario.projectInfo) store.setProjectInfo(scenario.projectInfo);
                if (scenario.siteParameters) {
                    Object.entries(scenario.siteParameters).forEach(([key, value]) => {
                        store.setSiteParameter(key as any, value as number);
                    });
                }
                if (scenario.optimizationGoals) {
                    Object.entries(scenario.optimizationGoals).forEach(([key, value]) => {
                        store.setOptimizationGoal(key as any, value as number);
                    });
                }
                if (scenario.geoContext) store.setGeoContext(scenario.geoContext);

                alert('✅ Senaryo başarıyla yüklendi!');
            } catch {
                alert('❌ Dosya okunamadı. Geçerli bir JSON dosyası seçin.');
            }
        };
        reader.readAsText(file);
        event.target.value = '';
    };

    // Get current step index
    const currentStepIndex = STEPS.findIndex(s => s.id === currentStep);

    return (
        <div className="absolute top-0 left-0 h-full w-96 bg-slate-900/95 backdrop-blur-md border-r border-slate-700 text-white flex flex-col z-20 shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-700">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                        <span className="font-bold text-xl">P</span>
                    </div>
                    <div>
                        <h1 className="font-bold text-xl leading-none tracking-tight">PlanifyAI</h1>
                        <span className="text-xs text-slate-400 font-medium">Akıllı Kampüs Stüdyosu</span>
                    </div>
                </div>

                {/* Save/Load */}
                <div className="flex gap-1">
                    <button onClick={handleExport} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors" title="Dışa Aktar">
                        <Download size={16} className="text-slate-400" />
                    </button>
                    <button onClick={() => fileInputRef.current?.click()} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors" title="Yükle">
                        <Upload size={16} className="text-slate-400" />
                    </button>
                    <input ref={fileInputRef} type="file" accept=".json" onChange={handleImport} className="hidden" />
                </div>
            </div>

            {/* Step Navigator */}
            <div className="px-4 py-3 border-b border-slate-700 bg-slate-800/30">
                <div className="flex items-center justify-between">
                    {STEPS.map((step, index) => {
                        const StepIcon = step.icon;
                        const isActive = step.id === currentStep;
                        const isPast = index < currentStepIndex;
                        const isValid = stepValidation[step.id];
                        const isClickable = canProceed(step.id);

                        return (
                            <React.Fragment key={step.id}>
                                {/* Step Circle */}
                                <button
                                    onClick={() => goToStep(step.id)}
                                    disabled={!isClickable}
                                    className={`relative flex flex-col items-center gap-1 transition-all ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
                                        }`}
                                    title={step.description}
                                >
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isActive
                                        ? 'bg-blue-600 text-white scale-110 shadow-lg shadow-blue-500/30'
                                        : isPast
                                            ? 'bg-green-600 text-white'
                                            : 'bg-slate-700 text-slate-400'
                                        }`}>
                                        {isPast ? <Check size={18} /> : <StepIcon size={18} />}
                                    </div>
                                    <span className={`text-[10px] font-medium ${isActive ? 'text-blue-400' : isPast ? 'text-green-400' : 'text-slate-500'
                                        }`}>
                                        {step.label}
                                    </span>

                                    {/* Validation indicator */}
                                    {isActive && !isValid && (
                                        <AlertCircle size={12} className="absolute -top-1 -right-1 text-amber-400" />
                                    )}
                                </button>

                                {/* Connector Line */}
                                {index < STEPS.length - 1 && (
                                    <div className={`flex-1 h-0.5 mx-1 rounded ${index < currentStepIndex ? 'bg-green-600' : 'bg-slate-700'
                                        }`} />
                                )}
                            </React.Fragment>
                        );
                    })}
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                {(currentStep === 'scope' || currentStep === 'clean') && <PrepTab />}
                {currentStep === 'design' && <DesignTab />}
                {currentStep === 'simulate' && (
                    <div className="p-4 space-y-4">
                        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                            <h3 className="text-lg font-semibold mb-2">Simülasyon Özeti</h3>
                            <div className="space-y-2 text-sm text-slate-300">
                                <div className="flex justify-between">
                                    <span>Toplam Bina:</span>
                                    <span className="font-bold text-white">{totalBuildings}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Konum:</span>
                                    <span className="font-mono text-xs">{geoContext.latitude.toFixed(4)}, {geoContext.longitude.toFixed(4)}</span>
                                </div>
                            </div>
                        </div>

                        {!stepValidation.simulate && (
                            <div className="bg-amber-900/30 border border-amber-600/50 rounded-lg p-3 text-amber-300 text-sm">
                                <AlertCircle size={16} className="inline mr-2" />
                                Simülasyon başlatmak için en az 1 bina seçin ve konum belirleyin.
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Navigation & Action Buttons */}
            <div className="p-4 border-t border-slate-700 bg-slate-900/50 space-y-2">
                {/* Step Navigation */}
                <div className="flex gap-2">
                    {currentStepIndex > 0 && (
                        <button
                            onClick={() => goToStep(STEPS[currentStepIndex - 1].id)}
                            className="flex-1 py-2 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition-colors"
                        >
                            ← Geri
                        </button>
                    )}
                    {currentStepIndex < STEPS.length - 1 && (
                        <button
                            onClick={() => goToStep(STEPS[currentStepIndex + 1].id)}
                            disabled={!stepValidation[currentStep]}
                            data-testid="next-step-button"
                            className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${stepValidation[currentStep]
                                ? 'bg-blue-600 hover:bg-blue-500 text-white'
                                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                                }`}
                        >
                            İleri →
                        </button>
                    )}
                </div>

                {/* Simulate Button (only on last step) */}
                {currentStep === 'simulate' && (
                    <button
                        onClick={onStartSimulation}
                        disabled={!stepValidation.simulate}
                        data-testid="start-simulation-button"
                        className={`w-full p-4 rounded-xl font-bold shadow-lg flex items-center justify-center gap-2 transition-all transform ${stepValidation.simulate
                            ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white hover:scale-[1.02] active:scale-[0.98]'
                            : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                            }`}
                    >
                        <Play size={20} fill="currentColor" />
                        <span>SİMÜLASYONU BAŞLAT</span>
                    </button>
                )}
            </div>
        </div>
    );
};

export default SidebarLayout;
