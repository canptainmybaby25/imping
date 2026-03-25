#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   ⚛️ IMPGING Q-Engine — Linux/macOS Installer
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════"
echo "  ⚛️  IMPGING Q-Engine Installer"
echo "═══════════════════════════════════════════════════════"
echo ""

# Detect platform
PLATFORM=$(uname -s)
echo "[*] Platform: $PLATFORM"

# Check Python
echo ""
echo "[1/3] Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Install Python 3.8+ first."
    exit 1
fi

$PYTHON_CMD --version
echo "✅ Python detected"

# Install dependencies
echo ""
echo "[2/3] Installing dependencies..."
$PYTHON_CMD -m pip install psutil --quiet
echo "✅ Dependencies installed"

# Create launcher alias / symlink
echo ""
echo "[3/3] Setting up launcher..."
LAUNCHER_SRC="$(pwd)/imping-launcher.py"
if [ "$PLATFORM" = "Darwin" ]; then
    export PATH="/Applications/IMPGING.app/Contents/MacOS:$PATH" 2>/dev/null || true
fi
echo "✅ Launcher ready at: $LAUNCHER_SRC"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ IMPGING installed successfully!"
echo ""
echo "  Usage:"
echo "    python imping-launcher.py scan       # Quantum scan"
echo "    python imping-launcher.py monitor    # Real-time monitor"
echo "    python imping-launcher.py entropy    # Entropy analysis"
echo "═══════════════════════════════════════════════════════"
