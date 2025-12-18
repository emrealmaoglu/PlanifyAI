import * as mapboxgl from 'mapbox-gl';
import { useEffect, useRef } from 'react';
import { useMapContext } from '../components/map/MapContext';
import { useOptimizationStore } from '../store/useOptimizationStore';

export const useBuildingInteraction = () => {
    const { map, isMapLoaded } = useMapContext();
    // Keep track of the active popup to close it if needed, or avoid duplicates
    const activePopup = useRef<mapboxgl.Popup | null>(null);

    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const mb = (mapboxgl as any).default || mapboxgl;

        const onClickBuilding = (e: mapboxgl.MapMouseEvent & { features?: mapboxgl.GeoJSONFeature[] }) => {
            const feature = e.features?.[0];
            if (feature && feature.properties?.osm_id) {
                const osmId = String(feature.properties.osm_id);
                const name = feature.properties.name || 'İsimsiz Bina';
                const type = feature.properties.building_type || 'Bilinmiyor';

                const currentStore = useOptimizationStore.getState();
                const isKept = currentStore.keptBuildingIds.includes(osmId);
                const isHidden = currentStore.hiddenBuildingIds.includes(osmId);

                // Create Popup Content
                const popupNode = document.createElement('div');
                popupNode.className = 'p-2 min-w-[160px]';

                const keepBtnClass = isKept
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-slate-50 text-slate-600 hover:bg-green-50 hover:text-green-600 border border-slate-200';

                const deleteBtnClass = isHidden
                    ? 'bg-red-100 text-red-700 border border-red-200'
                    : 'bg-slate-50 text-slate-600 hover:bg-red-50 hover:text-red-600 border border-slate-200';

                popupNode.innerHTML = `
                    <div class="mb-2">
                        <h3 class="font-bold text-sm text-slate-800 leading-tight">${name}</h3>
                        <p class="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">${type}</p>
                    </div>
                    <div class="flex gap-2">
                        <button id="btn-keep-${osmId}" class="flex-1 px-2 py-1.5 text-xs font-medium rounded transition-all ${keepBtnClass}">
                            ${isKept ? 'Korunuyor' : 'Koru'}
                        </button>
                        <button id="btn-delete-${osmId}" class="flex-1 px-2 py-1.5 text-xs font-medium rounded transition-all ${deleteBtnClass}">
                            ${isHidden ? 'Geri Al' : 'Sil'}
                        </button>
                    </div>
                `;

                const btnKeep = popupNode.querySelector(`#btn-keep-${osmId}`);
                const btnDelete = popupNode.querySelector(`#btn-delete-${osmId}`);

                // Close existing popup if any
                if (activePopup.current) {
                    activePopup.current.remove();
                }

                const popup = new mb.Popup({ closeButton: false, maxWidth: '200px' })
                    .setLngLat(e.lngLat)
                    .setDOMContent(popupNode)
                    .addTo(map);

                activePopup.current = popup;

                // Cleanup reference on close
                popup.on('close', () => {
                    activePopup.current = null;
                });

                if (btnKeep) {
                    btnKeep.addEventListener('click', () => {
                        useOptimizationStore.getState().toggleKeptBuilding(osmId);
                        popup.remove();
                    });
                }

                if (btnDelete) {
                    btnDelete.addEventListener('click', () => {
                        useOptimizationStore.getState().toggleHiddenBuilding(osmId);
                        popup.remove();
                    });
                }
            }
        };

        const onMouseEnter = () => {
            map.getCanvas().style.cursor = 'pointer';
        };
        const onMouseLeave = () => {
            map.getCanvas().style.cursor = '';
        };

        map.on('click', 'existing-buildings', onClickBuilding);
        map.on('mouseenter', 'existing-buildings', onMouseEnter);
        map.on('mouseleave', 'existing-buildings', onMouseLeave);

        // Cleanup listeners on unmount (or map change)
        return () => {
            map.off('click', 'existing-buildings', onClickBuilding);
            map.off('mouseenter', 'existing-buildings', onMouseEnter);
            map.off('mouseleave', 'existing-buildings', onMouseLeave);
            if (activePopup.current) {
                activePopup.current.remove();
            }
        };
    }, [map, isMapLoaded]);
};
