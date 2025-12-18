"""
Performance benchmarks for Turkish standards module
All operations must meet performance targets
"""

import pytest
from backend.core.turkish_standards import (
    TurkishBuildingClassifier,
    TurkishCostCalculator,
    TurkishComplianceChecker,
)
from shapely.geometry import box


class TestPerformanceBenchmarks:
    """Performance benchmark suite"""

    def test_bench_classify_building(self, benchmark):
        """Benchmark: Building classification
        Target: <1ms per call"""
        classifier = TurkishBuildingClassifier()

        result = benchmark(
            classifier.classify,
            "educational_university",
            5000,
            4,
        )

        # Verify result is correct
        assert result is not None
        # Benchmark will auto-report time

    def test_bench_get_class_info(self, benchmark):
        """Benchmark: Get class information
        Target: <1ms per call"""
        classifier = TurkishBuildingClassifier()
        from backend.core.turkish_standards import BuildingClass

        result = benchmark(
            classifier.get_class_info,
            BuildingClass.CLASS_V_A,
        )

        assert result is not None

    def test_bench_calculate_cost(self, benchmark):
        """Benchmark: Cost calculation
        Target: <5ms per call"""
        calculator = TurkishCostCalculator()

        result = benchmark(
            calculator.calculate_total_cost,
            "V-A",
            5000,
            4,
            "ankara",
            "standard",
        )

        assert result.total_tl > 0

    def test_bench_calculate_cost_with_factors(self, benchmark):
        """Benchmark: Cost calculation with location and quality factors
        Target: <5ms per call"""
        calculator = TurkishCostCalculator()

        result = benchmark(
            calculator.calculate_total_cost,
            "V-A",
            5000,
            4,
            "istanbul",
            "luxury",
        )

        assert result.total_tl > 0

    def test_bench_check_far(self, benchmark):
        """Benchmark: FAR compliance check
        Target: <2ms per call"""
        checker = TurkishComplianceChecker()

        result = benchmark(
            checker.check_far,
            1000,
            3,
            3000,
            "residential",
        )

        # Result can be None (compliant) or Violation

    def test_bench_check_setback(self, benchmark):
        """Benchmark: Setback compliance check
        Target: <3ms per call"""
        checker = TurkishComplianceChecker()

        building = box(10, 10, 40, 40)
        parcel = box(0, 0, 50, 50)

        result = benchmark(
            checker.check_setback,
            building,
            parcel,
        )

        assert isinstance(result, list)

    def test_bench_check_parking(self, benchmark):
        """Benchmark: Parking compliance check
        Target: <1ms per call"""
        checker = TurkishComplianceChecker()

        result = benchmark(
            checker.check_parking,
            5000,
            "residential",
            50,
        )

        # Result can be None (compliant) or Violation

    def test_bench_check_green_space(self, benchmark):
        """Benchmark: Green space compliance check
        Target: <1ms per call"""
        checker = TurkishComplianceChecker()

        result = benchmark(
            checker.check_green_space,
            20000,
            1000,
        )

        # Result can be None (compliant) or Violation

    def test_bench_full_compliance(self, benchmark):
        """Benchmark: Full compliance check
        Target: <10ms per call"""
        checker = TurkishComplianceChecker()

        building_data = {
            "area": 1000,
            "floors": 3,
            "type": "residential",
            "geometry": box(10, 10, 40, 40),
            "parking_spaces": 15,
        }
        parcel_data = {
            "area": 3000,
            "geometry": box(0, 0, 50, 50),
            "zone_type": "residential",
        }

        result = benchmark(
            checker.full_compliance_check,
            building_data,
            parcel_data,
        )

        assert result is not None

    def test_bench_batch_classification(self, benchmark):
        """Benchmark: Batch classification of 100 buildings
        Target: <100ms total"""
        classifier = TurkishBuildingClassifier()

        building_types = [
            "residential_low",
            "commercial_office",
            "educational_university",
            "health_hospital",
        ] * 25  # 100 buildings

        def classify_batch():
            return [classifier.classify(btype, 3000, 3) for btype in building_types]

        result = benchmark(classify_batch)
        assert len(result) == 100

    def test_bench_batch_cost_calculation(self, benchmark):
        """Benchmark: Batch cost calculation of 50 buildings
        Target: <250ms total"""
        calculator = TurkishCostCalculator()

        buildings = [
            ("V-A", 5000, 4, "ankara", "standard"),
            ("III-A", 3000, 3, "istanbul", "luxury"),
            ("V-B", 4000, 5, "izmir", "economy"),
        ] * 17  # 51 buildings

        def calculate_batch():
            return [
                calculator.calculate_total_cost(b[0], b[1], b[2], b[3], b[4])
                for b in buildings
            ]

        result = benchmark(calculate_batch)
        assert len(result) == 51

    def test_bench_compare_costs(self, benchmark):
        """Benchmark: Cost comparison
        Target: <10ms per call"""
        calculator = TurkishCostCalculator()

        result = benchmark(
            calculator.compare_costs,
            "III-A",
            "V-A",
            5000,
        )

        assert "difference_tl" in result
