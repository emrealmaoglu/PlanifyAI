"""
Pytest Configuration and Fixtures
"""
import logging

import pytest


@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


@pytest.fixture
def sample_buildings():
    """Sample buildings for testing"""
    from src.algorithms.building import Building, BuildingType

    return [
        Building("B1", BuildingType.RESIDENTIAL, 2000, 5),
        Building("B2", BuildingType.COMMERCIAL, 1500, 3),
        Building("B3", BuildingType.EDUCATIONAL, 3000, 4),
    ]


@pytest.fixture
def bounds():
    """Sample bounds"""
    return (0.0, 0.0, 500.0, 500.0)
