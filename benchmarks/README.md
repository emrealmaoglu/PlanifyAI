# Performance Benchmarking

Comprehensive benchmarking system for comparing NSGA-III and AdaptiveHSAGA optimization algorithms.

## Overview

This module provides a complete framework for:
- Running standardized test cases
- Measuring performance metrics (runtime, memory, quality)
- Generating comparative reports and visualizations
- Statistical analysis of algorithm performance

## Quick Start

### 1. Run Quick Example

```bash
python examples/benchmark_example.py
```

This runs a small benchmark suite with 2 test cases and generates a complete report.

### 2. Run Full Benchmark Suite

```bash
python benchmarks/run_benchmarks.py
```

This runs all test cases (small, medium, large) with default settings.

### 3. Custom Benchmark

```bash
# Run only small test cases
python benchmarks/run_benchmarks.py --category small

# Run with more runs for better statistics
python benchmarks/run_benchmarks.py --runs 10

# Run with larger population
python benchmarks/run_benchmarks.py --population 100 --generations 100

# Run specific test case
python benchmarks/run_benchmarks.py --test-case medium_mixed_campus
```

## Test Cases

### Small (3-4 buildings)
- `small_residential`: Simple residential campus (200x200m)
- `small_educational`: Small educational campus (250x250m)

**Purpose**: Quick convergence testing, algorithm validation

### Medium (6-8 buildings)
- `medium_mixed_campus`: Mixed-use campus (400x400m)
- `medium_university`: University campus (500x500m)

**Purpose**: Balanced performance testing, typical use cases

### Large (10-15 buildings)
- `large_comprehensive`: Comprehensive campus (600x600m, 12 buildings)
- `large_university_complex`: Large university (700x700m, 15 buildings)

**Purpose**: Scalability testing, stress testing

## Metrics Collected

### Performance Metrics
- **Runtime**: Total execution time (seconds)
- **Evaluations**: Number of fitness evaluations
- **Memory Peak**: Peak memory usage (MB)

### Solution Quality Metrics
- **Pareto Front Size**: Number of non-dominated solutions
- **Hypervolume**: Quality indicator for Pareto front
- **Best Objective Values**: Objectives of best compromise solution

## Generated Reports

After running benchmarks, the following files are generated in `benchmarks/reports/`:

### Text Reports
- `benchmark_summary.txt`: Detailed statistical summary with comparisons

### Visualizations
- `runtime_comparison.png`: Runtime comparison across test cases
- `hypervolume_comparison.png`: Solution quality comparison
- `pareto_size_comparison.png`: Pareto front size comparison
- `memory_comparison.png`: Memory usage comparison

### Data Files
- `benchmark_results.json`: Raw benchmark results
- `benchmark_statistics.json`: Statistical summary (mean, std, min, max)

## Configuration

### BenchmarkConfig Parameters

```python
from benchmarks import BenchmarkConfig
from src.algorithms.profiles import ProfileType

config = BenchmarkConfig(
    # NSGA-III settings
    nsga3_population_size=50,
    nsga3_n_generations=50,
    nsga3_n_partitions=12,

    # AdaptiveHSAGA settings
    hsaga_population_size=50,
    hsaga_n_iterations=50,
    hsaga_initial_temp=1000.0,
    hsaga_final_temp=0.01,

    # Objective profile
    objective_profile=ProfileType.RESEARCH_ENHANCED,

    # Number of runs per test case (for statistical significance)
    n_runs=5,

    # Random seeds for reproducibility
    seeds=[42, 123, 456, 789, 1011],

    # Verbosity
    verbose=False
)
```

### Objective Profiles

- `ProfileType.STANDARD`: Basic 3-objective optimization
- `ProfileType.RESEARCH_ENHANCED`: 4 research-based objectives (recommended)
- `ProfileType.FIFTEEN_MINUTE_CITY`: Accessibility-focused
- `ProfileType.CAMPUS_PLANNING`: Adjacency-focused

## Programmatic Usage

### Basic Usage

```python
from benchmarks import BenchmarkRunner, BenchmarkConfig, BenchmarkReporter
from benchmarks.test_cases import get_test_cases_by_category

# Configure
config = BenchmarkConfig(
    nsga3_population_size=50,
    nsga3_n_generations=50,
    n_runs=5
)

# Get test cases
test_cases = get_test_cases_by_category("small")

# Run benchmarks
runner = BenchmarkRunner(config)
results = runner.run_all_benchmarks(test_cases)

# Generate report
reporter = BenchmarkReporter(results, output_dir="my_reports")
reporter.generate_full_report()
```

### Custom Test Case

```python
from benchmarks.test_cases import BenchmarkTestCase
from src.algorithms.building import Building, BuildingType

# Create custom test case
custom_case = BenchmarkTestCase(
    name="my_test",
    description="My custom test case",
    buildings=[
        Building(id="lib", type=BuildingType.LIBRARY, area=3000, floors=3),
        Building(id="dorm", type=BuildingType.RESIDENTIAL, area=4000, floors=5),
    ],
    bounds=(0, 0, 300, 300),
    category="custom",
    expected_complexity="medium"
)

# Run benchmark
runner = BenchmarkRunner(config)
results = runner.run_benchmark(custom_case)
```

### Access Results

```python
# Get results by algorithm
nsga3_results = runner.get_results_by_algorithm("NSGA-III")
hsaga_results = runner.get_results_by_algorithm("AdaptiveHSAGA")

# Get results by test case
case_results = runner.get_results_by_test_case("small_residential")

# Compute statistics
reporter = BenchmarkReporter(results)
stats = reporter.compute_statistics()

# Access specific metrics
nsga3_runtime_mean = stats["NSGA-III"]["small_residential"]["runtime"]["mean"]
nsga3_hv_std = stats["NSGA-III"]["small_residential"]["hypervolume"]["std"]
```

### Generate Individual Plots

```python
reporter = BenchmarkReporter(results)

# Generate specific plots
reporter.plot_runtime_comparison(save_path="runtime.png")
reporter.plot_hypervolume_comparison(save_path="quality.png")
reporter.plot_pareto_size_comparison(save_path="size.png")
reporter.plot_memory_comparison(save_path="memory.png")

# Export data
reporter.export_json("results.json")
```

## Interpreting Results

### Runtime Comparison
- Lower is better
- Measures computational efficiency
- Important for real-time applications

### Hypervolume
- Higher is better
- Measures Pareto front quality and coverage
- Most important metric for multi-objective optimization

### Pareto Front Size
- Context-dependent
- Larger = more solution diversity
- Too large may indicate poor convergence

### Memory Usage
- Lower is better
- Important for resource-constrained environments
- May indicate algorithm efficiency

## Statistical Significance

Each test case is run multiple times (default: 5) with different random seeds to ensure statistical significance. Results include:

- **Mean**: Average performance
- **Std**: Standard deviation (variability)
- **Min**: Best case performance
- **Max**: Worst case performance

## Performance Tips

### Quick Testing
```bash
python benchmarks/run_benchmarks.py --category small --runs 3 --population 30 --generations 30
```

### Production Benchmarking
```bash
python benchmarks/run_benchmarks.py --category all --runs 10 --population 100 --generations 100
```

### Memory-Constrained
```bash
python benchmarks/run_benchmarks.py --population 30 --generations 50
```

## Example Output

```
================================================================================
Benchmarking: small_residential
Description: Small residential campus with 3 buildings
Category: small (3 buildings)
================================================================================

[NSGA-III]
  Run 1: Runtime=2.45s, Pareto=28, HV=125.32
  Run 2: Runtime=2.51s, Pareto=30, HV=128.15
  Run 3: Runtime=2.48s, Pareto=29, HV=126.78

[AdaptiveHSAGA]
  Run 1: Runtime=3.12s, Pareto=15, HV=98.45
  Run 2: Runtime=3.08s, Pareto=16, HV=101.23
  Run 3: Runtime=3.15s, Pareto=14, HV=97.82

Test Case: small_residential
--------------------------------------------------------------------------------

[NSGA-III]
  Runtime:        2.48s ±   0.03s (min=  2.45s, max=  2.51s)
  Evaluations:    2500 ±      0 (min=  2500, max=  2500)
  Pareto Size:    29.0 ±    1.0 (min=    28, max=    30)
  Hypervolume:  126.75 ±   1.42 (min=125.32, max=128.15)

[AdaptiveHSAGA]
  Runtime:        3.12s ±   0.04s (min=  3.08s, max=  3.15s)
  Evaluations:    2500 ±      0 (min=  2500, max=  2500)
  Pareto Size:    15.0 ±    1.0 (min=    14, max=    16)
  Hypervolume:   99.17 ±   1.79 (min= 97.82, max=101.23)

[Comparison]
  NSGA-III is 1.26x faster than AdaptiveHSAGA
  NSGA-III achieves 1.28x better hypervolume than AdaptiveHSAGA
```

## Integration with CI/CD

You can integrate benchmarks into your CI/CD pipeline:

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmark

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run benchmarks
        run: python benchmarks/run_benchmarks.py --category small --runs 3
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-reports
          path: benchmarks/reports/
```

## Troubleshooting

### ImportError
Ensure you're running from project root:
```bash
cd /path/to/PlanifyAI
python benchmarks/run_benchmarks.py
```

### Memory Issues
Reduce population size or use smaller test cases:
```bash
python benchmarks/run_benchmarks.py --category small --population 30
```

### Slow Execution
Reduce runs or generations:
```bash
python benchmarks/run_benchmarks.py --runs 3 --generations 30
```

## Future Enhancements

- [ ] Multi-threaded benchmark execution
- [ ] GPU acceleration benchmarks
- [ ] Convergence curve plotting
- [ ] Automated performance regression detection
- [ ] Benchmark result database
- [ ] Web-based report viewer

## Related Documentation

- [Examples README](../examples/README.md) - Usage examples
- [Development Roadmap](../DEVELOPMENT_ROADMAP.md) - Project progress
- [API Documentation](http://localhost:8000/docs) - REST API docs

## License

See main project LICENSE file.
