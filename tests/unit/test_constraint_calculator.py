"""
Unit tests for ConstraintCalculator.

Sprint 3, Faz 3.1.1 - Constraint Calculator Unit Tests
Tests boundary, overlap, setback, separation, and slope constraints.
"""

import pytest
from shapely.geometry import Polygon, LineString, Point
from shapely.affinity import translate

from backend.core.optimization.spatial_problem import ConstraintCalculator
from backend.core.optimization.encoding import BuildingGene
from backend.core.schemas.input import SiteParameters


@pytest.fixture
def square_boundary():
    """100x100 meter square boundary."""
    return Polygon([
        (0, 0), (100, 0), (100, 100), (0, 100), (0, 0)
    ])


@pytest.fixture
def site_params():
    """Default site parameters with Turkish code setbacks."""
    return SiteParameters(
        min_setback_front=5.0,
        min_setback_side=3.0,
        min_building_separation=6.0
    )


@pytest.fixture
def simple_roads():
    """A road along the bottom edge of the boundary."""
    return [LineString([(0, 0), (100, 0)])]


@pytest.fixture
def calculator(square_boundary, site_params, simple_roads):
    """ConstraintCalculator with default setup."""
    return ConstraintCalculator(
        boundary=square_boundary,
        site_params=site_params,
        road_geometries=simple_roads,
        dem_sampler=None  # No terrain for basic tests
    )


class TestBoundaryViolation:
    """Tests for boundary constraint."""
    
    def test_building_fully_inside_boundary(self, calculator):
        """Building completely inside boundary should have zero violation."""
        building = Polygon([
            (20, 20), (40, 20), (40, 40), (20, 40), (20, 20)
        ])
        violation = calculator.boundary_violation([building])
        assert violation == 0.0
    
    def test_building_partially_outside_boundary(self, calculator):
        """Building partially outside should have positive violation."""
        # Building extends 10m outside right edge
        building = Polygon([
            (90, 20), (110, 20), (110, 40), (90, 40), (90, 20)
        ])
        violation = calculator.boundary_violation([building])
        # Area outside = 10 * 20 = 200 m²
        assert violation > 0
        assert violation == pytest.approx(200.0, rel=0.01)
    
    def test_building_completely_outside_boundary(self, calculator):
        """Building completely outside should have full area as violation."""
        building = Polygon([
            (110, 110), (130, 110), (130, 130), (110, 130), (110, 110)
        ])
        violation = calculator.boundary_violation([building])
        # Full building area = 20 * 20 = 400 m²
        assert violation == pytest.approx(400.0, rel=0.01)


class TestOverlapViolation:
    """Tests for building overlap constraint."""
    
    def test_no_overlap_between_buildings(self, calculator):
        """Non-overlapping buildings should have zero violation."""
        building1 = Polygon([
            (10, 10), (30, 10), (30, 30), (10, 30), (10, 10)
        ])
        building2 = Polygon([
            (50, 50), (70, 50), (70, 70), (50, 70), (50, 50)
        ])
        violation = calculator.overlap_violation([building1, building2])
        assert violation == 0.0
    
    def test_partial_overlap_between_buildings(self, calculator):
        """Overlapping buildings should have positive violation."""
        building1 = Polygon([
            (10, 10), (30, 10), (30, 30), (10, 30), (10, 10)
        ])
        # Building 2 overlaps by 10x20 = 200 m²
        building2 = Polygon([
            (20, 10), (40, 10), (40, 30), (20, 30), (20, 10)
        ])
        violation = calculator.overlap_violation([building1, building2])
        assert violation > 0
        # Overlap area = 10 * 20 = 200 m²
        assert violation == pytest.approx(200.0, rel=0.01)
    
    def test_identical_buildings_full_overlap(self, calculator):
        """Identical buildings should have full area as overlap."""
        building = Polygon([
            (10, 10), (30, 10), (30, 30), (10, 30), (10, 10)
        ])
        violation = calculator.overlap_violation([building, building])
        # Full overlap = 20 * 20 = 400 m²
        assert violation == pytest.approx(400.0, rel=0.01)


class TestSeparationViolation:
    """Tests for minimum building separation constraint."""
    
    def test_buildings_with_sufficient_separation(self, calculator):
        """Buildings 10m apart should have no violation (min is 6m)."""
        building1 = Polygon([
            (10, 10), (20, 10), (20, 20), (10, 20), (10, 10)
        ])
        building2 = Polygon([
            (30, 10), (40, 10), (40, 20), (30, 20), (30, 10)
        ])
        violation = calculator.separation_violation([building1, building2])
        assert violation == 0.0
    
    def test_buildings_too_close(self, calculator):
        """Buildings 3m apart should have positive violation."""
        building1 = Polygon([
            (10, 10), (20, 10), (20, 20), (10, 20), (10, 10)
        ])
        building2 = Polygon([
            (23, 10), (33, 10), (33, 20), (23, 20), (23, 10)
        ])
        violation = calculator.separation_violation([building1, building2], min_sep=6.0)
        # They are 3m apart, need 6m, so violation = 6 - 3 = 3m
        assert violation > 0


class TestSetbackViolation:
    """Tests for road setback constraint."""
    
    def test_building_respects_setback(self, calculator):
        """Building 10m from road should have no violation (min is 5m)."""
        building = Polygon([
            (10, 10), (30, 10), (30, 30), (10, 30), (10, 10)
        ])
        violation = calculator.setback_violation([building])
        assert violation == 0.0
    
    def test_building_violates_setback(self, calculator):
        """Building 2m from road should have positive violation."""
        building = Polygon([
            (10, 2), (30, 2), (30, 12), (10, 12), (10, 2)
        ])
        violation = calculator.setback_violation([building])
        assert violation > 0


class TestMultipleConstraints:
    """Tests for multiple constraints at once."""
    
    def test_valid_layout_all_constraints_pass(self, calculator):
        """Valid layout should pass all constraints."""
        buildings = [
            Polygon([(20, 20), (35, 20), (35, 35), (20, 35), (20, 20)]),
            Polygon([(50, 50), (65, 50), (65, 65), (50, 65), (50, 50)]),
        ]
        
        assert calculator.boundary_violation(buildings) == 0.0
        assert calculator.overlap_violation(buildings) == 0.0
        assert calculator.separation_violation(buildings) == 0.0
        assert calculator.setback_violation(buildings) == 0.0
    
    def test_invalid_layout_multiple_violations(self, calculator):
        """Invalid layout should have multiple violations."""
        buildings = [
            # Outside boundary
            Polygon([(95, 95), (115, 95), (115, 115), (95, 115), (95, 95)]),
            # Overlaps with first
            Polygon([(105, 95), (125, 95), (125, 115), (105, 115), (105, 95)]),
        ]
        
        assert calculator.boundary_violation(buildings) > 0
        assert calculator.overlap_violation(buildings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
