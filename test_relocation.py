"""
Test script for campus relocation functionality
"""
import requests
import json

# Test 1: Check health endpoint
print("=" * 60)
print("TEST 1: Checking campus router health")
print("=" * 60)

health_response = requests.get("http://localhost:8000/api/campus/health")
print(f"Status: {health_response.status_code}")
print(json.dumps(health_response.json(), indent=2))
print()

# Test 2: Create a simple mock campus GeoJSON for testing
print("=" * 60)
print("TEST 2: Testing relocation with mock campus data")
print("=" * 60)

# Simple mock campus centered at (10, 10) with 2 gateways
mock_campus_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "layer": "boundary",
                "name": "Test Campus",
                "area_m2": 1000000
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [10.0, 10.0],
                    [10.01, 10.0],
                    [10.01, 10.01],
                    [10.0, 10.01],
                    [10.0, 10.0]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "layer": "gateway",
                "id": "gw1",
                "bearing": 90.0,
                "type": "main",
                "name": "Main Gate"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [10.0, 10.005]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "layer": "gateway",
                "id": "gw2",
                "bearing": 270.0,
                "type": "secondary",
                "name": "Side Gate"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [10.01, 10.005]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "layer": "existing_building",
                "id": "bld1",
                "building_type": "Faculty",
                "height": 20.0,
                "name": "Engineering Building"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [10.003, 10.003],
                    [10.007, 10.003],
                    [10.007, 10.007],
                    [10.003, 10.007],
                    [10.003, 10.003]
                ]]
            }
        }
    ]
}

# Test relocation to (0, 0) - empty space
relocation_request = {
    "campus_geojson": mock_campus_geojson,
    "target_lat": 0.0,
    "target_lon": 0.0,
    "preserve_topology": True,
    "clear_existing_buildings": True
}

print("Sending relocation request...")
print(f"Original campus center: approximately (10.005, 10.005)")
print(f"Target center: (0.0, 0.0)")
print(f"Clear existing buildings: True")
print()

relocation_response = requests.post(
    "http://localhost:8000/api/campus/relocate",
    json=relocation_request
)

print(f"Status: {relocation_response.status_code}")

if relocation_response.status_code == 200:
    result = relocation_response.json()
    print(f"\n✅ Relocation successful!")
    print(f"Topology preserved: {result['topology_preserved']}")
    print(f"Distance error: {result['distance_error']:.6f}")
    print(f"Translation vector: dx={result['translation_vector']['dx']:.2f}, dy={result['translation_vector']['dy']:.2f}")
    print(f"\nMetadata:")
    print(f"  - Original gateways: {result['metadata']['original_gateways']}")
    print(f"  - Relocated gateways: {result['metadata']['relocated_gateways']}")
    print(f"  - Original buildings: {result['metadata']['original_buildings']}")
    print(f"  - Relocated buildings: {result['metadata']['relocated_buildings']}")
    print(f"  - Buildings cleared: {result['metadata']['buildings_cleared']}")

    # Check relocated campus features
    relocated_features = result['relocated_campus']['features']
    print(f"\nRelocated campus features: {len(relocated_features)}")

    # Find boundary center
    for feature in relocated_features:
        if feature['properties']['layer'] == 'boundary':
            boundary_coords = feature['geometry']['coordinates'][0]
            # Calculate approximate center
            lons = [c[0] for c in boundary_coords[:-1]]
            lats = [c[1] for c in boundary_coords[:-1]]
            center_lon = sum(lons) / len(lons)
            center_lat = sum(lats) / len(lats)
            print(f"Relocated boundary center: approximately ({center_lon:.6f}, {center_lat:.6f})")

    # Check gateways
    gateway_count = sum(1 for f in relocated_features if f['properties']['layer'] == 'gateway')
    building_count = sum(1 for f in relocated_features if f['properties']['layer'] == 'existing_building')
    print(f"Gateways in relocated campus: {gateway_count}")
    print(f"Buildings in relocated campus: {building_count} (should be 0 if cleared)")

else:
    print(f"\n❌ Relocation failed!")
    print(f"Error: {relocation_response.text}")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
