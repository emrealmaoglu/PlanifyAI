from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_fetch_context_api():
    """Test the context fetch API endpoint."""
    # Kastamonu University coordinates
    lat = 41.3833
    lon = 33.7833
    radius = 500
    
    response = client.get(f"/api/context/fetch?lat={lat}&lon={lon}&radius={radius}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["type"] == "FeatureCollection"
    assert len(data["data"]["features"]) > 0
    
    summary = data["summary"]
    print(f"\nAPI Summary: {summary}")
    assert summary["existing_buildings"] >= 0
    assert summary["existing_roads"] >= 0
