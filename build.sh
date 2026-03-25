#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#   ⚛️ IMPGING Q-Engine — Linux/macOS Build
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "═══════════════════════════════════════════════════════"
echo "  ⚛️  IMPGING Q-Engine — Build Script"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        alias python3=python
    else
        echo "❌ Python 3 not found"
        exit 1
    fi
fi

echo "[1/4] Python: $(python3 --version)"

# Install dependencies
echo ""
echo "[2/4] Installing dependencies..."
pip3 install pyinstaller psutil --quiet
echo "✅ Dependencies ready"

# Build
echo ""
echo "[3/4] Building with PyInstaller..."
pyinstaller imping.spec --noconfirm
echo "✅ Build complete"

# Verify
echo ""
echo "[4/4] Verifying executable..."
if [ -f "desktop/IMPGING/IMPGING" ]; then
    echo "✅ Executable found: desktop/IMPGING/IMPGING"
    ./desktop/IMPGING/IMPGING scan
else
    echo "⚠️  Executable not at expected path — check desktop/build/"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ Build successful!"
echo "  Output: desktop/IMPGING/"
echo "═══════════════════════════════════════════════════════"
