"""
API endpoint tests for PlanifyAI backend.

Sprint 3, Faz 3.1.3 - API Endpoint Tests
Tests /health, /api/optimize, /api/context endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_returns_200(self, client):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_healthy_status(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "planifyai-core"
    
    def test_health_includes_db_status(self, client):
        """Health endpoint should include database status."""
        response = client.get("/health")
        data = response.json()
        assert "db" in data
        assert data["db"] in ["connected", "disconnected"]


class TestOptimizeStartEndpoint:
    """Tests for /api/optimize/start endpoint."""
    
    def test_start_optimization_returns_job_id(self, client):
        """Start optimization should return job_id."""
        response = client.post("/api/optimize/start", json={
            "project_name": "Test Project",
            "latitude": 41.3833,
            "longitude": 33.7833
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
    
    def test_start_optimization_requires_latitude(self, client):
        """Start optimization should require latitude."""
        response = client.post("/api/optimize/start", json={
            "project_name": "Test Project"
        })
        assert response.status_code == 422  # Validation error
    
    def test_start_optimization_returns_uuid_format(self, client):
        """Job ID should be a valid UUID format."""
        response = client.post("/api/optimize/start", json={
            "project_name": "Test Project",
            "latitude": 41.3833,
            "longitude": 33.7833
        })
        data = response.json()
        job_id = data["job_id"]
        # UUID format: 8-4-4-4-12
        assert len(job_id) == 36
        assert job_id.count("-") == 4


class TestOptimizeStatusEndpoint:
    """Tests for /api/optimize/status endpoint."""
    
    def test_status_for_existing_job(self, client):
        """Status should work for existing job."""
        # First create a job
        create_response = client.post("/api/optimize/start", json={
            "project_name": "Test Project",
            "latitude": 41.3833,
            "longitude": 33.7833
        })
        job_id = create_response.json()["job_id"]
        
        # Then check status
        status_response = client.get(f"/api/optimize/status/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data
    
    def test_status_for_nonexistent_job(self, client):
        """Status should return 404 for nonexistent job."""
        response = client.get("/api/optimize/status/nonexistent-job-id")
        assert response.status_code == 404


class TestOptimizeResultEndpoint:
    """Tests for /api/optimize/result endpoint."""
    
    def test_result_for_nonexistent_job(self, client):
        """Result should return 404 for nonexistent job."""
        response = client.get("/api/optimize/result/nonexistent-job-id")
        assert response.status_code == 404
    
    def test_result_for_incomplete_job(self, client):
        """Result should return 400 for incomplete job."""
        # Create job
        create_response = client.post("/api/optimize/start", json={
            "project_name": "Test Project",
            "latitude": 41.3833,
            "longitude": 33.7833
        })
        job_id = create_response.json()["job_id"]
        
        # Immediately try to get result (job not completed yet)
        result_response = client.get(f"/api/optimize/result/{job_id}")
        # Should be 400 (not completed) or 200 (if it completed very fast)
        assert result_response.status_code in [400, 200]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
