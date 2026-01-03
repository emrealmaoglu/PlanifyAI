"""
Unit tests for Pareto front visualization.

Tests ParetoVisualizer and TradeOffAnalyzer classes.

Created: 2026-01-03
"""

import numpy as np
import pytest

from src.visualization.pareto_visualization import ParetoVisualizer, TradeOffAnalyzer

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_objectives_2d():
    """Sample 2D objectives for testing."""
    np.random.seed(42)
    # Generate 20 Pareto-like solutions
    x = np.linspace(0, 10, 20)
    y = 10 - x + np.random.randn(20) * 0.5
    return np.column_stack([x, y])


@pytest.fixture
def sample_objectives_3d():
    """Sample 3D objectives for testing."""
    np.random.seed(42)
    # Generate 30 Pareto-like solutions
    n = 30
    x = np.random.rand(n) * 10
    y = np.random.rand(n) * 10
    z = 20 - x - y + np.random.randn(n) * 0.5
    return np.column_stack([x, y, z])


@pytest.fixture
def sample_objectives_4d():
    """Sample 4D objectives for testing."""
    np.random.seed(42)
    n = 40
    return np.random.rand(n, 4) * 10


@pytest.fixture
def sample_convergence_history():
    """Sample convergence history."""
    return [
        {"generation": i, "hypervolume": 50 + i * 2, "diversity": 0.8 - i * 0.01} for i in range(50)
    ]


# =============================================================================
# PARETO VISUALIZER TESTS
# =============================================================================


class TestParetoVisualizer:
    """Test ParetoVisualizer class."""

    def test_initialization(self):
        """Test visualizer initialization."""
        visualizer = ParetoVisualizer(figsize=(12, 10), dpi=150)
        assert visualizer.figsize == (12, 10)
        assert visualizer.dpi == 150
        assert "pareto" in visualizer.colors
        assert "best" in visualizer.colors

    def test_plot_pareto_front_2d(self, sample_objectives_2d, tmp_path):
        """Test 2D Pareto front plotting."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "pareto_2d.png"

        fig = visualizer.plot_pareto_front_2d(
            sample_objectives_2d,
            obj_names=["Cost", "Walking Distance"],
            best_idx=10,
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_pareto_front_2d_invalid_dimensions(self, sample_objectives_3d):
        """Test 2D plot with invalid dimensions."""
        visualizer = ParetoVisualizer()

        with pytest.raises(ValueError, match="Expected 2 objectives"):
            visualizer.plot_pareto_front_2d(sample_objectives_3d, show=False)

    def test_plot_pareto_front_3d(self, sample_objectives_3d, tmp_path):
        """Test 3D Pareto front plotting."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "pareto_3d.png"

        fig = visualizer.plot_pareto_front_3d(
            sample_objectives_3d,
            obj_names=["Cost", "Walking", "Adjacency"],
            best_idx=15,
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_pareto_front_3d_invalid_dimensions(self, sample_objectives_2d):
        """Test 3D plot with invalid dimensions."""
        visualizer = ParetoVisualizer()

        with pytest.raises(ValueError, match="Expected 3 objectives"):
            visualizer.plot_pareto_front_3d(sample_objectives_2d, show=False)

    def test_plot_parallel_coordinates_2d(self, sample_objectives_2d, tmp_path):
        """Test parallel coordinates with 2 objectives."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "parallel_2d.png"

        fig = visualizer.plot_parallel_coordinates(
            sample_objectives_2d,
            obj_names=["Cost", "Walking"],
            best_idx=5,
            normalize=True,
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_parallel_coordinates_4d(self, sample_objectives_4d, tmp_path):
        """Test parallel coordinates with 4 objectives."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "parallel_4d.png"

        fig = visualizer.plot_parallel_coordinates(
            sample_objectives_4d,
            obj_names=["Cost", "Walking", "Adjacency", "Diversity"],
            best_idx=20,
            normalize=True,
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_parallel_coordinates_without_normalization(self, sample_objectives_3d, tmp_path):
        """Test parallel coordinates without normalization."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "parallel_no_norm.png"

        fig = visualizer.plot_parallel_coordinates(
            sample_objectives_3d, normalize=False, save_path=str(save_path), show=False
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_objective_matrix_2d(self, sample_objectives_2d, tmp_path):
        """Test objective trade-off matrix with 2 objectives."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "matrix_2d.png"

        fig = visualizer.plot_objective_matrix(
            sample_objectives_2d,
            obj_names=["Cost", "Walking"],
            best_idx=8,
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_objective_matrix_3d(self, sample_objectives_3d, tmp_path):
        """Test objective trade-off matrix with 3 objectives."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "matrix_3d.png"

        fig = visualizer.plot_objective_matrix(
            sample_objectives_3d,
            obj_names=["Cost", "Walking", "Adjacency"],
            best_idx=12,
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_convergence(self, sample_convergence_history, tmp_path):
        """Test convergence history plotting."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "convergence.png"

        fig = visualizer.plot_convergence(
            sample_convergence_history,
            metrics=["hypervolume", "diversity"],
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_convergence_single_metric(self, sample_convergence_history, tmp_path):
        """Test convergence plotting with single metric."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "convergence_single.png"

        fig = visualizer.plot_convergence(
            sample_convergence_history,
            metrics=["hypervolume"],
            save_path=str(save_path),
            show=False,
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_convergence_all_metrics(self, sample_convergence_history, tmp_path):
        """Test convergence plotting with all metrics."""
        visualizer = ParetoVisualizer()
        save_path = tmp_path / "convergence_all.png"

        fig = visualizer.plot_convergence(
            sample_convergence_history, metrics=None, save_path=str(save_path), show=False
        )

        assert fig is not None
        assert save_path.exists()

    def test_plot_convergence_empty_history(self):
        """Test convergence plotting with empty history."""
        visualizer = ParetoVisualizer()

        with pytest.raises(ValueError, match="Convergence history is empty"):
            visualizer.plot_convergence([], show=False)


# =============================================================================
# TRADE-OFF ANALYZER TESTS
# =============================================================================


class TestTradeOffAnalyzer:
    """Test TradeOffAnalyzer class."""

    def test_compute_statistics_2d(self, sample_objectives_2d):
        """Test statistics computation for 2D objectives."""
        stats = TradeOffAnalyzer.compute_statistics(sample_objectives_2d)

        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "std" in stats
        assert "median" in stats
        assert "range" in stats

        assert stats["min"].shape == (2,)
        assert stats["max"].shape == (2,)
        assert np.all(stats["min"] <= stats["max"])
        assert np.all(stats["range"] == stats["max"] - stats["min"])

    def test_compute_statistics_4d(self, sample_objectives_4d):
        """Test statistics computation for 4D objectives."""
        stats = TradeOffAnalyzer.compute_statistics(sample_objectives_4d)

        assert stats["min"].shape == (4,)
        assert stats["max"].shape == (4,)
        assert stats["mean"].shape == (4,)
        assert stats["std"].shape == (4,)
        assert stats["median"].shape == (4,)

    def test_compute_correlations_2d(self, sample_objectives_2d):
        """Test correlation computation for 2D objectives."""
        corr = TradeOffAnalyzer.compute_correlations(sample_objectives_2d)

        assert corr.shape == (2, 2)
        assert np.allclose(np.diag(corr), 1.0)  # Diagonal should be 1
        assert np.allclose(corr, corr.T)  # Should be symmetric
        assert np.all(np.abs(corr) <= 1.0)  # Correlations in [-1, 1]

    def test_compute_correlations_3d(self, sample_objectives_3d):
        """Test correlation computation for 3D objectives."""
        corr = TradeOffAnalyzer.compute_correlations(sample_objectives_3d)

        assert corr.shape == (3, 3)
        assert np.allclose(np.diag(corr), 1.0)
        assert np.allclose(corr, corr.T)

    def test_find_extreme_solutions_2d(self, sample_objectives_2d):
        """Test finding extreme solutions for 2D objectives."""
        extremes = TradeOffAnalyzer.find_extreme_solutions(sample_objectives_2d)

        assert "obj_0" in extremes
        assert "obj_1" in extremes

        # Check structure
        sol_idx_0, obj_values_0 = extremes["obj_0"]
        assert isinstance(sol_idx_0, int)
        assert obj_values_0.shape == (2,)

        # Check that these are actually minima
        assert obj_values_0[0] == np.min(sample_objectives_2d[:, 0])

    def test_find_extreme_solutions_4d(self, sample_objectives_4d):
        """Test finding extreme solutions for 4D objectives."""
        extremes = TradeOffAnalyzer.find_extreme_solutions(sample_objectives_4d)

        assert len(extremes) == 4
        for i in range(4):
            assert f"obj_{i}" in extremes
            sol_idx, obj_values = extremes[f"obj_{i}"]
            assert obj_values[i] == np.min(sample_objectives_4d[:, i])

    def test_compute_hypervolume_approximation_2d(self, sample_objectives_2d):
        """Test hypervolume approximation for 2D objectives."""
        hv = TradeOffAnalyzer.compute_hypervolume_approximation(sample_objectives_2d)

        assert isinstance(hv, float)
        assert hv >= 0

    def test_compute_hypervolume_approximation_with_reference(self, sample_objectives_2d):
        """Test hypervolume with custom reference point."""
        ref_point = np.array([15.0, 15.0])
        hv = TradeOffAnalyzer.compute_hypervolume_approximation(
            sample_objectives_2d, reference_point=ref_point
        )

        assert isinstance(hv, float)
        assert hv >= 0

    def test_compute_hypervolume_approximation_3d(self, sample_objectives_3d):
        """Test hypervolume approximation for 3D objectives."""
        hv = TradeOffAnalyzer.compute_hypervolume_approximation(sample_objectives_3d)

        assert isinstance(hv, float)
        assert hv >= 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestVisualizationIntegration:
    """Integration tests for visualization workflow."""

    def test_complete_visualization_workflow_2d(self, sample_objectives_2d, tmp_path):
        """Test complete workflow with 2D objectives."""
        visualizer = ParetoVisualizer()

        # Generate all plots
        fig1 = visualizer.plot_pareto_front_2d(
            sample_objectives_2d,
            obj_names=["Cost", "Walking"],
            best_idx=10,
            save_path=str(tmp_path / "2d.png"),
            show=False,
        )

        fig2 = visualizer.plot_parallel_coordinates(
            sample_objectives_2d,
            obj_names=["Cost", "Walking"],
            best_idx=10,
            save_path=str(tmp_path / "parallel.png"),
            show=False,
        )

        fig3 = visualizer.plot_objective_matrix(
            sample_objectives_2d,
            obj_names=["Cost", "Walking"],
            best_idx=10,
            save_path=str(tmp_path / "matrix.png"),
            show=False,
        )

        # Compute analytics
        stats = TradeOffAnalyzer.compute_statistics(sample_objectives_2d)
        corr = TradeOffAnalyzer.compute_correlations(sample_objectives_2d)
        extremes = TradeOffAnalyzer.find_extreme_solutions(sample_objectives_2d)
        hv = TradeOffAnalyzer.compute_hypervolume_approximation(sample_objectives_2d)

        # Verify everything worked
        assert fig1 is not None
        assert fig2 is not None
        assert fig3 is not None
        assert stats is not None
        assert corr is not None
        assert extremes is not None
        assert hv > 0

    def test_complete_visualization_workflow_3d(self, sample_objectives_3d, tmp_path):
        """Test complete workflow with 3D objectives."""
        visualizer = ParetoVisualizer()

        # Generate all plots
        fig1 = visualizer.plot_pareto_front_3d(
            sample_objectives_3d,
            obj_names=["Cost", "Walking", "Adjacency"],
            best_idx=15,
            save_path=str(tmp_path / "3d.png"),
            show=False,
        )

        fig2 = visualizer.plot_parallel_coordinates(
            sample_objectives_3d,
            obj_names=["Cost", "Walking", "Adjacency"],
            best_idx=15,
            save_path=str(tmp_path / "parallel.png"),
            show=False,
        )

        fig3 = visualizer.plot_objective_matrix(
            sample_objectives_3d,
            obj_names=["Cost", "Walking", "Adjacency"],
            best_idx=15,
            save_path=str(tmp_path / "matrix.png"),
            show=False,
        )

        # Compute analytics
        stats = TradeOffAnalyzer.compute_statistics(sample_objectives_3d)
        hv = TradeOffAnalyzer.compute_hypervolume_approximation(sample_objectives_3d)

        assert fig1 is not None
        assert fig2 is not None
        assert fig3 is not None
        assert stats["min"].shape == (3,)
        assert hv > 0
