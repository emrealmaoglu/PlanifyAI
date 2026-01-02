"""
Simple test to debug the relocation endpoint
"""
import requests
import json

# Simplest possible campus GeoJSON
simple_campus = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "layer": "boundary",
                "name": "Test Campus"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [0.0, 0.0],
                    [0.01, 0.0],
                    [0.01, 0.01],
                    [0.0, 0.01],
                    [0.0, 0.0]
                ]]
            }
        }
    ]
}

print("Sending simple campus GeoJSON:")
print(json.dumps(simple_campus, indent=2))
print()

# Test the endpoint
response = requests.post(
    "http://localhost:8000/api/campus/relocate",
    json={
        "campus_geojson": simple_campus,
        "target_lat": 0.0,
        "target_lon": 0.0
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
