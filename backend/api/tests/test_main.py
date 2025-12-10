"""API tests."""

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "PlanifyAI" in response.json()["message"]

def test_health():
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"

def test_optimization_request_validation():
    """Test request validation."""
    # Invalid request (missing boundary)
    response = client.post("/api/optimization/run", json={})
    assert response.status_code == 422  # Validation error
    
    # Valid minimal request
    request = {
        "boundary": {
            "points": [
                {"x": 0, "y": 0},
                {"x": 1000, "y": 0},
                {"x": 1000, "y": 1000},
                {"x": 0, "y": 1000}
            ]
        },
        "config": {
            "population_size": 20,
            "n_generations": 10
        }
    }
    
    # Mock background tasks to avoid running actual optimization
    from unittest.mock import patch
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        response = client.post("/api/optimization/run", json=request)
        assert response.status_code == 200
        assert "request_id" in response.json()
        assert mock_add_task.called
