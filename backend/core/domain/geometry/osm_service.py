"""
OSMNx Integration for Real-World Campus Context.

Fetches existing buildings, roads, and boundaries from OpenStreetMap
to enable Brownfield (infill) planning around existing infrastructure.
"""

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
import math
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, MultiPoint
from shapely.ops import unary_union, transform
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from pyproj import Transformer
import warnings
import os

# Suppress OSMnx warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Configure OSMnx
ox.settings.use_cache = False # FORCE FRESH FETCH
ox.settings.log_console = True
ox.settings.timeout = 30

@dataclass
class ExistingBuilding:
    """An existing entity (building or green area) from OpenStreetMap."""
    osm_id: int
    geometry: Polygon
    building_type: Optional[str]  # OSM tag value
    name: Optional[str]
    height: Optional[float]  # meters
    levels: Optional[int]
    entity_type: str = "building"  # 'building', 'forest', 'grass', 'sports'
    
    @property
    def centroid(self) -> Tuple[float, float]:
        """Entity centroid in local coordinates."""
        c = self.geometry.centroid
        return (c.x, c.y)
    
    @property
    def area(self) -> float:
        """Entity footprint area in m²."""
        return self.geometry.area


@dataclass
class ExistingRoad:
    """An existing road from OpenStreetMap."""
    osm_id: int
    geometry: LineString
    road_type: str
    name: Optional[str]
    width: Optional[float]
    
    @property
    def length(self) -> float:
        return self.geometry.length


@dataclass
class CampusContext:
    """The complete context for a campus optimization problem."""
    boundary: Polygon
    existing_buildings: List[ExistingBuilding]
    existing_roads: List[ExistingRoad]
    existing_green_areas: List[ExistingBuilding]
    center_latlon: Tuple[float, float]
    crs_local: str
    bounds_meters: Tuple[float, float, float, float]
    existing_walkways: List[ExistingRoad] = field(default_factory=list)
    gateways: List[Dict[str, Any]] = field(default_factory=list)  # 🚪 New: Entry Points
    
    @property
    def buildable_area(self) -> Polygon:
        """Area available for new buildings (boundary - buildings - roads)."""
        if self.existing_buildings:
            building_footprints = unary_union([b.geometry for b in self.existing_buildings])
        else:
            building_footprints = Polygon()
        
        if self.existing_roads:
            road_buffers = unary_union([r.geometry.buffer(10) for r in self.existing_roads])
        else:
            road_buffers = Polygon()
            
        # Note: We do NOT subtract green areas by default, as they might be buildable 
        # depending on policy. For now, we treat them as buildable but visualized.
        
        buildable = self.boundary.difference(building_footprints)
        buildable = buildable.difference(road_buffers)
        return buildable
    
    @property
    def total_existing_building_area(self) -> float:
        return sum(b.area for b in self.existing_buildings)
    
    def to_geojson_wgs84(self) -> Dict[str, Any]:
        """Export context as GeoJSON in WGS84 (EPSG:4326)."""
        from shapely.geometry import mapping
        
        transformer = Transformer.from_crs(self.crs_local, "EPSG:4326", always_xy=True)
        
        def to_wgs84(geom):
            return transform(transformer.transform, geom)
        
        features = []
        
        # Boundary
        features.append({
            "type": "Feature",
            "properties": {"layer": "boundary"},
            "geometry": mapping(to_wgs84(self.boundary))
        })
        
        # Gateways (New Layer)
        for g in self.gateways:
            features.append({
                "type": "Feature",
                "properties": {
                    "layer": "gateway",
                    "type": g['type'],
                    "bearing": g['bearing'],
                    "road_name": g.get('road_name')
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [g['location'][1], g['location'][0]] # Lon, Lat
                }
            })
        
        # Buildings
        for b in self.existing_buildings:
            features.append({
                "type": "Feature",
                "properties": {
                    "layer": "existing_building",
                    "osm_id": b.osm_id,
                    "building_type": b.building_type,
                    "name": b.name,
                    "height": b.height or 10,
                    "area": b.area,
                    "entity_type": b.entity_type
                },
                "geometry": mapping(to_wgs84(b.geometry))
            })
            
        # Green Areas
        for g in self.existing_green_areas:
            features.append({
                "type": "Feature",
                "properties": {
                    "layer": "green_area",
                    "osm_id": g.osm_id,
                    "building_type": g.building_type, # e.g. park, forest
                    "name": g.name,
                    "entity_type": g.entity_type
                },
                "geometry": mapping(to_wgs84(g.geometry))
            })
            
        # Roads
        for r in self.existing_roads:
            features.append({
                "type": "Feature",
                "properties": {
                    "layer": "existing_road",
                    "osm_id": r.osm_id,
                    "road_type": r.road_type,
                    "name": r.name,
                    "width": r.width
                },
                "geometry": mapping(to_wgs84(r.geometry))
            })

        # Walkways
        for w in self.existing_walkways:
            features.append({
                "type": "Feature",
                "properties": {
                    "layer": "existing_walkway",
                    "osm_id": w.osm_id,
                    "road_type": w.road_type,
                    "name": w.name,
                    "width": w.width
                },
                "geometry": mapping(to_wgs84(w.geometry))
            })
            
        return {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "center": {"lat": self.center_latlon[0], "lon": self.center_latlon[1]},
                "crs": "EPSG:4326",
                "original_crs": self.crs_local
            }
        }
    
    def to_geojson(self) -> Dict[str, Any]:
        """Legacy support - redirects to WGS84 version."""
        return self.to_geojson_wgs84()


class OSMContextFetcher:
    """Fetches and processes OpenStreetMap data with Smart Boundary and Gateway Detection."""
    
    ROAD_WIDTHS = {
        'motorway': 12.0, 'trunk': 10.0, 'primary': 8.0, 'secondary': 7.0,
        'tertiary': 6.0, 'residential': 5.0, 'service': 4.0, 'footway': 2.0,
        'path': 1.5, 'cycleway': 2.0, 'pedestrian': 3.0, 'unclassified': 5.0
    }
    
    # Manual Overrides for specific buildings (OSM ID -> Type)
    MANUAL_OVERRIDES = {
        1042220394: "Rectory",   # Old ID
        # 280235950:  "Rectory",   # REMOVED: This is the Campus Polygon, not a building
        1042222957: "Research",  # Kastamonu Teknoloji Ofisi (School)
        1315363606: "Research",  # Kastamonu Teknoloji Ofisi (Yes)
        218036534:  "Dining",    # Yemekhane
        217693311:  "Social",    # Spor Salonu (Building -> Social)
        
        # Shotgun: Try to catch the "Grey Building"
        908092911:  "Social",    # Large unclassified building
        1023929069: "Social",    # Another large building
        
        # Emin Baydil (Main Pitch)
        1295418975: "Sports",    # Was 'Stadium', changed to 'Sports' for correct coloring
    }
    
    # IDs that are definitely buildings but might miss the tag
    FORCE_BUILDING_IDS = [1365731619, 1365731618] # Fatma Aliye Hanım Blocks
    
    # Keywords for Core Campus Detection
    CORE_KEYWORDS = ['Rektörlük', 'Fakülte', 'Yüksekokul', 'Enstitü', 'Merkez', 'Yurt']
    
    def __init__(self):
        self._transformer_cache: Dict[str, Transformer] = {}
    
    def _get_local_crs(self, lat: float, lon: float) -> str:
        zone = int((lon + 180) / 6) + 1
        return f"EPSG:326{zone:02d}" if lat >= 0 else f"EPSG:327{zone:02d}"
    
    def _get_transformer(self, from_crs: str, to_crs: str) -> Transformer:
        key = f"{from_crs}_{to_crs}"
        if key not in self._transformer_cache:
            self._transformer_cache[key] = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        return self._transformer_cache[key]
    
    def _transform_geometry(self, geom, transformer: Transformer):
        return transform(transformer.transform, geom)

    def fetch_by_point(
        self, 
        lat: float, 
        lon: float, 
        radius_meters: float = 2000,
        boundary_polygon: Polygon = None,
        clear_all_existing: bool = False,
        kept_building_ids: List[str] = None
    ) -> CampusContext:
        """Fetch context with Smart Boundary Detection and Clipping."""
        print(f"[OSM] Context request for {lat}, {lon}...")
        
        # 1. Setup CRS
        local_crs = self._get_local_crs(lat, lon)
        transformer = self._get_transformer("EPSG:4326", local_crs)
        to_wgs84 = self._get_transformer(local_crs, "EPSG:4326")
        
        # 2. Define Extended Tags
        tags = {
            'building': True,
            'amenity': ['university', 'parking', 'school', 'college', 'place_of_worship', 'restaurant', 'cafe', 'fast_food', 'library', 'public_building'],
            'leisure': ['park', 'pitch', 'garden', 'stadium', 'sports_centre'],
            'landuse': ['grass', 'forest', 'meadow', 'education', 'recreation_ground', 'residential'],
            'natural': ['wood', 'tree_row', 'scrub'],
            'sport': True
        }
        
        # 3. Path Finding for Offline File
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../../"))
        local_osm_path = os.path.join(project_root, "kastamonu_uni.osm")
        
        gdf = None
        G = None
        
        # 4. Load Data
        if os.path.exists(local_osm_path):
            print(f"[OSM] ✅ OFFLINE MODE: Loading {local_osm_path}...")
            try:
                gdf = ox.features_from_xml(local_osm_path, tags=tags)
                G = ox.graph_from_xml(local_osm_path)
            except Exception as e:
                print(f"[OSM] ❌ XML Load Error: {e}")
        
        if gdf is None or gdf.empty:
            print("[OSM] ⚠️ Online Mode: Fetching from API...")
            try:
                gdf = ox.features_from_point((lat, lon), tags, dist=radius_meters)
                G = ox.graph_from_point((lat, lon), dist=radius_meters, network_type='all')
            except Exception as e:
                print(f"[OSM] ❌ API Error: {e}")
                return self._generate_mock_context(lat, lon, local_crs, transformer)

        # 5. Smart Boundary Detection (or Use Custom)
        if boundary_polygon:
            print("[OSM] 🛠️ Using User-Provided Custom Boundary.")
            # Ensure it's in WGS84 (It should be passed as Shapely Polygon in WGS84)
            boundary_poly_wgs84 = boundary_polygon
        else:
            print("[OSM] 🧠 Detecting Smart Boundary...")
            boundary_poly_wgs84 = self._derive_smart_boundary(gdf)
        
        # 6. The "Noise Filter" (Clipping)
        print("[OSM] ✂️ Clipping data to Boundary...")
        
        if clear_all_existing:
             print("[OSM] 🧹 CLEAR ALL ENABLED: Removing buildings/roads, keeping nature.")
             # Filter to keep ONLY nature/green areas
             # We need to run the classification logic first or filter by raw tags here.
             # Better approach: Let the standard clipping happen, then filter the RESULTING objects in step 9.
             # But to save processing, let's filter the GDF here.
             
             # Keep rows where 'natural', 'landuse', 'leisure' are present AND NOT 'building'
             # This is complex because some tags overlap.
             # Simpler: Let everything proceed, and filter the final lists (buildings vs green_areas) at the end.
             pass 
        else:
             # Standard Clipping Logic
             pass
             
        try:
            # Clip features (Buildings/Nature)
            gdf_clipped = gpd.clip(gdf, boundary_poly_wgs84)
            
            # Clip graph (Roads)
            roads_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)
            roads_clipped = gpd.clip(roads_gdf, boundary_poly_wgs84)
            
        except Exception as e:
            print(f"[OSM] ⚠️ Clipping failed ({e}). Using unclipped data.")
            gdf_clipped = gdf
            roads_clipped = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # 7. Transform to Local CRS for Processing
        boundary_local = self._transform_geometry(boundary_poly_wgs84, transformer)
        
        # 8. Gateway Detection
        print("[OSM] 🚪 Detecting Gateways...")
        # We need roads in local CRS for accurate intersection/bearing
        roads_local_list = []
        if 'highway' in roads_clipped.columns:
             # Temporary processing to get local geometries for gateway detection
             for _, row in roads_clipped.iterrows():
                 if isinstance(row.geometry, LineString):
                     roads_local_list.append(self._process_single_road(row, transformer))
                     
        gateways = self._detect_gateways(boundary_local, roads_local_list, to_wgs84)
        print(f"[OSM] Found {len(gateways)} Gateways.")

        # 9. Process & Classify Features
        buildings = []
        green_areas = []
        
        # Process Polygons
        for idx, row in gdf_clipped.iterrows():
            geom = row.geometry
            if not isinstance(geom, (Polygon, MultiPolygon)):
                continue
            
            # Transform
            geom_local = self._transform_geometry(geom, transformer)
            if geom_local.area < 10: continue
            
            # Classify
            entity_type = self._classify_entity(row)
            
            if entity_type == 'ignored':
                continue
            
            osm_id = idx[1] if isinstance(idx, tuple) else idx
            name = row.get('name', None)
            
            if entity_type == 'building':
                b_type = self._classify_building_type(row)
            else:
                # Green area logic
                osm_id_check = idx[1] if isinstance(idx, tuple) else idx
                if osm_id_check in self.MANUAL_OVERRIDES:
                    b_type = self.MANUAL_OVERRIDES[osm_id_check]
                else:
                    sport = row.get('sport')
                    if sport and isinstance(sport, str) and sport != 'nan':
                        b_type = sport 
                    else:
                        b_type = row.get('building') or row.get('leisure') or row.get('landuse') or row.get('natural')
            
            height = self._parse_height(row)
            levels = self._parse_levels(row)
            
            # Default heights
            if height is None:
                if levels:
                    height = levels * 3.5
                else:
                    if b_type == 'Dormitory': height = 18.0
                    elif b_type == 'Faculty': height = 15.0
                    elif b_type == 'Rectory': height = 12.0
                    elif b_type == 'Library': height = 12.0
                    elif b_type == 'Sports': height = 10.0
                    elif b_type == 'Mosque': height = 15.0
                    else: height = 10.0

            entity = ExistingBuilding(
                osm_id=osm_id,
                geometry=geom_local,
                building_type=str(b_type),
                name=name,
                height=height,
                levels=levels,
                entity_type=entity_type
            )
            
            if entity_type == 'building':
                buildings.append(entity)
            else:
                green_areas.append(entity)
                
        # Process Roads & Walkways
        pedestrian_tags = ['footway', 'path', 'pedestrian', 'steps', 'track', 'cycleway', 'living_street']
        
        if 'highway' in roads_clipped.columns:
            def is_pedestrian(val):
                if isinstance(val, list): val = val[0]
                return val in pedestrian_tags

            mask_ped = roads_clipped['highway'].apply(is_pedestrian)
            
            walkways_gdf = roads_clipped[mask_ped]
            roads_gdf_veh = roads_clipped[~mask_ped]
            
            roads = self._process_roads_gdf(roads_gdf_veh, transformer)
            walkways = self._process_roads_gdf(walkways_gdf, transformer)
        else:
            roads = []
            walkways = []
        
        # 10. Recenter on Smart Boundary
        center_local = boundary_local.centroid
        center_lon, center_lat = to_wgs84.transform(center_local.x, center_local.y)
        
        # --- CLEAR ALL LOGIC (Post-Processing) ---
        if clear_all_existing:
            print(f"[OSM] 🧹 CLEAR ALL: Removing Buildings, Roads, and Grass. Keeping Forests.")
            
            # 1. Clear Buildings & Roads (But respect Kept IDs)
            kept_ids = set(map(str, kept_building_ids or []))
            
            original_building_count = len(buildings)
            buildings = [b for b in buildings if str(b.osm_id) in kept_ids]
            print(f"[OSM] 🧹 Buildings: {original_building_count} -> {len(buildings)} (Kept: {kept_ids})")
            
            roads = []
            walkways = []
            
            # 2. Filter Green Areas: Keep ONLY Forests (Trees)
            # entity_type 'forest' comes from natural=wood, landuse=forest, etc.
            # entity_type 'grass' comes from landuse=grass, leisure=park, etc.
            original_green_count = len(green_areas)
            green_areas = [g for g in green_areas if g.entity_type == 'forest']
            
            print(f"[OSM] 🧹 Green Areas: {original_green_count} -> {len(green_areas)} (Only Forests kept)")
        
        print(f"[OSM] Final Count: {len(buildings)} Buildings, {len(green_areas)} Green Areas, {len(roads)} Roads")
        
        return CampusContext(
            boundary=boundary_local,
            existing_buildings=buildings,
            existing_roads=roads,
            existing_green_areas=green_areas,
            existing_walkways=walkways,
            center_latlon=(center_lat, center_lon),
            crs_local=local_crs,
            bounds_meters=boundary_local.bounds,
            gateways=gateways
        )

    def _derive_smart_boundary(self, gdf: gpd.GeoDataFrame) -> Polygon:
        """
        Detects the 'Campus Core' and creates a buffered boundary.
        Logic:
        1. Check for Official Campus Polygon (ID 280235950 or amenity=university).
        2. If not found, Filter for Core Keywords and create Convex Hull + 100m Buffer.
        """
        # 1. Try to find the Official Campus Polygon
        # Check by ID (Kastamonu Üniversitesi Relation/Way)
        target_id = 280235950
        
        # Handle MultiIndex if present
        if isinstance(gdf.index, pd.MultiIndex):
            if target_id in gdf.index.get_level_values(1):
                print(f"[OSM] 🎯 Found Official Campus Polygon (ID {target_id})")
                # Extract the geometry. It might be a bit tricky with MultiIndex
                # We'll iterate to find it safely
                for idx, row in gdf.iterrows():
                    oid = idx[1] if isinstance(idx, tuple) else idx
                    if oid == target_id:
                        return row.geometry
        elif target_id in gdf.index:
             print(f"[OSM] 🎯 Found Official Campus Polygon (ID {target_id})")
             return gdf.loc[target_id].geometry

        # Check for any large amenity=university polygon
        if 'amenity' in gdf.columns:
            uni_polys = gdf[gdf['amenity'] == 'university']
            if not uni_polys.empty:
                # Pick the largest one
                largest = uni_polys.loc[uni_polys.area.idxmax()]
                if largest.area > 50000: # Min 50k m2 to avoid small buildings tagged as university
                    print(f"[OSM] 🎯 Found amenity=university Polygon (Area: {largest.area:.0f} m²)")
                    return largest.geometry

        # 2. Fallback: Smart Convex Hull
        print("[OSM] ⚠️ Official Boundary not found. Falling back to Smart Convex Hull.")
        
        mask_core = pd.Series(False, index=gdf.index)
        
        # Keyword search in 'name'
        if 'name' in gdf.columns:
            for keyword in self.CORE_KEYWORDS:
                mask_core |= gdf['name'].str.contains(keyword, case=False, na=False)
        
        core_gdf = gdf[mask_core]
        
        if not core_gdf.empty:
            print(f"[OSM] Found {len(core_gdf)} Core Campus features.")
            hull = core_gdf.geometry.unary_union.convex_hull
        else:
            print("[OSM] ⚠️ No Core Features found. Using Convex Hull of ALL buildings.")
            buildings = gdf[gdf['building'].notna()]
            if not buildings.empty:
                hull = buildings.geometry.unary_union.convex_hull
            else:
                hull = gdf.geometry.unary_union.convex_hull
                
        # Buffer (100m approx 0.001 degrees)
        return hull.buffer(0.001)

    def _detect_gateways(self, boundary_poly: Polygon, roads: List[ExistingRoad], to_wgs84: Transformer) -> List[Dict[str, Any]]:
        """
        Identifies points where roads enter the campus boundary.
        Calculates bearing (angle) for Tensor Field generation.
        Applies Spatial Clustering to merge nearby gateways.
        """
        raw_gateways = []
        boundary_line = boundary_poly.exterior
        
        for road in roads:
            # Check intersection
            intersection = road.geometry.intersection(boundary_line)
            
            if intersection.is_empty:
                continue
                
            # Handle intersection types
            points = []
            if isinstance(intersection, Point):
                points = [intersection]
            elif isinstance(intersection, MultiPoint):
                points = list(intersection.geoms)
            elif isinstance(intersection, LineString):
                 # Edge case: Road runs along boundary
                 points = [intersection.interpolate(0.5, normalized=True)]
                 
            for pt in points:
                # 1. Find the road segment intersecting the boundary
                coords = list(road.geometry.coords)
                best_segment = None
                min_dist = float('inf')
                
                for i in range(len(coords) - 1):
                    p1 = Point(coords[i])
                    p2 = Point(coords[i+1])
                    line = LineString([p1, p2])
                    dist = line.distance(pt)
                    
                    if dist < min_dist:
                        min_dist = dist
                        best_segment = (coords[i], coords[i+1])
                
                if best_segment:
                    u, v = best_segment
                    dx = v[0] - u[0]
                    dy = v[1] - u[1]
                    angle_rad = math.atan2(dy, dx)
                    
                    # Transform point to WGS84 for output
                    lon, lat = to_wgs84.transform(pt.x, pt.y)
                    
                    g_type = 'primary' if road.road_type in ['primary', 'trunk', 'secondary'] else 'secondary'
                    
                    raw_gateways.append({
                        "location": [lat, lon],
                        "bearing": angle_rad,
                        "type": g_type,
                        "road_name": road.name,
                        "local_pt": pt # Keep for clustering
                    })
        
        # --- Spatial Clustering (Non-Maximum Suppression) ---
        # Sort by importance (Primary first)
        raw_gateways.sort(key=lambda x: 0 if x['type'] == 'primary' else 1)
        
        final_gateways = []
        cluster_radius = 150.0 # meters (Increased to merge gates along boundary)
        
        for candidate in raw_gateways:
            # Check distance to existing selected gateways
            is_duplicate = False
            cand_pt = candidate['local_pt']
            
            for selected in final_gateways:
                sel_pt = selected['local_pt']
                dist = cand_pt.distance(sel_pt)
                if dist < cluster_radius:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                final_gateways.append(candidate)
        
        # Clean up internal keys
        return [{k: v for k, v in g.items() if k != 'local_pt'} for g in final_gateways]

    def _classify_entity(self, row) -> str:
        """Determine entity type based on tags."""
        # Check Forced Buildings first
        osm_id = row.name
        if isinstance(osm_id, tuple): osm_id = osm_id[1]
        
        # Explicitly Ignore the Campus Polygon (it's the boundary, not a building)
        if osm_id == 280235950:
            return 'ignored'
        
        if osm_id in self.FORCE_BUILDING_IDS:
            return 'building'
            
        # Check Manual Overrides
        if osm_id in self.MANUAL_OVERRIDES:
            return 'building'

        # Check for Green Areas / Nature first (keep them for context)
        leisure = row.get('leisure')
        natural = row.get('natural')
        landuse = row.get('landuse')
        
        if natural in ['wood', 'tree_row', 'scrub'] or landuse == 'forest':
            return 'forest'
        if landuse in ['grass', 'meadow'] or leisure in ['park', 'garden']:
            return 'grass'
        if leisure in ['pitch', 'stadium', 'sports_centre']:
            return 'sports'

        # --- STRICT UNIVERSITY FILTER ---
        # If it's a building, is it ours?
        if 'building' in row and pd.notna(row['building']):
            name = str(row.get('name', '')).lower()
            amenity = str(row.get('amenity', '')).lower()
            building = str(row.get('building', '')).lower()
            operator = str(row.get('operator', '')).lower()
            
            # 1. Explicit University Tags
            if amenity == 'university' or building == 'university' or building == 'dormitory':
                return 'building'
                
            # 2. Keywords in Name
            keywords = ['rektörlük', 'fakülte', 'yüksekokul', 'enstitü', 'merkez', 'yurt', 'spor', 'kütüphane', 'yemekhane', 'teknokent', 'cami', 'konferans']
            if any(k in name for k in keywords):
                return 'building'
                
            # 3. Operator
            if 'kastamonu' in operator or 'kyk' in operator:
                return 'building'
                
            # 4. Residential check (Exclude houses/apartments unless named)
            # 4. Residential / Context (Keep All Valid Structures)
            ignore_list = ['shed', 'garage', 'roof', 'ruins', 'construction', 'greenhouse']
            if building in ignore_list:
                return 'ignored'

            # Default: Keep it as a building
            return 'building'
            
        return 'green_area' # default fallback

    def _classify_building_type(self, row) -> str:
        """Classify building function based on tags."""
        # 0. Check Manual Overrides (The Sniper Logic)
        osm_id = row.name
        if isinstance(osm_id, tuple):
            osm_id = osm_id[1]
            
        if osm_id in self.MANUAL_OVERRIDES:
            return self.MANUAL_OVERRIDES[osm_id]

        name = str(row.get('name', '')).lower()
        amenity = str(row.get('amenity', '')).lower()
        building = str(row.get('building', '')).lower()
        leisure = str(row.get('leisure', '')).lower()
        operator = str(row.get('operator', '')).lower()
        
        # 1. FACULTY (Mavi)
        if any(x in name for x in ['fakülte', 'yüksekokul', 'myo', 'enstitü']):
            return 'Faculty'

        # 2. RECTORY (Mor)
        # Strict check: Must explicitly say "Rektörlük"
        if 'rektörlük' in name:
            return 'Rectory'
            
        # 3. DINING (Sarı)
        if any(x in name for x in ['yemekhane', 'kantin', 'cafe']) or amenity == 'restaurant':
            return 'Dining'
            
        # 4. LIBRARY (Turkuaz)
        if 'kütüphane' in name or amenity == 'library':
            return 'Library'
            
        # 5. DORM (Turuncu)
        if any(x in name for x in ['yurt', 'blok', 'kyk']) or building == 'dormitory' or building == 'residential' or 'kredi yurtlar' in operator:
            return 'Dormitory'
            
        # 6. SPORTS (Yeşil)
        if leisure in ['pitch', 'sports_centre', 'stadium'] or 'spor' in name:
            return 'Sports'
            
        # 7. MOSQUE
        if amenity == 'place_of_worship' or building == 'mosque' or 'cami' in name:
            return 'Mosque'
            
        # 8. RESEARCH / LAB (Pink)
        if any(x in name for x in ['teknokent', 'laboratuvar', 'lab', 'ar-ge', 'merkezi']):
            return 'Research'
            
        # 9. CONFERENCE
        if 'konferans' in name:
            return 'Social'
            
        # 10. RESIDENTIAL
        if building in ['house', 'apartments', 'residential', 'terrace', 'yes']:
             return 'Residential'

        # 11. FALLBACK / CONTEXT
        return 'Context'

    def _process_roads_gdf(self, gdf, transformer):
        roads = []
        for idx, row in gdf.iterrows():
            if isinstance(row.geometry, LineString):
                roads.append(self._process_single_road(row, transformer))
        return roads

    def _process_single_road(self, row, transformer) -> ExistingRoad:
        geom = row.geometry
        geom_local = self._transform_geometry(geom, transformer)
        
        osm_id = row.get('osmid', row.name)
        if isinstance(osm_id, list): osm_id = osm_id[0]
        if isinstance(osm_id, tuple): osm_id = osm_id[1] # Handle multi-index if needed
        
        r_type = row.get('highway', 'unclassified')
        if isinstance(r_type, list): r_type = r_type[0]
        
        return ExistingRoad(
            osm_id=osm_id,
            geometry=geom_local,
            road_type=str(r_type),
            name=row.get('name'),
            width=self.ROAD_WIDTHS.get(r_type, 5.0)
        )

    def _parse_height(self, row):
        try:
            if 'height' in row and row['height']:
                return float(str(row['height']).replace('m', '').strip())
        except: pass
        return None

    def _parse_levels(self, row):
        try:
            if 'building:levels' in row and row['building:levels']:
                return int(row['building:levels'])
        except: pass
        return None

    def _generate_mock_context(self, lat, lon, crs, transformer) -> CampusContext:
        """Generate synthetic data when API is down."""
        from shapely.geometry import box
        cx, cy = transformer.transform(lon, lat)
        boundary = box(cx - 500, cy - 500, cx + 500, cy + 500)
        
        # Mock Buildings
        buildings = [
            ExistingBuilding(1, box(cx-50, cy-50, cx+50, cy+50), "Rectory", "Rektörlük", 12.0, 3, "building"),
            ExistingBuilding(2, box(cx-150, cy+100, cx-50, cy+200), "Faculty", "Mühendislik", 15.0, 4, "building")
        ]
        
        return CampusContext(
            boundary=boundary,
            existing_buildings=buildings,
            existing_roads=[],
            existing_green_areas=[],
            existing_walkways=[],
            center_latlon=(lat, lon),
            crs_local=crs,
            bounds_meters=boundary.bounds
        )

def fetch_campus_context(location=None, lat=None, lon=None, radius=2000, bbox=None) -> CampusContext:
    fetcher = OSMContextFetcher()
    if lat and lon:
        return fetcher.fetch_by_point(lat, lon, radius)
    return fetcher.fetch_by_point(41.424274, 33.777434, 2000) # Default (Kuzeykent)
