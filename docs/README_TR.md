# PlanifyAI

## Genel Bakış

PlanifyAI, kampüs ve şehir planlama için intent-driven (niyet odaklı) optimizasyon platformudur.

## Özellikler

- **H-SAGA Algoritması**: Li et al. 2025 reverse hybrid yaklaşımı
- **Semantic Tensor Fields**: Building-type aware yol ağı üretimi
- **M1 Optimizasyonu**: Apple Silicon native performans
- **Türkçe/İngilizce**: Çift dil desteği

## Kurulum

```bash
# Conda environment oluştur
conda env create -f environment.yml
conda activate planifyai

# Uygulamayı çalıştır
streamlit run app.py
```

## Kullanım

```python
from src.algorithms.hsaga import HybridSAGA
from src.models.building import Building, BuildingType

# Binaları tanımla
buildings = [
    Building("B1", BuildingType.RESIDENTIAL, 2000, 5),
    Building("B2", BuildingType.COMMERCIAL, 1500, 3),
]

# Optimizer oluştur
optimizer = HybridSAGA(
    area_bounds=(0, 0, 500, 500),
    buildings=buildings,
    constraints={'green_areas': []}
)

# Optimize et
result = optimizer.optimize()
print(f"Fitness: {result['fitness']:.3f}")
```

## Dokümantasyon

- [API Dokümantasyonu (TR)](api/TR/)
- [Hızlı Başlangıç Kılavuzu](guides/TR/quickstart.md)
