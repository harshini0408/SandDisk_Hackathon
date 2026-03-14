#!/usr/bin/env python3
"""
AURA-AEGIS Installation & Launch Script
Handles dependency installation and app startup
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║  AURA-AEGIS — SSD Firmware Intelligence Simulation        ║
║  Installation & Launch Script                             ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Step 1: Install dependencies
    print("\n[1/4] Installing Python dependencies...")
    pip_cmd = f"{sys.executable} -m pip install -q streamlit plotly numpy pandas scikit-learn cryptography joblib"
    if not run_command(pip_cmd, "Installing pip packages"):
        print("WARNING: Some packages may not have installed correctly, but continuing...")
    
    # Step 2: Setup ML models
    print("\n[2/4] Setting up ML models...")
    if not run_command(f"{sys.executable} setup_models.py", "Creating ML models"):
        print("WARNING: Model setup had issues, but we can continue with fallback models.")
    
    # Step 3: Run validation
    print("\n[3/4] Running validation tests...")
    if not run_command(f"{sys.executable} validate.py", "Validation suite"):
        print("WARNING: Some validation tests may have failed.")
    
    # Step 4: Launch app
    print("\n[4/4] Launching AURA-AEGIS Streamlit App...")
    print("""
╔════════════════════════════════════════════════════════════╗
║  App will open at: http://localhost:8501                  ║
║  Press Ctrl+C to stop the server                          ║
╚════════════════════════════════════════════════════════════╝
    """)
    run_command(
        f"{sys.executable} -m streamlit run app.py --server.headless false --browser.gatherUsageStats false",
        "Starting Streamlit app"
    )

if __name__ == "__main__":
    main()
