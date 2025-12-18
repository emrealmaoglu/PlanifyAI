"""Server-Sent Events progress streaming."""

import asyncio
import json
from typing import AsyncGenerator
from queue import Queue

class ProgressTracker:
    """Track optimization progress for SSE streaming."""
    
    def __init__(self):
        self.queue = Queue()
        self.completed = False
        self.error = None
    
    def update(self, generation: int, total: int, best_objectives=None, message=""):
        """Add progress update to queue."""
        self.queue.put({
            "status": "running",
            "generation": generation,
            "total_generations": total,
            "best_objectives": best_objectives,
            "message": message
        })
    
    def complete(self, message="Optimization completed"):
        """Mark optimization as complete."""
        self.completed = True
        self.queue.put({
            "status": "completed",
            "message": message
        })
    
    def fail(self, error: str):
        """Mark optimization as failed."""
        self.error = error
        self.queue.put({
            "status": "failed",
            "message": error
        })
    
    async def stream(self) -> AsyncGenerator[str, None]:
        """Stream progress updates as SSE."""
        while not self.completed and not self.error:
            if not self.queue.empty():
                update = self.queue.get()
                yield json.dumps(update)
            else:
                await asyncio.sleep(0.1)  # Prevent busy wait
        
        # Send final status
        if self.error:
            yield json.dumps({'status': 'failed', 'message': self.error})
        else:
            yield json.dumps({'status': 'completed', 'message': 'Done'})
