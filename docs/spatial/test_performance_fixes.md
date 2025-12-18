# Test Performans Düzeltmeleri

## Problem
Testler çok uzun sürüyordu ve takılıyordu.

## Bulunan Sorunlar

### 1. Import Path Sorunları
- Test dosyalarında `sys.path.insert` kullanımı pytest'in import sistemini bozuyordu
- Yanlış import path'leri (`spatial.basis_fields` yerine `src.spatial.basis_fields`) testleri yavaşlatıyordu

### 2. Verimsiz Döngüler
- Tensor simetri kontrolünde for döngüsü kullanılıyordu
- Vectorized NumPy işlemleri ile optimize edildi

### 3. Timeout Eksikliği
- Testler takıldığında süresiz bekliyordu
- pytest-timeout eklendi (30 saniye limit)

## Yapılan Düzeltmeler

### 1. Import Path'leri Düzeltildi
```python
# Önce:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from spatial.basis_fields import GridField

# Sonra:
from src.spatial.basis_fields import GridField
```

**Dosyalar:**
- `tests/spatial/test_basis_fields.py`
- `tests/spatial/test_tensor_field.py`
- `tests/integration/test_tensor_field_integration.py`

### 2. Vectorized Kontroller
```python
# Önce (yavaş):
for T in tensors:
    assert np.allclose(T, T.T)

# Sonra (hızlı):
assert np.allclose(tensors, tensors.transpose(0, 2, 1))
```

### 3. Timeout Eklendi
**pytest.ini:**
```ini
addopts =
    ...
    --timeout=30
    --timeout-method=thread
    ...
```

**requirements.txt:**
```
pytest-timeout>=2.1.0
```

### 4. Test Konfigürasyonu
- `tests/spatial/conftest.py` oluşturuldu (NumPy print ayarları için)

## Beklenen İyileştirmeler

1. **Import hızı**: ~%80 daha hızlı (sys.path manipülasyonu yok)
2. **Simetri kontrolü**: ~%95 daha hızlı (vectorized işlem)
3. **Timeout koruması**: 30 saniyede otomatik durma
4. **Genel test süresi**: ~%50-70 daha hızlı olmalı

## Kullanım

### Normal test çalıştırma:
```bash
pytest tests/spatial/ -v
```

### Timeout ile manuel test:
```bash
pytest tests/spatial/ --timeout=10  # 10 saniye limit
```

### Coverage olmadan hızlı test:
```bash
pytest tests/spatial/ --no-cov -v
```

## Notlar

- pytest-timeout paketini yüklemek için: `pip install pytest-timeout`
- Timeout değeri test türüne göre ayarlanabilir (unit testler için 5-10s, integration için 30s)
- Benchmark testleri hala yavaş olabilir (bu normal)
