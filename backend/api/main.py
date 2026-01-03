import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

app = FastAPI(title="PlanifyAI Core")

# --- 1. CORS AYARI (Frontend ile konuşması için şart) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme modu: Herkese izin ver
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. ROUTER IMPORTS (with fallback for broken legacy routers) ---

# Critical: Context router (for OSM data fetching)
try:
    from backend.api.routers import context

    app.include_router(context.router)
    print("✅ Context router loaded")
except ImportError as e:
    print(f"❌ Context router failed: {e}")

# Critical: Optimize router (for H-SAGA simulation)
try:
    from backend.api.routers import optimize

    app.include_router(optimize.router)
    print("✅ Optimize router loaded")
except ImportError as e:
    print(f"❌ Optimize router failed: {e}")

# Critical: Constraints router
try:
    from backend.api.routers import constraints

    app.include_router(constraints.router)
    print("✅ Constraints router loaded")
except ImportError as e:
    print(f"❌ Constraints router failed: {e}")

# New: Campus router (for auto-detection)
try:
    from backend.api.routers import campus

    app.include_router(campus.router)
    print("✅ Campus router loaded")
except ImportError as e:
    print(f"❌ Campus router failed: {e}")

# New: NSGA-III router (for multi-objective optimization)
try:
    from backend.api.routers import nsga3

    app.include_router(nsga3.router)
    print("✅ NSGA-III router loaded")
except ImportError as e:
    print(f"❌ NSGA-III router failed: {e}")

# New: Visualization router (for result visualization)
try:
    from backend.api.routers import visualization

    app.include_router(visualization.router)
    print("✅ Visualization router loaded")
except ImportError as e:
    print(f"❌ Visualization router failed: {e}")


# --- 3. HEALTH CHECK (Load balancer / monitoring) ---
@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        status: healthy | degraded
        service: service name
        db: connected | disconnected
    """
    from backend.core.storage import SQLiteJobStore

    # Check database connectivity
    try:
        job_store = SQLiteJobStore("data/jobs.db")
        db_healthy = job_store.health_check()
    except Exception:
        db_healthy = False

    status = "healthy" if db_healthy else "degraded"

    return {
        "status": status,
        "service": "planifyai-core",
        "db": "connected" if db_healthy else "disconnected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
