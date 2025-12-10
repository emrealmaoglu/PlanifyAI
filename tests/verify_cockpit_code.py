import os
import sys

# Define paths
BASE_DIR = os.getcwd()
FRONTEND_SRC = os.path.join(BASE_DIR, 'frontend', 'src')

FILES_TO_CHECK = [
    os.path.join(FRONTEND_SRC, 'config', 'buildingConfig.ts'),
    os.path.join(FRONTEND_SRC, 'store', 'useOptimizationStore.ts'),
    os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'SidebarLayout.tsx'),
    os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'tabs', 'PrepTab.tsx'),
    os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'tabs', 'DesignTab.tsx'),
]

def check_file_existence():
    print("🔍 Checking File Existence...")
    all_exist = True
    for file_path in FILES_TO_CHECK:
        if os.path.exists(file_path):
            print(f"✅ Found: {os.path.basename(file_path)}")
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False
    if not all_exist:
        raise FileNotFoundError("Critical files are missing!")

def check_config_integrity():
    print("\n🔍 Checking Config Data Integrity...")
    config_path = os.path.join(FRONTEND_SRC, 'config', 'buildingConfig.ts')
    with open(config_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("$650-$850", "Cost Hint"),
        ("<300 kgCO2e", "Carbon Hint"),
        ("RECTORY", "Building Type: RECTORY"),
        ("DINING", "Building Type: DINING")
    ]
    
    for search_str, label in checks:
        if search_str in content:
            print(f"✅ {label} Found")
        else:
            raise ValueError(f"❌ {label} missing in buildingConfig.ts")

def check_store_structure():
    print("\n🔍 Checking Store Structure...")
    store_path = os.path.join(FRONTEND_SRC, 'store', 'useOptimizationStore.ts')
    with open(store_path, 'r') as f:
        content = f.read()
        
    if "projectInfo" in content:
        print("✅ projectInfo (Nested Object) Found")
    else:
        raise ValueError("❌ projectInfo missing in useOptimizationStore.ts")
        
    if "setCarbonTarget" in content:
        print("✅ Action setCarbonTarget Found")
    else:
        raise ValueError("❌ Action setCarbonTarget missing in useOptimizationStore.ts")

def check_ui_logic():
    print("\n🔍 Checking UI Component Logic...")
    
    # PrepTab
    prep_path = os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'tabs', 'PrepTab.tsx')
    with open(prep_path, 'r') as f:
        prep_content = f.read()
    
    if "COST_HINT" in prep_content or "SMART_HINTS" in prep_content:
        print("✅ PrepTab: Imports Hints")
    else:
        raise ValueError("❌ PrepTab does not import Hints")
        
    # DesignTab
    design_path = os.path.join(FRONTEND_SRC, 'features', 'cockpit', 'tabs', 'DesignTab.tsx')
    with open(design_path, 'r') as f:
        design_content = f.read()
        
    if "BUILDING_TYPES" in design_content and ".map" in design_content:
        print("✅ DesignTab: Maps Building Types")
    else:
        raise ValueError("❌ DesignTab does not map BUILDING_TYPES")

if __name__ == "__main__":
    try:
        check_file_existence()
        check_config_integrity()
        check_store_structure()
        check_ui_logic()
        print("\n🎉 All Cockpit Verification Checks Passed!")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        sys.exit(1)
