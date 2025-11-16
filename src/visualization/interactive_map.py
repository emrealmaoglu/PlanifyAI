"""
Interactive map visualization using Folium.

Provides Google Maps-style interactive visualization of campus layouts.
"""

from typing import Dict, List, Optional, Tuple

import folium
import numpy as np
from folium import plugins

from src.algorithms.building import Building, BuildingType
from src.algorithms.solution import Solution
from src.data.campus_data import CampusData


class InteractiveCampusMap:
    """
    Interactive campus map with building placement visualization.

    Features:
    - Google Maps-style pan/zoom
    - Building markers with info popups
    - Campus boundary overlay
    - Building type color coding
    - Constraint violation highlighting
    """

    # Building type colors (Material Design palette)
    BUILDING_COLORS = {
        BuildingType.RESIDENTIAL: "#1976D2",  # Blue
        BuildingType.EDUCATIONAL: "#388E3C",  # Green
        BuildingType.LIBRARY: "#7B1FA2",  # Purple
        BuildingType.ADMINISTRATIVE: "#F57C00",  # Orange
        BuildingType.SPORTS: "#C62828",  # Red
        BuildingType.HEALTH: "#00796B",  # Teal
        BuildingType.COMMERCIAL: "#5D4037",  # Brown
        BuildingType.SOCIAL: "#E91E63",  # Pink
        BuildingType.DINING: "#FF6F00",  # Deep Orange
    }

    # Building type icons (Font Awesome)
    BUILDING_ICONS = {
        BuildingType.RESIDENTIAL: "home",
        BuildingType.EDUCATIONAL: "graduation-cap",
        BuildingType.LIBRARY: "book",
        BuildingType.ADMINISTRATIVE: "building",
        BuildingType.SPORTS: "futbol",
        BuildingType.HEALTH: "hospital",
        BuildingType.COMMERCIAL: "store",
        BuildingType.SOCIAL: "users",
        BuildingType.DINING: "utensils",
    }

    def __init__(
        self,
        campus_data: Optional[CampusData] = None,
        buildings: Optional[List[Building]] = None,
        show_boundary: bool = True,
    ):
        """
        Initialize interactive map.

        Args:
            campus_data: Campus data with boundary and metadata
            buildings: List of buildings (for semantic naming)
            show_boundary: Whether to show campus boundary (default: True)
        """
        self.campus_data = campus_data
        self.buildings = buildings or []
        self.show_boundary = show_boundary
        self.map = None

    def create_map(
        self,
        solution: Solution,
        buildings: Optional[List[Building]] = None,
        center: Optional[Tuple[float, float]] = None,
        zoom_start: int = 16,
        tiles: str = "OpenStreetMap",
        major_roads: Optional[List[np.ndarray]] = None,
        minor_roads: Optional[List[np.ndarray]] = None,
    ) -> folium.Map:
        """
        Create interactive Folium map with building placement.

        Args:
            solution: Optimized building placement solution
            buildings: List of Building objects (if not provided, uses self.buildings)
            center: Map center (lat, lon). If None, calculated from campus bounds
            zoom_start: Initial zoom level (default: 16 for campus view)

        Returns:
            Folium map object
        """
        # Use provided buildings or fall back to instance variable
        if buildings is None:
            buildings = self.buildings

        # Create building lookup by ID
        building_dict = {b.id: b for b in buildings}

        # Calculate map center
        if center is None:
            if self.campus_data:
                bounds = self.campus_data.get_bounds()
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
            else:
                # Use solution positions
                positions = np.array(list(solution.positions.values()))
                if len(positions) > 0:
                    center_x, center_y = positions.mean(axis=0)
                else:
                    center_x, center_y = 0, 0

            # Convert meters to lat/lon (approximate for visualization)
            # Using Istanbul coordinates as reference
            center = self._meters_to_latlon(center_x, center_y)

        # Create base map
        self.map = folium.Map(
            location=center, zoom_start=zoom_start, tiles=tiles, control_scale=True
        )

        # Add campus boundary if available and enabled
        if self.show_boundary and self.campus_data and self.campus_data.boundary:
            self._add_campus_boundary()

        # Add existing buildings (if any)
        if self.campus_data and self.campus_data.buildings:
            self._add_existing_buildings()

        # Add new buildings from solution
        self._add_solution_buildings(solution, building_dict)

        # Add roads if provided
        if major_roads is not None:
            self._add_roads(major_roads, "major")
        if minor_roads is not None:
            self._add_roads(minor_roads, "minor")

        # Add legend
        self._add_legend()

        # Add measurement tool
        plugins.MeasureControl(
            position="topleft",
            primary_length_unit="meters",
            secondary_length_unit="kilometers",
            primary_area_unit="sqmeters",
        ).add_to(self.map)

        # Add fullscreen button
        plugins.Fullscreen(position="topright").add_to(self.map)

        # Add minimap
        minimap = plugins.MiniMap(toggle_display=True)
        self.map.add_child(minimap)

        return self.map

    def _add_campus_boundary(self):
        """Add campus boundary overlay to map"""
        if not self.campus_data or not self.campus_data.boundary:
            return

        # Convert boundary to lat/lon coordinates
        boundary_coords = []
        for x, y in self.campus_data.boundary.exterior.coords:
            lat, lon = self._meters_to_latlon(x, y)
            boundary_coords.append([lat, lon])

        # Add polygon
        folium.Polygon(
            locations=boundary_coords,
            color="#333333",
            weight=3,
            fill=True,
            fillColor="#CCCCCC",
            fillOpacity=0.1,
            popup="Campus Boundary",
            tooltip="Campus Area",
        ).add_to(self.map)

    def _add_existing_buildings(self):
        """Add existing buildings to map (shown in gray)"""
        if not self.campus_data or not self.campus_data.buildings:
            return

        for building in self.campus_data.buildings:
            if hasattr(building, "position") and building.position:
                x, y = building.position
                lat, lon = self._meters_to_latlon(x, y)

                # Calculate building radius for circle
                radius = np.sqrt(building.area / np.pi)

                # Add circle marker
                folium.Circle(
                    location=[lat, lon],
                    radius=radius,
                    color="#757575",
                    fill=True,
                    fillColor="#BDBDBD",
                    fillOpacity=0.4,
                    weight=2,
                    popup=self._create_building_popup(building, is_existing=True),
                    tooltip=f"Existing: {building.id}",
                ).add_to(self.map)

    def _add_solution_buildings(self, solution: Solution, building_dict: Dict[str, Building]):
        """Add new buildings from solution to map"""
        for building_id, position in solution.positions.items():
            building = building_dict.get(building_id)
            if not building:
                continue

            x, y = position
            lat, lon = self._meters_to_latlon(x, y)

            # Get building color and icon
            color = self.BUILDING_COLORS.get(building.type, "#757575")
            icon = self.BUILDING_ICONS.get(building.type, "building")

            # Calculate building radius
            radius = np.sqrt(building.footprint / np.pi)

            # Add circle marker for building footprint
            folium.Circle(
                location=[lat, lon],
                radius=radius,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
                weight=2,
                popup=self._create_building_popup(building, position),
                tooltip=self._get_building_name(building, building_dict),
            ).add_to(self.map)

            # Add icon marker at center
            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color=self._get_icon_color(building.type), icon=icon, prefix="fa"),
                popup=self._create_building_popup(building, position),
                tooltip=self._get_building_name(building, building_dict),
            ).add_to(self.map)

    def _create_building_popup(
        self,
        building: Building,
        position: Optional[Tuple[float, float]] = None,
        is_existing: bool = False,
    ) -> str:
        """
        Create HTML popup for building marker.

        Returns:
            HTML string with building information
        """
        status = "Existing" if is_existing else "New"

        html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 10px 0;
                color: {self.BUILDING_COLORS.get(building.type, '#757575')};">
                {building.id}
            </h4>
            <table style="width: 100%; font-size: 12px;">
                <tr>
                    <td><b>Status:</b></td>
                    <td>{status}</td>
                </tr>
                <tr>
                    <td><b>Type:</b></td>
                    <td>{building.type.name.title()}</td>
                </tr>
                <tr>
                    <td><b>Area:</b></td>
                    <td>{building.area:,.0f} m²</td>
                </tr>
                <tr>
                    <td><b>Floors:</b></td>
                    <td>{building.floors}</td>
                </tr>
                <tr>
                    <td><b>Total Floor Area:</b></td>
                    <td>{building.area * building.floors:,.0f} m²</td>
                </tr>
        """

        if position:
            html += f"""
                <tr>
                    <td><b>Position:</b></td>
                    <td>({position[0]:.1f}, {position[1]:.1f})</td>
                </tr>
            """

        html += """
            </table>
        </div>
        """

        return html

    def _add_legend(self):
        """Add legend to map"""
        legend_html = """
        <div style="position: fixed;
                    bottom: 50px; right: 50px;
                    border:2px solid grey;
                    background-color: white;
                    z-index:9999;
                    font-size:14px;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
            <p style="margin: 0 0 5px 0; font-weight: bold;">Building Types</p>
        """

        for btype, color in self.BUILDING_COLORS.items():
            icon = self.BUILDING_ICONS.get(btype, "building")
            legend_html += f"""
            <p style="margin: 5px 0;">
                <i class="fa fa-{icon}" style="color:{color}"></i>
                {btype.name.title()}
            </p>
            """

        legend_html += "</div>"

        self.map.get_root().html.add_child(folium.Element(legend_html))

    def _get_building_name(self, building: Building, building_dict: Dict[str, Building]) -> str:
        """
        Generate semantic building name.

        Examples:
            - B00 (RESIDENTIAL) → "Residential Hall 1"
            - B06 (LIBRARY) → "Main Library"
            - B09 (SPORTS) → "Sports Complex"
        """
        # Count buildings of same type for numbering
        same_type_count = 1
        for other_id, other in building_dict.items():
            if other.type == building.type and other.id < building.id:
                same_type_count += 1

        # Generate name based on type
        type_names = {
            BuildingType.RESIDENTIAL: f"Residential Hall {same_type_count}",
            BuildingType.EDUCATIONAL: f"Academic Building {same_type_count}",
            BuildingType.LIBRARY: "Main Library"
            if same_type_count == 1
            else f"Library {same_type_count}",
            BuildingType.ADMINISTRATIVE: "Administration Building"
            if same_type_count == 1
            else f"Admin {same_type_count}",
            BuildingType.SPORTS: "Sports Complex"
            if same_type_count == 1
            else f"Sports Facility {same_type_count}",
            BuildingType.HEALTH: "Health Center"
            if same_type_count == 1
            else f"Health Facility {same_type_count}",
            BuildingType.COMMERCIAL: f"Commercial Building {same_type_count}",
            BuildingType.SOCIAL: f"Social Center {same_type_count}",
            BuildingType.DINING: "Main Cafeteria"
            if same_type_count == 1
            else f"Cafeteria {same_type_count}",
        }

        return type_names.get(building.type, f"{building.type.name.title()} {same_type_count}")

    def _get_icon_color(self, building_type: BuildingType) -> str:
        """Get Folium icon color (limited palette)"""
        color_map = {
            BuildingType.RESIDENTIAL: "blue",
            BuildingType.EDUCATIONAL: "green",
            BuildingType.LIBRARY: "purple",
            BuildingType.ADMINISTRATIVE: "orange",
            BuildingType.SPORTS: "red",
            BuildingType.HEALTH: "lightblue",
            BuildingType.COMMERCIAL: "darkred",
            BuildingType.SOCIAL: "pink",
            BuildingType.DINING: "darkorange",
        }
        return color_map.get(building_type, "gray")

    def _add_roads(self, roads: List[np.ndarray], road_type: str = "major") -> None:
        """
        Add roads to the map.

        Args:
            roads: List of road paths, each is (N, 2) array of [x, y] coordinates
            road_type: 'major' or 'minor'
        """
        if road_type == "major":
            color = "#E74C3C"  # Red
            weight = 4
            opacity = 0.9
            popup_prefix = "Major Road"
        else:  # minor
            color = "#3498DB"  # Blue
            weight = 2
            opacity = 0.7
            popup_prefix = "Minor Road"

        for i, road in enumerate(roads):
            if len(road) < 2:
                continue

            # Convert road coordinates to lat/lon
            coords = []
            for point in road:
                x, y = point[0], point[1]
                lat, lon = self._meters_to_latlon(x, y)
                coords.append([lat, lon])

            # Add polyline
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=weight,
                opacity=opacity,
                popup=f"{popup_prefix} {i+1}",
                tooltip=f"{popup_prefix} {i+1}",
            ).add_to(self.map)

    def _meters_to_latlon(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert meters to lat/lon coordinates.

        Uses Istanbul as reference point (41.08°N, 29.05°E).
        Approximation: 1° lat ≈ 111km, 1° lon ≈ 79km (at Istanbul latitude)

        Args:
            x: X coordinate in meters (relative to campus origin)
            y: Y coordinate in meters (relative to campus origin)

        Returns:
            (latitude, longitude) tuple
        """
        # Istanbul reference
        ref_lat = 41.08
        ref_lon = 29.05

        # Conversion factors (approximate)
        meters_per_degree_lat = 111000  # ~111 km per degree
        meters_per_degree_lon = 79000  # ~79 km per degree at Istanbul latitude

        # Convert (assuming campus origin at reference point)
        lat = ref_lat + (y / meters_per_degree_lat)
        lon = ref_lon + (x / meters_per_degree_lon)

        return (lat, lon)

    def save_map(self, filepath: str):
        """Save map to HTML file"""
        if self.map:
            self.map.save(filepath)
