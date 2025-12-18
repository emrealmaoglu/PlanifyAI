
import React, { useState } from 'react';
import { useOptimizationStore } from "../../../store/useOptimizationStore";
import { MapPin, Ruler, Home, Edit2, Check, X } from 'lucide-react';

export const PrepTab: React.FC = () => {
    const {
        projectInfo, setProjectInfo,
        geoContext, setGeoContext,
        siteParameters, setSiteParameter,
        isBoundaryEditing, setBoundaryEditing,
        isDemolitionMode, setDemolitionMode,
        clearAllExisting, setClearAllExisting,
        existingBuildings, toggleHiddenBuilding, hiddenBuildingIds,
        keptBuildingIds, toggleKeptBuilding,
        updateBuilding
    } = useOptimizationStore();


    // Building edit state
    const [editingBuildingId, setEditingBuildingId] = useState<string | null>(null);
    const [editName, setEditName] = useState('');
    const [editType, setEditType] = useState('');

    return (
        <div className="space-y-6 p-4">
            {/* Project Info Section */}
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

            <div className="h-px bg-slate-200" />

            {/* Geo Context Section */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                    <MapPin className="w-5 h-5 text-purple-600" />
                    Konum ve Kapsam
                </h3>

                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">Enlem</label>
                        <input
                            type="number"
                            value={geoContext.latitude}
                            onChange={(e) => setGeoContext({ latitude: parseFloat(e.target.value) })}
                            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-md text-sm"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">Boylam</label>
                        <input
                            type="number"
                            value={geoContext.longitude}
                            onChange={(e) => setGeoContext({ longitude: parseFloat(e.target.value) })}
                            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-md text-sm"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1 flex justify-between">
                        <span>Analiz Yarıçapı</span>
                        <span className="text-slate-500">{geoContext.radius}m</span>
                    </label>
                    <input
                        type="range"
                        min="100"
                        max="2000"
                        step="50"
                        value={geoContext.radius}
                        onChange={(e) => setGeoContext({ radius: parseInt(e.target.value) })}
                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                </div>
            </div>

            <div className="h-px bg-slate-200" />

            {/* Site Boundaries Section */}
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
                        className={`w-full py-2 px-4 rounded-md font-medium transition-all flex items-center justify-center gap-2 ${isBoundaryEditing
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
                                <li>Yeni köşe eklemek için noktalar arasındaki silik tutamaçları sürükleyin.</li>
                            </ul>
                        </div>
                    )}
                </div>
            </div>

            <div className="h-px bg-slate-200" />

            {/* Existing Context Section */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                    <Home className="w-5 h-5 text-red-600" />
                    Mevcut Yapılaşma
                </h3>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-4">
                    <p className="text-sm text-slate-600">
                        Mevcut binaları koruyabilir, silebilir veya tamamen yok sayabilirsiniz.
                    </p>

                    {/* Demolition Mode */}
                    <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-700">Yıkım Modu</span>
                        <button
                            onClick={() => {
                                setDemolitionMode(!isDemolitionMode);
                                if (!isDemolitionMode) setClearAllExisting(false); // Disable clear all if entering demo mode
                            }}
                            disabled={clearAllExisting}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${isDemolitionMode ? 'bg-red-600' : 'bg-slate-200'
                                } ${clearAllExisting ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isDemolitionMode ? 'translate-x-6' : 'translate-x-1'
                                    }`}
                            />
                        </button>
                    </div>
                    {isDemolitionMode && (
                        <p className="text-xs text-red-600 bg-red-50 p-2 rounded border border-red-100">
                            Haritadaki binalara tıklayarak onları silebilirsiniz.
                        </p>
                    )}

                    {/* Building List (New Feature) */}
                    <div className="max-h-48 overflow-y-auto custom-scrollbar border border-slate-200 rounded-md bg-white">
                        {existingBuildings.length === 0 ? (
                            <div className="p-4 text-center text-xs text-slate-400">
                                Henüz bina verisi yüklenmedi.
                            </div>
                        ) : (
                            <div className="divide-y divide-slate-100">
                                {existingBuildings.map((b: any) => {
                                    const isHidden = hiddenBuildingIds.includes(String(b.id));
                                    const isKept = keptBuildingIds.includes(String(b.id));
                                    const isEditing = editingBuildingId === String(b.id);

                                    // Start editing a building
                                    const startEdit = () => {
                                        setEditingBuildingId(String(b.id));
                                        setEditName(b.name);
                                        setEditType(b.type);
                                    };

                                    // Save building edits
                                    const saveEdit = () => {
                                        updateBuilding(String(b.id), { name: editName, type: editType });
                                        setEditingBuildingId(null);
                                    };

                                    // Cancel editing
                                    const cancelEdit = () => {
                                        setEditingBuildingId(null);
                                    };

                                    return (
                                        <div key={b.id} className={`p-2 text-xs ${isHidden ? 'bg-red-50 opacity-50' : isKept ? 'bg-green-50' : 'hover:bg-slate-50'}`}>
                                            {isEditing ? (
                                                // Edit Mode
                                                <div className="space-y-2">
                                                    <input
                                                        type="text"
                                                        value={editName}
                                                        onChange={(e) => setEditName(e.target.value)}
                                                        className="w-full px-2 py-1 text-xs border border-blue-300 rounded focus:ring-1 focus:ring-blue-500"
                                                        placeholder="Bina adı"
                                                        autoFocus
                                                    />
                                                    <input
                                                        type="text"
                                                        value={editType}
                                                        onChange={(e) => setEditType(e.target.value)}
                                                        className="w-full px-2 py-1 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500"
                                                        placeholder="Bina türü (örn: Faculty, Dormitory)"
                                                    />
                                                    <div className="flex gap-1 justify-end">
                                                        <button onClick={saveEdit} className="p-1 text-green-600 hover:bg-green-100 rounded" title="Kaydet">
                                                            <Check className="w-4 h-4" />
                                                        </button>
                                                        <button onClick={cancelEdit} className="p-1 text-red-600 hover:bg-red-100 rounded" title="İptal">
                                                            <X className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                // View Mode
                                                <div className="flex items-center justify-between">
                                                    <div className="flex flex-col flex-1 min-w-0">
                                                        <span className={`font-medium truncate ${isHidden ? 'line-through text-slate-500' : isKept ? 'text-green-700' : 'text-slate-700'}`}>
                                                            {b.name}
                                                        </span>
                                                        <span className="text-[10px] text-slate-400">{b.type}</span>
                                                    </div>
                                                    <div className="flex gap-1 flex-shrink-0">
                                                        <button
                                                            onClick={startEdit}
                                                            className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                                            title="Düzenle"
                                                        >
                                                            <Edit2 className="w-3.5 h-3.5" />
                                                        </button>
                                                        <button
                                                            onClick={() => toggleKeptBuilding(String(b.id))}
                                                            disabled={isHidden}
                                                            className={`p-1.5 rounded transition-colors ${isKept
                                                                ? 'text-green-600 bg-green-100 hover:bg-green-200'
                                                                : 'text-slate-400 hover:text-green-600 hover:bg-green-50'
                                                                } ${isHidden ? 'opacity-20 cursor-not-allowed' : ''}`}
                                                            title={isKept ? "Korumayı Kaldır" : "Koru (Silinmez)"}
                                                        >
                                                            Koru
                                                        </button>
                                                        <button
                                                            onClick={() => toggleHiddenBuilding(String(b.id))}
                                                            disabled={isKept}
                                                            className={`p-1.5 rounded transition-colors ${isHidden
                                                                ? 'text-red-600 bg-red-100 hover:bg-red-200'
                                                                : 'text-slate-400 hover:text-red-600 hover:bg-red-50'
                                                                } ${isKept ? 'opacity-20 cursor-not-allowed' : ''}`}
                                                            title={isHidden ? "Geri Al" : "Sil"}
                                                        >
                                                            {isHidden ? 'Geri Al' : 'Sil'}
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Building Stats & Actions */}
                    {existingBuildings.length > 0 && (
                        <div className="flex items-center justify-between text-xs p-2 bg-slate-50 rounded-md">
                            <div className="text-slate-600">
                                <span className="font-medium">{existingBuildings.length}</span> bina,
                                <span className="text-green-600 ml-1">{keptBuildingIds.length} korunan</span>,
                                <span className="text-red-600 ml-1">{hiddenBuildingIds.length} silinen</span>
                            </div>
                            <button
                                onClick={() => {
                                    // Delete all buildings that are NOT in keptBuildingIds
                                    existingBuildings.forEach((b: any) => {
                                        const id = String(b.id);
                                        if (!keptBuildingIds.includes(id) && !hiddenBuildingIds.includes(id)) {
                                            toggleHiddenBuilding(id);
                                        }
                                    });
                                }}
                                disabled={keptBuildingIds.length === 0}
                                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${keptBuildingIds.length === 0
                                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                                    : 'bg-red-100 text-red-700 hover:bg-red-200'
                                    }`}
                                title="Korunan binalar hariç tümünü sil"
                            >
                                Kalanları Sil
                            </button>
                        </div>
                    )}

                    <div className="h-px bg-slate-200" />

                    {/* Clear All (Greenfield) */}
                    <div className="flex items-center justify-between">
                        <div>
                            <span className="block text-sm font-medium text-slate-700">Tümünü Temizle</span>
                            <span className="text-xs text-slate-500">Alanı boş arsa olarak kabul et</span>
                        </div>
                        <button
                            onClick={() => {
                                if (!clearAllExisting) {
                                    // Confirm before enabling
                                    const confirmed = window.confirm(
                                        '⚠️ DİKKAT!\n\nTüm mevcut binalar silinecek.\nBu işlem geri alınamaz.\n\nDevam etmek istiyor musunuz?'
                                    );
                                    if (!confirmed) return;
                                }
                                setClearAllExisting(!clearAllExisting);
                                if (!clearAllExisting) setDemolitionMode(false);
                            }}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${clearAllExisting ? 'bg-red-600' : 'bg-slate-200'
                                }`}
                        >
                            <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${clearAllExisting ? 'translate-x-6' : 'translate-x-1'
                                    }`}
                            />
                        </button>
                    </div>
                </div>
            </div>

            <div className="h-px bg-slate-200" />

            {/* Site Configuration (Setbacks) */}
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
                        <label className="block text-xs font-medium text-slate-500 mb-1">Ön Bahçe</label>
                        <div className="relative">
                            <input
                                type="number"
                                value={siteParameters.setback_front}
                                onChange={(e) => setSiteParameter('setback_front', parseFloat(e.target.value))}
                                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-emerald-500 focus:border-emerald-500"
                            />
                            <span className="absolute right-2 top-2 text-xs text-slate-400">m</span>
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">Yan Bahçe</label>
                        <div className="relative">
                            <input
                                type="number"
                                value={siteParameters.setback_side}
                                onChange={(e) => setSiteParameter('setback_side', parseFloat(e.target.value))}
                                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-emerald-500 focus:border-emerald-500"
                            />
                            <span className="absolute right-2 top-2 text-xs text-slate-400">m</span>
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">Arka Bahçe</label>
                        <div className="relative">
                            <input
                                type="number"
                                value={siteParameters.setback_rear}
                                onChange={(e) => setSiteParameter('setback_rear', parseFloat(e.target.value))}
                                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-emerald-500 focus:border-emerald-500"
                            />
                            <span className="absolute right-2 top-2 text-xs text-slate-400">m</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
