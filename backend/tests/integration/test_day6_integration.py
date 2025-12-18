"""
End-to-end integration tests for Day 6 features.

Tests the complete pipeline: data loading -> optimization -> export -> visualization.

Created: 2025-11-09
"""

import tempfile
from pathlib import Path

import pytest

from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA
from src.constraints.spatial_constraints import (
    ConstraintManager,
    CoverageRatioConstraint,
    FloorAreaRatioConstraint,
    SetbackConstraint,
)
from src.data.export import ResultExporter
from src.data.parser import CampusDataParser
from src.visualization.plot_utils import CampusPlotter


@pytest.fixture
def sample_campus_dict():
    """Create a sample campus dictionary for testing."""
    return {
        "name": "Test Campus",
        "location": "Istanbul, Turkey",
        "boundary": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]],
        },
        "existing_buildings": [],
        "constraints": {
            "setback_from_boundary": 10.0,
            "coverage_ratio_max": 0.3,
            "far_max": 2.0,
            "min_green_space_ratio": 0.4,
        },
        "metadata": {
            "total_area_m2": 1000000,
            "student_count": 5000,
            "established": 2020,
        },
    }


@pytest.fixture
def sample_buildings():
    """Create sample buildings for testing."""
    return [
        Building(id="B1", type=BuildingType.EDUCATIONAL, area=500, floors=2),
        Building(id="B2", type=BuildingType.LIBRARY, area=800, floors=3),
        Building(id="B3", type=BuildingType.RESIDENTIAL, area=600, floors=2),
        Building(id="B4", type=BuildingType.COMMERCIAL, area=400, floors=2),
        Building(id="B5", type=BuildingType.DINING, area=300, floors=1),
    ]


class TestFullPipeline:
    """Test complete pipeline with campus data."""

    def test_full_pipeline_with_dict(self, sample_campus_dict, sample_buildings):
        """Test full pipeline with dictionary data."""
        # 1. Parse campus data
        campus = CampusDataParser.from_dict(sample_campus_dict)

        # 2. Create constraints
        constraints = ConstraintManager()
        constraints.add_constraint(
            SetbackConstraint(setback_distance=campus.constraints["setback_from_boundary"])
        )
        constraints.add_constraint(
            CoverageRatioConstraint(max_coverage_ratio=campus.constraints["coverage_ratio_max"])
        )
        constraints.add_constraint(FloorAreaRatioConstraint(max_far=campus.constraints["far_max"]))

        # 3. Run optimization
        bounds = campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=campus,
            constraint_manager=constraints,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        # 4. Validate results
        assert result["fitness"] > 0
        assert "constraints" in result
        assert "best_solution" in result

        # 5. Test export
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export GeoJSON
            geojson_path = Path(tmpdir) / "solution.geojson"
            ResultExporter.to_geojson(result["best_solution"], campus, str(geojson_path))
            assert geojson_path.exists()

            # Export CSV
            csv_path = Path(tmpdir) / "solution.csv"
            ResultExporter.to_csv(result["best_solution"], str(csv_path))
            assert csv_path.exists()

            # Export JSON
            json_path = Path(tmpdir) / "result.json"
            ResultExporter.to_json(result, str(json_path))
            assert json_path.exists()

            # Export report
            report_path = Path(tmpdir) / "report.md"
            ResultExporter.generate_report(result, str(report_path))
            assert report_path.exists()

    def test_full_pipeline_with_real_campus(self, sample_buildings):
        """Test full pipeline with real campus data file."""
        # Check if campus data file exists
        campus_file = Path("data/campuses/bogazici_university.json")
        if not campus_file.exists():
            pytest.skip("Campus data file not found")

        # 1. Load campus data
        campus = CampusDataParser.from_geojson(str(campus_file))

        # 2. Create constraints
        constraints = ConstraintManager()
        if "setback_from_boundary" in campus.constraints:
            constraints.add_constraint(
                SetbackConstraint(setback_distance=campus.constraints["setback_from_boundary"])
            )
        if "coverage_ratio_max" in campus.constraints:
            constraints.add_constraint(
                CoverageRatioConstraint(max_coverage_ratio=campus.constraints["coverage_ratio_max"])
            )

        # 3. Run optimization
        bounds = campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings[:3],  # Use fewer buildings for speed
            bounds=bounds,
            campus_data=campus,
            constraint_manager=constraints,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        # 4. Validate results
        assert result["fitness"] > 0
        assert "constraints" in result

    def test_constraint_satisfaction_validation(self, sample_campus_dict, sample_buildings):
        """Test constraint satisfaction validation."""
        # Parse campus data
        campus = CampusDataParser.from_dict(sample_campus_dict)

        # Create constraints
        constraints = ConstraintManager()
        constraints.add_constraint(
            SetbackConstraint(setback_distance=campus.constraints["setback_from_boundary"])
        )
        constraints.add_constraint(
            CoverageRatioConstraint(max_coverage_ratio=campus.constraints["coverage_ratio_max"])
        )

        # Run optimization
        bounds = campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=campus,
            constraint_manager=constraints,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        # Check constraint information
        assert "constraints" in result
        assert "satisfied" in result["constraints"]
        assert "penalty" in result["constraints"]
        assert result["constraints"]["penalty"] >= 0.0

    def test_export_functionality(self, sample_campus_dict, sample_buildings):
        """Test export functionality."""
        # Parse campus data
        campus = CampusDataParser.from_dict(sample_campus_dict)

        # Run optimization
        bounds = campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=campus,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        # Test all export methods
        with tempfile.TemporaryDirectory() as tmpdir:
            # GeoJSON
            geojson_path = Path(tmpdir) / "test.geojson"
            ResultExporter.to_geojson(result["best_solution"], campus, str(geojson_path))
            assert geojson_path.exists()

            # CSV
            csv_path = Path(tmpdir) / "test.csv"
            ResultExporter.to_csv(result["best_solution"], str(csv_path))
            assert csv_path.exists()

            # JSON
            json_path = Path(tmpdir) / "test.json"
            ResultExporter.to_json(result, str(json_path))
            assert json_path.exists()

            # Report
            report_path = Path(tmpdir) / "test.md"
            ResultExporter.generate_report(result, str(report_path))
            assert report_path.exists()

    def test_visualization_generation(self, sample_campus_dict, sample_buildings):
        """Test visualization generation."""
        # Parse campus data
        campus = CampusDataParser.from_dict(sample_campus_dict)

        # Run optimization
        bounds = campus.get_bounds()
        optimizer = HybridSAGA(
            buildings=sample_buildings,
            bounds=bounds,
            campus_data=campus,
            sa_config={
                "initial_temp": 1000.0,
                "final_temp": 0.1,
                "cooling_rate": 0.95,
                "max_iterations": 10,
                "num_chains": 1,
                "chain_iterations": 10,
            },
            ga_config={
                "population_size": 10,
                "generations": 5,
                "crossover_rate": 0.8,
                "mutation_rate": 0.15,
                "elite_size": 2,
                "tournament_size": 3,
            },
        )

        result = optimizer.optimize()

        # Test visualization
        plotter = CampusPlotter(campus)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Plot solution
            solution_path = Path(tmpdir) / "solution.png"
            plotter.plot_solution(
                result["best_solution"],
                buildings=sample_buildings,
                save_path=str(solution_path),
            )
            assert solution_path.exists()

            # Plot convergence
            convergence_path = Path(tmpdir) / "convergence.png"
            plotter.plot_convergence(result, save_path=str(convergence_path))
            assert convergence_path.exists()

            # Plot objectives
            objectives_path = Path(tmpdir) / "objectives.png"
            plotter.plot_objectives(result, save_path=str(objectives_path))
            assert objectives_path.exists()
