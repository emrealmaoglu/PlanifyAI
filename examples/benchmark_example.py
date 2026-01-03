"""
Benchmark Example
=================

Quick example showing how to run benchmarks comparing NSGA-III and AdaptiveHSAGA.

This example runs a small benchmark suite and generates a comparison report.

Usage:
    python examples/benchmark_example.py

Requirements:
    - matplotlib
    - numpy

Created: 2026-01-03
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks import BenchmarkConfig, BenchmarkReporter, BenchmarkRunner
from benchmarks.test_cases import get_test_cases_by_category
from src.algorithms.profiles import ProfileType


def main():
    """Main execution."""
    print("=" * 70)
    print("Benchmark Example - NSGA-III vs AdaptiveHSAGA")
    print("=" * 70)

    # Configure benchmark with small settings for quick demo
    config = BenchmarkConfig(
        # Small population and generations for quick testing
        nsga3_population_size=30,
        nsga3_n_generations=30,
        hsaga_population_size=30,
        hsaga_n_iterations=30,
        # Use research-enhanced profile
        objective_profile=ProfileType.RESEARCH_ENHANCED,
        # Run 3 times for statistical significance
        n_runs=3,
        # Enable verbose output
        verbose=True,
    )

    print("\nConfiguration:")
    print(f"  Population: {config.nsga3_population_size}")
    print(f"  Generations: {config.nsga3_n_generations}")
    print(f"  Runs: {config.n_runs}")
    print(f"  Profile: {config.objective_profile.value}")

    # Get small test cases for quick demo
    test_cases = get_test_cases_by_category("small")
    print(f"\nRunning {len(test_cases)} small test cases:")
    for tc in test_cases:
        print(f"  • {tc.name}: {tc.description}")
        print(f"    Buildings: {len(tc.buildings)}, Bounds: {tc.bounds}")

    # Run benchmarks
    print("\n" + "=" * 70)
    print("Starting Benchmarks...")
    print("=" * 70)

    runner = BenchmarkRunner(config)
    results = runner.run_all_benchmarks(test_cases)

    print(f"\n✅ Benchmarks complete! Collected {len(results)} results.")

    # Generate report
    print("\n" + "=" * 70)
    print("Generating Report...")
    print("=" * 70)

    output_dir = "examples/benchmark_output"
    reporter = BenchmarkReporter(results, output_dir=output_dir)
    reporter.generate_full_report()

    # Show summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    stats = reporter.compute_statistics()

    for test_case in [tc.name for tc in test_cases]:
        print(f"\n{test_case}:")
        print("-" * 70)

        for algorithm in ["NSGA-III", "AdaptiveHSAGA"]:
            if algorithm in stats and test_case in stats[algorithm]:
                tc_stats = stats[algorithm][test_case]
                print(f"\n  [{algorithm}]")
                print(f"    Runtime:      {tc_stats['runtime']['mean']:.2f}s")
                print(f"    Hypervolume:  {tc_stats['hypervolume']['mean']:.2f}")
                print(f"    Pareto Size:  {tc_stats['pareto_size']['mean']:.1f}")

        # Quick comparison
        if (
            "NSGA-III" in stats
            and "AdaptiveHSAGA" in stats
            and test_case in stats["NSGA-III"]
            and test_case in stats["AdaptiveHSAGA"]
        ):
            nsga3_rt = stats["NSGA-III"][test_case]["runtime"]["mean"]
            hsaga_rt = stats["AdaptiveHSAGA"][test_case]["runtime"]["mean"]
            nsga3_hv = stats["NSGA-III"][test_case]["hypervolume"]["mean"]
            hsaga_hv = stats["AdaptiveHSAGA"][test_case]["hypervolume"]["mean"]

            print(f"\n  [Quick Comparison]")
            if nsga3_rt < hsaga_rt:
                print(f"    ⚡ NSGA-III is {hsaga_rt/nsga3_rt:.2f}x faster")
            else:
                print(f"    ⚡ AdaptiveHSAGA is {nsga3_rt/hsaga_rt:.2f}x faster")

            if nsga3_hv > hsaga_hv:
                print(f"    🏆 NSGA-III achieves {nsga3_hv/hsaga_hv:.2f}x better hypervolume")
            else:
                print(f"    🏆 AdaptiveHSAGA achieves {hsaga_hv/nsga3_hv:.2f}x better hypervolume")

    print("\n" + "=" * 70)
    print("✅ Benchmark Example Complete!")
    print("=" * 70)
    print(f"\nGenerated files in {output_dir}:")
    print("  • benchmark_summary.txt - Detailed text report")
    print("  • runtime_comparison.png - Runtime comparison chart")
    print("  • hypervolume_comparison.png - Solution quality chart")
    print("  • pareto_size_comparison.png - Pareto front size chart")
    print("  • memory_comparison.png - Memory usage chart")
    print("  • benchmark_results.json - Raw benchmark data")
    print("  • benchmark_statistics.json - Statistical summary")
    print("\nFor comprehensive benchmarks, use:")
    print("  python benchmarks/run_benchmarks.py --category all --runs 10")
    print("=" * 70)


if __name__ == "__main__":
    main()
