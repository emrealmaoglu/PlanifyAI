import os
import sys

# Define paths
BASE_DIR = os.getcwd()
FRONTEND_SRC = os.path.join(BASE_DIR, 'frontend', 'src')

def check_file_structure():
    print("🔍 Checking File Structure...")
    required_files = [
        os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'SidebarLayout.tsx'),
        os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'tabs', 'PrepTab.tsx'),
        os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'tabs', 'DesignTab.tsx'),
        os.path.join(FRONTEND_SRC, 'store', 'useOptimizationStore.ts'),
        os.path.join(FRONTEND_SRC, 'config', 'buildingConfig.ts')
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {os.path.basename(file_path)}")
        else:
            raise FileNotFoundError(f"❌ Missing: {file_path}")

def check_integration():
    print("\n🔍 Checking Integration in OptimizationResults.tsx...")
    file_path = os.path.join(FRONTEND_SRC, 'components', 'OptimizationResults.tsx')
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    checks = [
        ("<SidebarLayout", "SidebarLayout Component Mounted"),
        ("import SidebarLayout", "SidebarLayout Import"),
        ("useOptimizationStore()", "Store Connection")
    ]
    
    for search_str, label in checks:
        if search_str in content:
            print(f"✅ {label} Found")
        else:
            raise ValueError(f"❌ {label} NOT found in JSX/Code")

def check_store_logic():
    print("\n🔍 Checking Store Logic...")
    file_path = os.path.join(FRONTEND_SRC, 'store', 'useOptimizationStore.ts')
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    required_actions = ["setBudget", "setCarbonTarget"]
    
    for action in required_actions:
        if action in content:
            print(f"✅ Action '{action}' Found")
        else:
            raise ValueError(f"❌ Action '{action}' missing in store")

def check_config():
    print("\n🔍 Checking Configuration...")
    file_path = os.path.join(FRONTEND_SRC, 'config', 'buildingConfig.ts')
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    checks = [
        ("$650-$850", "Cost Hint"),
        ("<300 kgCO2e", "Carbon Hint")
    ]
    
    for search_str, label in checks:
        if search_str in content:
            print(f"✅ {label} Found")
        else:
            raise ValueError(f"❌ {label} missing in config")

if __name__ == "__main__":
    try:
        check_file_structure()
        check_integration()
        check_store_logic()
        check_config()
        print("\n✅ ALL INTEGRATION CHECKS PASSED")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        sys.exit(1)
