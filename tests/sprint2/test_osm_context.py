import pytest
import numpy as np
from shapely.geometry import Polygon, Point, LineString

from backend.core.context.osm_context import (
    OSMContextFetcher, CampusContext, ExistingBuilding, ExistingRoad,
    fetch_campus_context
)


class TestOSMContextFetcher:
    """Tests for OSMContextFetcher."""
    
    @pytest.fixture
    def fetcher(self):
        return OSMContextFetcher()
    
    def test_local_crs_northern_hemisphere(self, fetcher):
        """Should return correct UTM zone for northern hemisphere."""
        crs = fetcher._get_local_crs(lat=41.0, lon=33.0)
        assert crs.startswith("EPSG:326")  # Northern hemisphere
    
    def test_local_crs_southern_hemisphere(self, fetcher):
        """Should return correct UTM zone for southern hemisphere."""
        crs = fetcher._get_local_crs(lat=-33.0, lon=18.0)
        assert crs.startswith("EPSG:327")  # Southern hemisphere
    
    @pytest.mark.integration
    def test_fetch_by_point_ankara(self, fetcher):
        """Fetch context around a point in Ankara."""
        # Ankara city center
        context = fetcher.fetch_by_point(lat=39.925, lon=32.837, radius_meters=200)
        
        assert context is not None
        assert isinstance(context.boundary, Polygon)
        assert context.boundary.area > 0
        assert context.center_latlon == (39.925, 32.837)
        # Should find some buildings/roads in city center
        print(f"Found {len(context.existing_buildings)} buildings, {len(context.existing_roads)} roads")
    
    @pytest.mark.integration
    def test_fetch_by_point_kastamonu(self, fetcher):
        """Fetch context around Kastamonu University coordinates."""
        # Kastamonu University approximate location
        context = fetcher.fetch_by_point(lat=41.3833, lon=33.7833, radius_meters=500)
        
        assert context is not None
        assert isinstance(context.boundary, Polygon)
        print(f"Kastamonu: {len(context.existing_buildings)} buildings, {len(context.existing_roads)} roads")
    
    @pytest.mark.integration
    def test_fetch_by_bbox(self, fetcher):
        """Fetch context by bounding box."""
        # Small area in Ankara
        context = fetcher.fetch_by_bbox(
            north=39.93,
            south=39.92,
            east=32.84,
            west=32.83
        )
        
        assert context is not None
        assert context.boundary.area > 0


class TestCampusContext:
    """Tests for CampusContext data class."""
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample context for testing."""
        boundary = Polygon([(0, 0), (1000, 0), (1000, 800), (0, 800)])
        
        buildings = [
            ExistingBuilding(
                osm_id=1,
                geometry=Polygon([(100, 100), (200, 100), (200, 200), (100, 200)]),
                building_type="university",
                name="Main Building",
                height=15.0,
                levels=4
            ),
            ExistingBuilding(
                osm_id=2,
                geometry=Polygon([(400, 400), (550, 400), (550, 500), (400, 500)]),
                building_type="dormitory",
                name="Dorm A",
                height=18.0,
                levels=5
            )
        ]
        
        roads = [
            ExistingRoad(
                osm_id=100,
                geometry=LineString([(0, 300), (1000, 300)]),
                road_type="secondary",
                name="Main Road",
                width=7.0
            )
        ]
        
        return CampusContext(
            boundary=boundary,
            existing_buildings=buildings,
            existing_roads=roads,
            center_latlon=(41.0, 33.0),
            crs_local="EPSG:32636",
            bounds_meters=(0, 0, 1000, 800)
        )
    
    def test_buildable_area_excludes_buildings(self, sample_context):
        """Buildable area should exclude existing buildings."""
        buildable = sample_context.buildable_area
        
        # Check that existing buildings don't overlap with buildable area
        for building in sample_context.existing_buildings:
            intersection = buildable.intersection(building.geometry)
            assert intersection.area < 1.0  # Tiny tolerance
    
    def test_buildable_area_excludes_road_buffer(self, sample_context):
        """Buildable area should exclude road buffers."""
        buildable = sample_context.buildable_area
        
        # Roads are buffered by 10m
        for road in sample_context.existing_roads:
            road_buffer = road.geometry.buffer(10)
            intersection = buildable.intersection(road_buffer)
            assert intersection.area < 1.0
    
    def test_total_existing_building_area(self, sample_context):
        """Should calculate total existing building area."""
        total = sample_context.total_existing_building_area
        
        # Building 1: 100x100 = 10000
        # Building 2: 150x100 = 15000
        expected = 10000 + 15000
        assert abs(total - expected) < 1.0
    
    def test_to_geojson_structure(self, sample_context):
        """GeoJSON output should have correct structure."""
        geojson = sample_context.to_geojson()
        
        assert geojson["type"] == "FeatureCollection"
        assert "features" in geojson
        assert "metadata" in geojson
        
        # Should have boundary, 2 buildings, 1 road, and buildable area
        layers = [f["properties"]["layer"] for f in geojson["features"]]
        assert "boundary" in layers
        assert layers.count("existing_building") == 2
        assert layers.count("existing_road") == 1
        assert "buildable_area" in layers
    
    def test_existing_building_properties(self, sample_context):
        """Existing buildings should have correct properties."""
        building = sample_context.existing_buildings[0]
        
        assert building.osm_id == 1
        assert building.building_type == "university"
        assert building.name == "Main Building"
        assert building.height == 15.0
        assert building.levels == 4
        assert building.area == 10000  # 100x100
        assert building.centroid == (150, 150)  # Center of 100-200 square


class TestConvenienceFunction:
    """Tests for fetch_campus_context convenience function."""
    
    def test_requires_location_info(self):
        """Should raise error if no location info provided."""
        with pytest.raises(ValueError):
            fetch_campus_context()
    
    @pytest.mark.integration
    def test_by_coordinates(self):
        """Fetch by lat/lon coordinates."""
        context = fetch_campus_context(lat=39.925, lon=32.837, radius=100)
        assert context is not None


# Mark integration tests to skip in CI without network
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may need network)"
    )
