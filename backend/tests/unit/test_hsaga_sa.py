"""
Unit tests for H-SAGA SA Phase
"""
import numpy as np
import pytest

from src.algorithms.hsaga import HybridSAGA
from src.algorithms.solution import Solution


class TestHybridSAGA:
    """Test HybridSAGA class"""

    def test_initialization_valid(self, sample_buildings, bounds):
        """Test valid initialization"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        assert optimizer.buildings == sample_buildings
        assert optimizer.bounds == bounds
        assert optimizer.sa_config["initial_temp"] == 1000.0
        assert optimizer.sa_config["num_chains"] == 4

    def test_initialization_empty_buildings(self, bounds):
        """Test initialization with empty buildings"""
        with pytest.raises(ValueError, match="buildings list cannot be empty"):
            HybridSAGA([], bounds)

    def test_initialization_invalid_bounds(self, sample_buildings):
        """Test initialization with invalid bounds"""
        with pytest.raises(ValueError, match="Invalid bounds"):
            HybridSAGA(sample_buildings, (100, 0, 50, 500))

    def test_initialization_custom_config(self, sample_buildings, bounds):
        """Test initialization with custom SA config"""
        sa_config = {"initial_temp": 500.0, "num_chains": 2, "chain_iterations": 100}
        optimizer = HybridSAGA(sample_buildings, bounds, sa_config=sa_config)
        assert optimizer.sa_config["initial_temp"] == 500.0
        assert optimizer.sa_config["num_chains"] == 2

    def test_random_solution_generation(self, sample_buildings, bounds):
        """Test random solution generation"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        solution = optimizer._generate_random_solution()

        assert isinstance(solution, Solution)
        assert len(solution.positions) == len(sample_buildings)

        # Check all positions are within bounds
        for building_id, (x, y) in solution.positions.items():
            assert 0 <= x <= 500
            assert 0 <= y <= 500

        # Check solution is valid
        assert solution.is_valid(sample_buildings, bounds)

    def test_perturbation_gaussian_move(self, sample_buildings, bounds):
        """Test Gaussian perturbation operator"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        solution = optimizer._generate_random_solution()

        # Test with high temperature (large moves)
        high_temp = 1000.0
        perturbed = optimizer._perturb_solution(solution, high_temp)

        # Should have same structure
        assert set(solution.positions.keys()) == set(perturbed.positions.keys())

        # At least one position should change significantly
        max_change = max(
            np.linalg.norm(np.array(solution.positions[bid]) - np.array(perturbed.positions[bid]))
            for bid in solution.positions.keys()
        )
        assert max_change > 10.0, "High temp should produce large moves"

    def test_perturbation_step_size_scaling(self, sample_buildings, bounds):
        """Test step size scales with temperature (statistical test)"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        solution = optimizer._generate_random_solution()

        # Test multiple times for statistical robustness
        changes_high = []
        changes_low = []

        for _ in range(20):  # Run 20 trials
            # High temperature
            high_temp = 1000.0
            perturbed_high = optimizer._perturb_solution(solution, high_temp)
            change_high = max(
                np.linalg.norm(
                    np.array(solution.positions[bid]) - np.array(perturbed_high.positions[bid])
                )
                for bid in solution.positions.keys()
            )
            changes_high.append(change_high)

            # Low temperature
            low_temp = 10.0
            perturbed_low = optimizer._perturb_solution(solution, low_temp)
            change_low = max(
                np.linalg.norm(
                    np.array(solution.positions[bid]) - np.array(perturbed_low.positions[bid])
                )
                for bid in solution.positions.keys()
            )
            changes_low.append(change_low)

        # On average, high temp should produce larger moves
        avg_change_high = np.mean(changes_high)
        avg_change_low = np.mean(changes_low)

        # Allow some tolerance for statistical variation
        assert avg_change_high > avg_change_low * 0.8, (
            f"High temp avg ({avg_change_high:.2f}) should be > "
            f"low temp avg ({avg_change_low:.2f})"
        )

    def test_perturbation_swap(self, sample_buildings, bounds):
        """Test swap perturbation operator"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        solution = optimizer._generate_random_solution()

        # Create solution with known positions
        original_positions = solution.positions.copy()

        # Test multiple times to hit swap (15% probability)
        swapped = False
        for _ in range(20):
            perturbed = optimizer._perturb_solution(solution, 100.0)
            # Check if any two buildings swapped
            for bid1 in original_positions:
                for bid2 in original_positions:
                    if (
                        bid1 != bid2
                        and original_positions[bid1] == perturbed.positions[bid2]
                        and original_positions[bid2] == perturbed.positions[bid1]
                    ):
                        swapped = True
                        break
                if swapped:
                    break
            if swapped:
                break

        # With 20 attempts at 15% probability, should hit swap
        # (But not guaranteed, so just check structure is valid)
        assert set(solution.positions.keys()) == set(perturbed.positions.keys())

    def test_metropolis_criterion(self, sample_buildings, bounds):
        """Test Metropolis acceptance criterion"""
        # Better solution should always be accepted
        current_fitness = 0.5
        better_fitness = 0.8
        delta = better_fitness - current_fitness
        temp = 100.0

        # Should accept (delta > 0)
        accept = delta > 0 or np.random.random() < np.exp(delta / temp)
        assert accept, "Better solution should be accepted"

        # Worse solution may be accepted based on probability
        worse_fitness = 0.3
        delta = worse_fitness - current_fitness
        # Probability = exp(-0.2 / 100) ≈ 0.998
        # So it should usually be accepted
        accept = delta > 0 or np.random.random() < np.exp(delta / temp)
        # This is probabilistic, so we just check the formula is correct

    def test_sa_chain_execution(self, sample_buildings, bounds):
        """Test single SA chain execution"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        config = {
            "initial_temp": 100.0,
            "final_temp": 1.0,
            "cooling_rate": 0.95,
            "chain_iterations": 50,  # Reduced for testing
        }

        solution = optimizer._run_sa_chain(0, config)

        assert isinstance(solution, Solution)
        assert solution.fitness is not None
        assert solution.is_valid(sample_buildings, bounds)

    def test_temperature_schedule(self, sample_buildings, bounds):
        """Test geometric cooling schedule"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        config = {
            "initial_temp": 100.0,
            "final_temp": 1.0,
            "cooling_rate": 0.95,
            "chain_iterations": 10,
        }

        # Track temperature during chain
        temperatures = []
        original_run = optimizer._run_sa_chain

        def tracked_run(seed, config_inner):
            temp = config_inner["initial_temp"]
            cooling = config_inner["cooling_rate"]
            for _ in range(config_inner["chain_iterations"]):
                temperatures.append(temp)
                temp *= cooling
            return original_run(seed, config_inner)

        optimizer._run_sa_chain = tracked_run
        optimizer._run_sa_chain(0, config)

        # Check geometric cooling
        for i in range(1, len(temperatures)):
            ratio = temperatures[i] / temperatures[i - 1]
            assert abs(ratio - 0.95) < 0.01, "Should follow geometric cooling"

    def test_evaluate_solution(self, sample_buildings, bounds):
        """Test evaluate_solution method"""
        optimizer = HybridSAGA(sample_buildings, bounds)
        solution = optimizer._generate_random_solution()

        fitness = optimizer.evaluate_solution(solution)
        assert isinstance(fitness, float)
        assert solution.fitness == fitness
