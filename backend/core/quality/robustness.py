"""
Robustness Analysis for Campus Planning Solutions
==================================================

Quantifies solution sensitivity to parameter perturbations and uncertainty.

A robust solution maintains good performance under:
- Small parameter changes (building sizes, positions)
- Environmental variations (weather, usage patterns)
- Constraint relaxation/tightening

Key Metrics:
    - Sensitivity Score: Fitness change under perturbation
    - Confidence Interval: Performance bounds (Monte Carlo)
    - Worst-Case Analysis: Min-max robustness
    - Stability Radius: Max perturbation before constraint violation

References:
    - Beyer & Sendhoff (2007): Robust optimization
    - Jin & Branke (2005): Evolutionary optimization in uncertain environments
    - Taguchi (1986): Robust design methodology
    - Research: "Robustness Analysis Campus Planning.docx"

Created: 2026-01-01 (Week 3)
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class RobustnessMetrics:
    """
    Robustness quality indicators for a solution.

    Attributes:
        sensitivity_score: Mean fitness degradation under perturbation [0,1]
                          (lower = more robust)
        confidence_interval_95: (lower, upper) fitness bounds with 95% confidence
        worst_case_fitness: Minimum fitness observed in perturbation tests
        stability_radius: Maximum perturbation before constraint violation
        variance: Fitness variance under perturbations
        coefficient_of_variation: Std/Mean fitness (normalized stability)
    """

    sensitivity_score: float
    confidence_interval_95: Tuple[float, float]
    worst_case_fitness: float
    stability_radius: float
    variance: float
    coefficient_of_variation: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sensitivity_score": self.sensitivity_score,
            "confidence_interval_95": {
                "lower": self.confidence_interval_95[0],
                "upper": self.confidence_interval_95[1],
            },
            "worst_case_fitness": self.worst_case_fitness,
            "stability_radius": self.stability_radius,
            "variance": self.variance,
            "coefficient_of_variation": self.coefficient_of_variation,
            "robustness_grade": self.robustness_grade,
        }

    @property
    def robustness_grade(self) -> str:
        """
        Overall robustness grade based on sensitivity score.

        Returns:
            "EXCELLENT", "GOOD", "FAIR", "POOR"
        """
        if self.sensitivity_score < 0.05:
            return "EXCELLENT"  # < 5% degradation
        elif self.sensitivity_score < 0.15:
            return "GOOD"  # < 15% degradation
        elif self.sensitivity_score < 0.30:
            return "FAIR"  # < 30% degradation
        else:
            return "POOR"  # > 30% degradation


class RobustnessAnalyzer:
    """
    Analyzes solution robustness through perturbation testing.

    Usage:
        >>> analyzer = RobustnessAnalyzer(
        ...     evaluate_fitness=my_fitness_function,
        ...     n_samples=100
        ... )
        >>> metrics = analyzer.analyze_solution(
        ...     solution=best_solution,
        ...     perturbation_strength=0.05  # 5% noise
        ... )
        >>> print(f"Robustness: {metrics.robustness_grade}")
    """

    def __init__(
        self,
        evaluate_fitness: Callable[[Any], float],
        n_samples: int = 100,
        confidence_level: float = 0.95,
        random_seed: Optional[int] = None,
    ):
        """
        Initialize robustness analyzer.

        Args:
            evaluate_fitness: Function that evaluates solution fitness
            n_samples: Number of perturbation samples (Monte Carlo)
            confidence_level: Confidence level for intervals (default: 0.95)
            random_seed: Random seed for reproducibility
        """
        self.evaluate_fitness = evaluate_fitness
        self.n_samples = n_samples
        self.confidence_level = confidence_level
        self.rng = np.random.default_rng(random_seed)

    def analyze_solution(
        self,
        solution: Any,
        perturbation_strength: float = 0.05,
        perturbation_types: Optional[List[str]] = None,
    ) -> RobustnessMetrics:
        """
        Analyze solution robustness through Monte Carlo perturbation.

        Args:
            solution: Solution object to analyze
            perturbation_strength: Perturbation magnitude (0.05 = 5% noise)
            perturbation_types: Types of perturbations to apply
                               ["position", "size", "orientation"]

        Returns:
            RobustnessMetrics with sensitivity analysis results
        """
        if perturbation_types is None:
            perturbation_types = ["position", "size"]

        # Baseline fitness
        baseline_fitness = self.evaluate_fitness(solution)

        # Generate perturbed solutions
        perturbed_fitnesses = []

        for _ in range(self.n_samples):
            # Create perturbed copy
            perturbed = self._perturb_solution(solution, perturbation_strength, perturbation_types)

            # Evaluate
            fitness = self.evaluate_fitness(perturbed)
            perturbed_fitnesses.append(fitness)

        perturbed_fitnesses = np.array(perturbed_fitnesses)

        # Compute metrics
        sensitivity_score = self._compute_sensitivity(baseline_fitness, perturbed_fitnesses)

        ci_lower, ci_upper = self._compute_confidence_interval(
            perturbed_fitnesses, self.confidence_level
        )

        worst_case = np.min(perturbed_fitnesses)

        variance = np.var(perturbed_fitnesses)

        # Coefficient of variation (CV = std/mean)
        mean_fitness = np.mean(perturbed_fitnesses)
        cv = np.std(perturbed_fitnesses) / (mean_fitness + 1e-10)

        # Stability radius (max perturbation before failure)
        stability_radius = self._estimate_stability_radius(solution)

        return RobustnessMetrics(
            sensitivity_score=sensitivity_score,
            confidence_interval_95=(ci_lower, ci_upper),
            worst_case_fitness=worst_case,
            stability_radius=stability_radius,
            variance=variance,
            coefficient_of_variation=cv,
        )

    def _perturb_solution(
        self,
        solution: Any,
        strength: float,
        perturbation_types: List[str],
    ) -> Any:
        """
        Apply random perturbations to solution.

        Args:
            solution: Original solution
            strength: Perturbation magnitude
            perturbation_types: Types of perturbations

        Returns:
            Perturbed solution copy
        """
        # Create copy (assume solution has copy() method or is dict-like)
        if hasattr(solution, "copy"):
            perturbed = solution.copy()
        else:
            # Assume dict-like for positions
            perturbed = type(solution)(solution)

        # Apply perturbations
        if "position" in perturbation_types and hasattr(solution, "positions"):
            for building_id, (x, y) in solution.positions.items():
                # Gaussian noise
                noise_x = self.rng.normal(0, strength * 10.0)  # 10m base scale
                noise_y = self.rng.normal(0, strength * 10.0)

                perturbed.positions[building_id] = (x + noise_x, y + noise_y)

        if "size" in perturbation_types and hasattr(solution, "buildings"):
            # Perturb building sizes (if mutable)
            # This requires buildings to have mutable area/dimensions
            pass  # Implementation depends on solution structure

        if "orientation" in perturbation_types and hasattr(solution, "orientations"):
            for building_id in solution.orientations:
                noise_angle = self.rng.normal(0, strength * np.pi / 6)  # ~30deg
                perturbed.orientations[building_id] += noise_angle

        return perturbed

    def _compute_sensitivity(
        self,
        baseline: float,
        perturbed: np.ndarray,
    ) -> float:
        """
        Compute sensitivity score: mean fitness degradation.

        Args:
            baseline: Original fitness
            perturbed: Array of perturbed fitnesses

        Returns:
            Sensitivity score [0, 1] where 0 = perfectly robust
        """
        # Mean absolute deviation from baseline
        deviations = np.abs(perturbed - baseline)
        mean_deviation = np.mean(deviations)

        # Normalize by baseline (assuming fitness in [0, 1])
        sensitivity = mean_deviation / (baseline + 1e-10)

        return float(np.clip(sensitivity, 0.0, 1.0))

    def _compute_confidence_interval(
        self,
        samples: np.ndarray,
        confidence_level: float,
    ) -> Tuple[float, float]:
        """
        Compute confidence interval for fitness.

        Args:
            samples: Fitness samples
            confidence_level: Confidence level (0.95 = 95%)

        Returns:
            (lower_bound, upper_bound)
        """
        alpha = 1 - confidence_level
        lower = np.percentile(samples, 100 * alpha / 2)
        upper = np.percentile(samples, 100 * (1 - alpha / 2))

        return (float(lower), float(upper))

    def _estimate_stability_radius(self, solution: Any) -> float:
        """
        Estimate maximum perturbation before constraint violation.

        Uses binary search to find perturbation strength that causes failure.

        Args:
            solution: Solution to analyze

        Returns:
            Stability radius (perturbation strength at failure threshold)
        """
        # Binary search for failure threshold
        low, high = 0.0, 1.0  # Perturbation strength range
        threshold = 0.5  # Fitness drop threshold for "failure"

        baseline_fitness = self.evaluate_fitness(solution)

        for _ in range(10):  # Binary search iterations
            mid = (low + high) / 2

            # Test with mid perturbation
            perturbed = self._perturb_solution(solution, mid, ["position"])
            fitness = self.evaluate_fitness(perturbed)

            # Check if failed
            if fitness < baseline_fitness * threshold:
                # Too much perturbation, reduce
                high = mid
            else:
                # Still acceptable, increase
                low = mid

        return float(low)

    def compare_solutions(
        self,
        solutions: List[Any],
        perturbation_strength: float = 0.05,
    ) -> List[RobustnessMetrics]:
        """
        Compare robustness of multiple solutions.

        Args:
            solutions: List of solutions to compare
            perturbation_strength: Perturbation magnitude

        Returns:
            List of RobustnessMetrics, one per solution
        """
        return [self.analyze_solution(sol, perturbation_strength) for sol in solutions]

    def generate_report(
        self,
        solution: Any,
        metrics: RobustnessMetrics,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive robustness report.

        Args:
            solution: Analyzed solution
            metrics: Computed robustness metrics

        Returns:
            Dictionary with detailed analysis
        """
        baseline_fitness = self.evaluate_fitness(solution)

        return {
            "baseline_fitness": baseline_fitness,
            "robustness_metrics": metrics.to_dict(),
            "interpretation": {
                "grade": metrics.robustness_grade,
                "summary": self._interpret_robustness(metrics),
                "recommendations": self._generate_recommendations(metrics),
            },
            "confidence_interval_width": (
                metrics.confidence_interval_95[1] - metrics.confidence_interval_95[0]
            ),
            "relative_std": np.sqrt(metrics.variance) / (baseline_fitness + 1e-10),
        }

    def _interpret_robustness(self, metrics: RobustnessMetrics) -> str:
        """Generate human-readable interpretation."""
        grade = metrics.robustness_grade

        if grade == "EXCELLENT":
            return (
                "Solution is highly robust. Performance remains stable "
                "under parameter variations and environmental uncertainty."
            )
        elif grade == "GOOD":
            return (
                "Solution shows good robustness. Minor performance degradation "
                "under perturbations is expected but acceptable."
            )
        elif grade == "FAIR":
            return (
                "Solution has moderate robustness. Significant performance "
                "variations may occur under parameter changes."
            )
        else:  # POOR
            return (
                "Solution is fragile. Performance is highly sensitive to "
                "parameter variations. Consider alternative solutions."
            )

    def _generate_recommendations(self, metrics: RobustnessMetrics) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if metrics.sensitivity_score > 0.20:
            recommendations.append(
                "High sensitivity detected. Consider solutions with "
                "more conservative designs (larger safety margins)."
            )

        if metrics.coefficient_of_variation > 0.30:
            recommendations.append(
                "High variance in performance. Seek solutions with "
                "more uniform quality across perturbations."
            )

        if metrics.stability_radius < 0.10:
            recommendations.append(
                "Low stability radius. Solution is close to constraint "
                "boundaries. Add buffer zones or relax constraints."
            )

        if metrics.worst_case_fitness < 0.50:
            recommendations.append(
                "Worst-case performance is poor. For risk-averse scenarios, "
                "prefer solutions with higher worst-case guarantees."
            )

        if not recommendations:
            recommendations.append(
                "Solution demonstrates robust performance. " "No critical issues identified."
            )

        return recommendations
