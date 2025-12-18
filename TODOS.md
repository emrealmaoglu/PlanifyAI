# PlanifyAI - Kapsamlı Sistem Analizi ve TODO Listesi

> **Oluşturulma Tarihi:** 2025-12-09
> **Analiz Kapsamı:** Tüm belgeler, araştırmalar, kod tabanı, UI/UX, mimari
> **Son Güncelleme:** 2025-12-10 (Sprint 1-5 işaretlendi)

---

## 📊 PROJE DURUMU ÖZETİ

| Metrik | Değer |
|--------|-------|
| **Versiyon** | v10.1.0 |
| **Backend Kod** | 7,870 satır Python |
| **Frontend Kod** | ~3,000 satır TypeScript |
| **Araştırma Dokümanları** | 61 adet (.docx) |
| **Unit Testler** | **35 PASSED** |
| **TypeScript Check** | ✅ 0 hata |

---

## 🔴 KRİTİK SORUNLAR (P0)

### ~~1. Legacy Router Kırık~~ ✅ ÇÖZÜLDÜ (Sprint 1)
- **Dosya:** `backend/api/routers/optimization.py`
- **Çözüm:** Silindi veya güncellendi

### 2. Frontend Types Eksik
- **Dosya:** `frontend/src/types/index.ts`
- **Sorun:** `Gateway` ve `BoundaryGeoJSON` tanımları `types.ts`'de, `index.ts`'de değil
- **Etki:** Import tutarsızlıkları, tip güvenliği eksik
- **Çözüm:** Tüm tipleri `index.ts`'e birleştir

### 3. API Contract Uyumsuzluğu
| Frontend Bekliyor | Backend Sağlıyor |
|-------------------|------------------|
| `/api/optimization/run` | `/api/optimize/start` |
| `/api/optimization/result/{id}` | `/api/optimize/result/{id}` |
| `/health` | ❌ Yok |

### ~~4. Hardcoded URL'ler~~ ✅ ÇÖZÜLDÜ (Sprint 1)
- **Çözüm:** `config.apiBaseUrl` kullanıldı (`DrawingTools.tsx`, `SearchBar.tsx`, `App.tsx`)

---

## 🟡 ORTA ÖNCELİKLİ SORUNLAR (P1)

### ~~5. TypeScript Kullanılmayan Değişkenler~~ ✅ DÜZELTİLDİ (Sprint 5/11)
- **Not:** OptimizationResults.tsx refactor edildi (<250 satır).
- Kullanılmayan değişkenler temizlendi.

### 6. geoContext Tip Uyumsuzluğu
```typescript
// Store tanımı:
geoContext: { latitude: number; longitude: number; radius: number }

// OptimizationResults.tsx:659,711 kullanımı:
geoContext.features  // ❌ 'features' property yok!
```

### ~~7. In-Memory Job Storage~~ ✅ ÇÖZÜLDÜ (Sprint 2)
- **Çözüm:** SQLiteJobStore eklendi (`backend/core/storage/sqlite_store.py`)
- **Detay:** JobStore Protocol ile interface abstraction

### 8. SSE Stream Kullanılmıyor
- **Dosya:** `frontend/src/api/client.ts:39-42`
- **Tanımlanmış:** `createProgressStream()`
- **Kullanım:** Hiçbir yerde çağrılmıyor
- **Etki:** Real-time ilerleme gösterimi yok

---

## 🟢 DÜŞÜK ÖNCELİK / GELİŞTİRME ÖNERİLERİ (P2)

### 9. Araştırma-Kod Entegrasyonu Eksik
**docs/research/ klasöründe 61 araştırma dokümanı var:**

| Araştırma | Kod Durumu |
|-----------|------------|
| 3D Urban Design Optimization | ✅ physics_objectives.py |
| Wind Comfort Analysis | ✅ physics_objectives.py |
| Solar Gain Optimization | ✅ physics_objectives.py |
| Surrogate-Assisted EA (SAEA) | ❌ Uygulanmamış |
| Graph Neural Networks (GNN) | ❌ Uygulanmamış |
| Deep Reinforcement Learning | ❌ Uygulanmamış |
| VR/AR Integration | ❌ Uygulanmamış |
| IoT Spatial Planning | ❌ Uygulanmamış |

### 10. Dokümantasyon Tutarsızlıkları
- **CHANGELOG.md:** Phase 1'de durmuş, Phase 2-10 yok
- **README.md:** Güncel ama basit
- **SYSTEM_ARCHITECTURE.md:** Detaylı ve güncel ✅

### 11. Quick Optimization Disabled
```python
# optimize.py:151-171
@router.post("/quick")
async def quick_optimization(...):
    return {"success": True, "message": "Quick optimization temporarily disabled during refactor."}
```

### ~~12. Test Coverage Eksik~~ ✅ İYİLEŞTİRİLDİ (Sprint 3)
- **Mevcut:** **35 test** (ConstraintCalculator, SQLiteJobStore, API endpoints)
- Frontend testleri hâlâ eksik

---

## 🎨 UI/UX ANALİZİ

### Pozitif Bulgular ✅
1. **4-Adım Stepper** - Net workflow rehberliği
2. **Building Count Grid** - Görsel bina seçimi
3. **Collapsible Accordions** - Düzenli bilgi hiyerarşisi
4. **Turkish Localization** - Tam Türkçe arayüz
5. **Save/Load** - Senaryo dışa/içe aktarımı
6. **Dark Theme** - Modern görünüm

### Negatif Bulgular ❌
1. **Koordinat Alanları Boş** - geoContext güncellenmesi geç (düzeltildi)
2. **Silinen Binalar Görünmüyor** - opacity expression tip hatası (düzeltildi)
3. **Sınır Düzenleme** - Değişiklik kaydedilmiyor (düzeltildi)
4. **Loading State Eksik** - Simülasyon başlarken skeleton yok
5. **Error Feedback Yetersiz** - API hataları sessiz geçiliyor
6. **Undo/Redo Yok** - Kullanıcı hataları geri alınamıyor

### Önerilen UX İyileştirmeleri
1. ⏳ **Loading Skeleton** - Optimizasyon sırasında ilerleme
2. ✅ ~~**Toast Notifications**~~ - Başarı/hata mesajları (Sprint 6-7)
3. ⌨️ **Keyboard Shortcuts** - Ctrl+Z, Ctrl+S, Delete
4. 📊 **Pareto Front Visualization** - Çözüm karşılaştırması
5. 🗺️ **Mini Map** - Büyük kampüslerde navigasyon

---

## 🏗️ MİMARİ ANALİZİ

### Güçlü Yanlar ✅
1. **Modüler Backend** - 12 core modül, net sorumluluklar
2. **Zustand State** - Basit ve etkili state yönetimi
3. **H-SAGA Algorithm** - Araştırma destekli hibrit optimizasyon
4. **Turkish Standards** - Yerel mevzuat entegrasyonu
5. **GeoJSON API** - Standart veri formatı

### Zayıf Yanlar ❌
1. **Sıkı Bağlılık** - OptimizationResults.tsx 900+ satır
2. **Çift Tip Tanımı** - types.ts ve types/index.ts
3. **Magic Numbers** - Sabitler dağınık
4. **Error Handling** - Try-catch yakalanıp sessizce geçiliyor

### Önerilen Refaktörler
1. 📦 **OptimizationResults Bölünmesi:**
   - `MapContainer.tsx` (Mapbox logic)
   - `MapLayers.tsx` (Layer yönetimi)
   - `MapInteractions.tsx` (Click handlers)
   - `useMapData.ts` (Data fetching hook)

2. 📁 **Types Birleştirmesi:**
   ```
   types/
   ├── api.ts       (API contract types)
   ├── store.ts     (Zustand types)
   ├── map.ts       (Mapbox types)
   └── index.ts     (Re-exports)
   ```

3. 🔧 **Constants Dosyası:**
   ```typescript
   // constants/index.ts
   export const API_ENDPOINTS = {
     CONTEXT_FETCH: '/api/context/fetch',
     OPTIMIZE_START: '/api/optimize/start',
     // ...
   };
   ```

---

## � ARAŞTIRMA ENTEGRASYON DURUMU

### Uygulanmış (✅)
| Araştırma | Modül |
|-----------|-------|
| H-SAGA Hybrid Algorithm | `hsaga_runner.py` |
| Multi-Objective Optimization | `spatial_problem.py` |
| Wind Comfort Modeling | `physics_objectives.py` |
| Solar Gain Analysis | `physics_objectives.py` |
| Turkish Zoning Standards | `turkish_standards/` |
| XAI Visualization | `slope_grid_generator.py` |

### Planlanmış (📋)
| Araştırma | Hedef Phase |
|-----------|-------------|
| WebSocket Real-time | Phase 11 |
| Case-Based Reasoning | Phase 12 |

### Uygulanmamış (❌)
| Araştırma | Potansiyel Değer |
|-----------|------------------|
| SAEA (Surrogate-Assisted) | Hızlı yakınsama (özellikle büyük kampüsler) |
| GNN Spatial Learning | Otomatik layout pattern öğrenimi |
| DRL Building Placement | Dinamik karar verme |
| Traffic Microsimulation | Gerçekçi yaya/araç simülasyonu |
| Quantum Optimization | Büyük ölçekli kombinatoryal problemler |

---

## 📋 HIZLI DÜZELTME CHECKLIST

### Kritik (Bugün)
- [ ] `backend/api/routers/optimization.py` sil veya güncelle
- [ ] `/health` endpoint ekle (`main.py`)
- [ ] `client.ts` endpoint'lerini `/api/optimize/` olarak güncelle
- [ ] Hardcoded URL'leri `config.apiBaseUrl` ile değiştir

### Önemli (Bu Hafta)
- [ ] `types.ts` ve `types/index.ts` birleştir
- [ ] `geoContext.features` kullanımlarını düzelt
- [ ] Kullanılmayan değişkenleri temizle
- [ ] CHANGELOG.md'yi Phase 10'a kadar güncelle

### İyi Olur (Bu Ay)
- [x] Loading skeleton ekle (Partial)
- [x] Toast notification sistemi kur (Done)
- [ ] Frontend testleri (Vitest) başlat
- [x] OptimizationResults.tsx'i parçala (Done FE-UX-001-A)
- [ ] MapContext & MapContainer implementasyonu (FE-UX-002-A)

---

## 📊 API ENDPOINT TAM LİSTESİ

### Aktif Endpoint'ler

| Router | Prefix | Method | Path | Açıklama |
|--------|--------|--------|------|----------|
| `context` | `/api/context` | GET | `/fetch` | OSM veri çekme |
| `optimize` | `/api/optimize` | POST | `/start` | Job başlatma |
| | | GET | `/status/{id}` | Job durumu |
| | | GET | `/result/{id}` | Sonuç |
| | | GET | `/geojson/{id}` | GeoJSON çıktısı |
| | | POST | `/quick` | ⚠️ Disabled |
| | | POST | `/context/search` | Kampus arama |
| `constraints` | `/api/constraints` | POST | `/add` | Zone ekle |
| | | POST | `/add-building` | Sabit bina ekle |
| | | DELETE | `/remove/{sid}/{cid}` | Zone sil |
| | | GET | `/list/{sid}` | Zone listele |
| | | GET | `/geojson/{sid}` | Export GeoJSON |
| | | POST | `/import/{sid}` | Import GeoJSON |
| | | POST | `/check-violations/{sid}` | İhlal kontrolü |

### Kırık Endpoint'ler (Skipped)

| Router | Prefix | Sebep |
|--------|--------|-------|
| `optimization` | `/api/optimization` | Missing `backend.core.integration` |

---

## 🎯 ÖNCELİK MATRİSİ

```
         YÜKSEK ETKİ
              │
    ┌─────────┼─────────┐
    │    P0   │   P1    │
    │ KRITIK  │ ÖNEMLI  │
    │         │         │
────┼─────────┼─────────┼─── DÜŞÜK ÇABA
    │         │         │     ◄──────► YÜKSEK ÇABA
    │   P2    │   P3    │
    │ İYİ OLUR│ SONRA   │
    │         │         │
    └─────────┼─────────┘
              │
         DÜŞÜK ETKİ
```

| Öncelik | Öğe Sayısı | Tahmini Süre |
|---------|------------|-------------|
| P0 | 4 | 2-3 saat |
| P1 | 4 | 1 gün |
| P2 | 4 | 1 hafta |
| P3 | 8 | 1+ ay |

---

## � EK DOSYALAR

- [SYSTEM_ARCHITECTURE_AND_ROADMAP.md](SYSTEM_ARCHITECTURE_AND_ROADMAP.md) - Detaylı teknik mimari
- [README.md](README.md) - Proje genel bakış
- [CHANGELOG.md](CHANGELOG.md) - Versiyon geçmişi (güncelleme gerekli)

---

> 📝 **Not:** Bu belge otomatik analiz ile oluşturulmuştur. Öncelikler proje ihtiyaçlarına göre ayarlanabilir.

*Son Güncelleme: 2025-12-09 20:55*
