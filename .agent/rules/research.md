---
trigger: always_on
---

## 14. RESEARCH ALIGNMENT MODU

- `docs/research/` klasörünü sadece süs olarak görme:
  - Uyguladığın her ciddi algoritma / standart için, ilgili research dokümanını bulmaya çalış.
- Eğer research’te var, kodda yoksa:
  - Bunu açıkça “boşluk” olarak işaretle:
    - “GNN üzerine doküman var, kodda hiçbir iz yok.”
- Yeni bir teknik implemente ettiğinde:
  - `RESEARCH_IMPLEMENTATION_STATUS.md` dosyasını güncelle:
    - Doküman adı
    - Hangi dosyalarda karşılığı olduğu
    - Ne seviyede implemente edildi (prototype / partial / full)
- Roadmap önerirken:
  - Research işlerini her zaman “core feature”’dan sonra, “hardening + experiment” katmanı olarak planla.
