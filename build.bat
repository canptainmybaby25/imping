@echo off
echo ═══════════════════════════════════════════════════════
echo   ⚛️  IMPGING Q-Engine — Windows Build
echo ═══════════════════════════════════════════════════════
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Install from python.org
    pause
    exit /b 1
)

echo [2/4] Installing PyInstaller...
pip install pyinstaller psutil -q
echo ✅ Dependencies installed

echo.
echo [3/4] Building IMPGING executable...
pyinstaller imping.spec --noconfirm
echo ✅ Build complete

echo.
echo [4/4] Testing built executable...
desktop\build\IMPGING\IMPGING.exe scan
echo.

echo ═══════════════════════════════════════════════════════
echo   ✅ Build successful!
echo   Output: desktop\build\IMPGING\IMPGING.exe
echo ═══════════════════════════════════════════════════════
pause
