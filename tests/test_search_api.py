import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_search_context():
    """Test the search context endpoint."""
    response = client.post("/api/optimize/context/search", json={"query": "Kastamonu Üniversitesi"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["type"] == "FeatureCollection"
    assert len(data["data"]["features"]) > 0
    
    # Check for WGS84 coordinates (longitude should be around 33.7, latitude around 41.3)
    # Find a building
    building = next((f for f in data["data"]["features"] if f["properties"]["layer"] == "existing_building"), None)
    assert building is not None
    coords = building["geometry"]["coordinates"][0][0] # First point of polygon
    lon, lat = coords
    assert 30 < lon < 45  # Turkey longitude
    assert 35 < lat < 45  # Turkey latitude

def test_search_context_invalid():
    """Test search with invalid query."""
    response = client.post("/api/optimize/context/search", json={"query": "NonExistentPlace123456789"})
    assert response.status_code == 400
