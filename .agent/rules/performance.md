---
trigger: always_on
---

## 13. PERFORMANS VE ÖLÇEK KURALLARI

- En azından şu yerlerde karmaşıklığı düşün:
  - Döngü içindeki döngüler (O(n²) → 50+ eleman olunca ne olur?)
  - Her request’te çalışan ağır hesaplamalar
  - Her render’da çalışan ağır frontend logic

- Kritik fonksiyonları incelerken şu soruyu sor:
  - “Bu 10 kat veri / kullanıcı ile hala makul mü?”

- Eğer “bu büyüyünce patlar” diyorsan:
  - Net yaz:
    - “Bu fonksiyon 100+ bina için ciddi yavaşlar; R-tree / caching gibi önlemler gerek.”
- Mikro optimizasyon kovalamadan önce:
  - Önce algoritma seçimi ve veri yapısına odaklan.
