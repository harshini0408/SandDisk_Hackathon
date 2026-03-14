#!/usr/bin/env python3
"""
AURA-AEGIS Dependency Checker & Auto-Installer
Detects missing packages and installs them automatically
"""
import subprocess
import sys
import importlib
from pathlib import Path

# Define all required packages
REQUIRED_PACKAGES = {
    "streamlit": "streamlit>=1.32.0",
    "plotly": "plotly>=5.19.0",
    "numpy": "numpy>=1.26.0",
    "pandas": "pandas>=2.2.0",
    "sklearn": "scikit-learn>=1.4.0",
    "cryptography": "cryptography>=42.0.0",
    "joblib": "joblib>=1.3.0",
}

OPTIONAL_PACKAGES = {
    "torch": "torch>=2.2.0",
    "onnxruntime": "onnxruntime>=1.17.0",
}

def check_package(import_name):
    """Check if a package is installed"""
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def install_package(pip_spec):
    """Install a package using pip"""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", pip_spec],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║  AURA-AEGIS Dependency Checker                             ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    print("\n[1] Checking REQUIRED packages...")
    for import_name, pip_spec in REQUIRED_PACKAGES.items():
        status = "✓" if check_package(import_name) else "✗"
        print(f"  {status} {import_name:15} ... ", end="", flush=True)
        
        if not check_package(import_name):
            print("MISSING")
            missing_required.append(pip_spec)
        else:
            print("OK")
    
    # Check optional packages
    print("\n[2] Checking OPTIONAL packages...")
    for import_name, pip_spec in OPTIONAL_PACKAGES.items():
        status = "✓" if check_package(import_name) else "○"
        print(f"  {status} {import_name:15} ... ", end="", flush=True)
        
        if not check_package(import_name):
            print("NOT INSTALLED (optional)")
            missing_optional.append(pip_spec)
        else:
            print("OK")
    
    # Install missing packages
    if missing_required or missing_optional:
        print("\n[3] Installing missing packages...")
        
        if missing_required:
            print("\n  Required packages:")
            for pip_spec in missing_required:
                print(f"    Installing {pip_spec} ... ", end="", flush=True)
                if install_package(pip_spec):
                    print("✓")
                else:
                    print("✗ FAILED")
                    return False
        
        if missing_optional:
            print("\n  Optional packages (may fail, that's OK):")
            for pip_spec in missing_optional:
                print(f"    Installing {pip_spec} ... ", end="", flush=True)
                if install_package(pip_spec):
                    print("✓")
                else:
                    print("○ skipped (optional)")
    else:
        print("\n[3] All packages already installed!")
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  Dependency Check Complete ✓                              ║
║  Ready to launch: streamlit run app.py                    ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
