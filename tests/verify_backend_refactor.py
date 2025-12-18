import sys
import os
import json
from pydantic import ValidationError

# 1. System Path Setup
# Add the project root to sys.path so we can import 'backend'
sys.path.append(os.getcwd())

print("🛡️ Starting Backend Refactor Verification...")
print("-" * 50)

# ------------------------------------------------------------------
# TEST 1: IMPORT INTEGRITY
# ------------------------------------------------------------------
print("\n🧪 Test 1: Module Import Integrity")
try:
    from backend.core.domain.geometry.osm_service import fetch_campus_context
    print("   ✅ Import Check Passed: 'backend.core.domain.geometry.osm_service'")
except ImportError as e:
    print(f"   ❌ Import Check Failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Unexpected Error during import: {e}")
    sys.exit(1)


# ------------------------------------------------------------------
# TEST 2: SCHEMA VALIDATION (SUCCESS)
# ------------------------------------------------------------------
print("\n🧪 Test 2: Schema Validation (Valid Payload)")
try:
    from backend.core.schemas.input import OptimizationRequest
    
    valid_payload = {
        "project_name": "Kastamonu Future Campus",
        "description": "Testing new finance and energy modules",
        "latitude": 41.3833,
        "longitude": 33.7833,
        "radius": 600.0,
        "building_counts": {
            "Rectory": 1,
            "Faculty": 3,
            "Dormitory": 2,
            "Dining": 1
        },
        "constraints": {
            "type": "FeatureCollection",
            "features": []
        },
        "enable_solar": True,
        "enable_wind": True,
        "enable_carbon": True,
        "enable_cost": True,
        "enable_walkability": True,
        "budget_limit": 15000000.0,
        "carbon_target": 5000.0,
        "student_population": 2500
    }
    
    req = OptimizationRequest(**valid_payload)
    
    # Assertions
    assert req.budget_limit == 15000000.0
    assert req.project_name == "Kastamonu Future Campus"
    assert req.building_counts["Faculty"] == 3
    
    print("   ✅ Schema Valid Payload Passed")
    print(f"      Parsed Project: {req.project_name}")
    print(f"      Parsed Budget: ${req.budget_limit:,.2f}")

except Exception as e:
    print(f"   ❌ Schema Validation Failed: {e}")
    sys.exit(1)


# ------------------------------------------------------------------
# TEST 3: SCHEMA VALIDATION (FAILURE)
# ------------------------------------------------------------------
print("\n🧪 Test 3: Schema Validation (Invalid Payload)")
try:
    invalid_payload = {
        "project_name": "Broken Request",
        "latitude": "invalid_lat",  # Error: Wrong type (string instead of float)
        "longitude": 33.7833,
        # Missing required fields if any, or just type errors
        "budget_limit": "unlimited" # Error: Wrong type
    }
    
    req = OptimizationRequest(**invalid_payload)
    print("   ❌ Failed to catch invalid payload! (This is bad)")
    sys.exit(1)

except ValidationError as e:
    print("   ✅ Schema Invalid Payload Caught (Expected Behavior)")
    # Optional: Print the error details to verify it's the right error
    # print(e.json())
except Exception as e:
    print(f"   ❌ Unexpected Error type caught: {type(e)}")
    sys.exit(1)

print("-" * 50)
print("🎉 ALL TESTS PASSED. Backend Refactor is Verified.")
