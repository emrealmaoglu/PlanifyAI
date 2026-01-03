"""
Benchmark Test Cases
====================

Defines standard test cases for comparing optimization algorithms.

Test Case Categories:
    - Small: 3-4 buildings, quick convergence testing
    - Medium: 6-8 buildings, balanced testing
    - Large: 10-15 buildings, scalability testing
"""

from dataclasses import dataclass
from typing import List, Tuple

from src.algorithms.building import Building, BuildingType


@dataclass
class BenchmarkTestCase:
    """Single benchmark test case."""

    name: str
    description: str
    buildings: List[Building]
    bounds: Tuple[float, float, float, float]
    category: str  # "small", "medium", "large"
    expected_complexity: str  # "low", "medium", "high"


def create_test_cases() -> List[BenchmarkTestCase]:
    """
    Create standard benchmark test cases.

    Returns:
        List of benchmark test cases
    """
    test_cases = []

    # ========================================================================
    # SMALL TEST CASES (3-4 buildings)
    # ========================================================================

    test_cases.append(
        BenchmarkTestCase(
            name="small_residential",
            description="Small residential campus with 3 buildings",
            buildings=[
                Building(id="dorm_a", type=BuildingType.RESIDENTIAL, area=2000, floors=4),
                Building(id="cafeteria", type=BuildingType.DINING, area=1000, floors=2),
                Building(id="library", type=BuildingType.LIBRARY, area=1500, floors=2),
            ],
            bounds=(0, 0, 200, 200),
            category="small",
            expected_complexity="low",
        )
    )

    test_cases.append(
        BenchmarkTestCase(
            name="small_educational",
            description="Small educational campus with 4 buildings",
            buildings=[
                Building(id="classroom_a", type=BuildingType.EDUCATIONAL, area=1500, floors=3),
                Building(id="classroom_b", type=BuildingType.EDUCATIONAL, area=1500, floors=3),
                Building(id="library", type=BuildingType.LIBRARY, area=2000, floors=2),
                Building(id="admin", type=BuildingType.ADMINISTRATIVE, area=1000, floors=2),
            ],
            bounds=(0, 0, 250, 250),
            category="small",
            expected_complexity="low",
        )
    )

    # ========================================================================
    # MEDIUM TEST CASES (6-8 buildings)
    # ========================================================================

    test_cases.append(
        BenchmarkTestCase(
            name="medium_mixed_campus",
            description="Medium mixed-use campus with 6 buildings",
            buildings=[
                Building(id="library", type=BuildingType.LIBRARY, area=3000, floors=3),
                Building(id="dorm_a", type=BuildingType.RESIDENTIAL, area=4000, floors=5),
                Building(id="dorm_b", type=BuildingType.RESIDENTIAL, area=4000, floors=5),
                Building(id="cafeteria", type=BuildingType.DINING, area=1500, floors=2),
                Building(id="classroom", type=BuildingType.EDUCATIONAL, area=2500, floors=3),
                Building(id="sports", type=BuildingType.SPORTS, area=3000, floors=2),
            ],
            bounds=(0, 0, 400, 400),
            category="medium",
            expected_complexity="medium",
        )
    )

    test_cases.append(
        BenchmarkTestCase(
            name="medium_university",
            description="Medium university campus with 8 buildings",
            buildings=[
                Building(id="main_library", type=BuildingType.LIBRARY, area=4000, floors=4),
                Building(id="engineering", type=BuildingType.EDUCATIONAL, area=3500, floors=4),
                Building(id="sciences", type=BuildingType.EDUCATIONAL, area=3500, floors=4),
                Building(id="classroom_a", type=BuildingType.EDUCATIONAL, area=2000, floors=3),
                Building(id="classroom_b", type=BuildingType.EDUCATIONAL, area=2000, floors=3),
                Building(id="student_union", type=BuildingType.DINING, area=2500, floors=3),
                Building(id="admin", type=BuildingType.ADMINISTRATIVE, area=1500, floors=2),
                Building(id="sports_center", type=BuildingType.SPORTS, area=4000, floors=2),
            ],
            bounds=(0, 0, 500, 500),
            category="medium",
            expected_complexity="medium",
        )
    )

    # ========================================================================
    # LARGE TEST CASES (10-15 buildings)
    # ========================================================================

    test_cases.append(
        BenchmarkTestCase(
            name="large_comprehensive",
            description="Large comprehensive campus with 12 buildings",
            buildings=[
                Building(id="central_library", type=BuildingType.LIBRARY, area=5000, floors=5),
                Building(id="dorm_north_a", type=BuildingType.RESIDENTIAL, area=5000, floors=6),
                Building(id="dorm_north_b", type=BuildingType.RESIDENTIAL, area=5000, floors=6),
                Building(id="dorm_south_a", type=BuildingType.RESIDENTIAL, area=4500, floors=6),
                Building(id="dorm_south_b", type=BuildingType.RESIDENTIAL, area=4500, floors=6),
                Building(id="engineering", type=BuildingType.EDUCATIONAL, area=4000, floors=4),
                Building(id="sciences", type=BuildingType.EDUCATIONAL, area=4000, floors=4),
                Building(id="main_dining", type=BuildingType.DINING, area=3000, floors=2),
                Building(id="cafe_north", type=BuildingType.DINING, area=1500, floors=1),
                Building(id="classroom_block", type=BuildingType.EDUCATIONAL, area=3500, floors=4),
                Building(id="admin_center", type=BuildingType.ADMINISTRATIVE, area=2000, floors=3),
                Building(id="sports_complex", type=BuildingType.SPORTS, area=5000, floors=3),
            ],
            bounds=(0, 0, 600, 600),
            category="large",
            expected_complexity="high",
        )
    )

    test_cases.append(
        BenchmarkTestCase(
            name="large_university_complex",
            description="Large university complex with 15 buildings",
            buildings=[
                Building(id="main_library", type=BuildingType.LIBRARY, area=6000, floors=6),
                Building(id="branch_library", type=BuildingType.LIBRARY, area=3000, floors=3),
                Building(id="dorm_tower_1", type=BuildingType.RESIDENTIAL, area=6000, floors=8),
                Building(id="dorm_tower_2", type=BuildingType.RESIDENTIAL, area=6000, floors=8),
                Building(id="dorm_tower_3", type=BuildingType.RESIDENTIAL, area=5500, floors=7),
                Building(id="dorm_tower_4", type=BuildingType.RESIDENTIAL, area=5500, floors=7),
                Building(id="engineering_lab", type=BuildingType.EDUCATIONAL, area=4500, floors=5),
                Building(id="science_lab", type=BuildingType.EDUCATIONAL, area=4500, floors=5),
                Building(id="medical_lab", type=BuildingType.EDUCATIONAL, area=4000, floors=4),
                Building(id="main_cafeteria", type=BuildingType.DINING, area=3500, floors=3),
                Building(id="food_court", type=BuildingType.DINING, area=2000, floors=2),
                Building(id="lecture_hall_a", type=BuildingType.EDUCATIONAL, area=3000, floors=4),
                Building(id="lecture_hall_b", type=BuildingType.EDUCATIONAL, area=3000, floors=4),
                Building(
                    id="admin_building", type=BuildingType.ADMINISTRATIVE, area=2500, floors=4
                ),
                Building(id="athletics_center", type=BuildingType.SPORTS, area=6000, floors=3),
            ],
            bounds=(0, 0, 700, 700),
            category="large",
            expected_complexity="high",
        )
    )

    return test_cases


def get_test_case_by_name(name: str) -> BenchmarkTestCase:
    """
    Get a specific test case by name.

    Args:
        name: Test case name

    Returns:
        Test case

    Raises:
        ValueError: If test case not found
    """
    test_cases = create_test_cases()
    for tc in test_cases:
        if tc.name == name:
            return tc
    raise ValueError(f"Test case '{name}' not found")


def get_test_cases_by_category(category: str) -> List[BenchmarkTestCase]:
    """
    Get all test cases in a category.

    Args:
        category: Category name ("small", "medium", "large")

    Returns:
        List of test cases in category
    """
    test_cases = create_test_cases()
    return [tc for tc in test_cases if tc.category == category]
