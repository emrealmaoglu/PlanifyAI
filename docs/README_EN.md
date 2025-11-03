# PlanifyAI

## Overview

PlanifyAI is an intent-driven optimization platform for campus and urban planning.

## Features

- **H-SAGA Algorithm**: Li et al. 2025 reverse hybrid approach
- **Semantic Tensor Fields**: Building-type aware road network generation
- **M1 Optimization**: Apple Silicon native performance
- **Bilingual**: Turkish/English support

## Installation

```bash
# Create conda environment
conda env create -f environment.yml
conda activate planifyai

# Run application
streamlit run app.py
```

## Usage

```python
from src.algorithms.hsaga import HybridSAGA
from src.models.building import Building, BuildingType

# Define buildings
buildings = [
    Building("B1", BuildingType.RESIDENTIAL, 2000, 5),
    Building("B2", BuildingType.COMMERCIAL, 1500, 3),
]

# Create optimizer
optimizer = HybridSAGA(
    area_bounds=(0, 0, 500, 500),
    buildings=buildings,
    constraints={'green_areas': []}
)

# Optimize
result = optimizer.optimize()
print(f"Fitness: {result['fitness']:.3f}")
```

## Documentation

- [API Documentation (EN)](api/EN/)
- [Quick Start Guide](guides/EN/quickstart.md)

