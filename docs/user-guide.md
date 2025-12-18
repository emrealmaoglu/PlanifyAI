# PlanifyAI User Guide

**Version:** 1.0
**Date:** November 9, 2025

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Using Campus Data](#using-campus-data)
4. [Adding Constraints](#adding-constraints)
5. [Running Optimization](#running-optimization)
6. [Visualizing Results](#visualizing-results)
7. [Exporting Results](#exporting-results)
8. [Examples](#examples)

## Introduction

PlanifyAI is an AI-powered generative campus planning platform that uses hybrid optimization algorithms to automatically generate optimal building layouts. This guide will help you use the geospatial data integration, spatial constraints, and visualization features.

## Getting Started

### Basic Usage

```python
from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA

# Create buildings
buildings = [
    Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
    Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
    Building("B3", BuildingType.LIBRARY, 3000, 4),
]

# Define bounds
bounds = (0, 0, 1000, 1000)

# Run optimization
optimizer = HybridSAGA(buildings, bounds)
result = optimizer.optimize()

print(f"Best fitness: {result['fitness']:.4f}")
```

## Using Campus Data

### Loading Campus Data

PlanifyAI supports loading campus data from GeoJSON files:

```python
from src.data.parser import CampusDataParser

# Load campus data
campus = CampusDataParser.from_geojson('data/campuses/bogazici_university.json')

print(f"Campus: {campus.name}")
print(f"Location: {campus.location}")
print(f"Area: {campus.get_total_area():.0f}m²")
print(f"Existing buildings: {len(campus.buildings)}")
```

### Available Campus Data

The following Turkish university campus data files are available:

- `data/campuses/bogazici_university.json` - Boğaziçi University, Istanbul
- `data/campuses/metu.json` - Middle East Technical University, Ankara
- `data/campuses/itu.json` - Istanbul Technical University
- `data/campuses/bilkent.json` - Bilkent University, Ankara
- `data/campuses/sabanci.json` - Sabancı University, Istanbul

### Creating Custom Campus Data

You can create custom campus data using a dictionary:

```python
from src.data.parser import CampusDataParser
from shapely.geometry import Polygon

# Create campus data dictionary
campus_data = {
    "name": "My Campus",
    "location": "City, Country",
    "boundary": {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]]]
    },
    "existing_buildings": [
        {
            "id": "existing_lib",
            "type": "library",
            "position": [500, 500],
            "area": 3000,
            "floors": 3
        }
    ],
    "constraints": {
        "setback_from_boundary": 10,
        "coverage_ratio_max": 0.3,
        "far_max": 2.0,
        "min_green_space_ratio": 0.4
    },
    "metadata": {
        "total_area_m2": 1000000,
        "student_count": 10000,
        "established": 2000
    }
}

# Parse campus data
campus = CampusDataParser.from_dict(campus_data)
```

## Adding Constraints

### Constraint Types

PlanifyAI supports four types of spatial constraints:

1. **SetbackConstraint**: Buildings must be X meters from boundary
2. **CoverageRatioConstraint**: Building coverage ≤ max_ratio
3. **FloorAreaRatioConstraint**: Total floor area ≤ FAR × site area
4. **GreenSpaceConstraint**: Minimum green space ratio

### Creating Constraints

```python
from src.constraints.spatial_constraints import (
    ConstraintManager,
    SetbackConstraint,
    CoverageRatioConstraint,
    FloorAreaRatioConstraint,
    GreenSpaceConstraint,
)

# Create constraint manager
constraints = ConstraintManager()

# Add constraints
constraints.add_constraint(SetbackConstraint(setback_distance=10.0))
constraints.add_constraint(CoverageRatioConstraint(max_coverage_ratio=0.3))
constraints.add_constraint(FloorAreaRatioConstraint(max_far=2.0))
constraints.add_constraint(GreenSpaceConstraint(min_green_ratio=0.4))
```

### Loading Constraints from Campus Data

```python
from src.data.parser import CampusDataParser
from src.constraints.spatial_constraints import (
    ConstraintManager,
    SetbackConstraint,
    CoverageRatioConstraint,
    FloorAreaRatioConstraint,
    GreenSpaceConstraint,
)

# Load campus data
campus = CampusDataParser.from_geojson('data/campuses/bogazici_university.json')

# Create constraints from campus data
constraints = ConstraintManager()
constraints.add_constraint(
    SetbackConstraint(campus.constraints["setback_from_boundary"])
)
constraints.add_constraint(
    CoverageRatioConstraint(campus.constraints["coverage_ratio_max"])
)
constraints.add_constraint(
    FloorAreaRatioConstraint(campus.constraints["far_max"])
)
constraints.add_constraint(
    GreenSpaceConstraint(campus.constraints["min_green_space_ratio"])
)
```

## Running Optimization

### Basic Optimization

```python
from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA

# Create buildings
buildings = [
    Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
    Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
]

# Run optimization
optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))
result = optimizer.optimize()

print(f"Best fitness: {result['fitness']:.4f}")
print(f"Best solution: {result['best_solution']}")
```

### Optimization with Campus Data and Constraints

```python
from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA
from src.data.parser import CampusDataParser
from src.constraints.spatial_constraints import (
    ConstraintManager,
    SetbackConstraint,
    CoverageRatioConstraint,
)

# Load campus data
campus = CampusDataParser.from_geojson('data/campuses/bogazici_university.json')

# Create buildings
buildings = [
    Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
    Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
]

# Create constraints
constraints = ConstraintManager()
constraints.add_constraint(SetbackConstraint(10.0))
constraints.add_constraint(CoverageRatioConstraint(0.3))

# Run optimization
optimizer = HybridSAGA(
    buildings,
    campus.get_bounds(),
    campus_data=campus,
    constraint_manager=constraints,
)

# Configure optimizer
optimizer.sa_config["chain_iterations"] = 100
optimizer.ga_config["generations"] = 50
optimizer.ga_config["population_size"] = 50

# Run optimization
result = optimizer.optimize()

# Check results
print(f"Best fitness: {result['fitness']:.4f}")
print(f"Constraints satisfied: {result['constraints']['satisfied']}")
print(f"Constraint penalty: {result['constraints']['penalty']:.4f}")
```

## Visualizing Results

### Plotting Solutions

```python
from src.visualization.plot_utils import CampusPlotter

# Create plotter
plotter = CampusPlotter(campus)

# Plot solution
plotter.plot_solution(
    result['best_solution'],
    show_constraints=True,
    save_path='outputs/solution.png'
)
```

### Plotting Convergence

```python
# Plot convergence
plotter.plot_convergence(result, save_path='outputs/convergence.png')
```

### Plotting Objectives

```python
# Plot objectives
plotter.plot_objectives(result, save_path='outputs/objectives.png')
```

## Exporting Results

### Exporting to GeoJSON

```python
from src.data.export import ResultExporter

# Export solution as GeoJSON
ResultExporter.to_geojson(
    result['best_solution'],
    campus,
    'outputs/solution.geojson',
    buildings
)
```

### Exporting to CSV

```python
# Export building positions as CSV
ResultExporter.to_csv(
    result['best_solution'],
    'outputs/positions.csv',
    buildings
)
```

### Exporting to JSON

```python
# Export complete result as JSON
ResultExporter.to_json(result, 'outputs/result.json')
```

### Generating Report

```python
# Generate markdown report
ResultExporter.generate_report(result, 'outputs/report.md')
```

## Examples

### Complete Example

```python
from src.algorithms.building import Building, BuildingType
from src.algorithms.hsaga import HybridSAGA
from src.data.parser import CampusDataParser
from src.data.export import ResultExporter
from src.visualization.plot_utils import CampusPlotter
from src.constraints.spatial_constraints import (
    ConstraintManager,
    SetbackConstraint,
    CoverageRatioConstraint,
    FloorAreaRatioConstraint,
    GreenSpaceConstraint,
)

# 1. Load campus data
campus = CampusDataParser.from_geojson('data/campuses/bogazici_university.json')

# 2. Create buildings
buildings = [
    Building("B1", BuildingType.RESIDENTIAL, 2000, 3),
    Building("B2", BuildingType.EDUCATIONAL, 2500, 4),
    Building("B3", BuildingType.LIBRARY, 3000, 4),
    Building("B4", BuildingType.HEALTH, 2800, 3),
    Building("B5", BuildingType.DINING, 1500, 2),
]

# 3. Create constraints
constraints = ConstraintManager()
constraints.add_constraint(
    SetbackConstraint(campus.constraints["setback_from_boundary"])
)
constraints.add_constraint(
    CoverageRatioConstraint(campus.constraints["coverage_ratio_max"])
)
constraints.add_constraint(
    FloorAreaRatioConstraint(campus.constraints["far_max"])
)
constraints.add_constraint(
    GreenSpaceConstraint(campus.constraints["min_green_space_ratio"])
)

# 4. Run optimization
optimizer = HybridSAGA(
    buildings,
    campus.get_bounds(),
    campus_data=campus,
    constraint_manager=constraints,
)

result = optimizer.optimize()

# 5. Export results
ResultExporter.to_geojson(
    result['best_solution'],
    campus,
    'outputs/solution.geojson',
    buildings
)
ResultExporter.generate_report(result, 'outputs/report.md')

# 6. Visualize
plotter = CampusPlotter(campus)
plotter.plot_solution(
    result['best_solution'],
    save_path='outputs/solution.png'
)
plotter.plot_convergence(result, save_path='outputs/convergence.png')
```

## Troubleshooting

### Common Issues

1. **File not found**: Make sure the campus data file path is correct
2. **Invalid boundary**: Ensure the boundary polygon is valid and closed
3. **Constraint violations**: Adjust constraint parameters or building sizes
4. **Optimization timeout**: Reduce the number of iterations or generations

### Getting Help

For more information, see:
- [Architecture Documentation](architecture.md)
- [API Documentation](api/)
- [Day 6 Summary](daily-logs/day6-summary.md)
