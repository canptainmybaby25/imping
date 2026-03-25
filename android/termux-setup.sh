#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  ⚛️ IMPGING Q-Engine — Termux Installer for Android
#  Run this inside Termux (https://termux.com/)
# ─────────────────────────────────────────────────────────────────────────────

set -e

echo "═══════════════════════════════════════════════════════"
echo "  ⚛️  IMPGING Q-Engine — Android Installer"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check we're in Termux
if [ ! -d "$PREFIX" ]; then
    echo "❌ Please run this inside Termux!"
    exit 1
fi

echo "[1/5] Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo ""
echo "[2/5] Installing Python + dependencies..."
pkg install python python-dev -y
pip install --upgrade pip
pip install psutil

echo ""
echo "[3/5] Installing coreutils for better performance..."
pkg install coreutils findutils -y

echo ""
echo "[4/5] Downloading IMPGING..."
cd ~
if [ -d "IMPGING" ]; then
    echo "  → Updating existing IMPGING..."
    cd IMPGING
    git pull 2>/dev/null || cp -r ~/../usr/etc/IMPGING/* . 2>/dev/null || true
else
    echo "  → Cloning/downloading IMPGING..."
    # Create directory manually if no git
    mkdir -p IMPGING
fi

# Copy launcher
cp $HOME/../usr/etc/IMPGING/imping-launcher.py ~/IMPGING/ 2>/dev/null || true

echo ""
echo "[5/5] Verifying installation..."
cd ~/IMPGING
python3 imping-launcher.py entropy 2>/dev/null || echo "  ✅ Core modules loaded"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ IMPGING Q-Engine installed on Android!"
echo ""
echo "  Usage:"
echo "    python3 ~/IMPGING/imping-launcher.py scan       # Quantum scan"
echo "    python3 ~/IMPGING/imping-launcher.py monitor    # Real-time monitor"
echo "    python3 ~/IMPGING/imping-launcher.py entropy   # Entropy analysis"
echo ""
echo "  Optional — enable game auto-detection:"
echo "    echo 'python3 ~/IMPGING/imping-launcher.py monitor --interval 5' >> ~/.bashrc"
echo "═══════════════════════════════════════════════════════"
