"""
Pytest configuration for spatial tests.

Provides fixtures and settings specific to spatial tensor field tests.
"""
import numpy as np
import pytest

# Set numpy print options for better test output
np.set_printoptions(precision=4, suppress=True)
