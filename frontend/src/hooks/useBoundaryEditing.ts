import { useCallback } from 'react';
import { useOptimizationStore } from '../store/useOptimizationStore';
import type { BoundaryGeoJSON } from '../types';

interface UseBoundaryEditingProps {
    draw: any; // MapboxDraw instance
}

/**
 * useBoundaryEditing - Boundary düzenleme hook'u
 * 
 * OptimizationResults.tsx'den çıkarıldı (Faz 1.1.5)
 * Sorumluluklar:
 * - Draw tool'dan boundary güncelleme
 * - Store ile senkronizasyon
 */
export function useBoundaryEditing({ draw }: UseBoundaryEditingProps) {
    const { setCustomBoundary } = useOptimizationStore();

    /**
     * MapboxDraw'dan gelen update/create/delete eventlerini işler
     * ve boundary'yi store'a senkronize eder
     */
    const updateBoundaryFromDraw = useCallback((e: any) => {
        const data = draw?.getAll();
        console.log("Draw Update:", e.type, data);

        if (data && data.features.length > 0) {
            setCustomBoundary(data as BoundaryGeoJSON);
            console.log("Custom Boundary Updated in Store:", data);
        }
    }, [draw, setCustomBoundary]);

    /**
     * Boundary'yi programatik olarak sıfırlar
     */
    const clearBoundary = useCallback(() => {
        if (draw) {
            draw.deleteAll();
            setCustomBoundary(null);
        }
    }, [draw, setCustomBoundary]);

    /**
     * Mevcut boundary'yi draw tool'a yükler
     */
    const loadBoundaryToDraw = useCallback((boundary: BoundaryGeoJSON | null) => {
        if (draw && boundary) {
            draw.deleteAll();
            draw.add(boundary);
        }
    }, [draw]);

    return {
        updateBoundaryFromDraw,
        clearBoundary,
        loadBoundaryToDraw
    };
}

export default useBoundaryEditing;
