@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  AURA-AEGIS — SSD Firmware Intelligence
echo  Adaptive Unified Reliability Architecture
echo  Hackathon Demo Launcher
echo ========================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

echo [1/4] Checking and installing dependencies...
python check_dependencies.py
if errorlevel 1 (
    echo ERROR: Dependency check failed
    pause
    exit /b 1
)

echo.
echo [2/4] Setting up ML models...
python setup_models.py
if errorlevel 1 (
    echo WARNING: Model setup had issues, but we can continue with fallback models.
)

echo.
echo [3/4] Running validation tests...
python validate.py >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some validation tests failed, but continuing...
)

echo.
echo [4/4] Launching AURA-AEGIS Streamlit App...
echo.
echo   ╔════════════════════════════════════════════════════════════╗
echo   ║  App will open at: http://localhost:8501                  ║
echo   ║  Press Ctrl+C to stop the server                          ║
echo   ╚════════════════════════════════════════════════════════════╝
echo.

python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false

pause
