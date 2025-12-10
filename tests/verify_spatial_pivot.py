import sys
import os
from pydantic import ValidationError

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from backend.core.schemas.input import OptimizationRequest, OptimizationGoal, SiteParameters
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)

def check_backend_schema():
    print("Testing Backend Schema...")
    # Negative Test
    try:
        OptimizationRequest(
            latitude=41.0, 
            longitude=29.0, 
            budget_limit=1000 # Should fail
        )
        print("❌ Backend Check Failed: budget_limit was accepted!")
        return False
    except ValidationError:
        print("✅ Backend Negative Test Passed: budget_limit rejected.")
    except Exception as e:
        print(f"❌ Backend Check Failed with unexpected error: {e}")
        return False

    # Positive Test
    try:
        req = OptimizationRequest(
            latitude=41.0, 
            longitude=29.0,
            optimization_goals={OptimizationGoal.COMPACTNESS: 0.8},
            site_parameters={'setback_front': 10.0}
        )
        if req.site_parameters.setback_front == 10.0:
            print("✅ Backend Positive Test Passed: site_parameters accepted.")
        else:
            print(f"❌ Backend Positive Test Failed: Expected 10.0, got {req.site_parameters.setback_front}")
            return False
    except Exception as e:
        print(f"❌ Backend Positive Test Failed: {e}")
        return False
    
    return True

def check_frontend_store():
    print("\nTesting Frontend Store...")
    path = os.path.join(os.path.dirname(__file__), '../frontend/src/store/useOptimizationStore.ts')
    try:
        with open(path, 'r') as f:
            content = f.read()
            
        if 'setBudget' in content:
            print("❌ Frontend Store Check Failed: setBudget found!")
            return False
        else:
            print("✅ Frontend Store Negative Test Passed: setBudget not found.")
            
        if 'setSiteParameter' in content and 'optimizationGoals' in content:
            print("✅ Frontend Store Positive Test Passed: New fields found.")
        else:
            print("❌ Frontend Store Positive Test Failed: setSiteParameter or optimizationGoals missing.")
            return False
            
        return True
    except FileNotFoundError:
        print(f"❌ Frontend Store Check Failed: File not found at {path}")
        return False

def check_ui_component():
    print("\nTesting UI Component (PrepTab)...")
    path = os.path.join(os.path.dirname(__file__), '../frontend/src/features/cockpit/tabs/PrepTab.tsx')
    try:
        with open(path, 'r') as f:
            content = f.read()
            
        if 'Çekme Mesafeleri' in content:
            print("✅ UI Check Positive Test Passed: 'Çekme Mesafeleri' found.")
        else:
            print("❌ UI Check Positive Test Failed: 'Çekme Mesafeleri' not found.")
            return False
            
        # Check for Budget label
        if 'Bütçe' in content or 'Budget' in content:
             print("❌ UI Check Negative Test Failed: 'Bütçe' or 'Budget' found.")
             return False
        else:
             print("✅ UI Check Negative Test Passed: 'Bütçe'/'Budget' not found.")
             
        return True
    except FileNotFoundError:
        print(f"❌ UI Check Failed: File not found at {path}")
        return False

if __name__ == "__main__":
    b_ok = check_backend_schema()
    f_ok = check_frontend_store()
    u_ok = check_ui_component()
    
    if b_ok and f_ok and u_ok:
        print("\n✅ SPATIAL PIVOT SUCCESSFUL")
        sys.exit(0)
    else:
        print("\n❌ SPATIAL PIVOT FAILED")
        sys.exit(1)
