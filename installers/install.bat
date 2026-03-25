@echo off
echo ═══════════════════════════════════════════════════════
echo   ⚛️  IMPGING Q-Engine — Windows Installer
echo ═══════════════════════════════════════════════════════
echo.

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Install Python 3.8+ from python.org
    pause
    exit /b 1
)
echo ✅ Python detected

echo.
echo [2/3] Installing dependencies...
pip install psutil
if errorlevel 1 (
    echo ❌ Failed to install psutil
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo [3/3] Running IMPGING Q-Engine...
echo.
python imping-launcher.py --help

echo.
echo ═══════════════════════════════════════════════════════
echo   ✅ IMPGING installed successfully!
echo   Run 'python imping-launcher.py monitor' to start
echo ═══════════════════════════════════════════════════════
pause
