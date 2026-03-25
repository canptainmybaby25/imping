# ⚛️ IMPGING Q-Engine

**Quantum-Inspired Gaming Process Classifier** — monitors, classifies, and optimizes gaming environments using a superposition-based AI classification engine.

> *"Shifting algorithm odds via hardware mapping, network jamming, and real-time optimization"*

---

## 📦 Distribution Packages

| Platform | Method | Status | Output |
|----------|--------|--------|--------|
| **Android (Termux)** | Shell installer | ✅ Ready | `android/termux-setup.sh` |
| **Android (Native)** | BeeWare + Gradle | 🔧 Requires setup | `.apk` via `briefcase build android` |
| **Windows** | PyInstaller | 🔧 Run `build.bat` | `desktop/IMPGING.exe` |
| **Linux/macOS** | PyInstaller | 🔧 Run `build.sh` | `desktop/IMPGING` |
| **Zo Computer** | Built-in skill | ✅ Ready | `Skills/imping/` |

---

## 🚀 Quick Install

### Android (Termux — Easiest)
```bash
# Install Termux from F-Droid, then:
bash <(curl -fsSL https://your-server.com/termux-setup.sh)

# Or manually:
pkg update && pkg install python -y
pip install psutil
cp -r /path/to/IMPGING-Distro/Skills ~/
python3 ~/Skills/imping/scripts/apk-scanner.py --once
```

### Desktop (Windows/macOS/Linux)
```bash
# Download and extract the release for your platform
# Windows
.\install.bat

# Linux/macOS
chmod +x install.sh && ./install.sh

# Or use directly (requires Python 3.8+):
python3 imping-launcher.py scan
```

---

## ⚡ Usage

```bash
# ── Core Commands ─────────────────────────────────
imping scan           # One-shot quantum process scan
imping monitor        # Real-time monitoring (2s interval)
imping entropy        # Shannon entropy analysis

# ── Optimization Stack ────────────────────────────
imping game start --game VALORANT   # Start game detector
imping hw pin --pid 1234            # Pin process to P-cores
imping net start --target "VALORANT" --mode aggressive  # Network optimization
```

---

## ⚛️ Q-Engine Architecture

```
Process Name
     ↓
┌──────────────────────────────────────┐
│  L1: SUPERPOSITION SCAN             │
│  |Ψ⟩ = Σ cᵢ |stateᵢ⟩               │
│  char bigrams → 256-dim vector       │
└──────────────────────────────────────┘
     ↓
┌──────────────────────────────────────┐
│  L2: INTERFERENCE SCORING           │
│  γ = ⟨Ψ|cat⟩ / (|Ψ|·|cat|)         │
│  cosine similarity (no numpy)        │
└──────────────────────────────────────┘
     ↓
┌──────────────────────────────────────┐
│  L3: WAVE COLLAPSE (Born Rule)      │
│  P(state) = |γ|²                     │
│  highest probability → classification│
└──────────────────────────────────────┘
     ↓
  🃏 CASINO | 🎮 GAMING | ⚠️ MALWARE | 👁️ SUSPICIOUS | ❓ UNKNOWN
```

**Signature Database:** 45 casino + 41 gaming + 39 malware keywords = 125 total signatures

**Efficiency:** 16-worker ThreadPoolExecutor, zero-copy process cache, pure Python math

---

## 📁 Project Structure

```
IMPGING-Distro/
├── imping-launcher.py          # Cross-platform CLI launcher
├── requirements.txt           # psutil (only dependency)
├── imping.spec               # PyInstaller build spec
├── LICENSE                   # MIT
├── README.md                 # This file
│
├── android/                  # Android distribution
│   ├── termux-setup.sh      # Termux one-liner installer
│   ├── pyproject.toml       # BeeWare config
│   └── src/imping/          # BeeWare app source
│
├── desktop/                  # Built executables (after build)
│   └── IMPGING/             #   PyInstaller output
│
└── installers/
    ├── install.bat          # Windows installer
    └── install.sh           # Linux/macOS installer
```

---

## 🔨 Building Native Desktop Binary

```bash
# Install PyInstaller
pip install pyinstaller

# Build (from IMPGING-Distro/)
pyinstaller imping.spec

# Output → desktop/IMPGING/IMPGING(.exe)
```

## 🔨 Building Android APK (BriefWare)

```bash
# Install Briefcase
pip install briefcase

# Create Android project
cd android
briefcase create android

# Build APK
briefcase build android
# Output → android/imping/build/IMPGING-0.0.1-debug.apk
```

---

## Requirements

- Python 3.8+
- `psutil >= 5.9.0` (only runtime dependency)
- Root/sudo for hardware mapping and traffic shaping
