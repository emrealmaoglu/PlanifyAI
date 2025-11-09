"""
Result Export Utilities
=======================

Export optimization results to various formats.

Classes:
    ResultExporter: Export results to GeoJSON, CSV, JSON, Markdown

Created: 2025-11-09
"""

import json
from typing import Any, Dict, Optional

import pandas as pd

from ..algorithms.building import Building
from ..algorithms.solution import Solution
from ..data.campus_data import CampusData


class ResultExporter:
    """
    Export optimization results to various formats.

    Supports:
    - GeoJSON: Spatial data format
    - CSV: Building positions
    - JSON: Complete result dictionary
    - Markdown: Human-readable report

    Example:
        >>> exporter = ResultExporter()
        >>> exporter.to_geojson(solution, campus, 'output.geojson')
    """

    @staticmethod
    def to_geojson(
        solution: Solution,
        campus: CampusData,
        filepath: str,
        buildings: Optional[list[Building]] = None,
    ) -> None:
        """
        Export solution as GeoJSON.

        Args:
            solution: Solution to export
            campus: Campus data
            filepath: Output file path
            buildings: Optional list of Building objects (for metadata)
        """
        features = []

        # Add campus boundary
        boundary_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [list(campus.boundary.exterior.coords)],
            },
            "properties": {
                "name": campus.name,
                "type": "campus_boundary",
            },
        }
        features.append(boundary_feature)

        # Add buildings
        building_dict = {}
        if buildings:
            building_dict = {b.id: b for b in buildings}

        for building_id, position in solution.positions.items():
            x, y = position

            # Get building metadata
            building_type = "unknown"
            area = 0.0
            floors = 0

            if building_id in building_dict:
                building = building_dict[building_id]
                building_type = building.type.value
                area = building.area
                floors = building.floors

            building_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y],
                },
                "properties": {
                    "id": building_id,
                    "type": building_type,
                    "area": area,
                    "floors": floors,
                },
            }
            features.append(building_feature)

        # Create GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)

    @staticmethod
    def to_csv(
        solution: Solution,
        filepath: str,
        buildings: Optional[list[Building]] = None,
    ) -> None:
        """
        Export building positions as CSV.

        Args:
            solution: Solution to export
            filepath: Output file path
            buildings: Optional list of Building objects (for metadata)
        """
        building_dict = {}
        if buildings:
            building_dict = {b.id: b for b in buildings}

        data = []
        for building_id, position in solution.positions.items():
            x, y = position

            building_type = "unknown"
            area = 0.0
            floors = 0

            if building_id in building_dict:
                building = building_dict[building_id]
                building_type = building.type.value
                area = building.area
                floors = building.floors

            data.append(
                {
                    "building_id": building_id,
                    "x": x,
                    "y": y,
                    "type": building_type,
                    "area": area,
                    "floors": floors,
                }
            )

        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)

    @staticmethod
    def to_json(result: Dict[str, Any], filepath: str) -> None:
        """
        Export result dictionary as JSON.

        Handles custom objects by converting to serializable format.

        Args:
            result: Result dictionary to export
            filepath: Output file path
        """
        # Create serializable copy
        serializable_result = {}

        for key, value in result.items():
            if key == "best_solution":
                # Convert Solution to dict
                solution = value
                serializable_result[key] = {
                    "positions": {k: list(v) for k, v in solution.positions.items()},
                    "fitness": solution.fitness,
                    "objectives": solution.objectives if hasattr(solution, "objectives") else {},
                }
            elif key == "all_solutions":
                # Skip all_solutions (too large)
                serializable_result[key] = f"{len(value)} solutions (not serialized)"
            else:
                # Try to serialize directly
                try:
                    json.dumps(value)
                    serializable_result[key] = value
                except (TypeError, ValueError):
                    # Convert to string representation
                    serializable_result[key] = str(value)

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_result, f, indent=2)

    @staticmethod
    def generate_report(result: Dict[str, Any], filepath: str) -> None:
        """
        Generate markdown report.

        Args:
            result: Result dictionary to export
            filepath: Output file path
        """
        lines = []
        lines.append("# Optimization Report\n")
        lines.append("## Results\n")

        # Fitness
        fitness = result.get("fitness", 0.0)
        lines.append(f"**Best Fitness:** {fitness:.4f}\n")

        # Objectives
        objectives = result.get("objectives", {})
        if objectives:
            lines.append("### Objectives\n")
            for obj_name, score in objectives.items():
                lines.append(f"- **{obj_name.capitalize()}:** {score:.4f}")
            lines.append("")

        # Statistics
        statistics = result.get("statistics", {})
        if statistics:
            lines.append("### Statistics\n")
            lines.append(f"- **Runtime:** {statistics.get('runtime', 0):.2f}s")
            lines.append(f"- **Evaluations:** {statistics.get('evaluations', 0):,}")
            lines.append(f"- **Generations:** {statistics.get('ga_generations', 0)}")
            lines.append("")

        # Constraints
        constraints = result.get("constraints", {})
        if constraints:
            lines.append("### Constraints\n")
            lines.append(f"- **Satisfied:** {constraints.get('satisfied', False)}")
            lines.append(f"- **Penalty:** {constraints.get('penalty', 0.0):.4f}")

            violations = constraints.get("violations", {})
            if violations:
                lines.append("- **Violations:**")
                for desc, penalty in violations.items():
                    lines.append(f"  - {desc}: {penalty:.4f}")
            lines.append("")

        # Solution
        best_solution = result.get("best_solution")
        if best_solution:
            lines.append("### Solution\n")
            lines.append(f"- **Buildings:** {len(best_solution.positions)}")
            lines.append("- **Positions:**")
            for building_id, position in best_solution.positions.items():
                lines.append(f"  - {building_id}: ({position[0]:.2f}, {position[1]:.2f})")
            lines.append("")

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
