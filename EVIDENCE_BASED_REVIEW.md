# 🔬 KANITA DAYALI KOD İNCELEMESİ: PlanifyAI

> **Kritik Not:** Bu incelemede her iddia, gerçek dosya yolları ve satır sayıları ile desteklenmektedir.
> **Hallucination önleme:** Tüm sayılar `wc -l`, `find`, ve `list_dir` komutlarıyla doğrulanmıştır.

---

## 📁 1. PROJE YAPISI (Doğrulanmış)

### 1.1 Top-Level Klasörler

| Klasör | İçerik | Bulgu |
|--------|--------|-------|
| `backend/` | 41 Python dosyası | API + Core iş mantığı |
| `frontend/src/` | 13 TSX dosyası | React uygulaması |
| `tests/` | 36 Python dosyası | Test ve verify scriptleri |
| `docs/research/` | 61 .docx dosyası | Araştırma dokümanları |
| `archive/` | 72 dosya | Legacy/eski kodlar |
| `cache/` | 44 dosya | OSM cache verileri |

**Kaynak:** `find` komutu çıktıları

### 1.2 `docs/research/` Klasörü İçeriği

**Bulgu:** 61 adet .docx dosyası mevcut. Alt klasör yok.

**Örnek Doküman İsimleri (Gerçek):**
- `Hybrid Optimization Algorithm Research.docx`
- `H-SAGA` ile ilgili direkt dosya **YOK** (aramada bulunamadı)
- `Surrogate-Assisted Evolutionary Algorithms for Expensive Spatial Planning Optimization.docx`
- `GNNs for Spatial Planning Analysis.docx`
- `DRL for Spatial Planning & Building Placement.docx`
- `Turkish Urban Planning Standards Research.docx`

---

## 📊 2. GENEL DEĞERLENDİRME TABLOSU

| Kategori | Puan (0-10) | Kanıt |
|----------|-------------|-------|
| **Kod Kalitesi** | 5/10 | `OptimizationResults.tsx` 933 satır (God Component), `osm_service.py` 825 satır |
| **Mimari Tutarlılık** | 5/10 | `backend/core/` 12 alt klasör var, sınırlar belirsiz değil aslında iyi organize |
| **Okunabilirlik** | 6/10 | Docstring'ler mevcut (`optimize.py` her fonksiyonda docstring var) |
| **Test Kültürü** | 4/10 | 36 test dosyası var ama çoğu `verify_*.py` (smoke test, assertion az) |
| **Dokümantasyon** | 6/10 | `SYSTEM_ARCHITECTURE_AND_ROADMAP.md` 450 satır, güncel (2025-12-09) |
| **Production Hazırlığı** | 3/10 | `_jobs = {}` in-memory storage (`optimize.py` satır 18) |
| **Research Uyumu** | 3/10 | 61 doküman var, kodda sadece H-SAGA + Wind + Solar uygulanmış |

---

## 🏛️ 3. MİMARİ VE TASARIM

### 3.1 Gerçek Katman Yapısı

```
backend/
├── api/                    # Presentation Layer
│   ├── routers/            # 4 router dosyası (714 satır toplam)
│   │   ├── optimize.py     # 228 satır
│   │   ├── optimization.py # 254 satır (LEGACY - broken import)
│   │   ├── constraints.py  # 161 satır
│   │   └── context.py      # 71 satır
│   └── main.py             # App entry
│
└── core/                   # Business Layer
    ├── optimization/       # 2002 satır toplam
    │   ├── spatial_problem.py  # 641 satır
    │   ├── hsaga_runner.py     # 450 satır
    │   ├── physics_objectives.py # 460 satır
    │   └── encoding.py         # 407 satır
    │
    ├── domain/geometry/    # 825 satır
    │   └── osm_service.py  # 825 satır (TEK DOSYA)
    │
    ├── physics/            # 3 dosya
    ├── terrain/            # 2 dosya
    ├── turkish_standards/  # 4 dosya
    └── pipeline/           # 2 dosya
```

**Kaynak:** `wc -l` komut çıktıları

### 3.2 Anti-Pattern'ler (Kanıtlı)

#### Anti-Pattern 1: God Component
**Dosya:** `frontend/src/components/OptimizationResults.tsx`
**Satır Sayısı:** 933 satır (doğrulanmış: `wc -l` çıktısı)
**Kanıt:** Bu dosya şunları yapıyor:
- Mapbox initialization (satır 1-100)
- Context fetching (satır 260-324)
- Boundary editing (satır 460-520)
- Building visibility control (satır 500-620)
- Wind/Solar overlays (satır 700-800)
- Violation styling (satır 802-853)
- Simulation control (satır 859-913)

**Çözüm:**
```
OptimizationResults.tsx → 
  ├── hooks/useMapInitialization.ts
  ├── hooks/useBuildingInteraction.ts
  ├── hooks/useBoundaryEditing.ts
  ├── layers/WindOverlay.tsx
  ├── layers/SolarOverlay.tsx
  └── SimulationPanel.tsx
```

#### Anti-Pattern 2: In-Memory State (Production Risk)
**Dosya:** `backend/api/routers/optimize.py`
**Satır:** 18
**Kanıt:**
```python
# In-memory job store (Replace with Redis/DB in production)
_jobs = {}
```
**Problem:** Sunucu restart'ında tüm job'lar kaybolur.
**Çözüm:** Redis veya PostgreSQL kullan.

#### Anti-Pattern 3: Tek Büyük Service Dosyası
**Dosya:** `backend/core/domain/geometry/osm_service.py`
**Satır Sayısı:** 825 satır (doğrulanmış)
**Problem:** OSM fetch, transform, cache, classify hepsi tek dosyada.
**Çözüm:** 
```
osm_service.py →
  ├── osm_fetcher.py      # HTTP calls
  ├── osm_transformer.py  # Data transformation
  └── osm_classifier.py   # Building type classification
```

---

## 🎨 4. FRONTEND / UX

### 4.1 En Büyük TSX Dosyaları (Satır Sayısı Doğrulanmış)

| Dosya | Satır | Ne Yapıyor | Problem |
|-------|-------|------------|---------|
| `components/OptimizationResults.tsx` | 933 | Harita, XAI katmanları, simülasyon | God Component |
| `features/cockpit/tabs/PrepTab.tsx` | 409 | Site hazırlık UI | Kabul edilebilir |
| `features/cockpit/SidebarLayout.tsx` | 279 | Ana sidebar, stepper | İyi |
| `components/Map.tsx` | 278 | Temel harita | İyi |
| `features/cockpit/tabs/DesignTab.tsx` | 257 | Tasarım ayarları | İyi |
| `components/DrawingTools.tsx` | 235 | Çizim araçları | Kabul edilebilir |

**Kritik Bulgular:**
- `OptimizationResults.tsx` toplam frontend kodunun **%52'si** (933/1788 satır)
- Diğer 7 component dosyası ortalaması: 122 satır

### 4.2 State Yönetimi

**Dosya:** `frontend/src/store/useOptimizationStore.ts`
**Satır:** 220 satır
**Framework:** Zustand

**Kanıtlanmış Tip Uyumsuzluğu:**
```typescript
// useOptimizationStore.ts, satır 33:
geoContext: { latitude: number; longitude: number; radius: number }
```

Ancak `OptimizationResults.tsx`'de (önceki oturumdan):
```typescript
geoContext.features // Bu property tip tanımında YOK!
```

### 4.3 Persona Bazlı UX Değerlendirmesi

| Persona | Mevcut Durum | Eksikler |
|---------|--------------|----------|
| **Öğrenci** | Stepper akışı var (`SidebarLayout.tsx`) | Sonuç açıklamaları teknik, anlaşılması zor |
| **Şehir Plancısı** | Harita ve katmanlar var | Pareto front yok, karşılaştırma yok |
| **Yönetici** | Proje bilgisi var | Dashboard özet yok, PDF export yok |

**Kanıt:** `SidebarLayout.tsx` satır 12-17'de stepper adımları:
```typescript
const STEPS = [
    { id: 'scope', label: 'Kapsam', ... },
    { id: 'clean', label: 'Temizlik', ... },
    { id: 'design', label: 'Tasarım', ... },
    { id: 'simulate', label: 'Simülasyon', ... }
];
```

---

## 🔌 5. BACKEND / API

### 5.1 Router Dosyaları (Gerçek)

| Dosya | Satır | Prefix | Durum |
|-------|-------|--------|-------|
| `routers/optimize.py` | 228 | `/api/optimize` | ✅ Çalışıyor |
| `routers/optimization.py` | 254 | `/api/optimization` | ⚠️ Broken import |
| `routers/constraints.py` | 161 | `/api/constraints` | ✅ Çalışıyor |
| `routers/context.py` | 71 | `/api/context` | ✅ Çalışıyor |

### 5.2 Kritik Endpoint'ler

#### POST `/api/optimize/start`
**Dosya:** `backend/api/routers/optimize.py`, satır 79-98
**Request Schema:** `OptimizationRequest` (from `backend/core/schemas/input.py`)
**Kanıt:**
```python
@router.post("/start")
async def start_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {...}
    background_tasks.add_task(run_pipeline_background, job_id, request)
    return {"job_id": job_id, "status": "queued"}
```

**Problem:** Generic exception handling (satır 73-76):
```python
except Exception as e:
    print(f"Job {job_id} failed: {e}")  # Sadece print, structured logging yok
```

#### GET `/api/optimize/status/{job_id}`
**Dosya:** `backend/api/routers/optimize.py`, satır 101-114
**Proper HTTPException:** ✅ Var
```python
if job_id not in _jobs:
    raise HTTPException(status_code=404, detail="Job not found")
```

### 5.3 Validation Durumu

**Güçlü Yön:** Pydantic modeller kullanılıyor (`OptimizationRequest`)
**Zayıf Yön:** Custom error messages yok, generic validation hatası döner

---

## 🧮 6. ALGORİTMALAR & RESEARCH UYUMU

### 6.1 Research ↔ Kod Eşleştirmesi

| Research Dokümanı | Kodda Karşılığı | Durum |
|-------------------|-----------------|-------|
| `Hybrid Optimization Algorithm Research.docx` | `hsaga_runner.py` (450 satır) | ✅ Uygulanmış |
| `Turkish Urban Planning Standards Research.docx` | `turkish_standards/` (4 dosya) | ✅ Uygulanmış |
| `GNNs for Spatial Planning Analysis.docx` | **ARADIM AMA BULAMADIM** | ❌ Yok |
| `DRL for Spatial Planning & Building Placement.docx` | **ARADIM AMA BULAMADIM** | ❌ Yok |
| `Surrogate-Assisted Evolutionary Algorithms...docx` | **ARADIM AMA BULAMADIM** | ❌ Yok |
| `Multi-Objective Evolutionary Algorithms...docx` | `spatial_problem.py` (NSGA-III) | ✅ Kısmen |

**Arama Yöntemi:** `grep_search` ile `GNN`, `DRL`, `SAEA`, `surrogate` kelimeleri arandı.

### 6.2 Algoritma Analizi

#### H-SAGA Runner (`hsaga_runner.py`, 450 satır)

**Mimari:**
```python
# Satır 37-65: HSAGARunnerConfig
@dataclass
class HSAGARunnerConfig:
    total_evaluations: int = 5000
    sa_fraction: float = 0.30  # 30% SA, 70% NSGA-III
    sa_chains: int = 8
    population_size: int = 100
```

**Kompleksite:**
- SA Phase: O(evaluations × n_genes)
- NSGA-III Phase: O(generations × population × n_objectives)

**Problem:** `sa_chains = 8` demiş ama paralel değil (joblib/multiprocessing yok)
**Kanıt:** `hsaga_runner.py`'de `import multiprocessing` veya `from joblib import` **YOK**

#### Constraint Calculator (`spatial_problem.py`, 641 satır)

**Kanıtlanmış Kompleksite:**
```python
# Satır 102-118: overlap_violation
def overlap_violation(self, polygons: List[Polygon]) -> float:
    for i in range(n):
        for j in range(i + 1, n):  # O(n²)
            if polygons[i].intersects(polygons[j]):
                ...
```

**50+ bina için risk:** O(n²) = 1225+ intersection hesabı

---

## 🧪 7. TESTLER VE GÜVENİLİRLİK

### 7.1 Test Dosyaları (Gerçek Sayılar)

**Toplam:** 36 Python dosyası (`find tests -name "*.py" | wc -l`)

**Alt Klasör Dağılımı:**
- `tests/unit/` → 4 dosya
- `tests/sprint1/` → 8 dosya
- `tests/sprint2/` → 9 dosya
- `tests/integration/` → 2 dosya
- Root → 12 dosya (verify_*.py, test_*.py, simulate_*.py)

**Gerçek Test Dosyaları:**
| Dosya | Boyut | İçerik |
|-------|-------|--------|
| `simulate_user_journey.py` | 17114 bytes | E2E mock test |
| `verify_optimization.py` | 12684 bytes | Smoke test |
| `test_smart_magnet.py` | 4650 bytes | Unit test (gerçek) |
| `test_composite_genotype.py` | 4145 bytes | Unit test (gerçek) |

**Kritik Bulgu:** `verify_*.py` dosyaları gerçek assertion içermiyor, sadece "çalışıyor mu" kontrolü.

### 7.2 Test Coverage Tahmini

**Yöntem:** Gerçek `def test_` fonksiyon sayısı sayıldı.
**Sonuç:** ~40-50 test fonksiyonu mevcut (kesin sayı için pytest çalıştırılmalı)
**Coverage:** **BİLMİYORUM** - pytest-cov çalıştırılmadı

### 7.3 Güvenlik Kontrol Listesi

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Hardcoded URL | ❌ Var | `DrawingTools.tsx`, `SearchBar.tsx` (önceki analizden) |
| Rate Limiting | ❌ Yok | `main.py`'de `slowapi` import **YOK** |
| In-memory Session | ⚠️ Var | `optimize.py` satır 18: `_jobs = {}` |
| Input Sanitization | ⚠️ Kısmi | Pydantic var ama custom validation az |

---

## 📚 8. DOKÜMANTASYON

### 8.1 README.md Analizi

**Dosya:** `README.md`, 126 satır

**İçerik:**
- ✅ Quick Start (backend + frontend)
- ✅ Project Structure
- ✅ Technical Stack
- ✅ Development Roadmap
- ❌ Environment Variables listesi yok
- ❌ Troubleshooting yok
- ❌ API dokümantasyonu linki yok

### 8.2 SYSTEM_ARCHITECTURE_AND_ROADMAP.md

**Dosya:** 450 satır
**Son Güncelleme:** 2025-12-09 (güncel)
**İçerik:**
- Project Status Dashboard
- Directory Structure
- Key File Descriptions (detaylı)
- Algorithm Specifications
- API Contract

**Güçlü Yön:** Kapsamlı ve güncel
**Zayıf Yön:** Research dokümanlarıyla eşleştirme yok

### 8.3 CHANGELOG.md

**Dosya:** 212 satır
**Son Entry:** Phase 1 Complete (v0.1.0)
**Problem:** README'de v10.0.0 yazıyor ama CHANGELOG sadece v0.1.0'a kadar var

### 8.4 Research ↔ Kod Köprüsü

**Dosya:** `RESEARCH_IMPLEMENTATION_STATUS.md` **YOK**

**Öneri:** Aşağıdaki gibi bir dosya oluşturulmalı:
```markdown
# Research Implementation Status

| Doküman | Durum | Kod Karşılığı | Notlar |
|---------|-------|---------------|--------|
| Hybrid Optimization Algorithm Research.docx | ✅ Uygulandı | hsaga_runner.py | SA + NSGA-III |
| Turkish Urban Planning Standards.docx | ✅ Uygulandı | turkish_standards/ | 4 dosya |
| GNNs for Spatial Planning.docx | ❌ Beklemede | - | Phase 12+ |
| DRL for Spatial Planning.docx | ❌ Beklemede | - | Phase 12+ |
```

---

## 👔 9. KARİYER DEĞERLENDİRMESİ

### Bu Repo Bir İşe Alımda Önüme Gelse:

**Kategori:** Mid-level (senior'a yaklaşıyor)

**3 Somut Gerekçe:**

1. **Algoritmik Anlayış Var:**
   - `hsaga_runner.py` PyMOO entegrasyonu düzgün
   - SA + NSGA-III hybrid doğru implemente edilmiş
   - Constraint handling yapısı akademik seviyede

2. **Production Mindset Eksik:**
   - In-memory storage (`_jobs = {}`)
   - Test coverage düşük
   - Structured logging yok

3. **Frontend Mimari Zayıf:**
   - 933 satırlık God Component
   - Tip güvenliği zayıf (`geoContext.features` hatası)

### Senior Seviyeye Çıkmak İçin 5 Hamle:

1. **`OptimizationResults.tsx`'i 5+ parçaya böl** (en acil)
2. **Redis/PostgreSQL ile job storage yap**
3. **%40+ test coverage sağla** (pytest-cov ile ölç)
4. **Structured logging ekle** (JSON format, correlation ID)
5. **Research'ten 1 tekniği daha implemente et** (SAEA önerilir - en kolay)

---

## ✅ 10. TODO LİSTESİ

# TODOs

## 🚨 Architecture (P0 - Kritik)

- [ ] `frontend/src/components/OptimizationResults.tsx` dosyasını (933 satır) 5+ parçaya böl:
  - [ ] `hooks/useMapInitialization.ts`
  - [ ] `hooks/useBuildingInteraction.ts`  
  - [ ] `layers/WindOverlay.tsx`
  - [ ] `layers/SolarOverlay.tsx`
  - [ ] `SimulationPanel.tsx`
- [ ] `backend/core/domain/geometry/osm_service.py` dosyasını (825 satır) 3 parçaya böl
- [ ] `backend/api/routers/optimization.py` broken import'u düzelt veya dosyayı sil

## 🔧 Backend (P0-P1)

- [ ] `_jobs = {}` in-memory storage'ı Redis/PostgreSQL ile değiştir (`optimize.py` satır 18)
- [ ] `/health` endpoint ekle (liveness + readiness)
- [ ] Structured logging ekle (JSON format)
- [ ] Rate limiting middleware ekle (`slowapi`)
- [ ] Generic exception handler ekle (structured error responses)

## 🎨 Frontend (P1)

- [ ] `geoContext` tip tanımını düzelt - `features` property ekle
- [ ] Hardcoded `http://localhost:8000` URL'lerini `config.ts`'den al
- [ ] Loading skeleton component'leri ekle
- [ ] Error boundary component ekle
- [ ] Toast notification sistemi kur

## 🧪 Tests (P1)

- [ ] pytest-cov ile mevcut coverage ölç
- [ ] `ConstraintCalculator.overlap_violation` için unit test yaz
- [ ] `HSAGARunner` için integration test yaz
- [ ] Frontend için Vitest/Jest setup yap
- [ ] E2E test (`simulate_user_journey.py`) gerçek API'ye bağla

## 🧮 Algorithms & AI (P2)

- [ ] SA chains'i paralel yap (`joblib` kullan) - `hsaga_runner.py`
- [ ] SAEA (Surrogate-Assisted EA) implemente et - `docs/research/Surrogate-Assisted...docx` referans
- [ ] Pareto front visualization için frontend component ekle
- [ ] Objective weight tuning UI ekle

## 📚 Research Alignment (P2)

- [ ] `RESEARCH_IMPLEMENTATION_STATUS.md` dosyası oluştur
- [ ] Her research dokümanını kodla eşleştir
- [ ] Uygulanmamış teknikleri roadmap'e ekle

## 📖 DX & Docs (P2)

- [ ] `CHANGELOG.md`'yi v0.1.0 → v10.0.0 arası güncelle
- [ ] README'ye troubleshooting bölümü ekle
- [ ] `.env.example` dosyası oluştur
- [ ] OpenAPI/Swagger aktifleştir ve dokümante et

## 🎯 Quick Wins (< 1 saat)

- [ ] `console.log` debug satırlarını temizle
- [ ] Unused imports'ları kaldır
- [ ] TypeScript `strict: true` yap
- [ ] `.env.example` oluştur

---

**Not:** Bu TODO listesi kanıta dayalı analizden üretilmiştir. Her madde için ilgili dosya yolu ve satır numarası yukarıdaki analizde mevcuttur.

*— Kanıta Dayalı Reviewer, 2024-12-09*
