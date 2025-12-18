import { useCallback } from 'react';
import { useOptimizationStore } from '../store/useOptimizationStore';

interface UseSimulationRunnerResult {
    runSimulation: (apiBaseUrl: string) => Promise<{ job_id: string }>;
}

export const useSimulationRunner = (): UseSimulationRunnerResult => {
    const {
        projectInfo,
        geoContext,
        buildingCounts,
        siteParameters,
        optimizationGoals,
        customBoundary,
        hiddenBuildingIds,
        keptBuildingIds,
        clearAllExisting,
        analysisFlags
    } = useOptimizationStore();

    const runSimulation = useCallback(async (apiBaseUrl: string) => {
        const payload = {
            project_name: projectInfo.name,
            description: projectInfo.description,
            latitude: geoContext.latitude,
            longitude: geoContext.longitude,
            radius: geoContext.radius,
            building_counts: buildingCounts,
            site_parameters: siteParameters,
            optimization_goals: optimizationGoals,
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

        return await res.json();
    }, [
        projectInfo, geoContext, buildingCounts, siteParameters,
        optimizationGoals, customBoundary, hiddenBuildingIds,
        keptBuildingIds, clearAllExisting, analysisFlags
    ]);

    return { runSimulation };
};
