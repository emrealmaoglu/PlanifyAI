# Simulated Annealing Algorithm

## Overview

The Simulated Annealing (SA) phase of H-SAGA performs global exploration of the solution space. Based on the Li et al. 2025 reverse hybrid approach, SA is used first to explore diverse regions before Genetic Algorithm refinement.

## Algorithm Description

### Temperature Schedule

**Geometric Cooling Schedule:**
- Initial temperature: 1000.0
- Final temperature: 0.1
- Cooling rate: 0.95 (geometric)
- Formula: `T_new = T_old * cooling_rate`

The geometric schedule provides a smooth transition from exploration (high temperature) to exploitation (low temperature).

### Perturbation Operators

Three perturbation operators are used with different probabilities:

1. **Gaussian Move (80%)**
   - Perturbs a single building position
   - Step size: `σ = T/10` (temperature-adaptive)
   - Allows large moves when hot, fine-tuning when cold

2. **Swap Buildings (15%)**
   - Exchanges positions of two randomly selected buildings
   - Preserves overall layout structure

3. **Random Reset (5%)**
   - Completely randomizes one building position
   - Prevents getting stuck in local optima

### Acceptance Criterion

**Metropolis Criterion:**
- Better solutions (Δ > 0): Always accepted
- Worse solutions: Accepted with probability `exp(Δ / T)`
- As temperature decreases, acceptance probability decreases

### Parallel Execution

- Multiple independent SA chains run in parallel
- Default: 4 chains (optimized for M1's 4 performance cores)
- Each chain uses different random seed
- Best solution across all chains is selected

## Configuration Parameters

```python
sa_config = {
    'initial_temp': 1000.0,      # Starting temperature
    'final_temp': 0.1,            # Stopping temperature
    'cooling_rate': 0.95,         # Geometric cooling factor
    'max_iterations': 500,        # Maximum iterations per chain
    'num_chains': 4,              # Parallel chains (M1: 4 cores)
    'chain_iterations': 500       # Iterations per chain
}
```

## Performance Characteristics

- **Convergence**: Typically converges within 200-500 iterations
- **Runtime**: ~7.5s per chain for 10 buildings (500 iterations)
- **Scalability**: O(n²) for fitness evaluation (n = number of buildings)

## Research Basis

- Li et al. 2025: Reverse hybrid approach (SA → GA)
- Simulated Annealing Cooling Schedules Comparison: Geometric cooling (0.95)
- 15-Minute City Optimization: Ideal distance 50-150m between buildings
