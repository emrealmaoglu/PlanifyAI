"""
Analyze H-SAGA performance results and generate report.

Usage: python scripts/analyze_performance.py
"""
import os

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Skipping plot generation.")


def analyze_scaling():
    """Analyze performance scaling"""
    # Mock data - replace with actual benchmark results
    # In practice, this would load from benchmark output
    data = {
        10: {"runtime": 1.2, "evaluations": 1100, "fitness": 0.75},
        20: {"runtime": 3.5, "evaluations": 3200, "fitness": 0.72},
        50: {"runtime": 15.2, "evaluations": 8500, "fitness": 0.68},
    }

    buildings = list(data.keys())
    runtimes = [data[b]["runtime"] for b in buildings]
    evaluations = [data[b]["evaluations"] for b in buildings]

    # Create plots if matplotlib available
    if HAS_MATPLOTLIB:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Runtime scaling
        ax1.plot(buildings, runtimes, "o-", linewidth=2, markersize=8)
        ax1.set_xlabel("Number of Buildings", fontsize=12)
        ax1.set_ylabel("Runtime (seconds)", fontsize=12)
        ax1.set_title("H-SAGA Runtime Scaling", fontsize=14, fontweight="bold")
        ax1.grid(True, alpha=0.3)

        # Add linear reference
        linear_ref = [runtimes[0] * (b / buildings[0]) for b in buildings]
        ax1.plot(buildings, linear_ref, "--", alpha=0.5, label="Linear reference")
        ax1.legend()

        # Evaluations scaling
        ax2.plot(buildings, evaluations, "o-", linewidth=2, markersize=8, color="green")
        ax2.set_xlabel("Number of Buildings", fontsize=12)
        ax2.set_ylabel("Fitness Evaluations", fontsize=12)
        ax2.set_title(
            "Fitness Evaluations vs Building Count", fontsize=14, fontweight="bold"
        )
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        os.makedirs("outputs", exist_ok=True)
        plt.savefig("outputs/performance_scaling.png", dpi=150)
        print("✅ Scaling analysis saved to outputs/performance_scaling.png")

    # Calculate scaling efficiency
    print("\n" + "=" * 70)
    print("SCALING EFFICIENCY ANALYSIS")
    print("=" * 70)

    for i in range(1, len(buildings)):
        prev_b, curr_b = buildings[i - 1], buildings[i]
        prev_t, curr_t = runtimes[i - 1], runtimes[i]

        building_ratio = curr_b / prev_b
        time_ratio = curr_t / prev_t

        efficiency = building_ratio / time_ratio

        print(f"\n{prev_b}→{curr_b} buildings:")
        print(f"  Building ratio: {building_ratio:.2f}x")
        print(f"  Time ratio: {time_ratio:.2f}x")
        print(f"  Efficiency: {efficiency:.2f} (1.0 = linear, >1.0 = sub-linear)")

        if efficiency >= 0.8:
            print("  ✅ Good scaling")
        elif efficiency >= 0.5:
            print("  ⚠️  Acceptable scaling")
        else:
            print("  ❌ Poor scaling - needs optimization")


if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    analyze_scaling()
