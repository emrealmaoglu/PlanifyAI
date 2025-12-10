"""
SQLiteJobStore - SQLite-based job storage implementation.

Sprint 2, Faz 2.1.2
Karar: İlk iterasyonda SQLite kullanıyoruz (external dependency yok, setup kolay).
İleride config ile RedisJobStore'a switch edilebilir.
"""

import sqlite3
import json
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from .protocol import JobStore, JobData


class SQLiteJobStore:
    """
    SQLite-based implementation of JobStore.
    
    Thread-safe with connection per thread pattern.
    Auto-creates database and tables on initialization.
    """
    
    def __init__(self, db_path: str = "data/jobs.db"):
        """
        Initialize SQLite job store.
        
        Args:
            db_path: Path to SQLite database file. Directory will be created if needed.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'queued',
                progress INTEGER NOT NULL DEFAULT 0,
                stage TEXT,
                message TEXT,
                project_name TEXT,
                result TEXT,
                geojson TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)
        """)
        conn.commit()
    
    def create(self, job_id: str, data: JobData) -> None:
        """Create a new job record."""
        conn = self._get_connection()
        now = datetime.utcnow().isoformat()
        
        conn.execute("""
            INSERT INTO jobs (job_id, status, progress, stage, message, 
                            project_name, result, geojson, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            data.get('status', 'queued'),
            data.get('progress', 0),
            data.get('stage'),
            data.get('message'),
            data.get('project_name'),
            json.dumps(data.get('result')) if data.get('result') else None,
            json.dumps(data.get('geojson')) if data.get('geojson') else None,
            now,
            now
        ))
        conn.commit()
    
    def get(self, job_id: str) -> Optional[JobData]:
        """Get a job by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?",
            (job_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_job_data(row)
    
    def update(self, job_id: str, data: Dict[str, Any]) -> bool:
        """Update a job record."""
        conn = self._get_connection()
        
        # Build dynamic UPDATE query
        fields = []
        values = []
        
        for key, value in data.items():
            if key in ('result', 'geojson'):
                value = json.dumps(value) if value else None
            fields.append(f"{key} = ?")
            values.append(value)
        
        if not fields:
            return False
        
        fields.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(job_id)
        
        query = f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?"
        cursor = conn.execute(query, values)
        conn.commit()
        
        return cursor.rowcount > 0
    
    def delete(self, job_id: str) -> bool:
        """Delete a job record."""
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM jobs WHERE job_id = ?",
            (job_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> list[JobData]:
        """List jobs, optionally filtered by status."""
        conn = self._get_connection()
        
        if status:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        
        return [self._row_to_job_data(row) for row in cursor.fetchall()]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Delete jobs older than max_age_hours."""
        conn = self._get_connection()
        cutoff = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
        
        cursor = conn.execute(
            "DELETE FROM jobs WHERE created_at < ?",
            (cutoff,)
        )
        conn.commit()
        return cursor.rowcount
    
    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            conn = self._get_connection()
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def _row_to_job_data(self, row: sqlite3.Row) -> JobData:
        """Convert SQLite row to JobData dict."""
        return JobData(
            job_id=row['job_id'],
            status=row['status'],
            progress=row['progress'],
            stage=row['stage'],
            message=row['message'],
            project_name=row['project_name'],
            result=json.loads(row['result']) if row['result'] else None,
            geojson=json.loads(row['geojson']) if row['geojson'] else None,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
