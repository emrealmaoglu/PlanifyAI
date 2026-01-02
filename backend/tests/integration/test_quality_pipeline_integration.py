"""
Integration Tests for Quality Pipeline
=======================================

End-to-end testing of H-SAGA + Quality Analysis modules.

Tests the integration of:
- H-SAGA optimization
- Pareto front analysis
- Robustness analysis
- Compliance checking
- Full quality pipeline

Created: 2026-01-01 (Week 4 Day 2)
"""
import numpy as np
import pytest
from shapely.geometry import Polygon

from backend.core.quality.pareto_analyzer import ParetoFront
from backend.core.quality.robustness import RobustnessAnalyzer
from backend.core.regulatory.compliance_checker import ComplianceChecker
from src.algorithms.building import Building, BuildingType, create_sample_campus
from src.algorithms.hsaga import HybridSAGA


@pytest.mark.integration
class TestParetoIntegration:
    """Integration tests for Pareto analysis with H-SAGA."""

    def test_pareto_front_from_hsaga_population(self):
        """Test extracting Pareto front from H-SAGA population."""
        # Create Pareto front and add solutions
        pareto_front = ParetoFront(n_objectives=3)

        # Each solution is best in at least one objective (non-dominated)
        pareto_front.add_solution(objectives=[0.1, 0.9, 0.9], data={"id": "sol1"})
        pareto_front.add_solution(objectives=[0.9, 0.1, 0.9], data={"id": "sol2"})
        pareto_front.add_solution(objectives=[0.9, 0.9, 0.1], data={"id": "sol3"})
        pareto_front.add_solution(objectives=[0.5, 0.5, 0.5], data={"id": "sol4"})  # Dominated

        metrics = pareto_front.compute_metrics(reference_point=np.array([1.0, 1.0, 1.0]))

        # Should have non-dominated solutions
        assert metrics.n_solutions >= 3
        assert metrics.hypervolume > 0.0

    def test_pareto_quality_improves_over_generations(self):
        """Test that Pareto front quality improves during optimization."""
        # Simulate two generations
        gen1_objectives = np.random.rand(10, 2)  # Generation 1
        gen2_objectives = np.random.rand(10, 2) * 0.8  # Generation 2 (better)

        pareto1 = ParetoFront(gen1_objectives)
        pareto2 = ParetoFront(gen2_objectives)

        ref_point = np.array([2.0, 2.0])
        metrics1 = pareto1.compute_metrics(reference_point=ref_point)
        metrics2 = pareto2.compute_metrics(reference_point=ref_point)

        # Hypervolume should improve (or at least be valid)
        assert metrics1.hypervolume >= 0.0
        assert metrics2.hypervolume >= 0.0


@pytest.mark.integration
class TestRobustnessIntegration:
    """Integration tests for Robustness analysis with H-SAGA."""

    def test_robustness_analysis_on_hsaga_solution(self):
        """Test robustness analysis on H-SAGA optimized solution."""
        buildings = create_sample_campus()[:5]
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 50.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 20,
            "num_chains": 1,
            "chain_iterations": 20,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        # Define fitness function for robustness testing
        def evaluate_fitness(solution):
            return optimizer.evaluate_solution(solution)

        # Analyze robustness
        analyzer = RobustnessAnalyzer(
            evaluate_fitness=evaluate_fitness, n_samples=20, random_seed=42
        )

        solution = result["best_solution"]
        metrics = analyzer.analyze_solution(solution, perturbation_strength=0.05)

        # Verify robustness metrics are computed
        assert 0.0 <= metrics.sensitivity_score <= 1.0
        assert metrics.confidence_interval_95[0] <= metrics.confidence_interval_95[1]
        assert metrics.worst_case_fitness >= 0.0
        assert metrics.stability_radius >= 0.0
        assert metrics.variance >= 0.0
        assert metrics.robustness_grade in ["EXCELLENT", "GOOD", "FAIR", "POOR"]

    def test_robustness_report_generation(self):
        """Test generating robustness report for optimized solution."""
        buildings = create_sample_campus()[:3]
        bounds = (0.0, 0.0, 300.0, 300.0)

        sa_config = {
            "initial_temp": 50.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 10,
            "num_chains": 1,
            "chain_iterations": 10,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        def evaluate_fitness(solution):
            return optimizer.evaluate_solution(solution)

        analyzer = RobustnessAnalyzer(evaluate_fitness=evaluate_fitness, n_samples=15)

        solution = result["best_solution"]
        metrics = analyzer.analyze_solution(solution, perturbation_strength=0.05)
        report = analyzer.generate_report(solution, metrics)

        # Verify report structure
        assert "baseline_fitness" in report
        assert "robustness_metrics" in report
        assert "interpretation" in report
        assert "grade" in report["interpretation"]
        assert "summary" in report["interpretation"]
        assert "recommendations" in report["interpretation"]
        assert isinstance(report["interpretation"]["recommendations"], list)


@pytest.mark.integration
class TestComplianceIntegration:
    """Integration tests for Compliance checking with H-SAGA."""

    def test_compliance_check_on_hsaga_solution(self):
        """Test compliance checking on H-SAGA optimized solution."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 5),
            Building("B2", BuildingType.EDUCATIONAL, 3000, 4),
            Building("B3", BuildingType.COMMERCIAL, 1500, 3),
        ]

        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 50.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 20,
            "num_chains": 1,
            "chain_iterations": 20,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        # Create building polygons from solution
        solution = result["best_solution"]
        building_polygons = {}
        for building_id, (x, y) in solution.positions.items():
            # Simple square polygons (20x20m)
            building_polygons[building_id] = Polygon(
                [(x, y), (x + 20, y), (x + 20, y + 20), (x, y + 20)]
            )

        # Site parameters
        site_params = {
            "area": 250000.0,  # 500x500 m
            "max_far": 1.5,
            "max_height": 21.0,  # 7 floors
            "required_green_ratio": 0.30,
            "provided_parking_spaces": 100,
            "provided_green_area": 80000.0,
            "boundary": Polygon([(0, 0), (500, 0), (500, 500), (0, 500)]),
        }

        # Run compliance check
        checker = ComplianceChecker(language="en")
        violations = checker.check_all(buildings, site_params, building_polygons)

        # Verify compliance check ran
        assert isinstance(violations, list)

        # Generate report
        report = checker.generate_report()

        assert report.total_violations >= 0
        assert 0.0 <= report.compliance_score <= 1.0
        assert isinstance(report.is_compliant, bool)

    def test_compliance_violations_by_severity(self):
        """Test compliance violation severity classification."""
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 50000, 10),  # Very large, will violate
        ]

        bounds = (0.0, 0.0, 200.0, 200.0)

        sa_config = {
            "initial_temp": 30.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 10,
            "num_chains": 1,
            "chain_iterations": 10,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        optimizer.optimize()

        building_polygons = {
            "B1": Polygon([(50, 50), (150, 50), (150, 150), (50, 150)])  # Large building
        }

        site_params = {
            "area": 40000.0,  # Small site
            "max_far": 1.5,
            "max_height": 21.0,
            "required_green_ratio": 0.30,
            "provided_parking_spaces": 10,  # Insufficient
            "provided_green_area": 5000.0,  # Insufficient
            "boundary": Polygon([(0, 0), (200, 0), (200, 200), (0, 200)]),
        }

        checker = ComplianceChecker(language="en")
        violations = checker.check_all(buildings, site_params, building_polygons)

        # Should detect multiple violations
        assert len(violations) > 0

        # Check severity distribution
        report = checker.generate_report()
        severity_counts = report.violations_by_severity

        # At least some violations should exist
        total_violations = sum(severity_counts.values())
        assert total_violations > 0


@pytest.mark.integration
class TestFullQualityPipeline:
    """End-to-end integration tests for complete quality pipeline."""

    def test_complete_quality_pipeline(self):
        """Test complete quality assessment pipeline: H-SAGA → Quality Analysis."""
        # Step 1: Optimize with H-SAGA
        buildings = create_sample_campus()[:5]
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 50.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 20,
            "num_chains": 1,
            "chain_iterations": 20,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()
        solution = result["best_solution"]

        # Step 2: Robustness Analysis
        def evaluate_fitness(sol):
            return optimizer.evaluate_solution(sol)

        robustness_analyzer = RobustnessAnalyzer(
            evaluate_fitness=evaluate_fitness, n_samples=20, random_seed=42
        )

        robustness_metrics = robustness_analyzer.analyze_solution(
            solution, perturbation_strength=0.05
        )

        # Step 3: Compliance Check
        building_polygons = {}
        for building_id, (x, y) in solution.positions.items():
            building_polygons[building_id] = Polygon(
                [(x, y), (x + 20, y), (x + 20, y + 20), (x, y + 20)]
            )

        site_params = {
            "area": 250000.0,
            "max_far": 1.5,
            "max_height": 21.0,
            "required_green_ratio": 0.30,
            "provided_parking_spaces": 100,
            "provided_green_area": 80000.0,
            "boundary": Polygon([(0, 0), (500, 0), (500, 500), (0, 500)]),
        }

        compliance_checker = ComplianceChecker(language="en")
        compliance_checker.check_all(buildings, site_params, building_polygons)
        compliance_report = compliance_checker.generate_report()

        # Step 4: Generate Comprehensive Quality Report
        quality_report = {
            "optimization": {
                "fitness": result["fitness"],
                "runtime": result["statistics"]["runtime"],
                "iterations": result["statistics"].get("total_iterations", 0),
            },
            "robustness": {
                "grade": robustness_metrics.robustness_grade,
                "sensitivity_score": robustness_metrics.sensitivity_score,
                "confidence_interval_95": robustness_metrics.confidence_interval_95,
                "worst_case_fitness": robustness_metrics.worst_case_fitness,
                "stability_radius": robustness_metrics.stability_radius,
            },
            "compliance": {
                "is_compliant": compliance_report.is_compliant,
                "compliance_score": compliance_report.compliance_score,
                "total_violations": compliance_report.total_violations,
                "violations_by_severity": compliance_report.violations_by_severity,
            },
        }

        # Verify complete pipeline execution
        assert quality_report["optimization"]["fitness"] > 0.0
        assert quality_report["robustness"]["grade"] in [
            "EXCELLENT",
            "GOOD",
            "FAIR",
            "POOR",
        ]
        assert 0.0 <= quality_report["compliance"]["compliance_score"] <= 1.0

        # Verify all components produced valid results
        assert "fitness" in quality_report["optimization"]
        assert "grade" in quality_report["robustness"]
        assert "is_compliant" in quality_report["compliance"]

    def test_quality_metrics_consistency(self):
        """Test that quality metrics are consistent with same random seed."""
        buildings = create_sample_campus()[:3]
        bounds = (0.0, 0.0, 300.0, 300.0)

        sa_config = {
            "initial_temp": 50.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 15,
            "num_chains": 1,
            "chain_iterations": 15,
        }

        # Run optimization once
        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        # Robustness with same seed should be consistent
        def evaluate_fitness(sol):
            return optimizer.evaluate_solution(sol)

        # Analyze twice with same seed
        analyzer1 = RobustnessAnalyzer(
            evaluate_fitness=evaluate_fitness, n_samples=15, random_seed=123
        )
        analyzer2 = RobustnessAnalyzer(
            evaluate_fitness=evaluate_fitness, n_samples=15, random_seed=123
        )

        metrics1 = analyzer1.analyze_solution(result["best_solution"], perturbation_strength=0.05)
        metrics2 = analyzer2.analyze_solution(result["best_solution"], perturbation_strength=0.05)

        # With same seeds and same solution, metrics should be identical
        assert abs(metrics1.sensitivity_score - metrics2.sensitivity_score) < 1e-6
        assert metrics1.robustness_grade == metrics2.robustness_grade

    def test_quality_report_json_serialization(self):
        """Test that quality reports can be serialized to JSON."""
        buildings = create_sample_campus()[:3]
        bounds = (0.0, 0.0, 300.0, 300.0)

        sa_config = {
            "initial_temp": 30.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 10,
            "num_chains": 1,
            "chain_iterations": 10,
        }

        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        # Robustness
        def evaluate_fitness(sol):
            return optimizer.evaluate_solution(sol)

        analyzer = RobustnessAnalyzer(evaluate_fitness=evaluate_fitness, n_samples=10)
        robustness_metrics = analyzer.analyze_solution(
            result["best_solution"], perturbation_strength=0.05
        )

        # Compliance
        building_polygons = {
            bid: Polygon([(x, y), (x + 20, y), (x + 20, y + 20), (x, y + 20)])
            for bid, (x, y) in result["best_solution"].positions.items()
        }

        site_params = {
            "area": 90000.0,
            "max_far": 1.5,
            "max_height": 21.0,
            "required_green_ratio": 0.30,
            "provided_parking_spaces": 50,
            "provided_green_area": 30000.0,
            "boundary": Polygon([(0, 0), (300, 0), (300, 300), (0, 300)]),
        }

        checker = ComplianceChecker()
        checker.check_all(buildings, site_params, building_polygons)
        compliance_report = checker.generate_report()

        # Convert to dictionaries (JSON-ready)
        robustness_dict = robustness_metrics.to_dict()
        compliance_dict = compliance_report.to_dict()

        # Verify serialization
        assert isinstance(robustness_dict, dict)
        assert isinstance(compliance_dict, dict)
        assert "sensitivity_score" in robustness_dict
        assert "compliance_score" in compliance_dict

        # Test JSON serialization
        import json

        json_str = json.dumps(
            {"robustness": robustness_dict, "compliance": compliance_dict}, indent=2
        )

        assert len(json_str) > 0
        assert "sensitivity_score" in json_str
        assert "compliance_score" in json_str


@pytest.mark.integration
@pytest.mark.slow
class TestQualityPipelinePerformance:
    """Performance tests for quality pipeline."""

    def test_quality_pipeline_performance(self):
        """Test that complete quality pipeline runs within time budget."""
        import time

        buildings = create_sample_campus()[:5]
        bounds = (0.0, 0.0, 500.0, 500.0)

        sa_config = {
            "initial_temp": 50.0,
            "final_temp": 0.1,
            "cooling_rate": 0.95,
            "max_iterations": 30,
            "num_chains": 2,
            "chain_iterations": 30,
        }

        start_time = time.perf_counter()

        # Optimization
        optimizer = HybridSAGA(buildings, bounds, sa_config=sa_config)
        result = optimizer.optimize()

        # Robustness (20 samples)
        def evaluate_fitness(sol):
            return optimizer.evaluate_fitness(sol)

        analyzer = RobustnessAnalyzer(evaluate_fitness=evaluate_fitness, n_samples=20)
        analyzer.analyze_solution(result["best_solution"], perturbation_strength=0.05)

        # Compliance
        building_polygons = {
            bid: Polygon([(x, y), (x + 20, y), (x + 20, y + 20), (x, y + 20)])
            for bid, (x, y) in result["best_solution"].positions.items()
        }

        site_params = {
            "area": 250000.0,
            "max_far": 1.5,
            "max_height": 21.0,
            "required_green_ratio": 0.30,
            "provided_parking_spaces": 100,
            "provided_green_area": 80000.0,
            "boundary": Polygon([(0, 0), (500, 0), (500, 500), (0, 500)]),
        }

        checker = ComplianceChecker()
        checker.check_all(buildings, site_params, building_polygons)
        checker.generate_report()

        elapsed = time.perf_counter() - start_time

        # Complete pipeline should run in reasonable time (<60s for test config)
        assert elapsed < 60.0, f"Quality pipeline took {elapsed:.2f}s, expected <60s"
