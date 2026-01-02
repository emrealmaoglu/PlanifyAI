"""
Simplified Unit Tests for Compliance Checker
============================================

Focused tests for API validation and core functionality.

Created: 2026-01-01 (Week 4)
"""
from backend.core.regulatory.compliance_checker import (
    ComplianceChecker,
    ComplianceCitation,
    ComplianceReport,
    ComplianceSeverity,
    ComplianceViolation,
)


class TestComplianceCitation:
    """Tests for ComplianceCitation dataclass."""

    def test_citation_creation(self):
        """Test creating a compliance citation."""
        citation = ComplianceCitation(
            regulation="Yangın Yönetmeliği",
            article="42",
            clause="2",
            text="Test regulation text",
        )

        assert citation.regulation == "Yangın Yönetmeliği"
        assert citation.article == "42"
        assert citation.clause == "2"

    def test_citation_formatting(self):
        """Test citation format method."""
        citation = ComplianceCitation(
            regulation="PAIY",
            article="15",
            clause="3",
            text="...",
        )

        formatted = citation.format_citation()
        assert "PAIY" in formatted
        assert "15" in formatted


class TestComplianceViolation:
    """Tests for ComplianceViolation dataclass."""

    def test_violation_creation(self):
        """Test creating a violation."""
        citation = ComplianceCitation(regulation="Test", article="1", text="...")

        violation = ComplianceViolation(
            rule_name="Test Rule",
            severity=ComplianceSeverity.HIGH,
            citation=citation,
            affected_buildings=["B1"],
            explanation_tr="Türkçe",
            explanation_en="English",
        )

        assert violation.rule_name == "Test Rule"
        assert violation.severity == ComplianceSeverity.HIGH
        assert len(violation.affected_buildings) == 1

    def test_violation_to_dict(self):
        """Test to_dict conversion."""
        citation = ComplianceCitation(regulation="Test", article="1", text="...")

        violation = ComplianceViolation(
            rule_name="Test",
            severity=ComplianceSeverity.MEDIUM,
            citation=citation,
            affected_buildings=["B1"],
            explanation_tr="TR",
            explanation_en="EN",
        )

        result = violation.to_dict()

        assert "rule" in result
        assert "severity" in result
        assert "citation" in result


class TestComplianceReport:
    """Tests for ComplianceReport dataclass."""

    def test_report_creation(self):
        """Test creating a compliance report."""
        report = ComplianceReport(
            total_violations=2,
            violations_by_severity={"critical": 1, "high": 1},
            is_compliant=False,
            compliance_score=0.7,
            violations=[],
        )

        assert report.total_violations == 2
        assert report.is_compliant is False
        assert 0.0 <= report.compliance_score <= 1.0

    def test_report_to_dict(self):
        """Test report to_dict conversion."""
        report = ComplianceReport(
            total_violations=0,
            violations_by_severity={},
            is_compliant=True,
            compliance_score=1.0,
            violations=[],
        )

        result = report.to_dict()

        assert result["total_violations"] == 0
        assert result["is_compliant"] is True
        assert result["compliance_score"] == 1.0


class TestComplianceChecker:
    """Tests for ComplianceChecker class."""

    def test_initialization(self):
        """Test checker initialization."""
        checker = ComplianceChecker()
        assert checker.language == "tr"
        assert len(checker.violations) == 0

    def test_initialization_english(self):
        """Test checker initialization with English."""
        checker = ComplianceChecker(language="en")
        assert checker.language == "en"

    def test_check_all_runs(self):
        """Test that check_all runs without errors."""
        from shapely.geometry import Polygon

        from src.algorithms.building import Building, BuildingType

        checker = ComplianceChecker()

        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 2000, 5),
        ]

        site_params = {
            "area": 50000.0,
            "max_far": 1.5,
            "max_height": 21.0,
            "required_green_ratio": 0.30,
            "provided_parking_spaces": 100,
            "provided_green_area": 20000.0,
            "boundary": Polygon([(0, 0), (200, 0), (200, 250), (0, 250)]),
        }

        building_polygons = {
            "B1": Polygon([(50, 50), (70, 50), (70, 70), (50, 70)]),
        }

        violations = checker.check_all(buildings, site_params, building_polygons)

        assert isinstance(violations, list)

    def test_generate_report_empty_violations(self):
        """Test generating report with no violations."""
        checker = ComplianceChecker()
        checker.violations = []

        report = checker.generate_report()

        assert isinstance(report, ComplianceReport)
        assert report.total_violations == 0
        assert report.is_compliant is True
        assert report.compliance_score == 1.0

    def test_generate_report_with_violations(self):
        """Test generating report with violations."""
        checker = ComplianceChecker()

        citation = ComplianceCitation(regulation="Test", article="1", text="...")

        checker.violations = [
            ComplianceViolation(
                rule_name="Test1",
                severity=ComplianceSeverity.CRITICAL,
                citation=citation,
                affected_buildings=["B1"],
                explanation_tr="TR",
                explanation_en="EN",
            ),
            ComplianceViolation(
                rule_name="Test2",
                severity=ComplianceSeverity.MEDIUM,
                citation=citation,
                affected_buildings=["B2"],
                explanation_tr="TR",
                explanation_en="EN",
            ),
        ]

        report = checker.generate_report()

        assert report.total_violations == 2
        assert report.is_compliant is False
        assert 0.0 <= report.compliance_score < 1.0

    def test_compliance_score_calculation(self):
        """Test that compliance score decreases with violations."""
        checker = ComplianceChecker()
        citation = ComplianceCitation(regulation="Test", article="1", text="...")

        # No violations
        checker.violations = []
        report_none = checker.generate_report()

        # One medium violation
        checker.violations = [
            ComplianceViolation(
                rule_name="Test",
                severity=ComplianceSeverity.MEDIUM,
                citation=citation,
                affected_buildings=["B1"],
                explanation_tr="TR",
                explanation_en="EN",
            )
        ]
        report_medium = checker.generate_report()

        # One critical violation
        checker.violations = [
            ComplianceViolation(
                rule_name="Test",
                severity=ComplianceSeverity.CRITICAL,
                citation=citation,
                affected_buildings=["B1"],
                explanation_tr="TR",
                explanation_en="EN",
            )
        ]
        report_critical = checker.generate_report()

        # Score should decrease with severity
        assert report_none.compliance_score == 1.0
        assert report_medium.compliance_score < 1.0
        assert report_critical.compliance_score < report_medium.compliance_score
