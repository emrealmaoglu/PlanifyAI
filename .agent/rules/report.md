---
trigger: always_on
---

## 18. RAPORLAMA DAVRANIŞI

Her anlamlı iş bitiminde (bir roadmap maddesi, bir refactor, bir feature vb.) kullanıcıya **standart bir formatta** rapor vermek zorundasın.

### 18.1 Rapor Formatı

Raporun aşağıdaki başlıkları içermeli:

1. **Roadmap Maddesi**
   - Örnek: `Faz 1.1.2 – Building interaction hook'u ayır`
   - Eğer roadmap’te birebir karşılığı yoksa:  
     `Roadmap dışı iş: <kısa açıklama>`

2. **Yapılan İşler (Özet)**
   - Madde madde, maks 5–7 satır:
     - “OptimizationResults’ten map init logic’i alıp useMapInitialization’a taşıdım.”
     - “DrawingTools içindeki hardcoded URL’leri config’e çektim.”

3. **Dokunulan Dosyalar**
   - Liste şeklinde:
     - `frontend/src/components/OptimizationResults.tsx`
     - `frontend/src/hooks/useMapInitialization.ts`
     - `backend/api/routers/optimize.py`
   - Gereksiz dosya spam’i yapma, sadece anlamlı değişiklik olanları yaz.

4. **Çalıştırılan Komutlar & Sonuçları**
   - Örnek:
     - `npm run build` → ✅ geçti  
     - `pytest tests/unit/test_constraints.py` → ❌ failed (sebebi: …)
   - Hiç komut çalıştırmadıysan, dürüstçe yaz:
     - “Bu adımda test/build komutu ÇALIŞTIRMADIM.”

5. **Teknik Notlar / Riskler**
   - Kısa ama net:
     - “Şu an behavior değişmedi ama ileride job store değişirken migration gerekebilir.”
     - “Bu refactor UI davranışını değiştirmiyor; sadece iç yapıyı sadeleştiriyor.”

6. **Bir Sonraki Önerilen Adım**
   - Roadmap referansıyla:
     - “Öneri: Sırada Faz 1.1.3 – Boundary editing hook’u devreye alalım.”
     - “Alternatif: Backend job store’a geçmeden önce şu testleri yazmak mantıklı.”

### 18.2 Stil

- Kısa, net, teknik.
- “Baktım, biraz temizledim” gibi boş cümleler yok.
- Her rapor, başka bir mühendisin okuyunca:
  - “Ne değişmiş, nereye dokunulmuş, sırada ne var?” sorularına direkt cevap vermeli.
