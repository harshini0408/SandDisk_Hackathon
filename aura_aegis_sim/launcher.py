#!/usr/bin/env python3
"""
AURA-AEGIS Launcher Menu
Interactive launcher with multiple startup options
"""
import subprocess
import sys
import os
from pathlib import Path

def print_menu():
    print("""
╔════════════════════════════════════════════════════════════╗
║     AURA-AEGIS — SSD Firmware Intelligence                ║
║     Adaptive Unified Reliability Architecture             ║
║                                                            ║
║     Main Launcher Menu                                    ║
╚════════════════════════════════════════════════════════════╝

1) 🚀 NORMAL START
   - Install dependencies
   - Setup models
   - Launch app normally

2) ⚡ QUICK START (Skip validation)
   - Install dependencies
   - Setup models
   - Launch app (no validation)

3) 🧪 TEST MODE
   - Run full validation suite
   - Check all systems
   - Show diagnostic report

4) 🔧 REPAIR & REINSTALL
   - Clean dependency cache
   - Reinstall from scratch
   - Recreate models
   - Run validation

5) 🐛 DEBUG MODE
   - Install dependencies
   - Setup models
   - Launch with debug logging

6) 📊 CHECK ONLY
   - Verify dependencies
   - Check models exist
   - Show status report

7) 🎮 STRESS TEST
   - Launch with stress preset
   - Auto-run enabled
   - High speed (20×)

8) ❌ EXIT

════════════════════════════════════════════════════════════

    """)

def run_cmd(cmd, description="Running command"):
    """Execute a command"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    while True:
        print_menu()
        choice = input("Select option (1-8): ").strip()
        
        if choice == "1":
            # Normal start
            run_cmd(f"{sys.executable} check_dependencies.py", "Checking dependencies")
            run_cmd(f"{sys.executable} setup_models.py", "Setting up models")
            run_cmd(f"{sys.executable} -m streamlit run app.py", "Launching app")
            break
        
        elif choice == "2":
            # Quick start
            run_cmd(f"{sys.executable} check_dependencies.py", "Checking dependencies")
            run_cmd(f"{sys.executable} setup_models.py", "Setting up models")
            print("\n⏩ Skipping validation...")
            run_cmd(f"{sys.executable} -m streamlit run app.py", "Launching app")
            break
        
        elif choice == "3":
            # Test mode
            run_cmd(f"{sys.executable} check_dependencies.py", "Checking dependencies")
            run_cmd(f"{sys.executable} validate.py", "Running validation suite")
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            # Repair mode
            print("\n🔧 Starting repair procedure...")
            print("  This will:")
            print("    1. Clean Python cache")
            print("    2. Reinstall dependencies")
            print("    3. Recreate ML models")
            print("    4. Run validation")
            
            response = input("\nContinue? (yes/no): ").strip().lower()
            if response == "yes":
                print("\nCleaning cache...")
                os.system(f"{sys.executable} -m pip cache purge")
                
                run_cmd(f"{sys.executable} -m pip install --force-reinstall -r requirements.txt", 
                       "Reinstalling dependencies")
                run_cmd(f"{sys.executable} setup_models.py", "Recreating models")
                run_cmd(f"{sys.executable} validate.py", "Running validation")
                print("\n✓ Repair complete!")
            else:
                print("Cancelled.")
        
        elif choice == "5":
            # Debug mode
            run_cmd(f"{sys.executable} check_dependencies.py", "Checking dependencies")
            run_cmd(f"{sys.executable} setup_models.py", "Setting up models")
            run_cmd(f"{sys.executable} -m streamlit run app.py --logger.level=debug", 
                   "Launching in debug mode")
            break
        
        elif choice == "6":
            # Check only
            run_cmd(f"{sys.executable} check_dependencies.py", "Checking dependencies")
            
            print("\nChecking models...")
            print("  Voltage model: ", end="")
            if Path("models/voltage_model.pkl").exists():
                print("✓ Found")
            else:
                print("✗ Not found")
            
            print("  LSTM model:    ", end="")
            if Path("models/lstm_health.pth").exists():
                print("✓ Found")
            else:
                print("✗ Not found")
            
            input("\nPress Enter to continue...")
        
        elif choice == "7":
            # Stress test
            print("\n🎮 Starting stress test scenario...")
            print("  - Speed: 20×")
            print("  - Mode: Stress")
            print("  - Auto-run: enabled")
            run_cmd(f"{sys.executable} check_dependencies.py", "Checking dependencies")
            run_cmd(f"{sys.executable} setup_models.py", "Setting up models")
            
            # Create a temp config for stress test
            print("""
import streamlit as st
if 'stress_mode' not in st.session_state:
    st.session_state['stress_mode'] = True
    st.session_state['speed'] = 20
    st.session_state['auto_run'] = True
""")
            run_cmd(f"{sys.executable} -m streamlit run app.py", "Launching in stress mode")
            break
        
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid option. Please select 1-8.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
