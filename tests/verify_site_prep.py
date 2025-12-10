import sys
import os
import warnings

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.domain.geometry.osm_service import fetch_campus_context
import osmnx as ox

# Suppress warnings
warnings.filterwarnings('ignore')

def verify_site_prep():
    print("🚀 Starting Site Prep Logic Audit...")
    print("-" * 50)
    
    # 1. Load Raw Data for Comparison
    print("📊 Loading Raw OSM Data (kastamonu_uni.osm)...")
    local_osm_path = os.path.join(os.path.dirname(__file__), '../kastamonu_uni.osm')
    
    if not os.path.exists(local_osm_path):
        print("❌ Error: kastamonu_uni.osm not found!")
        return
        
    tags = {'building': True}
    raw_gdf = ox.features_from_xml(local_osm_path, tags=tags)
    raw_count = len(raw_gdf[raw_gdf['building'].notna()])
    print(f"   Raw Building Count: {raw_count}")
    
    # 2. Run Smart Pipeline
    print("\n⚙️ Running Smart Pipeline (fetch_campus_context)...")
    context = fetch_campus_context(radius=2000)
    processed_count = len(context.existing_buildings)
    print(f"   Processed Building Count: {processed_count}")
    
    # 3. Verify Noise Reduction
    print("\n📉 Noise Reduction Analysis:")
    if processed_count < raw_count:
        print(f"   ✅ SUCCESS: Filtered out {raw_count - processed_count} neighborhood buildings.")
    else:
        print("   ⚠️ WARNING: No buildings were filtered. Check clipping logic.")
        
    # 4. Verify Gateways
    print("\n🚪 Gateway Detection Analysis:")
    gateways = context.gateways
    if gateways:
        print(f"   ✅ SUCCESS: Found {len(gateways)} gateways.")
        print("   Sample Gateways:")
        for i, g in enumerate(gateways[:3]):
            print(f"     {i+1}. Loc: {g['location']} | Bearing: {g['bearing']:.2f} rad | Type: {g['type']} | Road: {g.get('road_name')}")
            
            # Verify bearing range (-pi to pi)
            if not (-3.15 <= g['bearing'] <= 3.15):
                print(f"     ❌ ERROR: Invalid bearing {g['bearing']}")
    else:
        print("   ❌ FAILURE: No gateways detected!")

    # 5. Verify Boundary & Center
    print("\n🎯 Boundary & Center Analysis:")
    print(f"   New Center: {context.center_latlon}")
    
    # Check if center is roughly correct (Kastamonu Uni coords)
    lat, lon = context.center_latlon
    if 41.3 < lat < 41.5 and 33.7 < lon < 33.9:
         print("   ✅ Center is within expected Kastamonu region.")
    else:
         print(f"   ⚠️ Center seems off: {lat}, {lon}")

    print("-" * 50)
    print("🏁 Audit Complete.")

if __name__ == "__main__":
    verify_site_prep()
