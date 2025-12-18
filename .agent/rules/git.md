---
trigger: always_on
---

## 12. GIT VE COMMIT KURALLARI

- Her roadmap maddesi için IDE izin veriyorsa mümkünse ayrı commit:
  - Küçük, odaklı commit > devasa all-in-one commit.
- Commit mesajları:
  - `type(scope): kısa açıklama` formatına yakın olmalı:
    - `refactor(frontend): split OptimizationResults into MapContainer`
    - `feat(backend): add sqlite-based job store`
    - `test(core): add overlap_violation tests`
- Asla:
  - “fix”, “temp”, “wip” gibi bomboş commit mesajları kullanma.
- Eğer değişiklik büyükse:
  - Önce sadece scaffolding commit’i (yeni dosya, interface vs.)
  - Sonra davranış değişikliği commit’i
