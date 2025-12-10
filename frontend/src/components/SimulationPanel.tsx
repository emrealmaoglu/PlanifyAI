import React, { useEffect, useState } from 'react';

interface SimulationPanelProps {
    loading: boolean;
    status: string;
}

/**
 * SimulationPanel - Loading ve status gösterimi için gelişmiş panel
 * Sorumluluk: Glassmorphism UI, status geçmişi ve animasyonlu loading
 */
export const SimulationPanel: React.FC<SimulationPanelProps> = ({
    loading,
    status
}) => {
    // Status history log
    const [logs, setLogs] = useState<string[]>([]);

    useEffect(() => {
        if (loading) {
            // Add new status only if it's different from the last one or log is empty
            setLogs(prev => {
                const lastLog = prev[prev.length - 1];
                if (lastLog !== status) {
                    return [...prev, status];
                }
                return prev;
            });
        } else {
            // Optional: Clear logs when loading finishes, or keep them for a moment?
            // Current UX decision: Panel disappears on !loading anyway, so reset is fine.
            setLogs([]);
        }
    }, [status, loading]);

    if (!loading) return null;

    return (
        <div className="absolute top-24 right-6 w-80 z-50">
            {/* Main Glass Card */}
            <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-xl shadow-2xl p-5 text-white animate-fade-in">

                {/* Header with Pulse */}
                <div className="flex items-center gap-3 mb-4">
                    <div className="relative flex items-center justify-center h-8 w-8">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-500 opacity-20"></span>
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
                    </div>
                    <div>
                        <h3 className="font-bold text-base bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300">
                            Simülasyon Çalışıyor
                        </h3>
                        <p className="text-xs text-slate-400">Yapay zeka optimizasyonu sürüyor...</p>
                    </div>
                </div>

                {/* Status Log List */}
                <div className="space-y-3 relative">
                    {/* Vertical Line Connector */}
                    <div className="absolute left-3.5 top-2 bottom-2 w-0.5 bg-slate-700/50"></div>

                    {logs.slice(-4).map((log, index) => {
                        const isLatest = index === logs.slice(-4).length - 1;
                        return (
                            <div key={index} className={`flex items-start gap-3 relative ${isLatest ? 'opacity-100' : 'opacity-50'}`}>
                                {/* Dot Indicator */}
                                <div className={`w-2 h-2 rounded-full mt-1.5 z-10 ${isLatest ? 'bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.6)]' : 'bg-slate-600'}`}></div>

                                {/* Status Text */}
                                <span className={`text-sm font-mono ${isLatest ? 'text-blue-100' : 'text-slate-500'}`}>
                                    {log}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Footer / Hint */}
                <div className="mt-4 pt-3 border-t border-slate-700/50 text-center">
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold flex items-center justify-center gap-2">
                        <span>H-SAGA Optimizer</span>
                        <span className="w-1 h-1 bg-slate-600 rounded-full"></span>
                        <span>Phase 6</span>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SimulationPanel;
