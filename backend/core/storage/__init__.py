"""
Job Storage Module - Persistent job state management.

This module provides an abstraction layer for job storage, allowing
easy switching between SQLite (development) and Redis (production).

Sprint 2, Faz 2.1
"""

from .protocol import JobStore, JobData
from .sqlite_store import SQLiteJobStore

__all__ = ['JobStore', 'JobData', 'SQLiteJobStore']
