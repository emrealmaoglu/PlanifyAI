"""
Pareto Front Visualization
===========================

Visualization tools for multi-objective optimization results.

Classes:
    ParetoVisualizer: Visualize Pareto fronts and objective trade-offs
    ObjectiveSpacePlotter: 2D/3D/parallel coordinate plots
    TradeOffAnalyzer: Interactive trade-off analysis

Created: 2026-01-03
"""

from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 - Required for 3D projection


class ParetoVisualizer:
    """
    Visualize Pareto fronts and multi-objective optimization results.

    Provides methods for plotting Pareto fronts in 2D, 3D, and parallel coordinates.

    Example:
        >>> visualizer = ParetoVisualizer()
        >>> visualizer.plot_pareto_front_2d(
        ...     objectives, obj_names=['Cost', 'Walking'],
        ...     save_path='pareto_2d.png'
        ... )
    """

    def __init__(self, figsize: Tuple[int, int] = (10, 8), dpi: int = 100):
        """
        Initialize Pareto visualizer.

        Args:
            figsize: Figure size (width, height)
            dpi: Dots per inch for saved figures
        """
        self.figsize = figsize
        self.dpi = dpi
        self.colors = {
            "pareto": "#2E86AB",
            "dominated": "#A23B72",
            "best": "#F18F01",
            "reference": "#C73E1D",
        }

    def plot_pareto_front_2d(
        self,
        objectives: np.ndarray,
        obj_names: Optional[List[str]] = None,
        best_idx: Optional[int] = None,
        title: str = "Pareto Front (2D)",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Figure:
        """
        Plot 2D Pareto front for 2 objectives.

        Args:
            objectives: Array of shape (n_solutions, 2) with objective values
            obj_names: Names of objectives (default: ['Obj 1', 'Obj 2'])
            best_idx: Index of best compromise solution
            title: Plot title
            save_path: Path to save figure
            show: Whether to show the plot

        Returns:
            Matplotlib figure object

        Raises:
            ValueError: If objectives is not 2D
        """
        if objectives.shape[1] != 2:
            raise ValueError(f"Expected 2 objectives, got {objectives.shape[1]}")

        if obj_names is None:
            obj_names = [f"Objective {i+1}" for i in range(2)]

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # Plot all solutions
        ax.scatter(
            objectives[:, 0],
            objectives[:, 1],
            c=self.colors["pareto"],
            s=100,
            alpha=0.7,
            label="Pareto Solutions",
            edgecolors="white",
            linewidth=1.5,
        )

        # Highlight best compromise
        if best_idx is not None:
            ax.scatter(
                objectives[best_idx, 0],
                objectives[best_idx, 1],
                c=self.colors["best"],
                s=300,
                marker="*",
                label="Best Compromise",
                edgecolors="black",
                linewidth=2,
                zorder=10,
            )

        # Connect points to show Pareto front
        sorted_idx = np.argsort(objectives[:, 0])
        ax.plot(
            objectives[sorted_idx, 0],
            objectives[sorted_idx, 1],
            c=self.colors["pareto"],
            alpha=0.3,
            linewidth=2,
            linestyle="--",
        )

        ax.set_xlabel(obj_names[0], fontsize=12, fontweight="bold")
        ax.set_ylabel(obj_names[1], fontsize=12, fontweight="bold")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
        ax.legend(fontsize=10, loc="best")
        ax.grid(True, alpha=0.3, linestyle="--")

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_pareto_front_3d(
        self,
        objectives: np.ndarray,
        obj_names: Optional[List[str]] = None,
        best_idx: Optional[int] = None,
        title: str = "Pareto Front (3D)",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Figure:
        """
        Plot 3D Pareto front for 3 objectives.

        Args:
            objectives: Array of shape (n_solutions, 3) with objective values
            obj_names: Names of objectives
            best_idx: Index of best compromise solution
            title: Plot title
            save_path: Path to save figure
            show: Whether to show the plot

        Returns:
            Matplotlib figure object

        Raises:
            ValueError: If objectives is not 3D
        """
        if objectives.shape[1] != 3:
            raise ValueError(f"Expected 3 objectives, got {objectives.shape[1]}")

        if obj_names is None:
            obj_names = [f"Objective {i+1}" for i in range(3)]

        fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        ax = fig.add_subplot(111, projection="3d")

        # Plot all solutions
        ax.scatter(
            objectives[:, 0],
            objectives[:, 1],
            objectives[:, 2],
            c=self.colors["pareto"],
            s=100,
            alpha=0.7,
            label="Pareto Solutions",
            edgecolors="white",
            linewidth=1.5,
        )

        # Highlight best compromise
        if best_idx is not None:
            ax.scatter(
                objectives[best_idx, 0],
                objectives[best_idx, 1],
                objectives[best_idx, 2],
                c=self.colors["best"],
                s=300,
                marker="*",
                label="Best Compromise",
                edgecolors="black",
                linewidth=2,
                zorder=10,
            )

        ax.set_xlabel(obj_names[0], fontsize=11, fontweight="bold", labelpad=10)
        ax.set_ylabel(obj_names[1], fontsize=11, fontweight="bold", labelpad=10)
        ax.set_zlabel(obj_names[2], fontsize=11, fontweight="bold", labelpad=10)
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
        ax.legend(fontsize=10, loc="best")

        # Set viewing angle
        ax.view_init(elev=20, azim=45)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_parallel_coordinates(
        self,
        objectives: np.ndarray,
        obj_names: Optional[List[str]] = None,
        best_idx: Optional[int] = None,
        normalize: bool = True,
        title: str = "Parallel Coordinates Plot",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Figure:
        """
        Plot parallel coordinates for N objectives.

        Args:
            objectives: Array of shape (n_solutions, n_objectives)
            obj_names: Names of objectives
            best_idx: Index of best compromise solution
            normalize: Whether to normalize objectives to [0, 1]
            title: Plot title
            save_path: Path to save figure
            show: Whether to show the plot

        Returns:
            Matplotlib figure object
        """
        n_solutions, n_objectives = objectives.shape

        if obj_names is None:
            obj_names = [f"Obj {i+1}" for i in range(n_objectives)]

        # Normalize objectives if requested
        data = objectives.copy()
        if normalize:
            obj_min = data.min(axis=0)
            obj_max = data.max(axis=0)
            obj_range = obj_max - obj_min
            obj_range[obj_range == 0] = 1.0  # Avoid division by zero
            data = (data - obj_min) / obj_range

        fig, ax = plt.subplots(figsize=(max(10, n_objectives * 2), 8), dpi=self.dpi)

        # Plot each solution
        x = np.arange(n_objectives)
        for i in range(n_solutions):
            if i == best_idx:
                # Highlight best solution
                ax.plot(
                    x,
                    data[i],
                    c=self.colors["best"],
                    linewidth=3,
                    alpha=1.0,
                    zorder=10,
                    label="Best Compromise",
                )
            else:
                ax.plot(x, data[i], c=self.colors["pareto"], linewidth=1.5, alpha=0.4)

        # Add objective names
        ax.set_xticks(x)
        ax.set_xticklabels(obj_names, fontsize=11, fontweight="bold", rotation=15)
        ax.set_ylabel("Normalized Value" if normalize else "Objective Value", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        if best_idx is not None:
            ax.legend(fontsize=10, loc="best")

        ax.grid(True, alpha=0.3, axis="y", linestyle="--")
        ax.set_ylim(-0.05, 1.05 if normalize else None)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_objective_matrix(
        self,
        objectives: np.ndarray,
        obj_names: Optional[List[str]] = None,
        best_idx: Optional[int] = None,
        title: str = "Objective Trade-off Matrix",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Figure:
        """
        Plot pairwise objective trade-offs in a matrix layout.

        Args:
            objectives: Array of shape (n_solutions, n_objectives)
            obj_names: Names of objectives
            best_idx: Index of best compromise solution
            title: Plot title
            save_path: Path to save figure
            show: Whether to show the plot

        Returns:
            Matplotlib figure object
        """
        n_objectives = objectives.shape[1]

        if obj_names is None:
            obj_names = [f"Obj {i+1}" for i in range(n_objectives)]

        fig, axes = plt.subplots(
            n_objectives,
            n_objectives,
            figsize=(3 * n_objectives, 3 * n_objectives),
            dpi=self.dpi,
        )

        # Handle single objective case
        if n_objectives == 1:
            axes = np.array([[axes]])

        for i in range(n_objectives):
            for j in range(n_objectives):
                ax = axes[i, j] if n_objectives > 1 else axes[0, 0]

                if i == j:
                    # Diagonal: histogram
                    ax.hist(
                        objectives[:, i],
                        bins=20,
                        color=self.colors["pareto"],
                        alpha=0.7,
                        edgecolor="white",
                    )
                    ax.set_ylabel("Frequency", fontsize=9)
                    if best_idx is not None:
                        ax.axvline(
                            objectives[best_idx, i],
                            color=self.colors["best"],
                            linewidth=2,
                            linestyle="--",
                        )
                else:
                    # Off-diagonal: scatter plot
                    ax.scatter(
                        objectives[:, j],
                        objectives[:, i],
                        c=self.colors["pareto"],
                        s=30,
                        alpha=0.6,
                    )
                    if best_idx is not None:
                        ax.scatter(
                            objectives[best_idx, j],
                            objectives[best_idx, i],
                            c=self.colors["best"],
                            s=100,
                            marker="*",
                            edgecolors="black",
                            linewidth=1,
                            zorder=10,
                        )

                # Labels
                if i == n_objectives - 1:
                    ax.set_xlabel(obj_names[j], fontsize=10, fontweight="bold")
                if j == 0:
                    ax.set_ylabel(obj_names[i], fontsize=10, fontweight="bold")

                ax.grid(True, alpha=0.2, linestyle="--")

        plt.suptitle(title, fontsize=16, fontweight="bold", y=0.995)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_convergence(
        self,
        convergence_history: List[Dict],
        metrics: Optional[List[str]] = None,
        title: str = "Convergence History",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Figure:
        """
        Plot convergence metrics over generations.

        Args:
            convergence_history: List of dicts with metrics per generation
            metrics: Metrics to plot (default: all available)
            title: Plot title
            save_path: Path to save figure
            show: Whether to show the plot

        Returns:
            Matplotlib figure object
        """
        if not convergence_history:
            raise ValueError("Convergence history is empty")

        # Extract available metrics
        available_metrics = list(convergence_history[0].keys())
        if "generation" in available_metrics:
            available_metrics.remove("generation")

        if metrics is None:
            metrics = available_metrics

        n_metrics = len(metrics)
        fig, axes = plt.subplots(
            n_metrics, 1, figsize=(self.figsize[0], 4 * n_metrics), dpi=self.dpi
        )

        if n_metrics == 1:
            axes = [axes]

        generations = [h.get("generation", i) for i, h in enumerate(convergence_history)]

        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            values = [h.get(metric, np.nan) for h in convergence_history]

            ax.plot(
                generations,
                values,
                linewidth=2.5,
                color=self.colors["pareto"],
                marker="o",
                markersize=4,
            )
            ax.set_xlabel("Generation", fontsize=11, fontweight="bold")
            ax.set_ylabel(metric.replace("_", " ").title(), fontsize=11, fontweight="bold")
            ax.grid(True, alpha=0.3, linestyle="--")

        plt.suptitle(title, fontsize=14, fontweight="bold", y=0.995)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")

        if show:
            plt.show()

        return fig


class TradeOffAnalyzer:
    """
    Analyze trade-offs between objectives in Pareto front.

    Provides statistical analysis and metrics for objective trade-offs.
    """

    @staticmethod
    def compute_statistics(objectives: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Compute statistics for each objective.

        Args:
            objectives: Array of shape (n_solutions, n_objectives)

        Returns:
            Dict with min, max, mean, std, median for each objective
        """
        return {
            "min": np.min(objectives, axis=0),
            "max": np.max(objectives, axis=0),
            "mean": np.mean(objectives, axis=0),
            "std": np.std(objectives, axis=0),
            "median": np.median(objectives, axis=0),
            "range": np.ptp(objectives, axis=0),
        }

    @staticmethod
    def compute_correlations(objectives: np.ndarray) -> np.ndarray:
        """
        Compute pairwise correlations between objectives.

        Args:
            objectives: Array of shape (n_solutions, n_objectives)

        Returns:
            Correlation matrix of shape (n_objectives, n_objectives)
        """
        return np.corrcoef(objectives.T)

    @staticmethod
    def find_extreme_solutions(
        objectives: np.ndarray,
    ) -> Dict[str, Tuple[int, np.ndarray]]:
        """
        Find solutions that minimize each objective.

        Args:
            objectives: Array of shape (n_solutions, n_objectives)

        Returns:
            Dict mapping objective index to (solution_index, objective_values)
        """
        n_objectives = objectives.shape[1]
        extremes = {}

        for obj_idx in range(n_objectives):
            sol_idx = np.argmin(objectives[:, obj_idx])
            extremes[f"obj_{obj_idx}"] = (int(sol_idx), objectives[sol_idx])

        return extremes

    @staticmethod
    def compute_hypervolume_approximation(
        objectives: np.ndarray, reference_point: Optional[np.ndarray] = None
    ) -> float:
        """
        Approximate hypervolume indicator (simplified version).

        Args:
            objectives: Array of shape (n_solutions, n_objectives)
            reference_point: Reference point (default: 1.1 * max for each objective)

        Returns:
            Approximate hypervolume value
        """
        if reference_point is None:
            reference_point = 1.1 * np.max(objectives, axis=0)

        # Simple approximation: sum of dominated rectangles
        # Sort by first objective
        sorted_idx = np.argsort(objectives[:, 0])
        sorted_obj = objectives[sorted_idx]

        volume = 0.0
        prev_point = reference_point.copy()

        for point in sorted_obj:
            # Check if point is dominated by reference point
            if np.all(point <= reference_point):
                # Compute rectangle volume
                rect_volume = np.prod(prev_point - point)
                volume += rect_volume
                prev_point = point.copy()

        return volume
