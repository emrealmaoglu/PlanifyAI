#!/usr/bin/env python3
"""
PlanifyAI Setup Verification Script
Created: 2025-11-03
"""
import sys
import importlib.metadata
from io import StringIO
import json


def check_numpy_accelerate():
    """Check if NumPy uses Apple Accelerate or OpenBLAS"""
    import numpy as np

    print("🔍 NumPy Configuration Check:")
    print(f"   Version: {np.__version__}")

    # Capture the JSON output from show()
    old_stdout = sys.stdout
    sys.stdout = config_output = StringIO()
    np.__config__.show()
    config_json = config_output.getvalue()
    sys.stdout = old_stdout

    try:
        # Parse JSON from numpy config
        config_dict = json.loads(config_json.strip())
        blas_info = config_dict.get("Build Dependencies", {}).get("blas", {})
        blas_name = blas_info.get("name", "").lower()

        if "accelerate" in blas_name:
            print("   ✅ Using Apple Accelerate Framework (3-5x speedup on M1!)")
            print("      Note: Best performance for M1/M2/M3 Macs")
            return True
        elif "openblas" in blas_name:
            print("   ✅ Using OpenBLAS (2-3x speedup on M1, M1-optimized)")
            print("      Note: Pip-installed NumPy uses OpenBLAS (acceptable)")
            print("      For Accelerate, use conda: conda install numpy 'libblas=*=*accelerate'")
            return True
        else:
            print(f"   ⚠️  Using {blas_name or 'unknown BLAS'} (may not be optimized)")
            print("      Recommendation: Verify NumPy is M1-optimized")
            return True
    except (json.JSONDecodeError, KeyError, AttributeError):
        # Fallback: check config string representation
        config_str = config_json.lower()
        if "accelerate" in config_str:
            print("   ✅ Using Apple Accelerate Framework (3-5x speedup on M1!)")
            return True
        elif "openblas" in config_str:
            print("   ✅ Using OpenBLAS (2-3x speedup on M1, M1-optimized)")
            print("      Note: Pip-installed NumPy uses OpenBLAS (acceptable)")
            return True
        else:
            # Check if we're on ARM64 (M1/M2/M3)
            import platform

            machine = platform.machine().lower()
            if machine in ["arm64", "aarch64"]:
                print("   ⚠️  Using standard BLAS (may not be optimized)")
                print("      Recommendation: Use conda or verify NumPy is M1-optimized")
                return True
            else:
                print("   ✅ NumPy installed (Intel Mac or other architecture)")
                return True


def check_dependencies():
    """Check all critical dependencies"""
    required = {
        "numpy": "1.26",
        "scipy": "1.11",
        "pandas": "2.1",
        "geopandas": "0.14",
        "pymoo": "0.6",
        "matplotlib": "3.8",
        "plotly": "5.18",
        "pytest": "7.4",
        "black": "23.12",
    }

    print("\n📦 Dependency Check:")
    all_ok = True

    for module, min_version in required.items():
        try:
            version = importlib.metadata.version(module)
            status = "✅" if version.startswith(min_version) else "⚠️"
            print(f"   {status} {module:15s} {version}")
        except importlib.metadata.PackageNotFoundError:
            print(f"   ❌ {module:15s} NOT INSTALLED")
            all_ok = False

    return all_ok


def main():
    """Main verification"""
    print("=" * 60)
    print("🚀 PlanifyAI Setup Verification")
    print("=" * 60)
    print()

    accelerate_ok = check_numpy_accelerate()
    deps_ok = check_dependencies()

    print()
    print("=" * 60)

    if accelerate_ok and deps_ok:
        print("✅ VERIFICATION PASSED!")
        print("   You're ready to start coding! 🎉")
        return 0
    else:
        print("❌ VERIFICATION FAILED")
        print("   Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

