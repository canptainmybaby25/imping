#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  ⚛️ IMPGING Q-Engine — Android APK Build Script
#  Builds a real Android APK with Chaquopy (Python embedded in Java)
# ─────────────────────────────────────────────────────────────────────────────

set -e
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DISTRO="$PROJECT_DIR/IMPGING-Distro"
ANDROID="$DISTRO/android-project"

echo "╔══════════════════════════════════════════════════════╗"
echo "║   ⚛️  IMPGING Q-Engine — Android APK Builder       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Check environment ───────────────────────────────────────────────
echo "[1/6] Checking build environment..."

if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Install OpenJDK 17+:"
    echo "   apt install openjdk-17-jdk"
    exit 1
fi

if ! command -v gradle &> /dev/null && [ ! -f "$ANDROID/gradlew" ]; then
    echo "⚠️  Gradle not found. Installing gradle wrapper..."
    # We'll download gradle wrapper manually
    GRADLE_VERSION=8.4
    mkdir -p "$ANDROID/gradle/wrapper"
    cat > "$ANDROID/gradle/wrapper/gradle-wrapper.properties" << EOF
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.4-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
EOF
fi

echo "   Java: $(java -version 2>&1 | head -1)"

# ── Step 2: Copy Python sources ───────────────────────────────────────────────
echo "[2/6] Bundling Python Q-Engine scripts..."
mkdir -p "$ANDROID/app/src/main/python"

# Copy core scripts
cp "$DISTRO/Skills/imping/scripts/apk-scanner.py" "$ANDROID/app/src/main/python/qengine_bridge.py"
cp "$DISTRO/Skills/imping/scripts/mimic-engine.py" "$ANDROID/app/src/main/python/mimic_engine.py"
cp "$DISTRO/Skills/imping/scripts/game-detector.py" "$ANDROID/app/src/main/python/game_detector.py"
cp "$DISTRO/Skills/imping/scripts/hardware-mapper.py" "$ANDROID/app/src/main/python/hardware_mapper.py"
cp "$DISTRO/Skills/imping/scripts/net-jammer.py" "$ANDROID/app/src/main/python/net_jammer.py"

# Create bootstrap
cat > "$ANDROID/app/src/main/python/__init__.py" << 'PYEOF'
"""⚛️ IMPGING Q-Engine — Python Core Bootstrap"""
PYEOF

cat > "$ANDROID/app/src/main/python/impging_standalone.py" << 'PYEOF'
"""Standalone Q-Engine that doesn't depend on system modules."""
import math, hashlib, threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor

VEC_DIM = 256
CASINO_KW = {"1xbet","22bet","7bit","andarbahar","baccarat","bet365","betfair","betway","betwinner","blackjack","bovada","casino","championsbet","cricbet","dream11","draftkings","exchange","fanduel","fc25","fifa","football","guts","jackpot","ladbrokes","leo","leovegas","liga","livecasino","lottery","luckia","marathonbet","megapari","melbet","mobilecasino","mrbet","netbet","nfl","odds","parlay","partypoker","poker","pokerstars","power","premierbet","props","racebook","rar","rivalry","rolletto","royal","sbotop","scratch","sexys","sidney","slot","snake","soccer","sportbet","sportsbet","sportsbook","stake","supersports","tennisi","tennis","tipsport","tonybet","topbet","unibet","vegas","victory","vikings","win","winpot","youwin","zodiac"}
GAMING_KW = {"valorant","cs2","csgo","apex","fortnite","overwatch","leagueoflegends","dota2","rocketleague","genshin","rust","pubg","wow","ffxiv","nba2k","fifa","callofduty","warzone","minecraft","roblox","steam","epic","gfn","geforcenow","battle","royale","shooter","game","play"}
MALWARE_KW = {"strace","gdb","ltrace","debug","hook","injector","frida","xposed","substrate","sandbox","vmdetect","vmware","virtualbox","vbox","qemu","kvm","hyperv","malware","virustotal","cuckoo","fiddler","mitmproxy","wireshark","metasploit","rkhunter","mimikatz","betblock","gamblock","gamban","netnanny","coldturkey","spam","stealer","keylog","rat","trojan","keygen","rootkit","backdoor","siphon","freevpn","hideit","cloack","cheat","crack"}
PROB_WEIGHTS = {"CASINO":0.35,"GAMING":0.30,"MALWARE":0.25,"SUSPICIOUS":0.07,"UNKNOWN":0.03}

class QClassifier:
    def __init__(self):
        self.entanglement_log = deque(maxlen=500)
        self._lock = threading.RLock()
    def _hash_idx(self, s):
        return sum(ord(c) * (7**i) % VEC_DIM for i, c in enumerate(s[:8])) % VEC_DIM
    def _ngram(self, name):
        n = max(2, len(name)//4)
        return [name[i:i+n] for i in range(max(1, len(name)-n+1))]
    def _superposition(self, name):
        vec = [0.0]*VEC_DIM
        for ng in self._ngram(name):
            idx = self._hash_idx(ng)
            vec[idx] += 0.15
        return vec
    def _interference(self, state_vec, kw_set, weight):
        for kw in kw_set:
            idx = self._hash_idx(kw)
            state_vec[idx] += weight
        mx = max(state_vec) if state_vec else 1.0
        return [v/mx for v in state_vec]
    def classify(self, name):
        name_lower = name.lower()
        sv = self._superposition(name_lower)
        sv = self._interference(sv, CASINO_KW & set(name_lower.split()), 0.4)
        sv = self._interference(sv, MALWARE_KW & set(name_lower.split()), 0.5)
        sv = self._interference(sv, GAMING_KW & set(name_lower.split()), 0.3)
        prob = sum(PROB_WEIGHTS.get(k,0.03) for k in ["CASINO","GAMING","MALWARE","SUSPICIOUS"])
        conf = min(1.0, max(sv[i] for i in range(min(len(sv),len(CASINO_KW)))))
        ent = -sum((c/len(name))*math.log2(c/len(name)) for c in [name.count(c) for c in set(name)] if c>0)
        cat = "CASINO" if any(k in name_lower for k in CASINO_KW) else "MALWARE" if any(k in name_lower for k in MALWARE_KW) else "GAMING" if any(k in name_lower for k in GAMING_KW) else "UNKNOWN"
        with self._lock:
            self.entanglement_log.append({"name":name,"cat":cat,"conf":conf})
        return {"name":name,"category":cat,"confidence":conf,"entropy":ent}
PYEOF

echo "   ✅ Python scripts bundled"

# ── Step 3: Create launcher icon ─────────────────────────────────────────────
echo "[3/6] Creating app icon..."
mkdir -p "$ANDROID/app/src/main/res/drawable"

python3 << 'IMGEOF'
import base64, zlib

# Minimal 48x48 green-on-black quantum icon as PNG
PNG_DATA = bytes([
    0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,0x00,0x00,0x00,0x0D,
    0x49,0x48,0x44,0x52,0x00,0x00,0x00,0x30,0x00,0x00,0x00,0x30,
    0x08,0x06,0x00,0x00,0x00,0x57,0x02,0xF9,0x87,0x00,0x00,0x00,
    0x01,0x73,0x52,0x47,0x42,0x00,0xAE,0xCE,0x1C,0xE9,0x00,0x00,
    0x00,0x04,0x67,0x41,0x4D,0x41,0x00,0x00,0xB1,0x8F,0x0B,0xFC,
    0x61,0x05,0x00,0x00,0x00,0x09,0x70,0x48,0x59,0x73,0x00,0x00,
    0x0E,0xC3,0x00,0x00,0x0E,0xC3,0x01,0xC7,0x6F,0xA8,0x64,0x00,
    0x00,0x00,0x19,0x49,0x44,0x41,0x54,0x78,0x9C,0xED,0xCE,0x31,
    0x0A,0xC0,0x20,0x0C,0x05,0xD0,0x6E,0x06,0x92,0x40,0x01,0x47,
    0xA3,0x14,0xA0,0x1A,0x08,0x30,0x22,0x00,0xB1,0x08,0x04,0x20,
    0x16,0x81,0x00,0xC4,0x22,0x10,0x00,0xD9,0x08,0x02,0x20,0x1B,0x41,0x00,0x64,0x23,0x08,0x80,0x6C,0x84,0x00,0x90,0x8D,0x10,0x00,0xB1,0x08,0x02,0x20,0x16,0x41,0x00,0xC4,0x22,0x08,0x80,0x58,0x84,0x00,0x10,0x8B,0x08,0x00,0xB1,0x08,0x01,0x00,0x29,0x8A,0x2A,0xE3,0xAE,0x3E,0x04,0x37,0x00,0x00,0x00,0x00,0x49,0x45,0x4E,0x44,0xAE,0x42,0x60,0x82
])

try:
    with open("/home/workspace/IMPGING-Distro/android-project/app/src/main/res/drawable/ic_launcher.png", "wb") as f:
        f.write(PNG_DATA)
    print("   ✅ Icon created")
except:
    # Create a simple 1x1 placeholder
    with open("/home/workspace/IMPGING-Distro/android-project/app/src/main/res/drawable/ic_launcher.png", "wb") as f:
        f.write(bytes([0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,0x00,0x00,0x00,0x0D,0x49,0x48,0x44,0x52,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,0xDE,0x00,0x00,0x00,0x0C,0x49,0x44,0x41,0x54,0x08,0xD7,0x63,0x28,0x69,0x00,0x00,0x00,0x82,0x00,0x81,0xED,0x36,0xBA,0xD7,0x00,0x00,0x00,0x00,0x49,0x45,0x4E,0x44,0xAE,0x42,0x60,0x82]))
    print("   ⚠️  Placeholder icon (build will use Android default)")
IMGEOF

# ── Step 4: Create Chaquopy Python bootstrap ──────────────────────────────────
cat > "$ANDROID/app/src/main/python/qengine_bridge.py" << 'PYEOF'
"""Chaquopy bridge — exposes QClassifier to Java."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from impging_standalone import QClassifier as _QC
_classifier = _QC()

def get_classifier():
    return _classifier

def classify_process(name):
    return _classifier.classify(name)
PYEOF

# ── Step 5: Download Gradle if needed ─────────────────────────────────────────
echo "[5/6] Setting up Gradle..."
if [ ! -f "$ANDROID/gradlew" ]; then
    GRADLE_URL="https://services.gradle.org/distributions/gradle-8.4-bin.zip"
    echo "   Downloading Gradle 8.4 (first time only)..."
    curl -L -o /tmp/gradle.zip "$GRADLE_URL" 2>/dev/null
    unzip -q /tmp/gradle.zip -d /tmp/ 2>/dev/null
    export PATH="/tmp/gradle-8.4/bin:$PATH"
fi

# Create gradlew wrapper script
cat > "$ANDROID/gradlew" << 'GRADLEOF'
#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
    mkdir -p gradle/wrapper
    curl -L -o gradle/wrapper/gradle-wrapper.jar \
        "https://raw.githubusercontent.com/gradle/gradle/v8.4.0/gradle/wrapper/gradle-wrapper.jar" 2>/dev/null
fi
exec gradle "$@"
GRADLEOF
chmod +x "$ANDROID/gradlew"

# ── Step 6: Build the APK ─────────────────────────────────────────────────────
echo "[6/6] Building APK..."
echo ""
cd "$ANDROID"

if [ -f "local.properties" ]; then
    echo "local.properties exists"
else
    echo "sdk.dir=$ANDROID_SDK_ROOT" > local.properties
fi

./gradlew assembleDebug --no-daemon 2>&1 | tail -30

APK="$ANDROID/app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK" ]; then
    SIZE=$(du -h "$APK" | cut -f1)
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║   ✅ APK BUILT SUCCESSFULLY!                          ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo "   📦 $APK"
    echo "   📊 Size: $SIZE"
    echo ""
    echo "   Install via ADB:"
    echo "   adb install $APK"
    echo "   Or transfer to phone and install directly."
else
    echo "❌ Build failed. Check errors above."
    echo ""
    echo "Common fixes:"
    echo "  - Install Android SDK: https://developer.android.com/studio"
    echo "  - Set ANDROID_SDK_ROOT environment variable"
    echo "  - Or open $ANDROID in Android Studio and build from there"
fi
