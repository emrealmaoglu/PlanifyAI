"""
Unit Tests for NSGA-III Components
===================================

Tests for reference point generation, non-dominated sorting, and niching.

Created: 2026-01-02 (Week 4 Day 4)
"""

import numpy as np
import pytest

from src.algorithms.nsga3 import (
    associate_to_reference_points,
    compute_ideal_point,
    compute_nadir_point,
    count_reference_points,
    crowding_distance,
    dominates_objective,
    fast_nondominated_sort,
    generate_reference_points,
    generate_two_layer_reference_points,
    get_recommended_partitions,
    niche_preserving_selection,
    normalize_objectives,
    pareto_front_2d_indices,
    perpendicular_distance,
)

# =============================================================================
# REFERENCE POINTS TESTS
# =============================================================================


class TestReferencePoints:
    """Test reference point generation."""

    def test_generate_reference_points_2d(self):
        """Test 2D reference point generation."""
        ref_points = generate_reference_points(n_objectives=2, n_partitions=10)

        # Should have 11 points for 2D with 10 partitions
        assert len(ref_points) == 11

        # All points should sum to 1.0 (on simplex)
        for point in ref_points:
            assert abs(np.sum(point) - 1.0) < 1e-6

        # All coordinates should be in [0, 1]
        assert np.all(ref_points >= 0)
        assert np.all(ref_points <= 1)

    def test_generate_reference_points_3d(self):
        """Test 3D reference point generation."""
        ref_points = generate_reference_points(n_objectives=3, n_partitions=12)

        # Should have 91 points
        assert len(ref_points) == 91

        # All points should sum to 1.0
        for point in ref_points:
            assert abs(np.sum(point) - 1.0) < 1e-6

    def test_count_reference_points(self):
        """Test counting reference points without generating."""
        # 2D
        assert count_reference_points(2, 10) == 11
        assert count_reference_points(2, 100) == 101

        # 3D
        assert count_reference_points(3, 12) == 91
        assert count_reference_points(3, 23) == 300

        # Higher dimensions
        assert count_reference_points(5, 6) == 210
        assert count_reference_points(8, 3) == 120  # C(3+8-1, 8-1) = C(10, 7) = 120

    def test_two_layer_reference_points(self):
        """Test two-layer reference points."""
        ref_points = generate_two_layer_reference_points(
            n_objectives=5,
            n_partitions_outer=6,
            n_partitions_inner=3,
        )

        # Should have outer + inner points
        n_outer = count_reference_points(5, 6)  # 210
        n_inner = count_reference_points(5, 3)  # 56
        assert len(ref_points) == n_outer + n_inner

    def test_get_recommended_partitions(self):
        """Test partition recommendation."""
        # For 3 objectives, ~100 points
        partitions = get_recommended_partitions(3, target_points=100)
        n_points = count_reference_points(3, partitions)
        assert 80 <= n_points <= 120  # Within reasonable range

        # For 5 objectives, ~200 points
        partitions = get_recommended_partitions(5, target_points=200)
        n_points = count_reference_points(5, partitions)
        assert 180 <= n_points <= 220

    def test_reference_points_scaling(self):
        """Test reference point scaling."""
        ref_points = generate_reference_points(n_objectives=2, n_partitions=4, scaling=2.0)

        # Points should sum to 2.0 with scaling=2.0
        for point in ref_points:
            assert abs(np.sum(point) - 2.0) < 1e-6


# =============================================================================
# NON-DOMINATED SORTING TESTS
# =============================================================================


class TestNonDominatedSorting:
    """Test non-dominated sorting algorithms."""

    def test_dominates_objective_basic(self):
        """Test basic domination check."""
        # obj1 dominates obj2
        obj1 = np.array([3.0, 2.0])
        obj2 = np.array([1.0, 1.0])
        assert dominates_objective(obj1, obj2) == True  # noqa: E712

        # obj2 does not dominate obj1
        assert dominates_objective(obj2, obj1) == False  # noqa: E712

        # Neither dominates (trade-off)
        obj3 = np.array([3.0, 1.0])
        obj4 = np.array([1.0, 3.0])
        assert dominates_objective(obj3, obj4) == False  # noqa: E712
        assert dominates_objective(obj4, obj3) == False  # noqa: E712

    def test_dominates_objective_equal(self):
        """Test domination with equal objectives."""
        obj1 = np.array([2.0, 2.0])
        obj2 = np.array([2.0, 2.0])

        # Equal objectives - no domination
        assert dominates_objective(obj1, obj2) == False  # noqa: E712
        assert dominates_objective(obj2, obj1) == False  # noqa: E712

    def test_fast_nondominated_sort_simple(self):
        """Test fast non-dominated sorting with simple case."""
        # 3 non-dominated solutions, 1 dominated
        objectives = np.array(
            [
                [3.0, 1.0],  # 0: Non-dominated
                [2.0, 2.0],  # 1: Non-dominated
                [1.0, 3.0],  # 2: Non-dominated
                [0.5, 0.5],  # 3: Dominated by all
            ]
        )

        fronts, ranks = fast_nondominated_sort(objectives)

        # Front 0 should have 3 solutions
        assert len(fronts[0]) == 3
        assert set(fronts[0]) == {0, 1, 2}

        # Front 1 should have 1 solution
        assert len(fronts[1]) == 1
        assert fronts[1][0] == 3

        # Check ranks
        assert ranks[0] == 0
        assert ranks[1] == 0
        assert ranks[2] == 0
        assert ranks[3] == 1

    def test_fast_nondominated_sort_all_nondominated(self):
        """Test when all solutions are non-dominated."""
        objectives = np.array(
            [
                [3.0, 1.0],
                [2.0, 2.0],
                [1.0, 3.0],
            ]
        )

        fronts, ranks = fast_nondominated_sort(objectives)

        # All in front 0
        assert len(fronts) == 1
        assert len(fronts[0]) == 3
        assert np.all(ranks == 0)

    def test_pareto_front_2d_fast(self):
        """Test fast 2D Pareto front extraction."""
        objectives = np.array(
            [
                [3.0, 1.0],
                [2.0, 2.0],
                [1.0, 3.0],
                [0.5, 0.5],  # Dominated
                [2.5, 0.5],  # Dominated
            ]
        )

        front_indices = pareto_front_2d_indices(objectives)

        # Should identify non-dominated solutions
        assert len(front_indices) == 3
        assert set(front_indices) == {0, 1, 2}

    def test_crowding_distance(self):
        """Test crowding distance calculation."""
        objectives = np.array(
            [
                [1.0, 3.0],
                [2.0, 2.0],
                [3.0, 1.0],
            ]
        )
        front = [0, 1, 2]

        distances = crowding_distance(objectives, front)

        # Boundary solutions should have infinite distance
        assert distances[0] == np.inf
        assert distances[2] == np.inf

        # Interior solution should have finite distance
        assert np.isfinite(distances[1])
        assert distances[1] > 0


# =============================================================================
# NORMALIZATION TESTS
# =============================================================================


class TestNormalization:
    """Test objective normalization."""

    def test_normalize_objectives_basic(self):
        """Test basic normalization."""
        objectives = np.array(
            [
                [1.0, 5.0],
                [2.0, 4.0],
                [3.0, 3.0],
            ]
        )

        ideal = np.array([1.0, 3.0])
        nadir = np.array([3.0, 5.0])

        normalized = normalize_objectives(objectives, ideal, nadir)

        # Check ranges
        assert np.all(normalized >= 0)
        assert np.all(normalized <= 1)

        # Check specific values
        assert np.allclose(normalized[0], [0.0, 1.0])  # Best obj1, worst obj2
        assert np.allclose(normalized[2], [1.0, 0.0])  # Worst obj1, best obj2

    def test_compute_ideal_point(self):
        """Test ideal point computation."""
        objectives = np.array(
            [
                [1.0, 5.0],
                [2.0, 4.0],
                [3.0, 3.0],
            ]
        )

        ideal = compute_ideal_point(objectives)

        # Ideal should be maximum of each objective
        assert np.allclose(ideal, [3.0, 5.0])

    def test_compute_nadir_point(self):
        """Test nadir point computation."""
        objectives = np.array(
            [
                [3.0, 1.0],
                [2.0, 2.0],
                [1.0, 3.0],
                [0.0, 0.0],  # Dominated
            ]
        )

        front = [0, 1, 2]  # Non-dominated solutions
        nadir = compute_nadir_point(objectives, front)

        # Nadir should be minimum among non-dominated solutions
        assert np.allclose(nadir, [1.0, 1.0])


# =============================================================================
# NICHING TESTS
# =============================================================================


class TestNiching:
    """Test niche preservation mechanisms."""

    def test_perpendicular_distance(self):
        """Test perpendicular distance calculation."""
        # Point (1, 1) to x-axis (direction [1, 0])
        point = np.array([1.0, 1.0])
        ref_dir = np.array([1.0, 0.0])
        dist = perpendicular_distance(point, ref_dir)
        assert abs(dist - 1.0) < 1e-6  # Distance should be 1.0

        # Point (1, 1) to y-axis (direction [0, 1])
        ref_dir = np.array([0.0, 1.0])
        dist = perpendicular_distance(point, ref_dir)
        assert abs(dist - 1.0) < 1e-6

        # Point (1, 1) to diagonal (direction [1, 1])
        ref_dir = np.array([1.0, 1.0])
        dist = perpendicular_distance(point, ref_dir)
        assert abs(dist) < 1e-6  # Point is on the line

    def test_associate_to_reference_points(self):
        """Test solution-reference point association."""
        # 2 solutions
        objectives = np.array(
            [
                [0.9, 0.1],  # Close to [1, 0]
                [0.1, 0.9],  # Close to [0, 1]
            ]
        )

        # 2 reference points
        ref_points = np.array(
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ]
        )

        associations, distances = associate_to_reference_points(objectives, ref_points)

        # Solution 0 should associate with ref point 0
        assert associations[0] == 0

        # Solution 1 should associate with ref point 1
        assert associations[1] == 1

        # Distances should be small
        assert distances[0] < 0.2
        assert distances[1] < 0.2

    def test_niche_preserving_selection(self):
        """Test niche-preserving selection."""
        front = [0, 1, 2, 3]

        # 2 solutions near ref point 0, 2 near ref point 1
        associations = np.array([0, 0, 1, 1])
        distances = np.array([0.1, 0.2, 0.15, 0.05])

        ref_points = np.array([[1, 0], [0, 1]])

        # Select 2 solutions
        selected = niche_preserving_selection(
            front=front,
            associations=associations,
            distances=distances,
            reference_points=ref_points,
            n_select=2,
        )

        # Should select one from each niche
        assert len(selected) == 2

        # Should select closest from each niche
        # Niche 0: solution 0 (dist=0.1) is closer than solution 1 (dist=0.2)
        # Niche 1: solution 3 (dist=0.05) is closer than solution 2 (dist=0.15)
        assert 0 in selected  # Closest in niche 0
        assert 3 in selected  # Closest in niche 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestNSGA3Integration:
    """Integration tests for NSGA-III components."""

    def test_full_selection_pipeline(self):
        """Test complete selection pipeline."""
        # Generate test data
        np.random.seed(42)
        n_solutions = 20
        n_objectives = 3

        objectives = np.random.rand(n_solutions, n_objectives)

        # Generate reference points
        ref_points = generate_reference_points(n_objectives=3, n_partitions=5)

        # Non-dominated sorting
        fronts, ranks = fast_nondominated_sort(objectives)

        # Normalize
        ideal = compute_ideal_point(objectives)
        nadir = compute_nadir_point(objectives, fronts[0])
        normalized = normalize_objectives(objectives, ideal, nadir)

        # Associate
        associations, distances = associate_to_reference_points(normalized, ref_points)

        # Select
        n_select = 10
        selected = []

        for front in fronts:
            if len(selected) + len(front) <= n_select:
                selected.extend(front)
            else:
                n_remaining = n_select - len(selected)
                front_selected = niche_preserving_selection(
                    front=front,
                    associations=associations,
                    distances=distances,
                    reference_points=ref_points,
                    n_select=n_remaining,
                )
                selected.extend(front_selected)
                break

        # Should have selected exactly n_select solutions
        assert len(selected) == n_select

        # All selected solutions should be unique
        assert len(set(selected)) == n_select


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
