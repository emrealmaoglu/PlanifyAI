"""
Visualization API Router
=========================

REST API endpoints for generating visualizations of optimization results.

Endpoints:
    - POST /api/visualize/pareto-2d - Generate 2D Pareto front plot
    - POST /api/visualize/pareto-3d - Generate 3D Pareto front plot
    - POST /api/visualize/parallel-coordinates - Generate parallel coordinates plot
    - POST /api/visualize/objective-matrix - Generate objective trade-off matrix
    - POST /api/visualize/statistics - Compute objective statistics

Created: 2026-01-03
"""

import base64
import io
import logging
from typing import Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualize", tags=["visualization"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================


class VisualizationRequest(BaseModel):
    """Request schema for visualization."""

    objectives: List[List[float]] = Field(
        ..., description="Objective values (n_solutions x n_objectives)"
    )
    objective_names: Optional[List[str]] = Field(default=None, description="Names of objectives")
    best_index: Optional[int] = Field(default=None, description="Index of best compromise solution")
    title: Optional[str] = Field(default=None, description="Plot title")


class ImageResponse(BaseModel):
    """Response with base64-encoded image."""

    success: bool
    image_base64: str = Field(..., description="Base64-encoded PNG image")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")


class StatisticsResponse(BaseModel):
    """Response with objective statistics."""

    success: bool
    statistics: Dict[str, List[float]] = Field(
        ...,
        description="Statistics (min, max, mean, std, median, range) for each objective",
    )
    correlations: List[List[float]] = Field(
        ..., description="Correlation matrix between objectives"
    )
    extreme_solutions: Dict[str, Dict] = Field(
        ..., description="Solutions that minimize each objective"
    )
    hypervolume: float = Field(..., description="Approximate hypervolume indicator")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def objectives_to_numpy(objectives: List[List[float]]) -> np.ndarray:
    """Convert objectives list to numpy array."""
    return np.array(objectives)


def fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64-encoded PNG."""
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/pareto-2d", response_model=ImageResponse)
async def visualize_pareto_2d(request: VisualizationRequest):
    """
    Generate 2D Pareto front visualization.

    Requires exactly 2 objectives.

    Args:
        request: Visualization request with objectives and parameters

    Returns:
        Base64-encoded PNG image

    Raises:
        HTTPException: If objectives is not 2D or visualization fails
    """
    try:
        from src.visualization.pareto_visualization import ParetoVisualizer

        objectives = objectives_to_numpy(request.objectives)

        if objectives.shape[1] != 2:
            raise HTTPException(
                status_code=400,
                detail=f"Expected 2 objectives for 2D plot, got {objectives.shape[1]}",
            )

        visualizer = ParetoVisualizer(figsize=(10, 8), dpi=100)

        obj_names = request.objective_names or [f"Objective {i+1}" for i in range(2)]
        title = request.title or "Pareto Front (2D)"

        fig = visualizer.plot_pareto_front_2d(
            objectives,
            obj_names=obj_names,
            best_idx=request.best_index,
            title=title,
            show=False,
        )

        img_base64 = fig_to_base64(fig)

        return ImageResponse(success=True, image_base64=img_base64, width=1000, height=800)

    except ImportError as e:
        logger.error(f"Visualization module import failed: {e}")
        raise HTTPException(status_code=500, detail="Visualization module not available")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/pareto-3d", response_model=ImageResponse)
async def visualize_pareto_3d(request: VisualizationRequest):
    """
    Generate 3D Pareto front visualization.

    Requires exactly 3 objectives.

    Args:
        request: Visualization request

    Returns:
        Base64-encoded PNG image
    """
    try:
        from src.visualization.pareto_visualization import ParetoVisualizer

        objectives = objectives_to_numpy(request.objectives)

        if objectives.shape[1] != 3:
            raise HTTPException(
                status_code=400,
                detail=f"Expected 3 objectives for 3D plot, got {objectives.shape[1]}",
            )

        visualizer = ParetoVisualizer(figsize=(10, 8), dpi=100)

        obj_names = request.objective_names or [f"Objective {i+1}" for i in range(3)]
        title = request.title or "Pareto Front (3D)"

        fig = visualizer.plot_pareto_front_3d(
            objectives,
            obj_names=obj_names,
            best_idx=request.best_index,
            title=title,
            show=False,
        )

        img_base64 = fig_to_base64(fig)

        return ImageResponse(success=True, image_base64=img_base64, width=1000, height=800)

    except ImportError:
        raise HTTPException(status_code=500, detail="Visualization module not available")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/parallel-coordinates", response_model=ImageResponse)
async def visualize_parallel_coordinates(request: VisualizationRequest):
    """
    Generate parallel coordinates plot for N objectives.

    Works with any number of objectives (2+).

    Args:
        request: Visualization request

    Returns:
        Base64-encoded PNG image
    """
    try:
        from src.visualization.pareto_visualization import ParetoVisualizer

        objectives = objectives_to_numpy(request.objectives)
        n_objectives = objectives.shape[1]

        visualizer = ParetoVisualizer(figsize=(max(10, n_objectives * 2), 8), dpi=100)

        obj_names = request.objective_names or [f"Objective {i+1}" for i in range(n_objectives)]
        title = request.title or "Parallel Coordinates Plot"

        fig = visualizer.plot_parallel_coordinates(
            objectives,
            obj_names=obj_names,
            best_idx=request.best_index,
            normalize=True,
            title=title,
            show=False,
        )

        img_base64 = fig_to_base64(fig)

        width = max(1000, n_objectives * 200)
        return ImageResponse(success=True, image_base64=img_base64, width=width, height=800)

    except ImportError:
        raise HTTPException(status_code=500, detail="Visualization module not available")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/objective-matrix", response_model=ImageResponse)
async def visualize_objective_matrix(request: VisualizationRequest):
    """
    Generate objective trade-off matrix.

    Shows pairwise scatter plots and histograms for all objectives.

    Args:
        request: Visualization request

    Returns:
        Base64-encoded PNG image
    """
    try:
        from src.visualization.pareto_visualization import ParetoVisualizer

        objectives = objectives_to_numpy(request.objectives)
        n_objectives = objectives.shape[1]

        visualizer = ParetoVisualizer(figsize=(3 * n_objectives, 3 * n_objectives), dpi=100)

        obj_names = request.objective_names or [f"Objective {i+1}" for i in range(n_objectives)]
        title = request.title or "Objective Trade-off Matrix"

        fig = visualizer.plot_objective_matrix(
            objectives,
            obj_names=obj_names,
            best_idx=request.best_index,
            title=title,
            show=False,
        )

        img_base64 = fig_to_base64(fig)

        size = 300 * n_objectives
        return ImageResponse(success=True, image_base64=img_base64, width=size, height=size)

    except ImportError:
        raise HTTPException(status_code=500, detail="Visualization module not available")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/statistics", response_model=StatisticsResponse)
async def compute_statistics(request: VisualizationRequest):
    """
    Compute statistical analysis of objectives.

    Includes min, max, mean, std, median, correlations, extreme solutions,
    and hypervolume approximation.

    Args:
        request: Visualization request with objectives

    Returns:
        Statistical analysis results
    """
    try:
        from src.visualization.pareto_visualization import TradeOffAnalyzer

        objectives = objectives_to_numpy(request.objectives)

        # Compute statistics
        stats = TradeOffAnalyzer.compute_statistics(objectives)
        correlations = TradeOffAnalyzer.compute_correlations(objectives)
        extremes = TradeOffAnalyzer.find_extreme_solutions(objectives)
        hypervolume = TradeOffAnalyzer.compute_hypervolume_approximation(objectives)

        # Format extremes for JSON response
        extremes_formatted = {}
        for key, (idx, values) in extremes.items():
            extremes_formatted[key] = {
                "solution_index": idx,
                "objective_values": values.tolist(),
            }

        return StatisticsResponse(
            success=True,
            statistics={k: v.tolist() for k, v in stats.items()},
            correlations=correlations.tolist(),
            extreme_solutions=extremes_formatted,
            hypervolume=float(hypervolume),
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Visualization module not available")
    except Exception as e:
        logger.error(f"Statistics computation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics computation failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for visualization service."""
    try:
        # Test if visualization modules are available
        from src.visualization.pareto_visualization import (  # noqa: F401
            ParetoVisualizer,
            TradeOffAnalyzer,
        )

        return {"status": "healthy", "service": "visualization"}
    except ImportError:
        return {
            "status": "degraded",
            "service": "visualization",
            "error": "Module not available",
        }
