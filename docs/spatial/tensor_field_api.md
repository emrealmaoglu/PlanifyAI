# Tensor Field API Documentation

## Overview

Semantic tensor field system for road network generation.

## Classes

### `TensorField`

Main class for managing tensor fields.

**Methods:**

- `add_grid_field(angle_degrees, strength)`: Add uniform directional field
- `add_radial_field(center, decay_radius, strength)`: Add radial field
- `get_eigenvectors(points, field_type)`: Query eigenvector field
- `get_tensor_at_points(points)`: Interpolate tensor at points

### `GridField`

Uniform directional basis field.

### `RadialField`

Radial basis field with Gaussian decay.

## Usage Example

```python
from src.spatial.tensor_field import TensorField

# Create field
field = TensorField(bounds=(0, 0, 1000, 1000), resolution=50)

# Add basis fields
field.add_grid_field(angle_degrees=0, strength=0.5)
field.add_radial_field(center=(500, 500), decay_radius=100, strength=0.8)

# Query eigenvectors
import numpy as np
points = np.array([[100, 100], [500, 500]])
major_vecs = field.get_eigenvectors(points, field_type='major')
```

## Performance

- Field creation: <1s for 50 buildings
- Eigenvector query: <0.2s for 1000 points
- Memory: ~10MB for 100x100 resolution field
