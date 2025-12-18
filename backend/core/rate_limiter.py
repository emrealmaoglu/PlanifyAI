"""
Simple in-memory rate limiter middleware for FastAPI.

Sprint 2, Faz 2.2.3 - Rate limiting (no external dependencies)
"""

import time
from collections import defaultdict
from functools import wraps
from typing import Dict, Tuple, Callable
from fastapi import HTTPException, Request


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    Note: This is suitable for single-instance deployments.
    For distributed systems, use Redis-based rate limiting.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self._requests: Dict[str, list[float]] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_id: str) -> None:
        """Remove requests outside the current window."""
        now = time.time()
        cutoff = now - self.window_size
        self._requests[client_id] = [
            ts for ts in self._requests[client_id] if ts > cutoff
        ]
    
    def is_allowed(self, request: Request) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        
        Returns:
            (allowed: bool, remaining: int)
        """
        client_id = self._get_client_id(request)
        self._cleanup_old_requests(client_id)
        
        current_count = len(self._requests[client_id])
        
        if current_count >= self.requests_per_minute:
            return False, 0
        
        self._requests[client_id].append(time.time())
        return True, self.requests_per_minute - current_count - 1
    
    def check(self, request: Request) -> None:
        """Raise HTTPException if rate limited."""
        allowed, remaining = self.is_allowed(request)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": "60"}
            )


# Default rate limiter instance
default_limiter = RateLimiter(requests_per_minute=60)


def rate_limit(limiter: RateLimiter = None):
    """
    Decorator for rate limiting endpoint functions.
    
    Usage:
        @router.post("/start")
        @rate_limit()
        async def start_optimization(request: Request, ...):
            ...
    """
    _limiter = limiter or default_limiter
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            if request:
                _limiter.check(request)
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator
