"""Tests for spatial indexing."""

import pytest
import numpy as np
from backend.core.integration.spatial_index import SpatialRoadIndex

def test_spatial_index_creation():
    """Test KDTree index builds correctly."""
    roads = [
        np.array([[0, 0], [100, 0]]),
        np.array([[0, 0], [0, 100]])
    ]
    
    index = SpatialRoadIndex(roads)
    
    assert index.tree is not None
    assert len(index.road_points) == 4

def test_nearest_query():
    """Test nearest road point query."""
    # Use dense points to approximate segment
    x_coords = np.linspace(0, 100, 101) # 101 points, 1m spacing
    road = np.column_stack((x_coords, np.zeros_like(x_coords)))
    roads = [road]
    index = SpatialRoadIndex(roads)
    
    # Building at (50, 50) - should be 50m from road
    buildings = np.array([[50, 50]])
    
    distances, indices, violation = index.query_nearest(buildings, min_clearance=10.0)
    
    assert len(distances) == 1
    assert 49.9 < distances[0] < 50.1  # Approximate 50m
    assert violation == 0  # No violation (50m > 10m clearance)

def test_violation_calculation():
    """Test violation score for close buildings."""
    # Use dense points
    x_coords = np.linspace(0, 100, 101)
    road = np.column_stack((x_coords, np.zeros_like(x_coords)))
    roads = [road]
    index = SpatialRoadIndex(roads)
    
    # Building at (50, 5) - only 5m from road
    buildings = np.array([[50, 5]])
    
    distances, indices, violation = index.query_nearest(buildings, min_clearance=10.0)
    
    assert 4.9 < distances[0] < 5.1  # ~5m
    assert 4.9 < violation < 5.1  # Violation = 10 - 5 = 5

def test_empty_roads():
    """Test handling of empty roads."""
    roads = []
    index = SpatialRoadIndex(roads)
    
    buildings = np.array([[50, 50]])
    distances, indices, violation = index.query_nearest(buildings)
    
    assert len(distances) == 0
    assert violation == 0.0
