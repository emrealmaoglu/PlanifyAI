
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.core.constraints.manual_constraints import ConstraintType

client = TestClient(app)

def test_start_optimization_with_constraints():
    """Test starting optimization with God Mode constraints."""
    
    # Mock GeoJSON from frontend
    constraint_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "test_zone_1",
                "properties": {
                    "user_constraint_type": "exclusion"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [33.78, 41.38],
                        [33.79, 41.38],
                        [33.79, 41.39],
                        [33.78, 41.39],
                        [33.78, 41.38]
                    ]]
                }
            }
        ]
    }
    
    payload = {
        "latitude": 41.3833,
        "longitude": 33.7833,
        "num_buildings": 5,
        "budget": 1000,
        "enable_solar": True,
        "enable_wind": True,
        "enable_critique": False,
        "constraint_geojson": constraint_geojson
    }
    
    response = client.post("/api/optimize/start", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "started"

if __name__ == "__main__":
    # Manually run if pytest is not available
    try:
        test_start_optimization_with_constraints()
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")
