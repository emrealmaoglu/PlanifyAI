
import sys
import os
import json
from shapely.geometry import Polygon

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.constraints.manual_constraints import ManualConstraintManager, ConstraintType

def test_frontend_payload_parsing():
    """Test parsing of MapboxDraw GeoJSON from frontend."""
    
    # Simulate payload from frontend
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "feature_1",
                "type": "Feature",
                "properties": {
                    "user_constraint_type": "exclusion",
                    "priority": 1
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]
                    ]
                }
            },
            {
                "id": "feature_2",
                "type": "Feature",
                "properties": {
                    "user_constraint_type": "green_space"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[20, 20], [20, 30], [30, 30], [30, 20], [20, 20]]
                    ]
                }
            }
        ]
    }
    
    print("Testing payload parsing...")
    manager = ManualConstraintManager.from_geojson(payload)
    
    print(f"Loaded {len(manager.constraints)} constraints")
    
    # Verify Exclusion Zone
    c1 = manager.constraints.get("feature_1")
    if c1:
        print(f"Constraint 1: Type={c1.constraint_type}, Expected={ConstraintType.EXCLUSION}")
        assert c1.constraint_type == ConstraintType.EXCLUSION
    else:
        print("Constraint 1 missing!")
        
    # Verify Green Space
    c2 = manager.constraints.get("feature_2")
    if c2:
        print(f"Constraint 2: Type={c2.constraint_type}, Expected={ConstraintType.GREEN_SPACE}")
        assert c2.constraint_type == ConstraintType.GREEN_SPACE
    else:
        print("Constraint 2 missing!")

    if len(manager.constraints) == 2 and c1 and c2:
        print("✅ SUCCESS: Backend correctly parses frontend God Mode constraints.")
    else:
        print("❌ FAILURE: Parsing failed.")

if __name__ == "__main__":
    test_frontend_payload_parsing()
