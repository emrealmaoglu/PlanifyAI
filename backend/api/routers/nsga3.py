"""
NSGA-III Multi-Objective Optimization API Router
=================================================

REST API endpoints for NSGA-III optimization.

Endpoints:
    - POST /api/nsga3/optimize - Run NSGA-III optimization
    - GET /api/nsga3/profiles - List available objective profiles

Created: 2026-01-03
"""

import logging
import traceback
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.api.schemas.nsga3_schemas import (
    CustomObjectiveProfile,
    NSGA3Request,
    NSGA3Response,
    ObjectiveProfileType,
    SolutionResponse,
)
from backend.core.optimization.nsga3_runner import NSGA3Runner, NSGA3RunnerConfig
from src.algorithms import (
    Building,
    BuildingType,
    ObjectiveProfile,
    ProfileType,
    create_custom_profile,
    list_available_profiles,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nsga3", tags=["nsga3"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def parse_building_type(type_str: str) -> BuildingType:
    """
    Parse building type string to BuildingType enum.

    Args:
        type_str: Building type string (case-insensitive)

    Returns:
        BuildingType enum

    Raises:
        ValueError: If building type is invalid
    """
    try:
        return BuildingType[type_str.upper()]
    except KeyError:
        valid_types = [bt.name for bt in BuildingType]
        raise ValueError(
            f"Invalid building type: {type_str}. Valid types: {', '.join(valid_types)}"
        )


def convert_request_to_buildings(request: NSGA3Request) -> list:
    """
    Convert API request buildings to domain Building objects.

    Args:
        request: NSGA3Request

    Returns:
        List of Building objects

    Raises:
        ValueError: If building data is invalid
    """
    buildings = []
    for b in request.buildings:
        try:
            building_type = parse_building_type(b.building_type)
            building = Building(id=b.name, type=building_type, area=b.area, floors=b.floors)
            buildings.append(building)
        except Exception as e:
            raise ValueError(f"Invalid building '{b.name}': {str(e)}")

    return buildings


def resolve_objective_profile(
    profile_input: CustomObjectiveProfile | ObjectiveProfileType,
) -> ObjectiveProfile:
    """
    Resolve objective profile from API input.

    Args:
        profile_input: Profile type enum or custom profile

    Returns:
        ObjectiveProfile instance

    Raises:
        ValueError: If profile is invalid
    """
    if isinstance(profile_input, CustomObjectiveProfile):
        # Custom profile
        return create_custom_profile(
            name=profile_input.name,
            use_enhanced=profile_input.use_enhanced,
            weights=profile_input.weights,
            walking_speed_kmh=profile_input.walking_speed_kmh,
            description=profile_input.description,
        )
    else:
        # Predefined profile
        try:
            profile_type = ProfileType(profile_input.value)
            from src.algorithms import get_profile

            return get_profile(profile_type)
        except ValueError as e:
            raise ValueError(f"Invalid profile type: {profile_input}. Error: {str(e)}")


def format_solution_response(solution_data: Dict, buildings: list) -> SolutionResponse:
    """
    Format solution data into SolutionResponse.

    Args:
        solution_data: Dict with solution, objectives, normalized_objectives, index
        buildings: List of Building objects

    Returns:
        SolutionResponse
    """
    solution = solution_data["solution"]

    # Convert solution positions to buildings list
    buildings_data = []
    for building in buildings:
        pos = solution.positions.get(building.id)
        buildings_data.append(
            {
                "name": building.id,
                "building_type": building.type.name,
                "area": building.area,
                "floors": building.floors,
                "x": pos[0] if pos else None,
                "y": pos[1] if pos else None,
            }
        )

    return SolutionResponse(
        index=solution_data["index"],
        buildings=buildings_data,
        objectives=solution_data["objectives"].tolist(),
        normalized_objectives=solution_data["normalized_objectives"].tolist(),
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/optimize", response_model=NSGA3Response)
async def run_optimization(request: NSGA3Request):
    """
    Run NSGA-III multi-objective optimization.

    This endpoint runs a pure NSGA-III optimization on the provided buildings
    and returns the Pareto front of non-dominated solutions.

    Args:
        request: NSGA3Request with buildings, bounds, and configuration

    Returns:
        NSGA3Response with Pareto front and statistics

    Raises:
        HTTPException: If validation or optimization fails
    """
    try:
        # Validate and convert buildings
        buildings = convert_request_to_buildings(request)

        # Validate bounds
        if len(request.bounds) != 4:
            raise ValueError("Bounds must have exactly 4 values [x_min, y_min, x_max, y_max]")

        bounds = tuple(request.bounds)

        # Resolve objective profile
        objective_profile = resolve_objective_profile(request.objective_profile)

        # Create runner configuration
        config = NSGA3RunnerConfig(
            population_size=request.population_size,
            n_generations=request.n_generations,
            n_partitions=request.n_partitions,
            use_two_layer=request.use_two_layer,
            n_partitions_inner=request.n_partitions_inner,
            crossover_rate=request.crossover_rate,
            mutation_rate=request.mutation_rate,
            objective_profile=objective_profile,
            seed=request.seed,
            verbose=request.verbose,
        )

        # Run optimization
        runner = NSGA3Runner(buildings, bounds, config)
        result = runner.run()

        # Format best compromise solution
        best_compromise = None
        if result["best_compromise"] is not None:
            best_compromise = format_solution_response(result["best_compromise"], buildings)

        # Prepare response
        response = NSGA3Response(
            success=True,
            message="Optimization completed successfully",
            pareto_size=len(result["pareto_front"]),
            n_objectives=result["pareto_objectives"].shape[1],
            best_compromise=best_compromise,
            evaluations=result["statistics"]["evaluations"],
            generations=config.n_generations,
            runtime=runner.stats["runtime"],
            # Include full Pareto front (may be large)
            pareto_front=[
                {
                    "buildings": [
                        {
                            "name": b.id,
                            "building_type": b.type.name,
                            "area": b.area,
                            "floors": b.floors,
                            "x": sol.positions.get(b.id)[0] if sol.positions.get(b.id) else None,
                            "y": sol.positions.get(b.id)[1] if sol.positions.get(b.id) else None,
                        }
                        for b in buildings
                    ]
                }
                for sol in result["pareto_front"]
            ],
            pareto_objectives=result["pareto_objectives"].tolist(),
        )

        return response

    except ValueError as e:
        # Validation error
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Unexpected error
        logger.error(f"Optimization failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/profiles")
async def get_available_profiles():
    """
    Get list of available predefined objective profiles.

    Returns a dictionary mapping profile names to descriptions.

    Returns:
        Dict[str, str]: Profile names and descriptions

    Example response:
        {
            "Standard": "Balanced multi-objective optimization with standard metrics",
            "Research-Enhanced": "All research-based enhanced objectives with diversity",
            "15-Minute City": "Accessibility-focused for 15-minute city planning",
            "Campus Planning": "Adjacency-focused for campus and educational facility planning"
        }
    """
    try:
        profiles = list_available_profiles()
        return JSONResponse(content={"success": True, "profiles": profiles})

    except Exception as e:
        logger.error(f"Failed to list profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list profiles: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for NSGA-III service.

    Returns:
        Dict with service status
    """
    return {"status": "healthy", "service": "nsga3-optimizer"}
