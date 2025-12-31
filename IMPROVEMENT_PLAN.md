# 🚀 PlanifyAI İyileştirme Planı

**Tarih:** 2025-12-30
**Hedef:** Otomatik kampüs tespiti ve yeni alana optimizasyon

---

## 🎯 Kullanıcı Talebi

> "başlangıçta şu anda kastamonu üniversitesinin alanı otomatik belirlenmiyor sonrasında bu alanı boş bir uzaya taşıyıp (giriş çıkış yollarının girdiği noktaları da koruyarak) yeni alan optimizasyonu yapmayı düşünüyorum."

### İhtiyaçlar:
1. ✅ **Otomatik Alan Tespiti:** Kastamonu Üniversitesi'nin kampüs sınırlarını otomatik belirle
2. ✅ **Giriş/Çıkış Noktaları:** Gateway'leri tespit et ve koru
3. ✅ **Yeni Alana Taşıma:** Kampüsü boş bir uzaya taşı
4. ✅ **Gateway Koruması:** Giriş/çıkış noktalarının relativepozisyonlarını koru
5. ✅ **Yeni Alan Optimizasyonu:** Taşınan alanda optimal yerleşim planla

---

## 📊 Mevcut Durum Analizi

### Şu Anda Ne Çalışıyor?

**1. OSM Context API (✅ Çalışıyor)**
```python
# backend/api/routers/context.py
GET /api/context/fetch?lat=41.424274&lon=33.777434&radius=500

Returns:
- boundary (kampüs sınırı) ✅
- existing_buildings (mevcut binalar) ✅
- gateways (giriş/çıkış noktaları) ✅
- roads (yollar) ✅
```

**Test:**
```bash
curl 'http://localhost:8000/api/context/fetch?lat=41.424274&lon=33.777434&radius=500'

✅ Status: success
✅ Buildings: 2
✅ Roads: 24
✅ Buildable Area: 1,542,289 m²
```

**2. Frontend Visualization (✅ Çalışıyor)**
```typescript
// frontend/src/components/map/layers/ExistingContextLayers.tsx
- Kampüs sınırını çizer (gold outline) ✅
- Mevcut binaları gösterir (3D) ✅
- Gateway'leri gösterir (cyan circles) ✅
```

### ❌ Ne Eksik?

1. **Manuel koordinat girişi gerekiyor:**
   - Şu anda: `lat=41.424274&lon=33.777434` manuel verilmeli
   - Gerekli: Kullanıcı "Kastamonu Üniversitesi" yazsın, otomatik bulsun

2. **Alan taşıma özelliği yok:**
   - Mevcut kampüs orijinal koordinatlarında
   - Boş alana taşıma mekanizması yok

3. **Gateway koruma mekanizması yok:**
   - Gateway'ler tespit ediliyor ama
   - Taşıma sırasında relative pozisyonları korunmuyor

---

## 🏗️ İyileştirme Aşamaları

### **Faz 1: Otomatik Kampüs Tespiti**

#### 1.1 Geocoding Integration
**Hedef:** Kullanıcı "Kastamonu Üniversitesi" yazsın, sistem otomatik bulsun.

**Implementasyon:**
```python
# backend/core/domain/geometry/geocoding_service.py (YENİ DOSYA)

from geopy.geocoders import Nominatim
from typing import Tuple, Optional

class UniversityCampusLocator:
    """
    Üniversite kampüslerini otomatik bulur.
    """

    def __init__(self):
        self.geolocator = Nominatim(user_agent="planifyai/2.0")

    def find_university(self, university_name: str, country: str = "Turkey") -> Optional[Tuple[float, float]]:
        """
        Üniversite adından lat/lon koordinatlarını bulur.

        Args:
            university_name: "Kastamonu Üniversitesi"
            country: "Turkey"

        Returns:
            (latitude, longitude) or None
        """
        query = f"{university_name}, {country}"
        location = self.geolocator.geocode(query)

        if location:
            return (location.latitude, location.longitude)
        return None

    def auto_detect_campus_boundary(self, lat: float, lon: float, radius: int = 1000):
        """
        Verilen koordinattan kampüs sınırını otomatik tespit eder.
        OSM'den 'amenity=university' tag'i olan polygon'u bulur.
        """
        # OSM Overpass API kullan
        # university boundary'sini query'le
        pass
```

**Frontend Integration:**
```typescript
// frontend/src/components/SearchBar.tsx
// Zaten var! Mapbox Geocoder kullanılıyor

// Sadece callback'i güncelle:
onGeocoderResult={(e) => {
  const { center } = e.result
  // Otomatik olarak context fetch'i tetikle
  fetchContextWithUI(center[1], center[0])
}}
```

**✅ Bu zaten çalışıyor!** Geocoder var, sadece backend'de auto-detection eklenecek.

---

#### 1.2 Smart Radius Detection
**Hedef:** Kampüs büyüklüğüne göre otomatik radius belirle.

**Problem:**
- Şu anda: `radius=500` sabit
- Kastamonu kampüsü: ~1.5M m² → 500m yeterli değil
- İdeal: Alan büyüklüğüne göre dinamik radius

**Implementasyon:**
```python
# backend/core/domain/geometry/osm_service.py (GÜNCELLE)

def auto_detect_radius(lat: float, lon: float) -> int:
    """
    Kampüs büyüklüğüne göre optimal radius hesaplar.

    Algorithm:
    1. İlk 500m radius ile query yap
    2. Boundary tespit et
    3. Boundary area'sını hesapla
    4. Eğer boundary eksikse, radius'u artır (750m, 1000m, 1500m)
    5. Optimal radius'u döndür
    """
    initial_radius = 500
    max_radius = 3000

    for radius in [500, 750, 1000, 1500, 2000, 3000]:
        context = fetch_campus_context(lat=lat, lon=lon, radius=radius)

        # Boundary tamamlandı mı kontrol et
        if context.is_boundary_complete():
            return radius

    return max_radius
```

---

### **Faz 2: Kampüs Verilerini Normalize Et**

#### 2.1 Campus Data Model
**Hedef:** Kampüs verilerini standart formata dönüştür.

```python
# backend/core/domain/models/campus.py (YENİ DOSYA)

from dataclasses import dataclass
from typing import List
from shapely.geometry import Polygon, Point

@dataclass
class Gateway:
    """Giriş/çıkış noktası"""
    id: str
    location: Point  # WGS84
    bearing: float  # Yolun yönü (derece)
    type: str  # 'main', 'secondary', 'service'

@dataclass
class ExistingBuilding:
    """Mevcut bina"""
    id: str
    geometry: Polygon
    building_type: str
    height: float

@dataclass
class CampusContext:
    """Kampüs bağlamı - tüm veriler"""
    boundary: Polygon  # Kampüs sınırı (WGS84)
    gateways: List[Gateway]  # Giriş/çıkış noktaları
    existing_buildings: List[ExistingBuilding]
    roads: List[Polygon]
    green_areas: List[Polygon]
    center: Point  # Kampüs merkezi
    area_m2: float  # Alan (m²)

    def to_local_coordinates(self):
        """
        WGS84 koordinatlarını local metric (meter) koordinatlara çevir.
        Merkezi (0,0) yap.
        """
        from pyproj import Transformer

        # WGS84 -> UTM projection
        utm_zone = self._get_utm_zone()
        transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_zone}")

        # Transform all geometries
        local_boundary = transform(transformer.transform, self.boundary)
        local_gateways = [
            Gateway(
                id=gw.id,
                location=transform(transformer.transform, gw.location),
                bearing=gw.bearing,
                type=gw.type
            )
            for gw in self.gateways
        ]

        # Center'ı (0,0) yap
        center_x, center_y = local_boundary.centroid.coords[0]
        offset_boundary = translate(local_boundary, xoff=-center_x, yoff=-center_y)

        # Return new CampusContext with local coordinates
        return CampusContext(
            boundary=offset_boundary,
            gateways=local_gateways,
            # ... diğer alanlar
        )
```

---

### **Faz 3: Yeni Alana Taşıma**

#### 3.1 Relocate Campus to Empty Space
**Hedef:** Kampüsü boş bir koordinat sistemine taşı.

```python
# backend/core/domain/geometry/relocation_service.py (YENİ DOSYA)

class CampusRelocator:
    """
    Kampüsü yeni bir alana taşır, gateway'leri korur.
    """

    def relocate_to_empty_space(
        self,
        campus: CampusContext,
        target_center: Point = Point(0, 0)
    ) -> CampusContext:
        """
        Kampüsü target_center'a taşır.

        Özellikler:
        - Boundary'yi taşır
        - Gateway'lerin relative pozisyonlarını korur
        - Mevcut binaları korur (opsiyonel)
        - Tüm geometrileri yeni koordinat sistemine çevirir
        """
        # 1. Mevcut merkezi hesapla
        current_center = campus.boundary.centroid

        # 2. Offset hesapla
        dx = target_center.x - current_center.x
        dy = target_center.y - current_center.y

        # 3. Tüm geometrileri taşı
        relocated_boundary = translate(campus.boundary, xoff=dx, yoff=dy)

        relocated_gateways = [
            Gateway(
                id=gw.id,
                location=Point(gw.location.x + dx, gw.location.y + dy),
                bearing=gw.bearing,  # Yön korunur
                type=gw.type
            )
            for gw in campus.gateways
        ]

        # 4. Yeni CampusContext oluştur
        return CampusContext(
            boundary=relocated_boundary,
            gateways=relocated_gateways,
            existing_buildings=[],  # Boş alan - mevcut binalar yok
            roads=[],
            green_areas=[],
            center=target_center,
            area_m2=campus.area_m2
        )

    def preserve_gateway_topology(self, original_gw: List[Gateway], relocated_gw: List[Gateway]):
        """
        Gateway'lerin birbirlerine göre relative pozisyonlarını doğrula.
        """
        # Distance matrix'leri karşılaştır
        orig_distances = self._compute_distance_matrix(original_gw)
        reloc_distances = self._compute_distance_matrix(relocated_gw)

        assert np.allclose(orig_distances, reloc_distances), "Gateway topology broken!"
```

---

#### 3.2 Gateway-Aware Optimization
**Hedef:** Yeni alanda optimization yaparken gateway'leri dikkate al.

```python
# backend/core/optimization/objectives/gateway_connectivity.py (YENİ DOSYA)

class GatewayConnectivityObjective:
    """
    Optimize edilmiş binaların gateway'lere erişimini maksimize eder.
    """

    def calculate(self, buildings: List[Building], gateways: List[Gateway]) -> float:
        """
        Her binanın en yakın gateway'e olan mesafesini minimize et.

        Algorithm:
        1. Her bina için en yakın gateway'i bul
        2. Ortalama mesafeyi hesapla
        3. Normalize et (0-1 arası)
        """
        total_distance = 0

        for building in buildings:
            min_dist = min(
                building.centroid.distance(gw.location)
                for gw in gateways
            )
            total_distance += min_dist

        avg_distance = total_distance / len(buildings)

        # Normalize: 0 = mükemmel, 1 = kötü
        max_expected_distance = 1000  # 1km
        normalized = min(avg_distance / max_expected_distance, 1.0)

        return normalized
```

**Constraint:** Gateway yakınlarına bina yerleştirme
```python
# backend/core/optimization/constraints/gateway_clearance.py (YENİ DOSYA)

class GatewayClearanceConstraint:
    """
    Gateway'lerin etrafında minimum boşluk bırak.
    """

    def __init__(self, min_clearance: float = 20.0):
        self.min_clearance = min_clearance  # meter

    def check(self, buildings: List[Building], gateways: List[Gateway]) -> float:
        """
        Gateway'lere min_clearance kadar yakın bina var mı?

        Returns:
            0.0 = ihlal yok
            > 0.0 = ihlal var (total violation area)
        """
        violation = 0.0

        for gw in gateways:
            clearance_zone = gw.location.buffer(self.min_clearance)

            for building in buildings:
                if building.geometry.intersects(clearance_zone):
                    overlap_area = building.geometry.intersection(clearance_zone).area
                    violation += overlap_area

        return violation
```

---

### **Faz 4: Road Network Integration**

#### 4.1 Gateway-Connected Road Network
**Hedef:** Yolları gateway'lerden başlat.

```python
# backend/core/optimization/road_network/gateway_roads.py (YENİ DOSYA)

class GatewayRoadGenerator:
    """
    Gateway'lerden başlayan yol ağı oluşturur.
    """

    def generate_from_gateways(
        self,
        gateways: List[Gateway],
        buildings: List[Building],
        boundary: Polygon
    ) -> List[Road]:
        """
        Algorithm:
        1. Her gateway'den tensor field streamline başlat
        2. Gateway bearing'ini initial direction olarak kullan
        3. Streamline'ları buildings'e doğru yönlendir
        4. Primary roads: Gateway → Campus Center
        5. Secondary roads: Primary roads → Buildings
        """
        roads = []

        # 1. Gateway'lerden primary roads
        for gateway in gateways:
            # Gateway'in bearing yönünde başla
            initial_direction = np.array([
                np.cos(np.radians(gateway.bearing)),
                np.sin(np.radians(gateway.bearing))
            ])

            # Tensor field streamline
            road_points = self.tensor_field.integrate_streamline(
                start_point=gateway.location,
                initial_direction=initial_direction,
                max_length=500  # 500m max
            )

            roads.append(Road(
                points=road_points,
                width=8.0,  # Primary road
                type='gateway_primary'
            ))

        # 2. Buildings'e secondary roads
        for building in buildings:
            nearest_primary = self._find_nearest_road(building, roads)
            connection = self._connect_to_road(building, nearest_primary)
            roads.append(connection)

        return roads
```

---

## 📋 API Endpoint Tasarımı

### **Yeni Endpoint 1: Auto-Detect Campus**
```python
# backend/api/routers/campus.py (YENİ DOSYA)

@router.get("/api/campus/detect")
async def detect_campus(
    university_name: str = Query(..., description="Üniversite adı"),
    country: str = Query("Turkey", description="Ülke")
):
    """
    Üniversite kampüsünü otomatik tespit eder.

    Example:
        GET /api/campus/detect?university_name=Kastamonu Üniversitesi

    Returns:
        {
            "status": "success",
            "location": {"lat": 41.424274, "lon": 33.777434},
            "boundary": {...},
            "gateways": [...],
            "area_m2": 1542289
        }
    """
    # 1. Geocode university name
    locator = UniversityCampusLocator()
    coords = locator.find_university(university_name, country)

    # 2. Auto-detect optimal radius
    radius = auto_detect_radius(coords[0], coords[1])

    # 3. Fetch campus context
    context = fetch_campus_context(lat=coords[0], lon=coords[1], radius=radius)

    return {
        "status": "success",
        "location": {"lat": coords[0], "lon": coords[1]},
        "boundary": context.boundary.to_geojson(),
        "gateways": [gw.to_dict() for gw in context.gateways],
        "area_m2": context.area_m2
    }
```

### **Yeni Endpoint 2: Relocate Campus**
```python
@router.post("/api/campus/relocate")
async def relocate_campus(
    campus_id: str,
    target_lat: float = 0.0,
    target_lon: float = 0.0
):
    """
    Kampüsü yeni koordinatlara taşır.

    Example:
        POST /api/campus/relocate
        {
            "campus_id": "kastamonu",
            "target_lat": 0.0,
            "target_lon": 0.0
        }

    Returns:
        {
            "status": "success",
            "relocated_boundary": {...},
            "relocated_gateways": [...],
            "preserved_topology": true
        }
    """
    # 1. Load original campus
    original = load_campus_context(campus_id)

    # 2. Relocate
    relocator = CampusRelocator()
    relocated = relocator.relocate_to_empty_space(
        original,
        target_center=Point(target_lon, target_lat)
    )

    # 3. Verify gateway topology
    topology_preserved = relocator.preserve_gateway_topology(
        original.gateways,
        relocated.gateways
    )

    return {
        "status": "success",
        "relocated_boundary": relocated.boundary.to_geojson(),
        "relocated_gateways": [gw.to_dict() for gw in relocated.gateways],
        "preserved_topology": topology_preserved
    }
```

### **Updated Endpoint 3: Optimize with Gateways**
```python
@router.post("/api/v1/optimize")
async def optimize_campus(
    boundary_geojson: dict,
    building_requirements: dict,
    gateways: List[dict] = None  # YENİ PARAMETRE
):
    """
    Kampüs optimizasyonu - gateway'leri dikkate alarak.

    Example:
        POST /api/v1/optimize
        {
            "boundary_geojson": {...},
            "building_requirements": {...},
            "gateways": [
                {"lat": 41.42, "lon": 33.77, "bearing": 45, "type": "main"},
                ...
            ]
        }
    """
    # Optimization with gateway connectivity objective
    optimizer.add_objective(GatewayConnectivityObjective())
    optimizer.add_constraint(GatewayClearanceConstraint(min_clearance=20))

    # Run optimization
    result = optimizer.optimize(...)

    return result
```

---

## 🎨 Frontend İyileştirmeleri

### **1. University Search Component**
```typescript
// frontend/src/components/UniversitySearch.tsx (YENİ DOSYA)

export const UniversitySearch = () => {
  const [universityName, setUniversityName] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    setLoading(true)

    const response = await fetch(
      `/api/campus/detect?university_name=${encodeURIComponent(universityName)}`
    )
    const data = await response.json()

    // Auto-zoom to detected campus
    map.flyTo({
      center: [data.location.lon, data.location.lat],
      zoom: 15
    })

    // Load campus context
    setCampusData(data)
    setLoading(false)
  }

  return (
    <div>
      <input
        type="text"
        placeholder="Üniversite adı (örn: Kastamonu Üniversitesi)"
        value={universityName}
        onChange={(e) => setUniversityName(e.target.value)}
      />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? 'Aranıyor...' : 'Kampüs Bul'}
      </button>
    </div>
  )
}
```

### **2. Relocation Control Panel**
```typescript
// frontend/src/components/RelocationPanel.tsx (YENİ DOSYA)

export const RelocationPanel = ({ campusData }) => {
  const [targetCoords, setTargetCoords] = useState({ lat: 0, lon: 0 })

  const handleRelocate = async () => {
    const response = await fetch('/api/campus/relocate', {
      method: 'POST',
      body: JSON.stringify({
        campus_id: campusData.id,
        target_lat: targetCoords.lat,
        target_lon: targetCoords.lon
      })
    })

    const relocated = await response.json()

    // Update map with relocated campus
    updateCampusLayers(relocated)
  }

  return (
    <div>
      <h3>Kampüsü Yeni Alana Taşı</h3>
      <div>
        <label>Hedef Koordinatlar:</label>
        <input
          type="number"
          placeholder="Latitude"
          value={targetCoords.lat}
          onChange={(e) => setTargetCoords({ ...targetCoords, lat: e.target.value })}
        />
        <input
          type="number"
          placeholder="Longitude"
          value={targetCoords.lon}
          onChange={(e) => setTargetCoords({ ...targetCoords, lon: e.target.value })}
        />
      </div>
      <button onClick={handleRelocate}>Taşı</button>

      <div className="info">
        <p>✅ Gateway pozisyonları korunacak</p>
        <p>✅ Relative mesafeler değişmeyecek</p>
      </div>
    </div>
  )
}
```

---

## 📊 İmplementasyon Sırası

### **Sprint 1: Auto-Detection** (1-2 gün)
1. ✅ `geocoding_service.py` - University locator
2. ✅ `auto_detect_radius()` - Smart radius
3. ✅ `/api/campus/detect` endpoint
4. ✅ Frontend: UniversitySearch component
5. ✅ Test: "Kastamonu Üniversitesi" otomatik bulunmalı

### **Sprint 2: Data Normalization** (1 gün)
1. ✅ `campus.py` - CampusContext model
2. ✅ `to_local_coordinates()` - WGS84 → local metric
3. ✅ Gateway data model
4. ✅ Test: Coordinate transformation accuracy

### **Sprint 3: Relocation** (2 gün)
1. ✅ `relocation_service.py` - CampusRelocator
2. ✅ `relocate_to_empty_space()` - Main function
3. ✅ `preserve_gateway_topology()` - Topology verification
4. ✅ `/api/campus/relocate` endpoint
5. ✅ Frontend: RelocationPanel component
6. ✅ Test: Gateway'ler doğru taşınmalı

### **Sprint 4: Gateway-Aware Optimization** (2-3 gün)
1. ✅ `gateway_connectivity.py` - New objective
2. ✅ `gateway_clearance.py` - New constraint
3. ✅ `gateway_roads.py` - Road network from gateways
4. ✅ Update `/api/v1/optimize` endpoint
5. ✅ Frontend: Gateway visualization
6. ✅ Test: Buildings gateway'lere bağlanmalı

### **Sprint 5: Integration & Testing** (1 gün)
1. ✅ End-to-end test: Search → Relocate → Optimize
2. ✅ UI/UX polish
3. ✅ Documentation update
4. ✅ Performance optimization

---

## ✅ Success Criteria

### Fonksiyonel Gereksinimler:
- [ ] Kullanıcı "Kastamonu Üniversitesi" yazınca otomatik bulunmalı
- [ ] Kampüs sınırları otomatik tespit edilmeli
- [ ] Gateway'ler doğru tespit edilmeli
- [ ] Kampüs boş alana taşınabilmeli
- [ ] Gateway relative pozisyonları korunmalı
- [ ] Yeni alanda optimization çalışmalı
- [ ] Buildings gateway'lere bağlanmalı

### Performans:
- [ ] Auto-detection < 5 saniye
- [ ] Relocation < 1 saniye
- [ ] Optimization + gateway-aware < 10 saniye

### Doğruluk:
- [ ] Gateway topology error < 1% (distance matrix)
- [ ] Coordinate transformation error < 1 meter
- [ ] Boundary area preservation 100%

---

## 🎯 Expected Outcome

### Before (Şu an):
```
1. Kullanıcı manuel koordinat girer: lat=41.424274, lon=33.777434
2. Backend OSM'den veriyi çeker
3. Frontend orijinal koordinatlarda gösterir
4. Optimization orijinal alanda yapılır
```

### After (İyileştirme sonrası):
```
1. Kullanıcı "Kastamonu Üniversitesi" yazar
2. Sistem otomatik bulur ve boundary tespit eder ✅
3. Kullanıcı "Boş alana taşı" der
4. Sistem kampüsü (0,0)'a taşır, gateway'leri korur ✅
5. Optimization yeni alanda gateway-aware olarak çalışır ✅
6. Sonuç: Optimal yerleşim + gateway bağlantıları ✅
```

---

## 📁 Yeni Dosyalar

```
backend/
├── core/domain/
│   ├── geometry/
│   │   ├── geocoding_service.py      # YENİ
│   │   └── relocation_service.py     # YENİ
│   └── models/
│       └── campus.py                  # YENİ
├── optimization/
│   ├── objectives/
│   │   └── gateway_connectivity.py   # YENİ
│   ├── constraints/
│   │   └── gateway_clearance.py      # YENİ
│   └── road_network/
│       └── gateway_roads.py          # YENİ
└── api/routers/
    └── campus.py                      # YENİ

frontend/
└── src/components/
    ├── UniversitySearch.tsx          # YENİ
    └── RelocationPanel.tsx           # YENİ
```

---

## 🚀 Hemen Başla

### Adım 1: Geocoding Service
```bash
cd backend
pip install geopy

# Test
python3 -c "
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent='planifyai/2.0')
location = geolocator.geocode('Kastamonu Üniversitesi, Turkey')
print(f'Lat: {location.latitude}, Lon: {location.longitude}')
"
```

Expected output:
```
Lat: 41.424274, Lon: 33.777434
```

✅ **Ready to implement!**

---

**Next Steps:** Sprint 1'i başlat → `geocoding_service.py` oluştur
