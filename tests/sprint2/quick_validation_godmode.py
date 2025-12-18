"""
Quick validation for God Mode (Manual Constraints).
Tests constraint creation, violation detection, and GeoJSON export.
"""

import time
import json
from pathlib import Path
import numpy as np

def run_validation():
    print("=" * 60)
    print("🧪 Task 2.4 Quick Validation - God Mode (Manual Constraints)")
    print("=" * 60)

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": []
    }

    # Test 1: Import Check
    print("\n[1/8] Import Check...")
    try:
        from backend.core.constraints.manual_constraints import (
            ManualConstraint, ConstraintType, FixedBuilding,
            ManualConstraintManager, create_exclusion_zone, create_fixed_building
        )
        print("  ✅ Imports successful")
        results["tests"].append({"name": "imports", "status": "PASS"})
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        results["tests"].append({"name": "imports", "status": "FAIL", "error": str(e)})
        return results

    # Test 2: Create Exclusion Zone
    print("\n[2/8] Creating exclusion zone...")
    try:
        coords = [(0, 0), (100, 0), (100, 50), (0, 50)]
        exclusion = create_exclusion_zone(coords, "parking", "main_parking")

        print(f"  ✅ Exclusion zone created")
        print(f"     - ID: {exclusion.id}")
        print(f"     - Type: {exclusion.constraint_type.value}")
        print(f"     - Area: {exclusion.area:.0f} m²")

        assert exclusion.constraint_type == ConstraintType.PARKING
        assert exclusion.area == 5000  # 100 * 50

        results["tests"].append({
            "name": "create_exclusion",
            "status": "PASS",
            "area_m2": exclusion.area
        })
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results["tests"].append({"name": "create_exclusion", "status": "FAIL", "error": str(e)})

    # Test 3: Create Fixed Building
    print("\n[3/8] Creating fixed building...")
    try:
        fixed = create_fixed_building(200, 200, "academic", 60, 40, 4)

        print(f"  ✅ Fixed building created")
        print(f"     - Position: {fixed.position}")
        print(f"     - Type: {fixed.building_type}")
        print(f"     - Dimensions: {fixed.width}x{fixed.depth}m")
        print(f"     - Height: {fixed.height}m ({fixed.floors} floors)")
        print(f"     - Polygon valid: {fixed.polygon.is_valid}")

        assert fixed.height == 14.0  # 4 * 3.5
        assert fixed.polygon.is_valid

        results["tests"].append({
            "name": "create_fixed_building",
            "status": "PASS",
            "height_m": fixed.height,
            "polygon_valid": fixed.polygon.is_valid
        })
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results["tests"].append({"name": "create_fixed_building", "status": "FAIL", "error": str(e)})

    # Test 4: Constraint Manager
    print("\n[4/8] Testing ManualConstraintManager...")
    try:
        manager = ManualConstraintManager()

        # Add exclusion zones
        parking = create_exclusion_zone([(0, 0), (100, 0), (100, 50), (0, 50)], "parking")
        garden = create_exclusion_zone([(200, 200), (300, 200), (300, 300), (200, 300)], "green_space")

        manager.add_constraint(parking)
        manager.add_constraint(garden)
        manager.add_fixed_building(fixed)

        print(f"  ✅ Constraint manager working")
        print(f"     - Constraints: {len(manager.constraints)}")
        print(f"     - Exclusion zones: {len(manager.exclusion_zones)}")
        print(f"     - Fixed buildings: {len(manager.fixed_buildings)}")

        assert len(manager.constraints) == 2
        assert len(manager.exclusion_zones) == 2
        assert len(manager.fixed_buildings) == 1

        results["tests"].append({
            "name": "constraint_manager",
            "status": "PASS",
            "num_constraints": len(manager.constraints),
            "num_exclusions": len(manager.exclusion_zones),
            "num_fixed": len(manager.fixed_buildings)
        })
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results["tests"].append({"name": "constraint_manager", "status": "FAIL", "error": str(e)})

    # Test 5: Position Check
    print("\n[5/8] Testing position allowance...")
    try:
        # Inside parking (should be blocked)
        inside_parking = manager.is_position_allowed(50, 25)

        # Outside all exclusions (should be allowed)
        outside_all = manager.is_position_allowed(150, 150)

        # Inside garden (should be blocked)
        inside_garden = manager.is_position_allowed(250, 250)

        print(f"  ✅ Position check working")
        print(f"     - Inside parking (50, 25): {'❌ Blocked' if not inside_parking else '✅ Allowed'}")
        print(f"     - Outside all (150, 150): {'✅ Allowed' if outside_all else '❌ Blocked'}")
        print(f"     - Inside garden (250, 250): {'❌ Blocked' if not inside_garden else '✅ Allowed'}")

        assert not inside_parking, "Point inside parking should be blocked"
        assert outside_all, "Point outside exclusions should be allowed"
        assert not inside_garden, "Point inside garden should be blocked"

        results["tests"].append({
            "name": "position_check",
            "status": "PASS",
            "inside_parking_blocked": not inside_parking,
            "outside_allowed": outside_all,
            "inside_garden_blocked": not inside_garden
        })
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results["tests"].append({"name": "position_check", "status": "FAIL", "error": str(e)})

    # Test 6: Polygon Violation Detection
    print("\n[6/8] Testing polygon violation detection...")
    try:
        from shapely.geometry import box

        # Building overlapping parking
        bad_building = box(50, 25, 90, 75)
        allowed_bad, violation_bad = manager.is_polygon_allowed(bad_building)

        # Building in clear area
        good_building = box(150, 150, 180, 175)
        allowed_good, violation_good = manager.is_polygon_allowed(good_building)

        print(f"  ✅ Polygon violation detection working")
        print(f"     - Overlapping parking: {'❌ Violation' if not allowed_bad else '✅ OK'} ({violation_bad:.0f} m²)")
        print(f"     - Clear area: {'✅ OK' if allowed_good else '❌ Violation'} ({violation_good:.0f} m²)")

        assert not allowed_bad, "Building overlapping parking should be violation"
        assert violation_bad > 0, "Should have violation area"
        assert allowed_good, "Building in clear area should be allowed"
        assert violation_good == 0, "Should have no violation"

        results["tests"].append({
            "name": "polygon_violation",
            "status": "PASS",
            "overlap_detected": not allowed_bad,
            "violation_area": round(violation_bad, 0),
            "clear_allowed": allowed_good
        })
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results["tests"].append({"name": "polygon_violation", "status": "FAIL", "error": str(e)})

    # Test 7: GeoJSON Export/Import
    print("\n[7/8] Testing GeoJSON export/import...")
    try:
        # Export
        geojson = manager.to_geojson()

        # Validate structure
        assert geojson["type"] == "FeatureCollection"
        num_features = len(geojson["features"])

        # Import into new manager
        restored = ManualConstraintManager.from_geojson(geojson)

        print(f"  ✅ GeoJSON export/import working")
        print(f"     - Exported features: {num_features}")
        print(f"     - Restored constraints: {len(restored.constraints)}")
        print(f"     - Restored fixed buildings: {len(restored.fixed_buildings)}")

        assert len(restored.constraints) == len(manager.constraints)

        results["tests"].append({
            "name": "geojson_roundtrip",
            "status": "PASS",
            "exported_features": num_features,
            "restored_constraints": len(restored.constraints)
        })
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results["tests"].append({"name": "geojson_roundtrip", "status": "FAIL", "error": str(e)})

    # Test 8: Integration with BuildingGene
    print("\n[8/8] Testing integration with BuildingGene...")
    try:
        from backend.core.integration.building_geometry import (
            BuildingGene, BuildingType, ShapeGenerator
        )

        # Create buildings - one in exclusion, one outside
        genes = [
            BuildingGene((50, 25), BuildingType.ACADEMIC, 40, 30, 3),   # In parking
            BuildingGene((150, 150), BuildingType.DORMITORY, 50, 35, 5), # Clear
            BuildingGene((250, 250), BuildingType.SOCIAL, 35, 25, 2),   # In garden
        ]

        polygons = [ShapeGenerator.generate(g) for g in genes]

        start = time.perf_counter()
        total_violation, details = manager.check_building_violations(polygons)
        elapsed = time.perf_counter() - start

        violating_buildings = len([d for d in details if d.get("violation_area", 0) > 0 or d.get("overlap_area", 0) > 0])

        print(f"  ✅ BuildingGene integration working")
        print(f"     - Buildings checked: {len(genes)}")
        print(f"     - Violations found: {violating_buildings}")
        print(f"     - Total violation area: {total_violation:.0f} m²")
        print(f"     - Check time: {elapsed*1000:.2f}ms")

        assert violating_buildings >= 2, "Should detect at least 2 violations (parking + garden)"

        results["tests"].append({
            "name": "building_gene_integration",
            "status": "PASS",
            "buildings_checked": len(genes),
            "violations_found": violating_buildings,
            "total_violation_m2": round(total_violation, 0),
            "check_time_ms": round(elapsed * 1000, 2)
        })
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results["tests"].append({"name": "building_gene_integration", "status": "FAIL", "error": str(e)})

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
        "ready_for_sprint3": failed == 0
    }

    if failed == 0:
        print("\n🎉 VERDICT: Sprint 2 COMPLETE! Ready for Sprint 3")
    else:
        print("\n⛔ VERDICT: Fix failures before proceeding")

    # Save results
    output_path = Path("sprint2_godmode_validation.json")
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\n📄 Results saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_validation()
