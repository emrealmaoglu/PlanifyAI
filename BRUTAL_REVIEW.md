# 🔥 ACIMASIZ KOD İNCELEMESİ: PlanifyAI

> **Tek cümlelik özet:** Bu repo, akademik bir prototip seviyesinde; production'a çıkması ciddi risk, research ile kod arasında uçurum var, ancak temel algoritmik altyapı düşünceli kurulmuş.

---

## 📊 1. GENEL DEĞERLENDİRME

| Kategori | Puan (0-10) | Yorum |
|----------|-------------|-------|
| **Kod Kalitesi** | 5/10 | Backend temiz, frontend spagetti. TypeScript kullanılmış ama tip güvenliği yok. |
| **Mimarinin Tutarlılığı** | 4/10 | Katmanlar var ama sınırlar bulanık. API contract'lar frontend-backend arasında uyumsuz. |
| **Okunabilirlik** | 6/10 | Docstring'ler iyi, ama 900+ satırlık component'ler okunabilirliği öldürüyor. |
| **Test Kültürü** | 3/10 | ~8000 satır test kodu var ama çoğu "verify" scripti. Gerçek unit test yok denecek kadar az. |
| **Dokümantasyon** | 6/10 | SYSTEM_ARCHITECTURE.md detaylı, ancak güncel değil. CHANGELOG fosil. |
| **Production Hazırlığı** | 2/10 | **Bu haliyle production'a çıkmak ciddiye risk.** In-memory storage, hardcoded URL'ler, sıfır rate limiting. |
| **Research Uyumu** | 3/10 | 61 doküman var, 6'sı kullanımda. Vizyon ile kod arasında uçurum. |

**Genel Puan: 4.1/10 — "İyi niyetli akademik prototip"**

---

## 🏛️ 2. MİMARİ VE TASARIM ELEŞTİRİSİ

### 2.1 Katman Ayrımı: "Var ama Yok"

```
backend/
├── api/           # Presentation katmanı ✅
│   └── routers/   # HTTP handlers
├── core/          # Business logic ⚠️ KARIŞIK
│   ├── domain/    # Domain modelleri
│   ├── optimization/  # Algoritmalar
│   ├── physics/   # Fizik hesaplamaları
│   └── pipeline/  # Orchestration
```

**Sorunlar:**
1. **`core/` klasörü God Package:** İçinde domain, application, infrastructure hepsi karışık.
2. **Circular import riski:** `optimization` → `domain` → `physics` → `optimization` zinciri var.
3. **`osm_service.py` = 850+ satırlık canavar:** Bu tek dosya, veri çekme, dönüştürme, validasyon hepsini yapıyor.

### 2.2 Anti-Pattern'ler

| Anti-Pattern | Nerede? | Etki |
|--------------|---------|------|
| **God Object** | `OptimizationResults.tsx` (934 satır) | Test edilemez, okunmaz, bakımı imkansız |
| **Spaghetti** | Frontend state yönetimi | `useEffect` zincirleri birbirini tetikliyor |
| **Anemic Domain Model** | `backend/core/schemas/input.py` | Sadece veri tutucu, iş mantığı yok |
| **Hardcoded Config** | `DrawingTools.tsx`, `SearchBar.tsx` | `http://localhost:8000` direkt kodda |
| **In-Memory State** | `constraints.py`, `optimize.py` | `_jobs = {}` — sunucu yeniden başlayınca her şey uçar |

### 2.3 Ölçeklenme Kırılma Noktaları

1. **10x Kullanıcı:** In-memory job storage patlar. Redis/DB şart.
2. **100x Kullanıcı:** OSMnx API rate limit, DEM cache dolması.
3. **1000x Kullanıcı:** Single-process Python backend ölür. Worker queue (Celery) lazım.

**ÇÖZÜM:**
```diff
- _jobs: Dict[str, OptimizationJob] = {}
+ from redis import Redis
+ jobs = Redis().hgetall("optimization:jobs")
```

---

## 🎨 3. FRONTEND / UX DEĞERLENDİRMESİ

### 3.1 Component Yapısı: Felaket

```
src/
├── components/
│   └── OptimizationResults.tsx  # 934 SATIR! Bu rezalet.
├── features/
│   └── cockpit/
│       ├── SidebarLayout.tsx     # 280 satır
│       └── tabs/                 # Biraz daha mantıklı
```

**`OptimizationResults.tsx` bir God Component:**
- Mapbox initialization
- Context fetching
- Boundary editing
- Building visibility
- Wind/solar overlays
- Violation styling
- Simulation control

**Bu dosya en az 8 parçaya bölünmeli:**
1. `MapContainer.tsx`
2. `hooks/useMapInitialization.ts`
3. `hooks/useBuildingInteraction.ts`
4. `hooks/useBoundaryEditing.ts`
5. `layers/WindLayer.tsx`
6. `layers/SolarLayer.tsx`
7. `layers/ViolationLayer.tsx`
8. `SimulationControls.tsx`

### 3.2 State Yönetimi

Zustand kullanılmış — iyi seçim. AMA:

```typescript
// useOptimizationStore.ts
geoContext: { latitude: number; longitude: number; radius: number }
```

**Sonra kodda:**
```typescript
// OptimizationResults.tsx
geoContext.features // ??? Bu tip tanımında yok!
```

**Type safety sıfır.** TypeScript kullanmanın anlamı kalmamış.

### 3.3 UX Perspektifi (Farklı Kullanıcı Tipleri)

| Persona | Durum | Problem |
|---------|-------|---------|
| **Öğrenci** | 😐 | Stepper akışı iyi, ama simülasyon sonuçları anlaşılmaz |
| **Şehir Plancısı** | 😞 | Pareto front yok, karşılaştırma yok, katman filtreleme primitif |
| **Yönetici** | 😢 | Özet dashboard yok, export raporları yok |
| **Yatırımcı** | 😡 | ROI, maliyet analizi sıfır |

**ÇÖZÜM:**
```markdown
- [ ] Persona bazlı dashboard view'ları ekle
- [ ] Pareto front görselleştirmesi (scatter plot)
- [ ] "Sonuçları PDF olarak dışa aktar" butonu
- [ ] Türkçe açıklamalar her metriğin yanında (tooltip)
```

---

## 🔌 4. BACKEND / API / VERİ MODELİ

### 4.1 API Tutarsızlıkları

| Frontend Çağrısı | Backend Endpoint | Durum |
|------------------|------------------|-------|
| `/api/optimization/run` | `/api/optimize/start` | ❌ UYUMSUZ |
| `/health` | Tanımsız | ❌ YOK |
| `/api/context/fetch` | `/api/context/fetch` | ✅ Çalışıyor |

**Bu uyuşmazlık canlıda patlar.** Birisi frontend'i, birisi backend'i geliştirmiş, konuşmamışlar.

### 4.2 Validation ve Error Handling

```python
# optimize.py
try:
    result = await run_optimization(request)
except Exception as e:
    return {"error": str(e)}  # 💀 Generic error, status code yok
```

**Production'da:**
- Hata logları anlamsız olur
- Frontend hangi hatayı göstereceğini bilemez
- Debugging imkansız

**ÇÖZÜM:**
```python
from fastapi import HTTPException

class OptimizationError(Exception):
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

@router.post("/start")
async def start_optimization(request: OptimizationRequest):
    try:
        ...
    except ConstraintInfeasibleError as e:
        raise HTTPException(
            status_code=422,
            detail={"code": "INFEASIBLE", "message": str(e), "constraints": e.violations}
        )
```

### 4.3 Domain Model

```
ExistingBuilding → osm_id, building_type, height, geometry
OptimizationRequest → project_name, latitude, building_counts, ...
```

**Sorun:** Bunlar "anemic" — sadece veri tutucu. İş mantığı dışarıda.

**Gerçek bir şehir planlama domain modeli:**
```python
class Campus(Entity):
    boundary: Polygon
    buildings: List[Building]
    roads: List[Road]
    
    def add_building(self, building: Building) -> Result[None, ConstraintViolation]:
        """Validate and add, returning errors if constraints fail."""
        violations = self.constraint_checker.check(building)
        if violations:
            return Err(violations)
        self._buildings.append(building)
        self.emit(BuildingAddedEvent(building))
        return Ok(None)
```

---

## 🧮 5. ALGORİTMALAR VE OPTİMİZASYON

### 5.1 Research Uyumu: Uçurum Var

**Research'de bahsedilen ama kodda OLMAYAN:**

| Teknik | Doküman | Kod | Durum |
|--------|---------|-----|-------|
| SAEA (Surrogate-Assisted EA) | ✅ 5 doküman | ❌ | Yok |
| GNN (Graph Neural Network) | ✅ 3 doküman | ❌ | Yok |
| DRL (Deep Reinforcement Learning) | ✅ 4 doküman | ❌ | Yok |
| Bayesian Optimization | ✅ 2 doküman | ❌ | Yok |
| H-SAGA | ✅ Ana doküman | ✅ | **Uygulanmış** |
| Wind Physics | ✅ | ✅ | Uygulanmış |
| Solar Physics | ✅ | ✅ | Uygulanmış |

**Sonuç:** 61 araştırma dokümanından sadece 6'sı gerçekten koda yansımış. Geri kalanı "bir gün yapacağız" listesi.

### 5.2 Algoritma Kalitesi: İyi Ama Basit

```python
# hsaga_runner.py
class SAExplorer:
    """Simulated Annealing for exploration."""
    
    def _scalarize(self, F, G):
        obj_sum = np.sum(F)
        penalty = self.config.constraint_penalty * np.sum(np.maximum(0, G))
        return obj_sum + penalty
```

**İyi olan:** Açık, anlaşılır, PyMOO entegrasyonu düzgün.

**Kötü olan:**
1. **Scalarization basit:** Equal weight kullanılmış. Research'de TOPSIS, fuzzy AHP var — hiçbiri yok.
2. **Constraint handling:** Tek penalty parametresi. Adaptive penalty, ε-constraint yok.
3. **Parallelism:** `sa_chains = 8` demiş ama gerçek paralel çalışmıyor.

**ÇÖZÜM:**
```python
from joblib import Parallel, delayed

def run_parallel_sa(self, n_chains: int):
    results = Parallel(n_jobs=n_chains)(
        delayed(self._run_single_chain)(i) for i in range(n_chains)
    )
    return merge_pareto_fronts(results)
```

### 5.3 Karmaşıklık Analizi

| Fonksiyon | Karmaşıklık | Sorun |
|-----------|-------------|-------|
| `overlap_violation()` | O(n²) | 100+ bina ile yavaşlar |
| `dynamic_setback_violation()` | O(n × e × r) | n=binalar, e=kenarlar, r=yollar |
| `decode_all_to_polygons()` | O(n) | ✅ İyi |

**50+ bina senaryosunda test et — muhtemelen 10s+ sürer.**

---

## 🧪 6. TESTLER VE GÜVENİLİRLİK

### 6.1 Test Durumu: Hobi Projesi Seviyesi

```bash
$ find tests -name "*.py" | xargs wc -l
    7983 total  # Çok görünüyor ama...
```

**Gerçekte:**
- `simulate_user_journey.py` → Mock test, gerçek API çağrısı yok
- `verify_*.py` → Smoke test, assertion yok çoğunda
- `test_*.py` → Birkaç gerçek unit test var

**Unit test coverage tahmini: %5-10**

### 6.2 Güvenlik Açıkları

| Açık | Dosya | Severity |
|------|-------|----------|
| Hardcoded API URL | `DrawingTools.tsx` | Medium |
| No rate limiting | Tüm API | High |
| In-memory session | `constraints.py` | Medium |
| No input sanitization | `osm_service.py` | Medium |
| CORS wildcard muhtemelen | `main.py` | Medium |

**ÇÖZÜM:**
```python
# main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/optimize/start")
@limiter.limit("10/minute")
async def start_optimization(...):
    ...
```

---

## 📚 7. DOKÜMANTASYON VE DX

### 7.1 README: Vitrin, Gerçekçi Değil

```markdown
# PlanifyAI - Akıllı Kampüs Stüdyosu

Yeni nesil kampüs yerleşim aracı...
```

**Eksikler:**
- Environment variables listesi yok
- Troubleshooting bölümü yok
- API dokümantasyonu yok (Swagger/OpenAPI var mı?)
- Contribution guide yok

### 7.2 CHANGELOG: Fosil

```markdown
# Changelog
## Phase 1 Complete (v0.1.0)
...
```

**Şu an v10.0.0 — CHANGELOG'da v0.1.0 var.** 9 version kayıp.

### 7.3 Research → Kod Köprüsü: Yok

`research/` klasöründe 61 doküman var. Bunları kodla eşleştiren bir `RESEARCH_IMPLEMENTATION_STATUS.md` yok.

---

## 👔 8. KARİYER DEĞERLENDİRMESİ

### Bu repo önüme gelse:

**Kategori: Mid-level, Senior olmaya çalışan**

**Artılar:**
- Karmaşık bir domaine cesurca dalınmış
- Algoritmik düşünce var (H-SAGA, constraint handling)
- PyMOO, Mapbox gibi profesyonel kütüphaneler kullanılmış
- Dokümantasyon çabası var

**Eksiler:**
- Production mindset yok (in-memory storage, no tests)
- Frontend'de separation of concerns kavramı oturmamış
- "Çalışıyor" seviyesinde kalmış, "ölçekleniyor" değil
- Research vizyonu ile uygulama arasında uçurum

### Senior Seviyeye Çıkmak İçin 5 Kritik İyileştirme:

1. **`OptimizationResults.tsx`'i 8+ parçaya böl** — Bu tek başına junior-senior farkını gösterir
2. **API contract'ları OpenAPI ile dokümante et** ve frontend-backend uyumunu sağla
3. **En az %40 unit test coverage** — Happy path + edge case + error case
4. **In-memory storage'ı Redis/PostgreSQL ile değiştir** — Production-ready düşün
5. **Research'ten bir tekniği (örn: SAEA) gerçekten implemente et** — Sadece H-SAGA var

---

## ✅ 10. TODO LİSTESİ (PRİORİTE SIRALI)

# TODOs

## 🚨 Critical (P0) — Production Blocker

### Architecture
- [ ] `backend/api/routers/optimization.py` silinen modülü import ediyor — kaldır veya düzelt
- [ ] `frontend/src/config.ts` tek merkezi config dosyası kullan, hardcoded URL'leri temizle
- [ ] Rate limiting middleware ekle (`slowapi` veya FastAPI-limiter)
- [ ] In-memory `_jobs` dict'i Redis/PostgreSQL ile değiştir

### Backend
- [ ] `/health` endpoint'i ekle (liveness + readiness)
- [ ] API prefix'lerini düzelt: `/api/optimization/` → `/api/optimize/` veya tersi
- [ ] Global exception handler ekle (structured error responses)
- [ ] Pydantic validation error'larını kullanıcı-dostu mesajlara çevir

### Frontend
- [ ] `OptimizationResults.tsx`'i en az 5 parçaya böl
- [ ] `geoContext` tip tanımını düzelt (features property ekle)
- [ ] Hardcoded `http://localhost:8000` URL'lerini config'den al

---

## ⚠️ High (P1) — Quality & Maintainability

### Architecture
- [ ] `osm_service.py`'ı 3 dosyaya böl: `osm_fetcher.py`, `osm_transformer.py`, `osm_cache.py`
- [ ] Domain model'leri zenginleştir (behavior ekle, anemic olmaktan çıkar)
- [ ] Event-driven mimari için basit event bus ekle

### Backend
- [ ] Async job polling yerine WebSocket/SSE progress stream kullan
- [ ] OSMnx rate limiting ve retry logic ekle
- [ ] DEM data'yı cache'le (file-based veya Redis)
- [ ] Structured logging ekle (JSON format, correlation ID)

### Frontend
- [ ] Loading skeleton component'leri ekle
- [ ] Toast notification sistemi kur
- [ ] Error boundary component ekle
- [ ] Keyboard shortcuts ekle (ESC=cancel, Enter=confirm)

### Tests
- [ ] `ConstraintCalculator` için unit test yaz (en kritik)
- [ ] `hsaga_runner.py` için integration test yaz
- [ ] Frontend için Vitest/Jest setup yap

---

## 📋 Medium (P2) — Good to Have

### Algorithms & AI
- [ ] Research'ten SAEA'yı implemente et (en kolay olanı)
- [ ] Parallel SA chains'i gerçekten paralel yap (joblib)
- [ ] Pareto front visualization için frontend component ekle
- [ ] Objective weight tuning UI'ı ekle

### Research Alignment
- [ ] `RESEARCH_IMPLEMENTATION_STATUS.md` oluştur
- [ ] Her uygulanmış tekniği ilgili dokümanla eşle
- [ ] "Roadmap vs Reality" bölümü ekle

### DX & Docs
- [ ] README'ye troubleshooting bölümü ekle
- [ ] CHANGELOG'u güncel tut (v1.0 → v10.0 arası)
- [ ] OpenAPI/Swagger dokümantasyonu aktifleştir
- [ ] Environment variables listesi oluştur

---

## 🔮 Low (P3) — Future Enhancements

### Frontend UX
- [ ] Persona bazlı dashboard view'ları
- [ ] PDF/Excel export
- [ ] Dark/light mode toggle (tutarlı)
- [ ] Mini-map navigation
- [ ] Undo/redo for boundary editing

### Backend
- [ ] Celery worker queue for long-running optimizations
- [ ] Result caching (same input = cached result)
- [ ] Multi-tenancy support (organization-based isolation)

### Algorithms
- [ ] GNN-based building placement suggestion
- [ ] DRL-based iterative improvement
- [ ] Case-based reasoning (similar campus lookup)

---

## 📌 Quick Wins (< 1 hour each)

- [ ] `CHANGELOG.md`'yi güncel version'a getir
- [ ] `console.log` debug satırlarını temizle
- [ ] Unused imports'ları kaldır (frontend)
- [ ] `.env.example` dosyası oluştur
- [ ] `TypeScript strict: true` yap ve hataları düzelt

---

**Son söz:** Bu repo iyi niyetle başlanmış, akademik potansiyeli var, ama production'a hazır değil. Yukarıdaki P0'ları halletmeden deploy etme. P1'leri halletmeden kullanıcı testine çıkma.

*— Acımasız Reviewer, 2024*
