# Agent Memory - PlanifyAI Mühendislik Kararları

> Son Güncelleme: 2025-12-10

---

## 2025-12-10 – SQLite Job Storage Mimarisi (Sprint 2, Faz 2.1)

**Bağlam:**
- Sprint 2, Faz 2.1 – Job Storage Mimarisi
- Dosyalar: `backend/core/storage/protocol.py`, `sqlite_store.py`, `__init__.py`
- Etkilenen: `backend/api/routers/optimize.py`, `backend/api/main.py`

**Karar:**
- In-memory `_jobs = {}` dictionary yerine SQLite-based persistent storage kullanıyoruz
- `JobStore` Protocol pattern ile interface tanımlandı
- İlk implementasyon: `SQLiteJobStore` (external dependency yok)

**Gerekçe:**
1. **Production Risk:** In-memory storage sunucu restart'ında tüm job'ları kaybediyordu
2. **Simplicity:** SQLite external dependency gerektirmiyor, setup kolay
3. **Future-proof:** Protocol pattern sayesinde Redis'e geçiş kolay olacak

**Etkiler:**
- Kısa vade: Job'lar artık restart'lardan sonra kaybolmuyor
- Uzun vade: Config ile Redis/Postgres'e switch için sadece yeni implementasyon gerekiyor

**İlgili Dosyalar:**
- `backend/core/storage/protocol.py` - JobStore Protocol + JobData TypedDict
- `backend/core/storage/sqlite_store.py` - SQLiteJobStore implementasyonu
- `backend/api/routers/optimize.py` - Migrate edildi
- `backend/api/main.py` - /health endpoint'e DB check eklendi

---

## 2025-12-10 – Frontend Ölü Kod Temizliği (Sprint 1, Faz 0-1)

**Bağlam:**
- Sprint 1 - Frontend refactor
- 7 dosya silindi, 8 dosya eklendi

**Karar:**
- Kullanılmayan component'lar silindi: ControlPanel, Sidebar, ProgressDisplay, Map, ErrorBoundary, api/client
- Legacy optimization router silindi

**Gerekçe:**
- Bu dosyalar hiçbir yerde import edilmiyordu
- Build hatalarına neden oluyorlardı (type mismatch)

**Dikkat:**
- `Map.tsx` silindi ama `OptimizationResults.tsx` hâlâ map yönetimini içeriyor
- Gelecekte MapContainer extraction yapılacaksa bu kararı hatırla

---
