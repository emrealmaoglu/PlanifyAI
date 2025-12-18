import React, { useCallback, useState } from 'react';
import SidebarLayout from '../features/cockpit/SidebarLayout';
import { useBoundaryEditor } from '../hooks/useBoundaryEditor';
import { useBuildingInteraction } from '../hooks/useBuildingInteraction';
import { useContextFetcher } from '../hooks/useContextFetcher';
import { useSimulationRunner } from '../hooks/useSimulationRunner';
import { useOptimizationStore } from '../store/useOptimizationStore';
import { SlopeOverlay, WindOverlay } from './layers';
import ViolationStyling from './layers/ViolationStyling';
import { InitialContextFetcher } from './map/InitialContextFetcher';
import { ExistingContextLayers } from './map/layers/ExistingContextLayers';
import { GatewayLayer } from './map/layers/GatewayLayer';
import { MapContainer } from './map/MapContainer';
import SimulationPanel from './SimulationPanel';
import { useToast } from './Toast';

// CSS imported in index.css to avoid duplication
// import 'mapbox-gl/dist/mapbox-gl.css';
// import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css';
// import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

const MapLogicHooks: React.FC = () => {
    // MapContainer.children altında, bu yüzden useMapContext güvenli
    useBoundaryEditor();
    useBuildingInteraction();
    return null;
};

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
    // Store Connection
    const {
        previewContext, // Used for layers
        analysisFlags,
        gateways
    } = useOptimizationStore();

    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('Hazır');

    // Toast notifications
    const { success, error: showError } = useToast();

    // Hooks
    const { fetchContext } = useContextFetcher();
    const { runSimulation } = useSimulationRunner();

    // UI Wrapper for Context Fetch
    const fetchContextWithUI = useCallback(async (lat: number, lon: number) => {
        setStatus('Bölge taranıyor (OpenStreetMap)...');
        setLoading(true);

        try {
            await fetchContext(apiBaseUrl, lat, lon);
            setStatus('Hazır');
            success('Bağlam verileri yüklendi!');
        } catch (err) {
            console.error(err);
            setStatus('Hata: Bağlantı kurulamadı.');
            showError('Bağlam verileri yüklenemedi. Lütfen tekrar deneyin.');
        } finally {
            setLoading(false);
        }
    }, [apiBaseUrl, fetchContext, success, showError]);

    // --- SIMULATION HANDLING ---
    const handleStartSimulation = async () => {
        setLoading(true);
        setStatus("Simülasyon Başlatılıyor...");
        try {
            const data = await runSimulation(apiBaseUrl);
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

            <MapContainer
                mapboxToken={mapboxToken}
                initialCenter={initialCenter}
                initialZoom={initialZoom}
                onGeocoderResult={(e: any) => {
                    const { center } = e.result;
                    fetchContextWithUI(center[1], center[0]);
                }}
            >
                <SimulationPanel loading={loading} status={status} />

                {/* Map logic hook'ları artık context üzerinden çalışıyor */}
                <MapLogicHooks />

                {/* İlk yüklemede mevcut center için context fetch */}
                <InitialContextFetcher onInitialCenter={fetchContextWithUI} />

                {/* Layer Overlay Components - now using MapContext internally */}
                <ExistingContextLayers
                    geojson={previewContext as GeoJSON.FeatureCollection | null}
                />

                <GatewayLayer gateways={gateways} />

                <WindOverlay
                    windEnabled={analysisFlags.wind}
                    features={features}
                />

                <SlopeOverlay
                    slopeEnabled={analysisFlags.walkability}
                    features={features}
                />

                {/* İhlal (violations) bazlı stil katmanı */}
                <ViolationStyling />
            </MapContainer>
        </div>
    );
};

export default OptimizationResults;
