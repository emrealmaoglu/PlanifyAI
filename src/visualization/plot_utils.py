"""
Visualization Utilities
=======================

Visualization utilities for campus planning results.

Classes:
    CampusPlotter: Visualize campus layouts and solutions

Created: 2025-11-09
"""

import os
from typing import Dict, List, Optional

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from src.algorithms.building import Building, BuildingType
from src.algorithms.solution import Solution
from src.data.campus_data import CampusData


class CampusPlotter:
    """
    Visualize campus layouts and solutions.

    Provides methods for plotting solutions, convergence, and objectives.

    Example:
        >>> plotter = CampusPlotter(campus)
        >>> plotter.plot_solution(solution, save_path='output.png')
    """

    # Color map for building types
    BUILDING_COLORS = {
        BuildingType.RESIDENTIAL: "#FF6B6B",
        BuildingType.EDUCATIONAL: "#4ECDC4",
        BuildingType.COMMERCIAL: "#45B7D1",
        BuildingType.HEALTH: "#FFA07A",
        BuildingType.SOCIAL: "#98D8C8",
        BuildingType.ADMINISTRATIVE: "#F7DC6F",
        BuildingType.SPORTS: "#BB8FCE",
        BuildingType.LIBRARY: "#85C1E2",
        BuildingType.DINING: "#F8B739",
    }

    def __init__(self, campus_data: CampusData):
        """
        Initialize campus plotter.

        Args:
            campus_data: Campus data to visualize
        """
        self.campus_data = campus_data

    def plot_solution(
        self,
        solution: Solution,
        show_constraints: bool = True,
        save_path: Optional[str] = None,
        buildings: Optional[List[Building]] = None,
    ) -> None:
        """
        Plot campus layout with solution.

        Args:
            solution: Solution to plot
            show_constraints: Whether to show constraint zones
            save_path: Optional path to save plot
            buildings: Optional list of Building objects for metadata
        """
        fig, ax = plt.subplots(figsize=(12, 10))

        # Plot campus boundary
        boundary_coords = list(self.campus_data.boundary.exterior.coords)
        boundary_x = [c[0] for c in boundary_coords]
        boundary_y = [c[1] for c in boundary_coords]
        ax.plot(boundary_x, boundary_y, "k-", linewidth=2, label="Campus Boundary")
        ax.fill(boundary_x, boundary_y, alpha=0.1, color="gray")

        # Plot existing buildings
        existing_labeled = False
        for building in self.campus_data.buildings:
            if building.position:
                x, y = building.position
                radius = building.radius
                label = "Existing Building" if not existing_labeled else None
                circle = patches.Circle((x, y), radius, color="gray", alpha=0.5, label=label)
                ax.add_patch(circle)
                existing_labeled = True

        # Plot new buildings
        building_dict = {b.id: b for b in buildings} if buildings else {}
        plotted_types = set()
        for building_id, position in solution.positions.items():
            x, y = position
            building = building_dict.get(building_id)
            building_type = building.type if building else BuildingType.RESIDENTIAL
            color = self.BUILDING_COLORS.get(building_type, "#CCCCCC")
            radius = building.radius if building else 10.0

            # Add label only once per building type
            label = None
            if building_type not in plotted_types:
                label = building_type.value.capitalize()
                plotted_types.add(building_type)

            circle = patches.Circle((x, y), radius, color=color, alpha=0.7, label=label)
            ax.add_patch(circle)
            ax.text(x, y, building_id, ha="center", va="center", fontsize=8)

        # Show setback zones if requested
        if show_constraints and "setback_from_boundary" in self.campus_data.constraints:
            setback = self.campus_data.constraints["setback_from_boundary"]
            # Create inner boundary with setback
            inner_boundary = self.campus_data.boundary.buffer(-setback)
            if inner_boundary.is_valid and hasattr(inner_boundary, "exterior"):
                inner_coords = list(inner_boundary.exterior.coords)
                inner_x = [c[0] for c in inner_coords]
                inner_y = [c[1] for c in inner_coords]
                ax.plot(
                    inner_x,
                    inner_y,
                    "r--",
                    linewidth=1,
                    alpha=0.5,
                    label=f"Setback Zone ({setback}m)",
                )

        ax.set_xlabel("X (meters)")
        ax.set_ylabel("Y (meters)")
        ax.set_title(f"Campus Layout - {self.campus_data.name}")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal")

        if save_path:
            os.makedirs(
                os.path.dirname(save_path) if os.path.dirname(save_path) else ".",
                exist_ok=True,
            )
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            plt.close()
        else:
            plt.show()

    def plot_convergence(self, result: Dict, save_path: Optional[str] = None) -> None:
        """
        Plot optimization convergence.

        Args:
            result: Optimization result dictionary
            save_path: Optional path to save plot
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        convergence = result.get("convergence", {})
        ga_best = convergence.get("ga_best_history", [])
        ga_avg = convergence.get("ga_avg_history", [])

        if ga_best:
            generations = range(len(ga_best))
            ax.plot(generations, ga_best, "b-", label="Best Fitness", linewidth=2)
            if ga_avg:
                ax.plot(generations, ga_avg, "r--", label="Average Fitness", linewidth=1)

        ax.set_xlabel("Generation")
        ax.set_ylabel("Fitness")
        ax.set_title("Optimization Convergence")
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            os.makedirs(
                os.path.dirname(save_path) if os.path.dirname(save_path) else ".",
                exist_ok=True,
            )
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            plt.close()
        else:
            plt.show()

    def plot_objectives(self, result: Dict, save_path: Optional[str] = None) -> None:
        """
        Plot objective breakdown.

        Args:
            result: Optimization result dictionary
            save_path: Optional path to save plot
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Plot objective scores
        objectives = result.get("objectives", {})
        if objectives:
            obj_names = list(objectives.keys())
            obj_values = list(objectives.values())
            colors = ["#4ECDC4", "#45B7D1", "#FF6B6B"]
            ax1.bar(
                obj_names,
                obj_values,
                color=colors[: len(obj_names)],
            )
            ax1.set_xlabel("Objective")
            ax1.set_ylabel("Score")
            ax1.set_title("Objective Breakdown")
            ax1.grid(True, alpha=0.3, axis="y")

        # Plot constraint violations
        constraints = result.get("constraints", {})
        violations = constraints.get("violations", {})
        if violations:
            violation_names = list(violations.keys())
            violation_values = list(violations.values())
            ax2.barh(violation_names, violation_values, color="#FF6B6B")
            ax2.set_xlabel("Penalty")
            ax2.set_ylabel("Constraint")
            ax2.set_title("Constraint Violations")
            ax2.grid(True, alpha=0.3, axis="x")
        else:
            ax2.text(0.5, 0.5, "No violations", ha="center", va="center")
            ax2.set_title("Constraint Violations")

        plt.tight_layout()

        if save_path:
            os.makedirs(
                os.path.dirname(save_path) if os.path.dirname(save_path) else ".",
                exist_ok=True,
            )
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            plt.close()
        else:
            plt.show()
