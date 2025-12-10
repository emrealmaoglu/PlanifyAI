"""
Quick validation for Wind Analysis integration.
Tests wind data fetch, alignment scoring, and penalty calculation.
"""

import time
import json
from pathlib import Path
import numpy as np

def run_validation():
    print("=" * 60)
    print("🧪 Task 2.3 Quick Validation - Wind Analysis")
    print("=" * 60)

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": []
    }

    # Test 1: Import Check
    print("\n[1/7] Import Check...")
    try:
        from backend.core.physics.wind import (
            WindData, WindDataFetcher, WindAlignmentCalculator,
            WindPenaltyCalculator, fetch_wind_data, quick_wind_score
        )
        print("  ✅ Imports successful")
        results["tests"].append({"name": "imports", "status": "PASS"})
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        results["tests"].append({"name": "imports", "status": "FAIL", "error": str(e)})
        return results

    # Test 2: Wind Data Fetch (Kastamonu)
    print("\n[2/7] Fetching wind data (Kastamonu, 30 days)...")
    try:
        start = time.perf_counter()
        fetcher = WindDataFetcher()
        wind_data = fetcher.fetch(latitude=41.3833, longitude=33.7833, days=30)
        fetch_time = time.perf_counter() - start

        print(f"  ✅ Wind data fetch successful in {fetch_time:.2f}s")
        print(f"     - Dominant direction: {wind_data.dominant_direction_name} ({wind_data.dominant_direction:.0f}°)")
        print(f"     - Average speed: {wind_data.average_speed:.1f} m/s")
        print(f"     - Max speed: {wind_data.max_speed:.1f} m/s")
        print(f"     - Direction frequencies: {wind_data.direction_frequencies}")

        results["tests"].append({
            "name": "wind_data_fetch",
            "status": "PASS",
            "fetch_time_s": round(fetch_time, 2),
            "dominant_direction": wind_data.dominant_direction_name,
            "dominant_degrees": round(wind_data.dominant_direction, 0),
            "avg_speed_ms": round(wind_data.average_speed, 1),
            "max_speed_ms": round(wind_data.max_speed, 1)
        })
    except Exception as e:
        print(f"  ❌ Wind data fetch failed: {e}")
        print("  ⚠️ Using fallback data...")
        try:
            wind_data = fetcher._get_fallback(41.3833, 33.7833, 30)
            print(f"  ✅ Fallback data loaded")
            print(f"     - Dominant direction: {wind_data.dominant_direction_name}")
            results["tests"].append({
                "name": "wind_data_fetch",
                "status": "WARN",
                "note": "Used fallback data",
                "dominant_direction": wind_data.dominant_direction_name
            })
        except Exception as e2:
            results["tests"].append({"name": "wind_data_fetch", "status": "FAIL", "error": str(e2)})
            return results

    # Test 3: Direction Conversion (Meteorological to Math)
    print("\n[3/7] Testing direction conversion...")
    try:
        # Test known conversions
        test_cases = [
            (0, "N", np.pi/2),      # North → π/2 radians
            (90, "E", 0),           # East → 0 radians
            (180, "S", -np.pi/2),   # South → -π/2 radians
            (270, "W", [np.pi, -np.pi]),  # West → ±π radians (both valid)
        ]

        all_correct = True
        for deg, name, expected_rad in test_cases:
            test_data = WindData(
                dominant_direction=deg,
                dominant_direction_name=name,
                average_speed=5.0,
                max_speed=15.0,
                direction_frequencies={},
                latitude=41.0,
                longitude=33.0,
                data_period_days=30
            )
            actual_rad = test_data.dominant_direction_radians

            # Handle West case where both π and -π are valid
            if isinstance(expected_rad, list):
                if not any(abs(actual_rad - e) < 0.1 for e in expected_rad):
                    print(f"  ❌ {name} ({deg}°) → expected {expected_rad}, got {actual_rad:.2f}")
                    all_correct = False
            else:
                if abs(actual_rad - expected_rad) > 0.1:
                    print(f"  ❌ {name} ({deg}°) → expected {expected_rad:.2f}, got {actual_rad:.2f}")
                    all_correct = False

        if all_correct:
            print(f"  ✅ Direction conversion correct")
            print(f"     - N (0°) → π/2 rad")
            print(f"     - E (90°) → 0 rad")
            print(f"     - S (180°) → -π/2 rad")
            results["tests"].append({"name": "direction_conversion", "status": "PASS"})
        else:
            results["tests"].append({"name": "direction_conversion", "status": "FAIL"})

    except Exception as e:
        print(f"  ❌ Direction conversion failed: {e}")
        results["tests"].append({"name": "direction_conversion", "status": "FAIL", "error": str(e)})

    # Test 4: Road Alignment Scoring
    print("\n[4/7] Testing road alignment scoring...")
    try:
        # Create calculator with North wind
        north_wind = WindData(
            dominant_direction=0,  # North
            dominant_direction_name="N",
            average_speed=5.0,
            max_speed=15.0,
            direction_frequencies={},
            latitude=41.0,
            longitude=33.0,
            data_period_days=30
        )
        calc = WindAlignmentCalculator(north_wind)

        # Test cases
        # North-south road (parallel to north wind) → score ≈ 1.0
        score_parallel = calc.road_alignment_score((0, 0), (0, 100))

        # East-west road (perpendicular to north wind) → score ≈ 0.0
        score_perpendicular = calc.road_alignment_score((0, 0), (100, 0))

        # Diagonal road (45°) → score ≈ 0.5
        score_diagonal = calc.road_alignment_score((0, 0), (100, 100))

        print(f"  ✅ Road alignment scoring successful")
        print(f"     - N-S road (parallel to N wind): {score_parallel:.2f} (expected ~1.0)")
        print(f"     - E-W road (perpendicular): {score_perpendicular:.2f} (expected ~0.0)")
        print(f"     - Diagonal road (45°): {score_diagonal:.2f} (expected ~0.5)")

        # Validate
        assert score_parallel > 0.9, f"Parallel score {score_parallel} should be > 0.9"
        assert score_perpendicular < 0.1, f"Perpendicular score {score_perpendicular} should be < 0.1"
        assert 0.4 < score_diagonal < 0.6, f"Diagonal score {score_diagonal} should be ~0.5"

        results["tests"].append({
            "name": "road_alignment_scoring",
            "status": "PASS",
            "parallel_score": round(score_parallel, 2),
            "perpendicular_score": round(score_perpendicular, 2),
            "diagonal_score": round(score_diagonal, 2)
        })
    except Exception as e:
        print(f"  ❌ Road alignment scoring failed: {e}")
        results["tests"].append({"name": "road_alignment_scoring", "status": "FAIL", "error": str(e)})

    # Test 5: Road Network Scoring
    print("\n[5/7] Testing road network scoring...")
    try:
        # Create mixed road network
        roads = [
            np.array([[0, 0], [0, 100]]),      # N-S (100m, aligned)
            np.array([[0, 0], [100, 0]]),      # E-W (100m, perpendicular)
            np.array([[50, 0], [50, 50]])      # N-S (50m, aligned)
        ]

        start = time.perf_counter()
        network_score, details = calc.road_network_score(roads)
        calc_time = time.perf_counter() - start

        # Expected: (1.0*100 + 0.0*100 + 1.0*50) / 250 = 0.6
        expected_score = 0.6

        print(f"  ✅ Road network scoring successful")
        print(f"     - Network score: {network_score:.2f} (expected ~{expected_score})")
        print(f"     - Total length: {details['total_length']:.0f}m")
        print(f"     - Segments: {details['num_segments']}")
        print(f"     - Calc time: {calc_time*1000:.2f}ms")

        assert 0.5 < network_score < 0.7, f"Network score {network_score} out of expected range"

        results["tests"].append({
            "name": "road_network_scoring",
            "status": "PASS",
            "network_score": round(network_score, 2),
            "total_length_m": round(details['total_length'], 0),
            "num_segments": details['num_segments'],
            "calc_time_ms": round(calc_time * 1000, 2)
        })
    except Exception as e:
        print(f"  ❌ Road network scoring failed: {e}")
        results["tests"].append({"name": "road_network_scoring", "status": "FAIL", "error": str(e)})

    # Test 6: Penalty Calculation
    print("\n[6/7] Testing penalty calculation...")
    try:
        # Create penalty calculator with known wind
        penalty_calc = WindPenaltyCalculator(41.0, 33.0, wind_data=north_wind)

        # Aligned roads (low penalty)
        aligned_roads = [
            np.array([[0, 0], [0, 100]]),   # N-S
            np.array([[50, 0], [50, 100]])  # N-S
        ]

        # Perpendicular roads (high penalty)
        perp_roads = [
            np.array([[0, 0], [100, 0]]),   # E-W
            np.array([[0, 50], [100, 50]])  # E-W
        ]

        penalty_aligned, details_aligned = penalty_calc.calculate_penalty(aligned_roads)
        penalty_perp, details_perp = penalty_calc.calculate_penalty(perp_roads)

        print(f"  ✅ Penalty calculation successful")
        print(f"     - Aligned roads penalty: {penalty_aligned:.2f} (should be low)")
        print(f"     - Perpendicular roads penalty: {penalty_perp:.2f} (should be high)")
        print(f"     - Difference: {penalty_perp - penalty_aligned:.2f}")

        assert penalty_aligned < penalty_perp, "Aligned roads should have lower penalty"
        assert penalty_aligned < 0.3, f"Aligned penalty {penalty_aligned} too high"
        assert penalty_perp > 0.5, f"Perpendicular penalty {penalty_perp} too low"

        results["tests"].append({
            "name": "penalty_calculation",
            "status": "PASS",
            "aligned_penalty": round(penalty_aligned, 2),
            "perpendicular_penalty": round(penalty_perp, 2),
            "penalty_difference": round(penalty_perp - penalty_aligned, 2)
        })
    except Exception as e:
        print(f"  ❌ Penalty calculation failed: {e}")
        results["tests"].append({"name": "penalty_calculation", "status": "FAIL", "error": str(e)})

    # Test 7: Integration with SmartMagnet
    print("\n[7/7] Testing integration with SmartMagnet roads...")
    try:
        from backend.core.integration.smart_magnet import SmartMagnet
        from backend.core.integration.building_geometry import (
            BuildingGene, BuildingType, ShapeGenerator
        )

        # Create road network
        roads = [
            np.array([[0, 200], [500, 200]]),     # Main horizontal
            np.array([[250, 0], [250, 400]]),     # Main vertical
            np.array([[100, 100], [200, 100]]),   # Secondary
        ]

        # Create buildings
        genes = [
            BuildingGene((100, 100), BuildingType.ACADEMIC, 60, 45, 4),
            BuildingGene((350, 100), BuildingType.DORMITORY, 50, 40, 5),
            BuildingGene((100, 300), BuildingType.SOCIAL, 40, 30, 2),
            BuildingGene((350, 300), BuildingType.ADMIN, 35, 25, 3),
        ]

        # Align buildings to roads
        magnet = SmartMagnet(roads)
        aligned_genes = magnet.align_buildings(genes)

        # Calculate wind scores
        # Use actual fetched wind data
        wind_calc = WindAlignmentCalculator(wind_data)

        start = time.perf_counter()
        road_score, road_details = wind_calc.road_network_score(roads)

        building_scores = []
        for gene in aligned_genes:
            b_score = wind_calc.building_orientation_score(
                gene.orientation, gene.base_width, gene.base_depth
            )
            building_scores.append(b_score)

        elapsed = time.perf_counter() - start

        print(f"  ✅ SmartMagnet integration successful")
        print(f"     - Road network score: {road_score:.2f}")
        print(f"     - Building scores: {[f'{s:.2f}' for s in building_scores]}")
        print(f"     - Avg building score: {np.mean(building_scores):.2f}")
        print(f"     - Calc time: {elapsed*1000:.2f}ms")

        results["tests"].append({
            "name": "smartmagnet_integration",
            "status": "PASS",
            "road_score": round(road_score, 2),
            "building_scores": [round(s, 2) for s in building_scores],
            "avg_building_score": round(np.mean(building_scores), 2),
            "calc_time_ms": round(elapsed * 1000, 2)
        })
    except Exception as e:
        print(f"  ❌ SmartMagnet integration failed: {e}")
        results["tests"].append({"name": "smartmagnet_integration", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    warned = sum(1 for t in results["tests"] if t["status"] == "WARN")
    failed = sum(1 for t in results["tests"] if t["status"] == "FAIL")
    total = len(results["tests"])

    print(f"  ✅ Passed: {passed}/{total}")
    print(f"  ⚠️ Warnings: {warned}/{total}")
    print(f"  ❌ Failed: {failed}/{total}")

    results["summary"] = {
        "passed": passed,
        "warned": warned,
        "failed": failed,
        "total": total,
        "ready_for_next_task": failed == 0
    }

    if failed == 0:
        print("\n🚀 VERDICT: Ready to proceed to Task 2.4 (God Mode)")
    else:
        print("\n⛔ VERDICT: Fix failures before proceeding")

    # Save results
    output_path = Path("sprint2_wind_validation.json")
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\n📄 Results saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_validation()
