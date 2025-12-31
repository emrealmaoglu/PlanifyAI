# 🚀 Sprint 3: Gateway-Aware Optimization

**Tarih:** 2025-12-30
**Durum:** Ready to Start
**Önceki Sprint:** Sprint 2 (Campus Relocation) ✅ Completed

---

## 📊 Sprint 2 Özet

### ✅ Tamamlanan İşler
1. ✅ `relocation_service.py` - CampusRelocator class
2. ✅ Gateway topology preservation (distance matrix verification)
3. ✅ `/api/campus/relocate` endpoint (POST)
4. ✅ WGS84 → UTM → Local metric coordinate transformation
5. ✅ GeoJSON parsing and serialization
6. ✅ Test suite with mock campus data

### 📦 Deliverables
- **Backend:** Fully functional relocation API
- **Test:** Topology preserved with 0.000000% error
- **Status:** Production-ready

---

## 🎯 Sprint 3 Hedefleri

### Ana Hedef
Yeni alana taşınan kampüste **gateway-aware optimization** yapmak. Yani, optimize edilmiş bina yerleşiminde:
1. Gateway'lere kolay erişim sağlanmalı
2. Gateway'lerin yönlerine (bearing) uygun yol ağı oluşturulmalı
3. Gateway clearance (minimum boşluk) korunmalı

### Kullanıcı Hikayesi
> "Kastamonu Üniversitesi kampüsünü boş alana taşıdım. Şimdi bu alanda yeni binalar optimal bir şekilde yerleştirilmeli. Ancak optimize edilmiş yerleşim gateway'leri dikkate almalı - binalar gateway'lere yakın olmalı, gateway'lerin önü açık kalmalı ve yollar gateway'lere bağlanmalı."

---

## 🏗️ Mimari Tasarım

### 1. Gateway-Aware Objective Functions

#### 1.1 Gateway Connectivity Objective
**Amaç:** Binaların gateway'lere ortalama mesafesini minimize et.

**Dosya:** `backend/core/optimization/objectives/gateway_connectivity.py`

```python
"""
Gateway Connectivity Objective

Binaların gateway'lere erişimini optimize eder.
"""

from typing import List
import numpy as np
from shapely.geometry import Point, Polygon
from backend.core.domain.models.campus import Gateway

class GatewayConnectivityObjective:
    """
    Optimize edilmiş binaların gateway'lere erişimini maksimize eder.

    Formula:
        score = 1 / (1 + average_gateway_distance / max_campus_dimension)

    Score range: [0, 1]
    - 1.0 = Tüm binalar gateway'lerin hemen yanında
    - 0.0 = Tüm binalar gateway'lerden çok uzak
    """

    def __init__(self, gateways: List[Gateway], weight: float = 1.0):
        """
        Args:
            gateways: Kampüsteki gateway listesi
            weight: Objective weight (default: 1.0)
        """
        self.gateways = gateways
        self.weight = weight

    def calculate(self, buildings: List[Polygon]) -> float:
        """
        Her binanın en yakın gateway'e olan mesafesini hesapla.

        Args:
            buildings: Optimize edilmiş binalar

        Returns:
            Normalized score (0-1)
        """
        if not buildings or not self.gateways:
            return 0.0

        total_min_distance = 0.0

        for building in buildings:
            building_centroid = building.centroid

            # En yakın gateway'i bul
            min_distance = min(
                building_centroid.distance(gw.location)
                for gw in self.gateways
            )

            total_min_distance += min_distance

        # Ortalama mesafe
        avg_distance = total_min_distance / len(buildings)

        # Normalize (campus boyutuna göre)
        campus_bounds = self._get_campus_bounds(buildings)
        max_dimension = max(
            campus_bounds['max_x'] - campus_bounds['min_x'],
            campus_bounds['max_y'] - campus_bounds['min_y']
        )

        # Score: Mesafe azaldıkça score artar
        normalized_distance = avg_distance / max_dimension
        score = 1.0 / (1.0 + normalized_distance)

        return score * self.weight

    def _get_campus_bounds(self, buildings: List[Polygon]) -> dict:
        """Campus sınırlarını hesapla."""
        all_coords = []
        for building in buildings:
            all_coords.extend(building.exterior.coords)

        xs = [c[0] for c in all_coords]
        ys = [c[1] for c in all_coords]

        return {
            'min_x': min(xs),
            'max_x': max(xs),
            'min_y': min(ys),
            'max_y': max(ys)
        }
```

---

#### 1.2 Gateway Clearance Constraint
**Amaç:** Gateway'lerin etrafında minimum boşluk garantile.

**Dosya:** `backend/core/optimization/constraints/gateway_clearance.py`

```python
"""
Gateway Clearance Constraint

Gateway'lerin önünde minimum boşluk bırakır.
"""

from typing import List
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from backend.core.domain.models.campus import Gateway

class GatewayClearanceConstraint:
    """
    Gateway'lerin etrafında minimum clearance zone oluşturur.

    Özellikler:
    - Her gateway için circular clearance zone
    - Binalar bu zone'a giremez
    - Gateway bearing'e göre directional clearance (opsiyonel)
    """

    def __init__(
        self,
        gateways: List[Gateway],
        clearance_radius: float = 50.0,  # meters
        use_directional_clearance: bool = True
    ):
        """
        Args:
            gateways: Gateway listesi
            clearance_radius: Minimum clearance mesafesi (metre)
            use_directional_clearance: Bearing yönünde daha fazla boşluk bırak
        """
        self.gateways = gateways
        self.clearance_radius = clearance_radius
        self.use_directional_clearance = use_directional_clearance

        # Clearance zones oluştur
        self.clearance_zones = self._create_clearance_zones()

    def _create_clearance_zones(self) -> Polygon:
        """
        Tüm gateway'ler için clearance zone'ları oluştur.

        Returns:
            Union of all clearance zones
        """
        zones = []

        for gw in self.gateways:
            if self.use_directional_clearance:
                # Bearing yönünde elliptical clearance
                zone = self._create_directional_zone(gw)
            else:
                # Simple circular clearance
                zone = gw.location.buffer(self.clearance_radius)

            zones.append(zone)

        return unary_union(zones)

    def _create_directional_zone(self, gateway: Gateway) -> Polygon:
        """
        Gateway bearing'e göre directional clearance zone oluştur.

        Bearing yönünde 2x radius, diğer yönlerde 1x radius.
        """
        import math
        from shapely.affinity import rotate, scale

        # Base circle
        base_circle = gateway.location.buffer(self.clearance_radius)

        # Bearing yönünde scale et (2x)
        # Bearing: 0° = Kuzey, 90° = Doğu
        bearing_rad = math.radians(gateway.bearing)

        # Ellipse oluştur (bearing yönünde uzun)
        ellipse = scale(base_circle, xfact=1.0, yfact=2.0)

        # Bearing açısına göre rotate et
        rotated_ellipse = rotate(ellipse, gateway.bearing, origin=gateway.location)

        return rotated_ellipse

    def is_valid(self, building: Polygon) -> bool:
        """
        Binanın clearance zone'u ihlal edip etmediğini kontrol et.

        Args:
            building: Kontrol edilecek bina

        Returns:
            True if building does NOT violate clearance
        """
        return not building.intersects(self.clearance_zones)

    def get_violation_distance(self, building: Polygon) -> float:
        """
        Clearance violation mesafesini hesapla.

        Returns:
            0.0 if no violation, else distance of intrusion
        """
        if not building.intersects(self.clearance_zones):
            return 0.0

        # Intersection area as proxy for violation severity
        intersection = building.intersection(self.clearance_zones)
        return intersection.area
```

---

### 2. Gateway-Based Road Network Generation

**Dosya:** `backend/core/domain/geometry/gateway_roads.py`

```python
"""
Gateway Road Network Generator

Gateway'lerden kampüs içine yol ağı oluşturur.
"""

from typing import List, Tuple
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from scipy.spatial import Delaunay
from backend.core.domain.models.campus import Gateway

class GatewayRoadNetwork:
    """
    Gateway'lere bağlanan optimal yol ağı oluşturur.

    Algoritma:
    1. Gateway'leri ve bina merkezlerini düğüm olarak al
    2. Delaunay triangulation ile düğümleri bağla
    3. Minimum spanning tree ile gereksiz yolları kaldır
    4. Gateway bearing'e uygun yolları önceliklendir
    """

    def __init__(self, gateways: List[Gateway]):
        self.gateways = gateways

    def generate_road_network(
        self,
        buildings: List[Polygon],
        boundary: Polygon
    ) -> List[LineString]:
        """
        Gateway'lere bağlı optimal yol ağı oluştur.

        Args:
            buildings: Optimize edilmiş binalar
            boundary: Kampüs sınırı

        Returns:
            List of road LineStrings
        """
        # 1. Düğümleri topla (gateway + building centroids)
        nodes = []

        # Gateway nodes
        for gw in self.gateways:
            nodes.append((gw.location.x, gw.location.y, 'gateway'))

        # Building nodes
        for building in buildings:
            centroid = building.centroid
            nodes.append((centroid.x, centroid.y, 'building'))

        # 2. Delaunay triangulation
        points = np.array([(n[0], n[1]) for n in nodes])
        tri = Delaunay(points)

        # 3. Extract edges from triangulation
        edges = set()
        for simplex in tri.simplices:
            for i in range(3):
                edge = tuple(sorted([simplex[i], simplex[(i+1)%3]]))
                edges.add(edge)

        # 4. Create roads from edges
        roads = []
        for edge in edges:
            p1 = Point(points[edge[0]])
            p2 = Point(points[edge[1]])
            road = LineString([p1, p2])

            # Only keep roads within boundary
            if boundary.contains(road) or boundary.intersects(road):
                roads.append(road)

        # 5. Filter: Prioritize roads connected to gateways
        gateway_connected_roads = self._filter_gateway_roads(roads, nodes)

        return gateway_connected_roads

    def _filter_gateway_roads(
        self,
        roads: List[LineString],
        nodes: List[Tuple]
    ) -> List[LineString]:
        """
        Gateway'lere bağlı yolları önceliklendir.

        MST (Minimum Spanning Tree) kullanarak gereksiz yolları kaldır.
        """
        # TODO: Implement MST-based filtering
        # For now, return all roads
        return roads
```

---

### 3. Integration with Existing Optimization

**Değişiklik:** `backend/api/routers/optimize.py`

```python
# Existing optimize endpoint'e gateway-aware parameters ekle

@router.post("/optimize")
async def optimize_layout(
    campus_geojson: dict,
    requirements: dict,
    use_gateway_optimization: bool = True,  # NEW
    gateway_connectivity_weight: float = 1.0,  # NEW
    gateway_clearance_radius: float = 50.0  # NEW
):
    """
    Optimize layout with optional gateway-awareness.

    Args:
        campus_geojson: Relocated campus (from /relocate endpoint)
        requirements: Building requirements
        use_gateway_optimization: Enable gateway-aware optimization
        gateway_connectivity_weight: Weight for gateway connectivity objective
        gateway_clearance_radius: Minimum clearance around gateways (meters)
    """
    # Parse campus
    campus = parse_campus_geojson(campus_geojson)

    # Setup optimizer
    optimizer = CampusOptimizer()

    # Add gateway objectives if enabled
    if use_gateway_optimization and campus.gateways:
        # Add gateway connectivity objective
        gateway_connectivity = GatewayConnectivityObjective(
            gateways=campus.gateways,
            weight=gateway_connectivity_weight
        )
        optimizer.add_objective(gateway_connectivity)

        # Add gateway clearance constraint
        gateway_clearance = GatewayClearanceConstraint(
            gateways=campus.gateways,
            clearance_radius=gateway_clearance_radius
        )
        optimizer.add_constraint(gateway_clearance)

    # Run optimization
    result = optimizer.optimize(campus, requirements)

    # Generate roads if gateways exist
    if campus.gateways:
        road_network = GatewayRoadNetwork(campus.gateways)
        roads = road_network.generate_road_network(
            buildings=result.buildings,
            boundary=campus.boundary
        )
        result.roads = roads

    return result.to_geojson()
```

---

## 📋 Implementation Tasks

### Task List

#### Backend (Core Logic)
- [ ] **Task 3.1:** Create `gateway_connectivity.py` objective
  - [ ] Implement `calculate()` method
  - [ ] Unit tests for score calculation
  - [ ] Edge case: No gateways
  - [ ] Edge case: No buildings

- [ ] **Task 3.2:** Create `gateway_clearance.py` constraint
  - [ ] Implement circular clearance zones
  - [ ] Implement directional clearance (bearing-aware)
  - [ ] Unit tests for `is_valid()`
  - [ ] Visualization helper for debugging

- [ ] **Task 3.3:** Create `gateway_roads.py` network generator
  - [ ] Implement Delaunay triangulation
  - [ ] Implement MST filtering
  - [ ] Ensure roads connect to gateways
  - [ ] Unit tests with mock data

#### Backend (API Integration)
- [ ] **Task 3.4:** Update `/api/v1/optimize` endpoint
  - [ ] Add gateway-aware parameters
  - [ ] Integrate `GatewayConnectivityObjective`
  - [ ] Integrate `GatewayClearanceConstraint`
  - [ ] Add road generation step
  - [ ] Update response format (include roads)

#### Testing
- [ ] **Task 3.5:** Create integration test
  - [ ] End-to-end test: Detect → Relocate → Optimize with gateways
  - [ ] Use Kastamonu data
  - [ ] Verify gateway connectivity score > 0.7
  - [ ] Verify clearance violations = 0
  - [ ] Verify roads connect gateways to buildings

#### Frontend (Optional - if time permits)
- [ ] **Task 3.6:** Visualize gateway clearance zones
  - [ ] Add clearance zone layer to map
  - [ ] Show gateway bearing as arrows
  - [ ] Highlight violations in red

---

## 🧪 Test Scenarios

### Scenario 1: Simple Campus with 2 Gateways
```python
# Input
gateways = [
    Gateway(id="north", location=Point(0, 500), bearing=180),
    Gateway(id="south", location=Point(0, -500), bearing=0)
]
boundary = Polygon([(-500, -500), (500, -500), (500, 500), (-500, 500)])
requirements = {"Faculty": 5, "Dormitory": 2}

# Expected Output
- Buildings should cluster near gateways
- Gateway connectivity score > 0.8
- Clearance zones respected (0 violations)
- Roads connect both gateways to all buildings
```

### Scenario 2: Kastamonu University (Real Data)
```python
# Input
- Fetch Kastamonu campus via /detect
- Relocate to (0, 0) via /relocate
- Optimize with gateway-awareness

# Expected Output
- Gateway count: 3-5 (from OSM data)
- Optimized layout respects gateway positions
- Road network connects all gateways
- Connectivity score > 0.7
```

---

## 📊 Success Metrics

### Quantitative
1. **Gateway Connectivity Score:** > 0.7 (70%)
2. **Clearance Violations:** 0 (zero violations)
3. **Road Coverage:** All buildings connected to at least 1 gateway
4. **Performance:** Optimization completes in < 30 seconds

### Qualitative
1. Visual inspection: Buildings clustered near gateways
2. Visual inspection: Clearance zones visible and respected
3. Visual inspection: Road network logical and connected
4. User feedback: "Gateway positions are meaningful in the layout"

---

## 🚀 Sprint Execution Plan

### Week 1: Core Implementation
**Days 1-2:** Tasks 3.1, 3.2 (Objectives & Constraints)
**Days 3-4:** Task 3.3 (Road Network Generator)
**Day 5:** Task 3.4 (API Integration)

### Week 2: Testing & Refinement
**Days 6-7:** Task 3.5 (Integration Testing)
**Days 8-9:** Bug fixes and refinement
**Day 10:** Documentation and demo preparation

---

## 📦 Deliverables

1. **Code:**
   - `gateway_connectivity.py`
   - `gateway_clearance.py`
   - `gateway_roads.py`
   - Updated `/api/v1/optimize`

2. **Tests:**
   - Unit tests for each component
   - Integration test (end-to-end)
   - Test with Kastamonu data

3. **Documentation:**
   - API documentation update
   - Algorithm explanation (distance matrix, MST)
   - Usage examples

---

## 🔗 Dependencies

### From Previous Sprints
- ✅ Sprint 1: `geocoding_service.py`, `campus.py` models
- ✅ Sprint 2: `relocation_service.py`, `/relocate` endpoint

### External Libraries
- `scipy` (for Delaunay triangulation, MST)
- `shapely` (geometry operations)
- `numpy` (matrix calculations)

### Installation
```bash
pip install scipy>=1.11.0
```

---

## 🎯 Next Sprint Preview (Sprint 4)

After Sprint 3, we'll have a complete pipeline:
1. Detect campus → 2. Relocate to empty space → 3. Optimize with gateways

**Sprint 4 will focus on:**
- Frontend integration (visualization)
- End-to-end workflow automation
- Performance optimization
- Production deployment

---

## 📝 Notes

- Gateway bearing is critical - it indicates the direction of incoming/outgoing traffic
- Clearance zones prevent buildings from blocking gateway access
- Road network should prioritize gateway connections over building-to-building roads
- Delaunay triangulation ensures roads don't cross unnecessarily

---

**Status:** Ready to Start
**Estimated Duration:** 10 days
**Start Date:** 2025-12-30
**Target Completion:** 2026-01-08
