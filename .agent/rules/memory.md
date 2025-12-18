---
trigger: always_on
---

## 19. HAFIZA DOSYASI (AGENT_MEMORY.md)

Bu projede ajan olarak uzun vadeli hafızanı **tek bir dosyada** tutacaksın:  
Önerilen dosya: `docs/AGENT_MEMORY.md`  
(İstersen adı `DEV_MEMORY.md` / `ENGINEERING_JOURNAL.md` vb. olabilir ama tek dosya olmalı.)

### 19.1 Amaç

`AGENT_MEMORY.md` şu tip bilgileri tutmak için var:

- Uzun vadeli teknik kararlar  
  - Örn: “Job store için ilk iterasyonda SQLite seçildi, arayüz Redis’e geçişi destekleyecek şekilde tasarlandı.”
- Mimaride alınan kritik kararlar / trade-off’lar  
  - Örn: “OptimizationResults tamamen parçalanmadı, şu kısım bilerek dosyada bırakıldı çünkü…”
- Tekrar tekrar düşmemek istediğimiz tuzaklar  
  - Örn: “Mapbox draw event’leri için şu tipler kullanılmalı; `any` kullanmak bug’a yol açıyor.”
- Roadmap ile gerçeklik arasındaki sapmalar  
  - Örn: “Faz 1.2 ertelendi, çünkü Faz 2.1’e geçmeden önce X problemi çıkıyor.”

Geçici şeyler, günlük ufak işler, trivial bug fix’ler buraya yazılmaz.  
Burası **mühendislik hafızası + karar günlüğü**.

### 19.2 Yazma Zamanı

Aşağıdaki durumlarda `AGENT_MEMORY.md` içine yeni bir entry ekle:

- Mimaride anlamlı bir değişiklik yaptığında (özellikle backend / job store / state management).
- Roadmap’ten sapmak zorunda kaldığında.
- İleride kendine “neden böyle yaptık?” diye soracağın bir karar aldığında.
- Aynı hatanın tekrar edilmesini istemediğin bir şey öğrendiğinde.

Her ufak iş için yazma;  
**“Bu bilgi 1–6 ay sonra işime yarar mı?”** diye sor; cevabın evet ise yaz.

### 19.3 Format

Her entry aşağı yukarı şöyle olmalı:

```markdown
## [Tarih] – [Kısa Başlık]

**Bağlam:**
- (İlgili Faz / roadmap maddesi / dosya)
- Örn: Faz 2.1.1 – Job store geçişi, `backend/core/storage/job_store.py`

**Karar:**
- Ne yapmaya karar verdin?
- Örn: “İlk iterasyonda SQLiteJobStore kullanıyoruz, JobStore arayüzü future Redis implementasyonunu destekliyor.”

**Gerekçe:**
- Neden bu kararı aldın? (1–3 madde)
- Örn:
  - “Geliştirme ortamında Redis kurulum yükünü istemiyoruz.”
  - “Tek process için SQLite yeterli, ama interface sayesinde Redis’e geçiş basit olacak.”

**Etkiler:**
- Kısa vadeli etki:
  - “Restart sonrası job’lar artık kaybolmuyor.”
- Uzun vadeli risk / plan:
  - “Scale artırmak gerekirse RedisJobStore eklenmeli; AGENT_MEMORY’deki bu entry referans alınmalı.”

**İlgili Dosyalar:**
- `backend/core/storage/job_store.py`
- `backend/api/routers/optimize.py`
- `docs/ROADMAP.md` (Faz 2.1 güncellendi)
