#!/usr/bin/env python3
"""
IMPGING - Cross-Platform Launcher
Handles all IMPGING operations from a single unified interface.
"""
import sys, os, argparse, time, importlib.util, psutil
from pathlib import Path

# Resolve IMPGING scripts path (works in Zo Computer + standalone)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_IMPING = os.path.join(SCRIPT_DIR, "Skills", "imping", "scripts")
ALT_SCRIPTS = os.path.join(SCRIPT_DIR, "scripts")

def resolve_script(name):
    """Find script in local scripts/ folder"""
    here = Path(__file__).parent
    local = here / "scripts" / name
    if local.exists():
        return str(local)
    return None

def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def _load_qclassifier():
    path = resolve_script("apk-scanner.py")
    mod = load_mod("apk_scanner", path)
    return mod.QClassifier(), mod.parallel_scan, mod.scan_proc, mod.shannon_entropy

def cmd_scan(args):
    clf, parallel_scan, _, _ = _load_qclassifier()
    procs = list(psutil.process_iter(['pid','name','exe','create_time']))
    results = parallel_scan(procs, clf)
    for res, info in sorted(results, key=lambda x: -x[0]['confidence'])[:20]:
        icon = res.get('icon','❓')
        print(f"{icon} {res['category']:12s} {res['confidence']:.2f}  {info['name']} (PID:{info['pid']})")

def cmd_monitor(args):
    clf, parallel_scan, _, _ = _load_qclassifier()
    interval = args.interval or 2
    seen_pids = set()
    print(f"⚛️  IMPGING Q-Engine Active — monitoring every {interval}s  (Ctrl+C to stop)")
    try:
        while True:
            procs = list(psutil.process_iter(['pid','name','exe','create_time']))
            results = parallel_scan(procs, clf)
            flagged = [(r,i) for r,i in results if r['confidence'] >= 0.25 and r['category'] not in ('UNKNOWN','BENIGN')]
            new = [(r,i) for r,i in flagged if i['pid'] not in seen_pids]
            for r,i in new:
                seen_pids.add(i['pid'])
                bar = '█'*int(r['confidence']*20)+'░'*(20-int(r['confidence']*20))
                flag = '🔴' if r['category'] in ('CASINO','MALWARE') else '🟡'
                print(f"\n{flag} [{r['category']:12}] {bar} {r['confidence']:.2f}  {i['name']} (PID:{i['pid']})")
            if not new:
                print(f"✅ {len(procs)} processes — clean", end='\r')
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n⏹️  IMPGING Q-Engine stopped.")

def cmd_entropy(args):
    _, _, _, sh_entropy = _load_qclassifier()
    test_names = ["javaw","svchost","LsASS","cmd","~TM465xz","xH4ck.exe","FortniteLauncher","bet365","explorer"]
    clf, _, _, _ = _load_qclassifier()
    print(f"\n  {'Process':<26} {'Entropy':>7}  {'Classification'}")
    print(f"  {'-'*26} {'-'*7}  {'-'*20}")
    for tn in test_names:
        r = clf.classify(tn)
        print(f"  {tn:<26} {sh_entropy(tn):>7.4f}  {r['category']} ({r['confidence']:.3f})")

def cmd_game(args):
    path = resolve_script("game-detector.py")
    if not path:
        print("❌ game-detector.py not found")
        return
    mod = load_mod("game_detector", path)
    det = mod.GameDetector()
    if args.action == "start":
        det.start_monitoring(args.game or "DETECT")
    elif args.action == "stop":
        det.stop_monitoring()
    elif args.action == "status":
        det.status()

def cmd_hw(args):
    path = resolve_script("hardware-mapper.py")
    if not path:
        print("❌ hardware-mapper.py not found")
        return
    mod = load_mod("hardware_mapper", path)
    hm = mod.HardwareMapper()
    if args.action == "pin":
        hm.pin_process(args.pid)
    elif args.action == "release":
        hm.release_process(args.pid)
    elif args.action == "status":
        hm.status()

def cmd_mimic(args):
    path = resolve_script("mimic-engine.py")
    if not path:
        print("❌ mimic-engine.py not found")
        return
    mod = load_mod("mimic_engine", path)
    import threading
    engine = mod.MimicEngine(
        mode=args.mode,
        interval=args.interval,
        protect=not args.no_protect,
        efficiency=not args.no_efficiency,
        kill=not args.no_kill,
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
        print(f"  Mimic candidates : {mimic}")
        print(f"  Energy budget    : {engine.energy_budget:.3f}")
        return
    print(f"⚛️  Mimic Engine running in {args.mode} mode — Ctrl+C to stop")
    engine.start()

def cmd_net(args):
    path = resolve_script("net-jammer.py")
    if not path:
        print("❌ net-jammer.py not found")
        return
    mod = load_mod("net_jammer", path)
    nj = mod.NetworkJammer()
    if args.action == "start":
        nj.start(game_name=args.target, mode=args.mode)
    elif args.action == "stop":
        nj.stop()
    elif args.action == "status":
        nj.status()

def main():
    parser = argparse.ArgumentParser(
        prog="imping",
        description="⚛️ IMPGING Q-Engine — Quantum-Inspired Gaming Optimizer"
    )
    sub = parser.add_subparsers()

    p = sub.add_parser("scan", help="Quantum process scan")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("monitor", help="Real-time quantum monitoring")
    p.add_argument("--interval", type=int, help="Scan interval in seconds")
    p.set_defaults(func=cmd_monitor)

    p = sub.add_parser("entropy", help="Shannon entropy analysis")
    p.set_defaults(func=cmd_entropy)

    p = sub.add_parser("game", help="Game detector control")
    p.add_argument("action", choices=["start","stop","status"])
    p.add_argument("--game", type=str)
    p.set_defaults(func=cmd_game)

    p = sub.add_parser("hw", help="Hardware mapper control")
    p.add_argument("action", choices=["pin","release","status"])
    p.add_argument("--pid", type=int)
    p.set_defaults(func=cmd_hw)

    p = sub.add_parser("net", help="Network jammer control")
    p.add_argument("action", choices=["start","stop","status"])
    p.add_argument("--target", type=str)
    p.add_argument("--mode", type=str, default="balanced", choices=["light","balanced","aggressive"])
    p.set_defaults(func=cmd_net)

    p_mimic = sub.add_parser("mimic", help="⚛️ Mimic Engine — stealth self-protection")
    p_mimic.add_argument("--mode", type=str, default="stealth",
                        choices=["stealth","protect","efficiency","killer"])
    p_mimic.add_argument("--interval", type=float, default=2.0)
    p_mimic.add_argument("--once", action="store_true")
    p_mimic.add_argument("--status", action="store_true")
    p_mimic.add_argument("--no-kill", action="store_true")
    p_mimic.add_argument("--no-efficiency", action="store_true")
    p_mimic.add_argument("--no-protect", action="store_true")
    p_mimic.set_defaults(func=cmd_mimic)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
