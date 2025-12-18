"""
Quick validation for OSMnx integration.
Tests real-world data fetch and integration with optimizer.
"""

import time
import json
from pathlib import Path

def run_validation():
    print("=" * 60)
    print("🧪 Task 2.1 Quick Validation - OSMnx Integration")
    print("=" * 60)

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": []
    }

    # Test 1: Import Check
    print("\n[1/5] Import Check...")
    try:
        from backend.core.context.osm_context import (
            OSMContextFetcher, CampusContext, fetch_campus_context
        )
        print("  ✅ Imports successful")
        results["tests"].append({"name": "imports", "status": "PASS"})
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        results["tests"].append({"name": "imports", "status": "FAIL", "error": str(e)})
        return results

    # Test 2: Fetch Real Data (Kastamonu University area)
    print("\n[2/5] Fetching real OSM data (Kastamonu, 300m radius)...")
    try:
        start = time.perf_counter()
        context = fetch_campus_context(lat=41.3833, lon=33.7833, radius=300)
        fetch_time = time.perf_counter() - start

        print(f"  ✅ Fetch successful in {fetch_time:.2f}s")
        print(f"     - Buildings found: {len(context.existing_buildings)}")
        print(f"     - Roads found: {len(context.existing_roads)}")
        print(f"     - Boundary area: {context.boundary.area:.0f} m²")
        print(f"     - Buildable area: {context.buildable_area.area:.0f} m²")

        results["tests"].append({
            "name": "fetch_osm_data",
            "status": "PASS",
            "fetch_time_s": round(fetch_time, 2),
            "buildings": len(context.existing_buildings),
            "roads": len(context.existing_roads),
            "boundary_area_m2": round(context.boundary.area, 0),
            "buildable_area_m2": round(context.buildable_area.area, 0)
        })
    except Exception as e:
        print(f"  ❌ Fetch failed: {e}")
        results["tests"].append({"name": "fetch_osm_data", "status": "FAIL", "error": str(e)})
        return results

    # Test 3: GeoJSON Export
    print("\n[3/5] Testing GeoJSON export...")
    try:
        geojson = context.to_geojson()

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) > 0
        assert "metadata" in geojson

        # Count feature types
        layers = {}
        for f in geojson["features"]:
            layer = f["properties"]["layer"]
            layers[layer] = layers.get(layer, 0) + 1

        print(f"  ✅ GeoJSON export successful")
        print(f"     - Features: {len(geojson['features'])}")
        print(f"     - Layers: {layers}")

        results["tests"].append({
            "name": "geojson_export",
            "status": "PASS",
            "feature_count": len(geojson["features"]),
            "layers": layers
        })
    except Exception as e:
        print(f"  ❌ GeoJSON export failed: {e}")
        results["tests"].append({"name": "geojson_export", "status": "FAIL", "error": str(e)})

    # Test 4: Coordinate System Validation
    print("\n[4/5] Validating coordinate system (meters, not degrees)...")
    try:
        # Check that areas are in reasonable range (meters, not degrees)
        # 300m radius circle ≈ 282,743 m² (π * 300²)
        expected_area = 3.14159 * 300 * 300
        actual_area = context.boundary.area

        # Should be within 50% (accounting for non-circular shapes)
        ratio = actual_area / expected_area

        if 0.5 < ratio < 2.0:
            print(f"  ✅ Coordinates in meters (area ratio: {ratio:.2f})")
            results["tests"].append({
                "name": "coordinate_system",
                "status": "PASS",
                "expected_area": round(expected_area, 0),
                "actual_area": round(actual_area, 0),
                "ratio": round(ratio, 2)
            })
        else:
            print(f"  ⚠️ Suspicious area ratio: {ratio:.2f} (may be in wrong units)")
            results["tests"].append({
                "name": "coordinate_system",
                "status": "WARN",
                "ratio": round(ratio, 2)
            })
    except Exception as e:
        print(f"  ❌ Coordinate validation failed: {e}")
        results["tests"].append({"name": "coordinate_system", "status": "FAIL", "error": str(e)})

    # Test 5: Integration with BuildingGene
    print("\n[5/5] Testing integration with Sprint 1 components...")
    try:
        from backend.core.integration.building_geometry import (
            BuildingGene, BuildingType, ShapeGenerator
        )
        from backend.core.integration.smart_magnet import SmartMagnet
        import numpy as np

        # Create sample buildings within buildable area
        buildable = context.buildable_area
        if buildable.is_empty:
            print("  ⚠️ No buildable area available")
            results["tests"].append({
                "name": "sprint1_integration",
                "status": "WARN",
                "reason": "No buildable area"
            })
        else:
            # Get a point inside buildable area
            centroid = buildable.centroid

            # Create a test building
            gene = BuildingGene(
                position=(centroid.x, centroid.y),
                building_type=BuildingType.ACADEMIC,
                base_width=50,
                base_depth=40,
                floors=4
            )

            polygon = ShapeGenerator.generate(gene)

            # Check if it overlaps with existing buildings
            overlaps_existing = False
            for existing in context.existing_buildings:
                if polygon.intersects(existing.geometry):
                    overlaps_existing = True
                    break

            # Align to existing roads if available
            if context.existing_roads:
                road_arrays = [np.array(r.geometry.coords) for r in context.existing_roads]
                magnet = SmartMagnet(road_arrays)
                aligned = magnet.align_buildings([gene])
                aligned_polygon = ShapeGenerator.generate(aligned[0])

                print(f"  ✅ Sprint 1 integration successful")
                print(f"     - Test building at: ({centroid.x:.1f}, {centroid.y:.1f})")
                print(f"     - Building area: {polygon.area:.1f} m²")
                print(f"     - Overlaps existing: {overlaps_existing}")
                print(f"     - Aligned orientation: {aligned[0].orientation:.2f} rad")
            else:
                print(f"  ✅ Sprint 1 integration successful (no roads for alignment)")

            results["tests"].append({
                "name": "sprint1_integration",
                "status": "PASS",
                "test_building_area": round(polygon.area, 1),
                "overlaps_existing": overlaps_existing
            })

    except Exception as e:
        print(f"  ❌ Sprint 1 integration failed: {e}")
        results["tests"].append({"name": "sprint1_integration", "status": "FAIL", "error": str(e)})

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
        "ready_for_sprint2": failed == 0
    }

    if failed == 0:
        print("\n🚀 VERDICT: Ready to proceed to Task 2.2 (Solar Analysis)")
    else:
        print("\n⛔ VERDICT: Fix failures before proceeding")

    # Save results
    output_path = Path("sprint2_osm_validation.json")
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\n📄 Results saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_validation()
