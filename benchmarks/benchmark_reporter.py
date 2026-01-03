"""
Benchmark Reporter
==================

Generates reports and visualizations from benchmark results.

Report Components:
    - Statistical summary tables
    - Convergence plots
    - Performance comparison charts
    - Trade-off analysis
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

from .benchmark_runner import BenchmarkResult


class BenchmarkReporter:
    """
    Generate reports and visualizations from benchmark results.
    """

    def __init__(self, results: List[BenchmarkResult], output_dir: str = "benchmarks/reports"):
        """
        Initialize reporter.

        Args:
            results: List of benchmark results
            output_dir: Output directory for reports
        """
        self.results = results
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compute_statistics(self) -> Dict:
        """
        Compute statistical summary of results.

        Returns:
            Dictionary with statistics per algorithm and test case
        """
        stats = {}

        # Group by algorithm and test case
        for result in self.results:
            key = (result.algorithm, result.test_case_name)
            if key not in stats:
                stats[key] = {
                    "runtimes": [],
                    "evaluations": [],
                    "pareto_sizes": [],
                    "hypervolumes": [],
                    "memory_peaks": [],
                }

            stats[key]["runtimes"].append(result.runtime)
            stats[key]["evaluations"].append(result.evaluations)
            stats[key]["pareto_sizes"].append(result.pareto_size)
            stats[key]["hypervolumes"].append(result.hypervolume)
            stats[key]["memory_peaks"].append(result.memory_peak_mb)

        # Compute mean, std, min, max for each metric
        summary = {}
        for key, data in stats.items():
            algorithm, test_case = key
            if algorithm not in summary:
                summary[algorithm] = {}

            summary[algorithm][test_case] = {
                "runtime": {
                    "mean": np.mean(data["runtimes"]),
                    "std": np.std(data["runtimes"]),
                    "min": np.min(data["runtimes"]),
                    "max": np.max(data["runtimes"]),
                },
                "evaluations": {
                    "mean": np.mean(data["evaluations"]),
                    "std": np.std(data["evaluations"]),
                    "min": np.min(data["evaluations"]),
                    "max": np.max(data["evaluations"]),
                },
                "pareto_size": {
                    "mean": np.mean(data["pareto_sizes"]),
                    "std": np.std(data["pareto_sizes"]),
                    "min": np.min(data["pareto_sizes"]),
                    "max": np.max(data["pareto_sizes"]),
                },
                "hypervolume": {
                    "mean": np.mean(data["hypervolumes"]),
                    "std": np.std(data["hypervolumes"]),
                    "min": np.min(data["hypervolumes"]),
                    "max": np.max(data["hypervolumes"]),
                },
                "memory_peak_mb": {
                    "mean": np.mean(data["memory_peaks"]),
                    "std": np.std(data["memory_peaks"]),
                    "min": np.min(data["memory_peaks"]),
                    "max": np.max(data["memory_peaks"]),
                },
            }

        return summary

    def generate_summary_report(self) -> str:
        """
        Generate text summary report.

        Returns:
            Report as string
        """
        stats = self.compute_statistics()

        report = []
        report.append("=" * 80)
        report.append("BENCHMARK SUMMARY REPORT")
        report.append("=" * 80)
        report.append("")

        # Get all test cases
        test_cases = set()
        for algo_stats in stats.values():
            test_cases.update(algo_stats.keys())
        test_cases = sorted(test_cases)

        for test_case in test_cases:
            report.append(f"\nTest Case: {test_case}")
            report.append("-" * 80)

            for algorithm in ["NSGA-III", "AdaptiveHSAGA"]:
                if algorithm not in stats or test_case not in stats[algorithm]:
                    continue

                tc_stats = stats[algorithm][test_case]
                report.append(f"\n[{algorithm}]")

                # Runtime
                rt = tc_stats["runtime"]
                report.append(
                    f"  Runtime:      {rt['mean']:8.2f}s ± {rt['std']:6.2f}s "
                    f"(min={rt['min']:6.2f}s, max={rt['max']:6.2f}s)"
                )

                # Evaluations
                ev = tc_stats["evaluations"]
                report.append(
                    f"  Evaluations:  {ev['mean']:8.0f} ± {ev['std']:6.0f} "
                    f"(min={ev['min']:6.0f}, max={ev['max']:6.0f})"
                )

                # Pareto size
                ps = tc_stats["pareto_size"]
                report.append(
                    f"  Pareto Size:  {ps['mean']:8.1f} ± {ps['std']:6.1f} "
                    f"(min={ps['min']:6.0f}, max={ps['max']:6.0f})"
                )

                # Hypervolume
                hv = tc_stats["hypervolume"]
                report.append(
                    f"  Hypervolume:  {hv['mean']:8.2f} ± {hv['std']:6.2f} "
                    f"(min={hv['min']:6.2f}, max={hv['max']:6.2f})"
                )

                # Memory
                mem = tc_stats["memory_peak_mb"]
                report.append(
                    f"  Memory Peak:  {mem['mean']:8.2f}MB ± {mem['std']:6.2f}MB "
                    f"(min={mem['min']:6.2f}MB, max={mem['max']:6.2f}MB)"
                )

            # Comparison
            if "NSGA-III" in stats and "AdaptiveHSAGA" in stats:
                if test_case in stats["NSGA-III"] and test_case in stats["AdaptiveHSAGA"]:
                    nsga3_stats = stats["NSGA-III"][test_case]
                    hsaga_stats = stats["AdaptiveHSAGA"][test_case]

                    report.append("\n[Comparison]")

                    # Runtime speedup
                    rt_ratio = hsaga_stats["runtime"]["mean"] / nsga3_stats["runtime"]["mean"]
                    if rt_ratio > 1:
                        report.append(f"  NSGA-III is {rt_ratio:.2f}x faster than AdaptiveHSAGA")
                    else:
                        report.append(f"  AdaptiveHSAGA is {1/rt_ratio:.2f}x faster than NSGA-III")

                    # Hypervolume quality
                    hv_ratio = (
                        nsga3_stats["hypervolume"]["mean"] / hsaga_stats["hypervolume"]["mean"]
                    )
                    if hv_ratio > 1:
                        report.append(
                            f"  NSGA-III achieves {hv_ratio:.2f}x better hypervolume "
                            f"than AdaptiveHSAGA"
                        )
                    else:
                        report.append(
                            f"  AdaptiveHSAGA achieves {1/hv_ratio:.2f}x better hypervolume "
                            f"than NSGA-III"
                        )

        report.append("\n" + "=" * 80)
        return "\n".join(report)

    def plot_runtime_comparison(self, save_path: Optional[str] = None):
        """
        Plot runtime comparison across test cases.

        Args:
            save_path: Optional path to save figure
        """
        stats = self.compute_statistics()

        # Get test cases
        test_cases = set()
        for algo_stats in stats.values():
            test_cases.update(algo_stats.keys())
        test_cases = sorted(test_cases)

        # Extract data
        nsga3_runtimes = []
        hsaga_runtimes = []
        nsga3_stds = []
        hsaga_stds = []

        for tc in test_cases:
            if "NSGA-III" in stats and tc in stats["NSGA-III"]:
                nsga3_runtimes.append(stats["NSGA-III"][tc]["runtime"]["mean"])
                nsga3_stds.append(stats["NSGA-III"][tc]["runtime"]["std"])
            else:
                nsga3_runtimes.append(0)
                nsga3_stds.append(0)

            if "AdaptiveHSAGA" in stats and tc in stats["AdaptiveHSAGA"]:
                hsaga_runtimes.append(stats["AdaptiveHSAGA"][tc]["runtime"]["mean"])
                hsaga_stds.append(stats["AdaptiveHSAGA"][tc]["runtime"]["std"])
            else:
                hsaga_runtimes.append(0)
                hsaga_stds.append(0)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(test_cases))
        width = 0.35

        ax.bar(
            x - width / 2,
            nsga3_runtimes,
            width,
            yerr=nsga3_stds,
            label="NSGA-III",
            capsize=5,
            color="#3498db",
        )
        ax.bar(
            x + width / 2,
            hsaga_runtimes,
            width,
            yerr=hsaga_stds,
            label="AdaptiveHSAGA",
            capsize=5,
            color="#e74c3c",
        )

        ax.set_xlabel("Test Case", fontsize=12, fontweight="bold")
        ax.set_ylabel("Runtime (seconds)", fontsize=12, fontweight="bold")
        ax.set_title("Runtime Comparison Across Test Cases", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(test_cases, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Saved runtime comparison to {save_path}")
        else:
            plt.savefig(self.output_dir / "runtime_comparison.png", dpi=150, bbox_inches="tight")

        plt.close()

    def plot_hypervolume_comparison(self, save_path: Optional[str] = None):
        """
        Plot hypervolume comparison across test cases.

        Args:
            save_path: Optional path to save figure
        """
        stats = self.compute_statistics()

        # Get test cases
        test_cases = set()
        for algo_stats in stats.values():
            test_cases.update(algo_stats.keys())
        test_cases = sorted(test_cases)

        # Extract data
        nsga3_hvs = []
        hsaga_hvs = []
        nsga3_stds = []
        hsaga_stds = []

        for tc in test_cases:
            if "NSGA-III" in stats and tc in stats["NSGA-III"]:
                nsga3_hvs.append(stats["NSGA-III"][tc]["hypervolume"]["mean"])
                nsga3_stds.append(stats["NSGA-III"][tc]["hypervolume"]["std"])
            else:
                nsga3_hvs.append(0)
                nsga3_stds.append(0)

            if "AdaptiveHSAGA" in stats and tc in stats["AdaptiveHSAGA"]:
                hsaga_hvs.append(stats["AdaptiveHSAGA"][tc]["hypervolume"]["mean"])
                hsaga_stds.append(stats["AdaptiveHSAGA"][tc]["hypervolume"]["std"])
            else:
                hsaga_hvs.append(0)
                hsaga_stds.append(0)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(test_cases))
        width = 0.35

        ax.bar(
            x - width / 2,
            nsga3_hvs,
            width,
            yerr=nsga3_stds,
            label="NSGA-III",
            capsize=5,
            color="#2ecc71",
        )
        ax.bar(
            x + width / 2,
            hsaga_hvs,
            width,
            yerr=hsaga_stds,
            label="AdaptiveHSAGA",
            capsize=5,
            color="#f39c12",
        )

        ax.set_xlabel("Test Case", fontsize=12, fontweight="bold")
        ax.set_ylabel("Hypervolume", fontsize=12, fontweight="bold")
        ax.set_title("Hypervolume Comparison Across Test Cases", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(test_cases, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Saved hypervolume comparison to {save_path}")
        else:
            plt.savefig(
                self.output_dir / "hypervolume_comparison.png", dpi=150, bbox_inches="tight"
            )

        plt.close()

    def plot_pareto_size_comparison(self, save_path: Optional[str] = None):
        """
        Plot Pareto front size comparison.

        Args:
            save_path: Optional path to save figure
        """
        stats = self.compute_statistics()

        # Get test cases
        test_cases = set()
        for algo_stats in stats.values():
            test_cases.update(algo_stats.keys())
        test_cases = sorted(test_cases)

        # Extract data
        nsga3_sizes = []
        hsaga_sizes = []
        nsga3_stds = []
        hsaga_stds = []

        for tc in test_cases:
            if "NSGA-III" in stats and tc in stats["NSGA-III"]:
                nsga3_sizes.append(stats["NSGA-III"][tc]["pareto_size"]["mean"])
                nsga3_stds.append(stats["NSGA-III"][tc]["pareto_size"]["std"])
            else:
                nsga3_sizes.append(0)
                nsga3_stds.append(0)

            if "AdaptiveHSAGA" in stats and tc in stats["AdaptiveHSAGA"]:
                hsaga_sizes.append(stats["AdaptiveHSAGA"][tc]["pareto_size"]["mean"])
                hsaga_stds.append(stats["AdaptiveHSAGA"][tc]["pareto_size"]["std"])
            else:
                hsaga_sizes.append(0)
                hsaga_stds.append(0)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(test_cases))
        width = 0.35

        ax.bar(
            x - width / 2,
            nsga3_sizes,
            width,
            yerr=nsga3_stds,
            label="NSGA-III",
            capsize=5,
            color="#9b59b6",
        )
        ax.bar(
            x + width / 2,
            hsaga_sizes,
            width,
            yerr=hsaga_stds,
            label="AdaptiveHSAGA",
            capsize=5,
            color="#1abc9c",
        )

        ax.set_xlabel("Test Case", fontsize=12, fontweight="bold")
        ax.set_ylabel("Pareto Front Size", fontsize=12, fontweight="bold")
        ax.set_title("Pareto Front Size Comparison", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(test_cases, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Saved Pareto size comparison to {save_path}")
        else:
            plt.savefig(
                self.output_dir / "pareto_size_comparison.png", dpi=150, bbox_inches="tight"
            )

        plt.close()

    def plot_memory_comparison(self, save_path: Optional[str] = None):
        """
        Plot memory usage comparison.

        Args:
            save_path: Optional path to save figure
        """
        stats = self.compute_statistics()

        # Get test cases
        test_cases = set()
        for algo_stats in stats.values():
            test_cases.update(algo_stats.keys())
        test_cases = sorted(test_cases)

        # Extract data
        nsga3_mems = []
        hsaga_mems = []
        nsga3_stds = []
        hsaga_stds = []

        for tc in test_cases:
            if "NSGA-III" in stats and tc in stats["NSGA-III"]:
                nsga3_mems.append(stats["NSGA-III"][tc]["memory_peak_mb"]["mean"])
                nsga3_stds.append(stats["NSGA-III"][tc]["memory_peak_mb"]["std"])
            else:
                nsga3_mems.append(0)
                nsga3_stds.append(0)

            if "AdaptiveHSAGA" in stats and tc in stats["AdaptiveHSAGA"]:
                hsaga_mems.append(stats["AdaptiveHSAGA"][tc]["memory_peak_mb"]["mean"])
                hsaga_stds.append(stats["AdaptiveHSAGA"][tc]["memory_peak_mb"]["std"])
            else:
                hsaga_mems.append(0)
                hsaga_stds.append(0)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(test_cases))
        width = 0.35

        ax.bar(
            x - width / 2,
            nsga3_mems,
            width,
            yerr=nsga3_stds,
            label="NSGA-III",
            capsize=5,
            color="#e67e22",
        )
        ax.bar(
            x + width / 2,
            hsaga_mems,
            width,
            yerr=hsaga_stds,
            label="AdaptiveHSAGA",
            capsize=5,
            color="#34495e",
        )

        ax.set_xlabel("Test Case", fontsize=12, fontweight="bold")
        ax.set_ylabel("Peak Memory (MB)", fontsize=12, fontweight="bold")
        ax.set_title("Memory Usage Comparison", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(test_cases, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Saved memory comparison to {save_path}")
        else:
            plt.savefig(self.output_dir / "memory_comparison.png", dpi=150, bbox_inches="tight")

        plt.close()

    def generate_all_plots(self):
        """Generate all comparison plots."""
        print("\nGenerating comparison plots...")
        self.plot_runtime_comparison()
        print("  ✓ Runtime comparison")
        self.plot_hypervolume_comparison()
        print("  ✓ Hypervolume comparison")
        self.plot_pareto_size_comparison()
        print("  ✓ Pareto size comparison")
        self.plot_memory_comparison()
        print("  ✓ Memory comparison")
        print(f"\nAll plots saved to {self.output_dir}/")

    def export_json(self, filepath: Optional[str] = None):
        """
        Export results to JSON.

        Args:
            filepath: Optional output filepath
        """
        if filepath is None:
            filepath = self.output_dir / "benchmark_results.json"

        # Convert results to serializable format
        results_data = []
        for result in self.results:
            results_data.append(
                {
                    "algorithm": result.algorithm,
                    "test_case_name": result.test_case_name,
                    "seed": result.seed,
                    "run_number": result.run_number,
                    "runtime": result.runtime,
                    "evaluations": result.evaluations,
                    "pareto_size": result.pareto_size,
                    "hypervolume": result.hypervolume,
                    "memory_peak_mb": result.memory_peak_mb,
                    "best_objective_values": result.best_objective_values,
                    "metadata": result.metadata,
                }
            )

        with open(filepath, "w") as f:
            json.dump(results_data, f, indent=2)

        print(f"Exported results to {filepath}")

    def generate_full_report(self):
        """Generate complete benchmark report with all components."""
        print("\n" + "=" * 70)
        print("Generating Full Benchmark Report")
        print("=" * 70)

        # 1. Text summary
        summary = self.generate_summary_report()
        summary_path = self.output_dir / "benchmark_summary.txt"
        with open(summary_path, "w") as f:
            f.write(summary)
        print(f"\n✓ Summary report: {summary_path}")

        # 2. All plots
        self.generate_all_plots()

        # 3. JSON export
        self.export_json()

        # 4. Statistics
        stats_path = self.output_dir / "benchmark_statistics.json"
        stats = self.compute_statistics()
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2, default=str)
        print(f"✓ Statistics: {stats_path}")

        print("\n" + "=" * 70)
        print("Report Generation Complete!")
        print("=" * 70)
        print(f"\nAll files saved to: {self.output_dir}/")
        print("\nGenerated files:")
        print("  • benchmark_summary.txt - Text report")
        print("  • runtime_comparison.png - Runtime chart")
        print("  • hypervolume_comparison.png - Quality chart")
        print("  • pareto_size_comparison.png - Front size chart")
        print("  • memory_comparison.png - Memory usage chart")
        print("  • benchmark_results.json - Raw results")
        print("  • benchmark_statistics.json - Statistical summary")
        print("=" * 70)
