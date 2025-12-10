"""
Unit tests for SQLiteJobStore.

Sprint 3, Faz 3.1.4 - SQLiteJobStore Unit Tests
Tests CRUD operations, persistence, and cleanup.
"""

import pytest
import tempfile
import os
from pathlib import Path

from backend.core.storage import SQLiteJobStore, JobData


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def job_store(temp_db):
    """SQLiteJobStore with temporary database."""
    return SQLiteJobStore(temp_db)


class TestJobStoreCreate:
    """Tests for job creation."""
    
    def test_create_job(self, job_store):
        """Should create a job successfully."""
        job_store.create("job-1", JobData(
            job_id="job-1",
            status="queued",
            progress=0,
            project_name="Test Project"
        ))
        
        job = job_store.get("job-1")
        assert job is not None
        assert job["job_id"] == "job-1"
        assert job["status"] == "queued"
        assert job["progress"] == 0
    
    def test_create_job_with_minimal_data(self, job_store):
        """Should create a job with minimal data."""
        job_store.create("job-2", JobData(
            job_id="job-2",
            status="queued",
            progress=0
        ))
        
        job = job_store.get("job-2")
        assert job is not None
        assert job["project_name"] is None


class TestJobStoreGet:
    """Tests for job retrieval."""
    
    def test_get_existing_job(self, job_store):
        """Should return existing job."""
        job_store.create("job-1", JobData(job_id="job-1", status="queued", progress=0))
        
        job = job_store.get("job-1")
        assert job is not None
    
    def test_get_nonexistent_job(self, job_store):
        """Should return None for nonexistent job."""
        job = job_store.get("nonexistent")
        assert job is None


class TestJobStoreUpdate:
    """Tests for job updates."""
    
    def test_update_status(self, job_store):
        """Should update job status."""
        job_store.create("job-1", JobData(job_id="job-1", status="queued", progress=0))
        
        result = job_store.update("job-1", {"status": "running", "progress": 50})
        assert result is True
        
        job = job_store.get("job-1")
        assert job["status"] == "running"
        assert job["progress"] == 50
    
    def test_update_nonexistent_job(self, job_store):
        """Should return False for nonexistent job."""
        result = job_store.update("nonexistent", {"status": "running"})
        assert result is False
    
    def test_update_with_result(self, job_store):
        """Should update job with JSON result."""
        job_store.create("job-1", JobData(job_id="job-1", status="queued", progress=0))
        
        result_data = {"solutions": [{"id": 1}], "best_fitness": 0.5}
        job_store.update("job-1", {"status": "completed", "result": result_data})
        
        job = job_store.get("job-1")
        assert job["status"] == "completed"
        assert job["result"]["solutions"][0]["id"] == 1


class TestJobStoreDelete:
    """Tests for job deletion."""
    
    def test_delete_existing_job(self, job_store):
        """Should delete existing job."""
        job_store.create("job-1", JobData(job_id="job-1", status="queued", progress=0))
        
        result = job_store.delete("job-1")
        assert result is True
        
        job = job_store.get("job-1")
        assert job is None
    
    def test_delete_nonexistent_job(self, job_store):
        """Should return False for nonexistent job."""
        result = job_store.delete("nonexistent")
        assert result is False


class TestJobStoreList:
    """Tests for job listing."""
    
    def test_list_all_jobs(self, job_store):
        """Should list all jobs."""
        job_store.create("job-1", JobData(job_id="job-1", status="queued", progress=0))
        job_store.create("job-2", JobData(job_id="job-2", status="running", progress=50))
        
        jobs = job_store.list_jobs()
        assert len(jobs) == 2
    
    def test_list_jobs_by_status(self, job_store):
        """Should filter jobs by status."""
        job_store.create("job-1", JobData(job_id="job-1", status="queued", progress=0))
        job_store.create("job-2", JobData(job_id="job-2", status="running", progress=50))
        job_store.create("job-3", JobData(job_id="job-3", status="running", progress=75))
        
        running_jobs = job_store.list_jobs(status="running")
        assert len(running_jobs) == 2


class TestJobStoreHealthCheck:
    """Tests for health check."""
    
    def test_health_check_healthy(self, job_store):
        """Should return True for healthy database."""
        assert job_store.health_check() is True
    
    def test_health_check_new_database(self, temp_db):
        """Should work with new database file."""
        store = SQLiteJobStore(temp_db)
        assert store.health_check() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
