"""
API endpoints for optimization pipeline.

Sprint 2, Faz 2.1.3 - SQLiteJobStore Migration
"""

import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.core.pipeline.orchestrator import OptimizationPipeline, PipelineConfig
from backend.core.schemas.input import OptimizationRequest
from backend.core.storage import JobData, SQLiteJobStore

router = APIRouter(prefix="/api/optimize", tags=["optimize"])

# Persistent job store (SQLite-based, survives restarts)
job_store = SQLiteJobStore("data/jobs.db")


class JobStatus(BaseModel):
    """Job status response."""

    job_id: str
    status: str
    progress: int
    stage: Optional[str] = None
    message: Optional[str] = None


def update_callback(job_id: str, stage: str, progress: int):
    """Callback to update job status."""
    job_store.update(job_id, {"stage": str(stage), "progress": progress})


def run_pipeline_background(job_id: str, request: OptimizationRequest):
    """Wrapper to run pipeline in background."""
    try:
        job_store.update(job_id, {"status": "running"})

        # Create callback wrapper
        def callback(stage, progress):
            update_callback(job_id, stage, progress)

        config = PipelineConfig(
            enable_solar=request.enable_solar, enable_wind=request.enable_wind, verbose=True
        )

        pipeline = OptimizationPipeline(config)
        result = pipeline.run(
            request.latitude,
            request.longitude,
            constraint_geojson=request.constraints,
            boundary_geojson=request.boundary_geojson,
            campus_geojson=request.campus_geojson,  # Sprint 3: Gateway support
            clear_all_existing=request.clear_all_existing,
            kept_building_ids=request.kept_building_ids,
            building_counts=request.building_counts,
            callback=callback,
        )

        job_store.update(
            job_id,
            {
                "status": "completed" if result.success else "failed",
                "progress": 100,
                "result": result.to_dict(),
                "geojson": result.geojson,
                "message": "Optimization complete",
            },
        )

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        job_store.update(job_id, {"status": "failed", "message": str(e)})


@router.post("/start")
async def start_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """
    Start a new optimization job based on the Research-Backed Schema.
    """
    job_id = str(uuid.uuid4())

    # Initialize Job Status in SQLite
    job_store.create(
        job_id,
        JobData(
            job_id=job_id,
            status="queued",
            progress=0,
            project_name=request.project_name,
            stage="initialized",
            message="Job queued",
        ),
    )

    background_tasks.add_task(run_pipeline_background, job_id, request)

    return {"job_id": job_id, "status": "queued"}


@router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> JobStatus:
    """Get status of an optimization job."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        stage=job.get("stage"),
        message=job.get("message"),
    )


@router.get("/result/{job_id}")
async def get_job_result(job_id: str):
    """Get result of a completed optimization job."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")

    return job.get("result")


@router.get("/geojson/{job_id}")
async def get_job_geojson(job_id: str):
    """Get GeoJSON output of a completed job."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed. Status: {job['status']}")

    return job.get("geojson", {})


@router.post("/quick")
async def quick_optimization(
    latitude: float = 41.3833, longitude: float = 33.7833, num_buildings: int = 5
):
    """
    Run a quick synchronous optimization for testing.

    Warning: May timeout for large problems.
    """
    # Quick optimization temporarily disabled during refactor
    # May be re-enabled once pipeline stabilizes
    return {
        "success": True,
        "message": "Quick optimization temporarily disabled during refactor.",
    }


class SearchRequest(BaseModel):
    """Request to search for campus context."""

    query: str


@router.post("/context/search")
async def search_context(request: SearchRequest):
    """
    Search for a campus location and return its context.

    Returns boundary, buildings, and roads.
    """
    from backend.core.domain.geometry.osm_service import fetch_campus_context

    try:
        # Parse query as "lat,lon" or fallback to default
        try:
            lat, lon = map(float, request.query.split(","))
            ctx = fetch_campus_context(lat=lat, lon=lon)
        except Exception:
            # Fallback to default coordinates
            ctx = fetch_campus_context(lat=41.3833, lon=33.7833)

        # Convert to GeoJSON (WGS84 for frontend)
        geojson = ctx.to_geojson_wgs84()

        import math

        def sanitize(obj):
            if isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return obj
            if isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sanitize(v) for v in obj]
            return obj

        return sanitize(
            {
                "success": True,
                "message": f"Found {len(ctx.existing_buildings)} buildings",
                "data": geojson,
                "center": {"lat": ctx.center_latlon[0], "lon": ctx.center_latlon[1]},
            }
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
