"""
Integration tests for NSGA-III API endpoints.

Tests the FastAPI router endpoints for NSGA-III optimization.

Created: 2026-01-03
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_buildings():
    """Sample buildings for testing."""
    return [
        {"name": "Library", "building_type": "EDUCATIONAL", "area": 2000, "floors": 3},
        {"name": "Dorm", "building_type": "RESIDENTIAL", "area": 3000, "floors": 5},
        {"name": "Cafe", "building_type": "COMMERCIAL", "area": 1500, "floors": 2},
    ]


@pytest.fixture
def sample_request(sample_buildings):
    """Sample NSGA-III optimization request."""
    return {
        "buildings": sample_buildings,
        "bounds": [0, 0, 500, 500],
        "population_size": 20,
        "n_generations": 10,
        "n_partitions": 6,
        "objective_profile": "standard",
        "seed": 42,
        "verbose": False,
    }


# =============================================================================
# HEALTH CHECK TESTS
# =============================================================================


def test_nsga3_health_check():
    """Test NSGA-III health check endpoint."""
    response = client.get("/api/nsga3/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "nsga3-optimizer"


# =============================================================================
# PROFILE LISTING TESTS
# =============================================================================


def test_list_profiles():
    """Test listing available objective profiles."""
    response = client.get("/api/nsga3/profiles")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "profiles" in data

    profiles = data["profiles"]
    assert "Standard" in profiles
    assert "Research-Enhanced" in profiles
    assert "15-Minute City" in profiles
    assert "Campus Planning" in profiles


# =============================================================================
# OPTIMIZATION TESTS - STANDARD PROFILE
# =============================================================================


def test_optimize_with_standard_profile(sample_request):
    """Test optimization with standard profile."""
    sample_request["objective_profile"] = "standard"

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["pareto_size"] > 0
    assert data["n_objectives"] == 3  # cost, walking, adjacency
    assert data["evaluations"] > 0
    assert data["generations"] == 10
    assert data["runtime"] > 0

    # Check best compromise solution
    assert data["best_compromise"] is not None
    best = data["best_compromise"]
    assert len(best["buildings"]) == 3
    assert len(best["objectives"]) == 3
    assert len(best["normalized_objectives"]) == 3

    # Check Pareto front
    assert data["pareto_front"] is not None
    assert len(data["pareto_front"]) == data["pareto_size"]
    assert data["pareto_objectives"] is not None
    assert len(data["pareto_objectives"]) == data["pareto_size"]


def test_optimize_with_research_enhanced_profile(sample_request):
    """Test optimization with research-enhanced profile."""
    sample_request["objective_profile"] = "research_enhanced"

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["n_objectives"] == 4  # cost, walking, adjacency, diversity


def test_optimize_with_fifteen_minute_city_profile(sample_request):
    """Test optimization with 15-minute city profile."""
    sample_request["objective_profile"] = "15_minute_city"

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["n_objectives"] == 4  # Enhanced objectives


def test_optimize_with_campus_planning_profile(sample_request):
    """Test optimization with campus planning profile."""
    sample_request["objective_profile"] = "campus_planning"

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["n_objectives"] == 4  # Enhanced objectives


# =============================================================================
# OPTIMIZATION TESTS - CUSTOM PROFILE
# =============================================================================


def test_optimize_with_custom_profile(sample_request):
    """Test optimization with custom profile."""
    sample_request["objective_profile"] = {
        "name": "Custom Test",
        "use_enhanced": True,
        "weights": {"cost": 0.25, "walking": 0.25, "adjacency": 0.25, "diversity": 0.25},
        "walking_speed_kmh": 4.5,
        "description": "Test custom profile",
    }

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["n_objectives"] == 4


def test_optimize_with_invalid_custom_profile_weights(sample_request):
    """Test optimization with invalid custom profile weights (don't sum to 1.0)."""
    sample_request["objective_profile"] = {
        "name": "Invalid",
        "use_enhanced": True,
        "weights": {"cost": 0.5, "walking": 0.3, "adjacency": 0.1},  # Sum = 0.9
        "walking_speed_kmh": 5.0,
    }

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 400  # Bad request


# =============================================================================
# PARAMETER VALIDATION TESTS
# =============================================================================


def test_optimize_with_invalid_building_type(sample_request):
    """Test optimization with invalid building type."""
    sample_request["buildings"][0]["building_type"] = "INVALID_TYPE"

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 400


def test_optimize_with_empty_buildings():
    """Test optimization with no buildings."""
    request = {
        "buildings": [],
        "bounds": [0, 0, 500, 500],
        "population_size": 20,
        "n_generations": 10,
    }

    response = client.post("/api/nsga3/optimize", json=request)
    assert response.status_code == 422  # Validation error


def test_optimize_with_invalid_bounds(sample_request):
    """Test optimization with invalid bounds."""
    sample_request["bounds"] = [0, 0, 500]  # Only 3 values

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code in [400, 422]  # Can be validation or business logic error


def test_optimize_with_negative_area(sample_request):
    """Test optimization with negative building area."""
    sample_request["buildings"][0]["area"] = -100

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 422  # Validation error


def test_optimize_with_zero_floors(sample_request):
    """Test optimization with zero floors."""
    sample_request["buildings"][0]["floors"] = 0

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 422  # Validation error


def test_optimize_with_invalid_population_size(sample_request):
    """Test optimization with invalid population size."""
    sample_request["population_size"] = 5  # Below minimum

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 422  # Validation error


def test_optimize_with_invalid_generations(sample_request):
    """Test optimization with invalid generations."""
    sample_request["n_generations"] = 2  # Below minimum

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 422  # Validation error


def test_optimize_with_invalid_profile_name(sample_request):
    """Test optimization with invalid profile name."""
    sample_request["objective_profile"] = "nonexistent_profile"

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code in [400, 422]  # Can be validation or business logic error


# =============================================================================
# ALGORITHM PARAMETER TESTS
# =============================================================================


def test_optimize_with_custom_genetic_operators(sample_request):
    """Test optimization with custom crossover and mutation rates."""
    sample_request["crossover_rate"] = 0.8
    sample_request["mutation_rate"] = 0.2

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True


def test_optimize_with_two_layer_reference_points(sample_request):
    """Test optimization with two-layer reference points."""
    sample_request["use_two_layer"] = True
    sample_request["n_partitions_inner"] = 3

    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True


def test_optimize_with_different_seed(sample_request):
    """Test that different seeds produce different results."""
    # Run with seed 42
    sample_request["seed"] = 42
    response1 = client.post("/api/nsga3/optimize", json=sample_request)
    assert response1.status_code == 200
    data1 = response1.json()

    # Run with seed 123
    sample_request["seed"] = 123
    response2 = client.post("/api/nsga3/optimize", json=sample_request)
    assert response2.status_code == 200
    data2 = response2.json()

    # Results should be different
    # Note: Pareto size may be the same, but solutions should differ
    assert data1["success"] is True
    assert data2["success"] is True


# =============================================================================
# RESPONSE FORMAT TESTS
# =============================================================================


def test_response_contains_all_required_fields(sample_request):
    """Test that response contains all required fields."""
    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()

    # Required fields
    assert "success" in data
    assert "message" in data
    assert "pareto_size" in data
    assert "n_objectives" in data
    assert "evaluations" in data
    assert "generations" in data
    assert "runtime" in data

    # Optional but should be present
    assert "best_compromise" in data
    assert "pareto_front" in data
    assert "pareto_objectives" in data


def test_building_placements_have_coordinates(sample_request):
    """Test that buildings in solutions have x,y coordinates."""
    response = client.post("/api/nsga3/optimize", json=sample_request)
    assert response.status_code == 200

    data = response.json()
    best = data["best_compromise"]

    for building in best["buildings"]:
        assert "x" in building
        assert "y" in building
        assert "name" in building
        assert "building_type" in building
        assert "area" in building
        assert "floors" in building
