"""
JobStore Protocol - Abstract interface for job storage.

Sprint 2, Faz 2.1.1
Karar: Interface/Protocol pattern kullanarak future Redis migration'ı kolaylaştırıyoruz.
"""

from typing import Protocol, TypedDict, Optional, Any, Dict
from datetime import datetime


class JobData(TypedDict, total=False):
    """Job data structure - stored in job store."""
    job_id: str
    status: str  # queued, running, completed, failed
    progress: int  # 0-100
    stage: Optional[str]
    message: Optional[str]
    project_name: Optional[str]
    result: Optional[Dict[str, Any]]
    geojson: Optional[Dict[str, Any]]
    created_at: str  # ISO format
    updated_at: str  # ISO format


class JobStore(Protocol):
    """
    Protocol for job storage implementations.
    
    Allows switching between SQLite (development) and Redis (production)
    without changing the calling code.
    
    Usage:
        store: JobStore = SQLiteJobStore("jobs.db")
        store.create("job-123", {"status": "queued", "progress": 0})
        job = store.get("job-123")
        store.update("job-123", {"status": "running", "progress": 50})
    """
    
    def create(self, job_id: str, data: JobData) -> None:
        """Create a new job record."""
        ...
    
    def get(self, job_id: str) -> Optional[JobData]:
        """Get a job by ID. Returns None if not found."""
        ...
    
    def update(self, job_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a job. Returns True if job exists and was updated.
        Only updates the fields provided in data dict.
        """
        ...
    
    def delete(self, job_id: str) -> bool:
        """Delete a job. Returns True if job existed and was deleted."""
        ...
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> list[JobData]:
        """List jobs, optionally filtered by status."""
        ...
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Delete jobs older than max_age_hours.
        Returns number of deleted jobs.
        """
        ...
    
    def health_check(self) -> bool:
        """Return True if storage is healthy and accessible."""
        ...
