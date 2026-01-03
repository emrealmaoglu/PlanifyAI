"""
Run Benchmarks
==============

Main script to execute comprehensive benchmarks comparing NSGA-III and AdaptiveHSAGA.

Usage:
    # Run all test cases
    python benchmarks/run_benchmarks.py

    # Run specific category
    python benchmarks/run_benchmarks.py --category small

    # Run specific test case
    python benchmarks/run_benchmarks.py --test-case small_residential

    # Custom configuration
    python benchmarks/run_benchmarks.py --runs 10 --population 100 --generations 100
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks import BenchmarkConfig, BenchmarkReporter, BenchmarkRunner, create_test_cases
from benchmarks.test_cases import get_test_case_by_name, get_test_cases_by_category
from src.algorithms.objective_profiles import ProfileType


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run benchmarks comparing NSGA-III and AdaptiveHSAGA"
    )

    # Test case selection
    parser.add_argument(
        "--category",
        type=str,
        choices=["small", "medium", "large", "all"],
        default="all",
        help="Test case category to run",
    )
    parser.add_argument("--test-case", type=str, help="Specific test case name to run")

    # Algorithm configuration
    parser.add_argument(
        "--population", type=int, default=50, help="Population size for both algorithms"
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=50,
        help="Number of generations/iterations for both algorithms",
    )
    parser.add_argument("--runs", type=int, default=5, help="Number of runs per test case")

    # Objective profile
    parser.add_argument(
        "--profile",
        type=str,
        choices=["standard", "research_enhanced", "fifteen_minute_city", "campus_planning"],
        default="research_enhanced",
        help="Objective profile to use",
    )

    # Output
    parser.add_argument(
        "--output-dir", type=str, default="benchmarks/reports", help="Output directory for reports"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    return parser.parse_args()


def main():
    """Main execution."""
    args = parse_args()

    print("\n" + "=" * 80)
    print("NSGA-III vs AdaptiveHSAGA Benchmark Suite")
    print("=" * 80)

    # Parse profile
    profile_map = {
        "standard": ProfileType.STANDARD,
        "research_enhanced": ProfileType.RESEARCH_ENHANCED,
        "fifteen_minute_city": ProfileType.FIFTEEN_MINUTE_CITY,
        "campus_planning": ProfileType.CAMPUS_PLANNING,
    }
    profile = profile_map[args.profile]

    # Configure benchmark
    config = BenchmarkConfig(
        nsga3_population_size=args.population,
        nsga3_n_generations=args.generations,
        hsaga_population_size=args.population,
        hsaga_n_iterations=args.generations,
        objective_profile=profile,
        n_runs=args.runs,
        verbose=args.verbose,
    )

    print("\nConfiguration:")
    print(f"  Population Size: {args.population}")
    print(f"  Generations/Iterations: {args.generations}")
    print(f"  Runs per Test Case: {args.runs}")
    print(f"  Objective Profile: {args.profile}")
    print(f"  Output Directory: {args.output_dir}")

    # Get test cases
    if args.test_case:
        print(f"\nRunning single test case: {args.test_case}")
        test_cases = [get_test_case_by_name(args.test_case)]
    elif args.category == "all":
        print("\nRunning all test cases")
        test_cases = create_test_cases()
    else:
        print(f"\nRunning {args.category} test cases")
        test_cases = get_test_cases_by_category(args.category)

    print(f"Total test cases: {len(test_cases)}")
    for tc in test_cases:
        print(f"  • {tc.name} ({tc.category}, {len(tc.buildings)} buildings)")

    # Run benchmarks
    runner = BenchmarkRunner(config)
    results = runner.run_all_benchmarks(test_cases)

    # Generate report
    reporter = BenchmarkReporter(results, output_dir=args.output_dir)
    reporter.generate_full_report()

    # Print summary
    print("\n" + reporter.generate_summary_report())


if __name__ == "__main__":
    main()
