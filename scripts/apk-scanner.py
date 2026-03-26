#!/usr/bin/env python3
"""
IMPGING Q-Engine: Quantum-Inspired Process Classifier
Superposition states, interference scoring, entanglement tracking.
Pure-Python implementation — no numpy dependency.
"""
import os, sys, time, argparse, logging, hashlib, json, re, psutil, threading, math
from pathlib import Path
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='[IMPGING-Q] %(asctime)s | %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# ── Signature Database ───────────────────────────────────────
CASINO_KW  = ["jackpot","casino","poker","slots","betting","bookie","rummy","teenpatti","andarbahar","tongits","sweepstakes","lottery","keno","bingo","sportsbet","bet365","betway","parimatch","1xbet","22bet","betfair","williamhill","dafabet","bodog","bovada","mybookie","betonline","craps","roulette","baccarat","minigame","lucky","fortune","vegas","streak","gambling","wager","stake","roobet","bitstarz","mbit","7bit","fairspin","betplay","betcrypto"]
GAMING_KW  = ["roblox","minecraft","fortnite","valorant","pubg","genshin","gta","fifa","nba2k","cod","overwatch","apex","league","legends","dota","csgo","cs2","steam","epic","origin","mobilelegends","mobile legends","bangbang","wildrift","call of duty","subway","candy crush","tiktok","discord","steamweb","battle.net","leagueoflegends","steamwebhelper","hlv","halflife","left4dead","portal","teamfortress","tf2","unreal","unity"]
MALWARE_KW = ["hack","crack","cheat","injector","spoofer","modmenu","gameguardian","gg","freedom","lucky","patcher","cracked","keygen","loader","activator","exploit","hax","aimbot","wallhack","speedhack","teleport","triggerbot","ghost","phantom","skull","menux","liberty","postern","vpnhub","ultrasurf","lantern","psiphon","freevpn","hideit","cloack","banking","stealer","keylog","rat"]
SUSPICIOUS_PATTERNS = [re.compile(r'^[a-z0-9]{32,}$', re.I), re.compile(r'(temp|tmp|cache|download).+\.exe$', re.I), re.compile(r'(screen|capture|record|keylog|hook)', re.I), re.compile(r'(proxy|tunnel|vpn|tor)', re.I)]
PROB_WEIGHTS = {'CASINO': 1.0, 'GAMING': 0.9, 'MALWARE': 1.2, 'SUSPICIOUS': 0.6}
VEC_DIM = 256

# ── Quantum Classifier ─────────────────────────────────────────
class QClassifier:
    def __init__(self):
        self.db = {'CASINO': CASINO_KW, 'GAMING': GAMING_KW, 'MALWARE': MALWARE_KW}
        self.entanglement_log = deque(maxlen=1024)
        self.phase_history    = deque(maxlen=256)
        self.process_cache    = {}
        self._compile_signatures()

    def _hash_kw(self, s: str) -> int:
        return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) % VEC_DIM

    def _compile_signatures(self):
        self.kw_vectors = {}
        for cat, kws in self.db.items():
            vec = [0.0] * VEC_DIM
            for kw in kws:
                idx = self._hash_kw(kw)
                vec[idx] = 1.0
            self.kw_vectors[cat] = vec
        self.susp_vec = [0.0] * VEC_DIM
        for p in SUSPICIOUS_PATTERNS:
            try:
                idx = self._hash_kw(p.pattern[:16])
                self.susp_vec[idx] = 0.7
            except: pass

    def _dot(self, a, b):
        return sum(x*y for x,y in zip(a,b))

    def _norm(self, v):
        m = math.sqrt(sum(x*x for x in v))
        return m if m > 1e-9 else 1.0

    def _interference(self, proc_vec, cat_vec) -> float:
        dot  = self._dot(proc_vec, cat_vec)
        magP = self._norm(proc_vec)
        magC = self._norm(cat_vec)
        return dot / (magP * magC)

    def _superposition_scan(self, name: str) -> dict:
        proc_vec = [0.0] * VEC_DIM
        for i in range(0, max(len(name)-3, 1), 2):
            chunk = name[i:i+4]
            idx   = self._hash_kw(chunk)
            proc_vec[idx] += 1.0
        n = self._norm(proc_vec)
        if n > 1e-9:
            proc_vec = [x/n for x in proc_vec]
        results = {}
        for cat, cat_vec in self.kw_vectors.items():
            interf = self._interference(proc_vec, cat_vec)
            phase  = interf * math.pi
            amp    = interf
            prob   = amp ** 2
            results[cat] = {'interference': interf, 'phase': phase, 'probability': prob, 'amplitude': amp}
        return results

    def classify(self, name: str, path: str = "", pid: int = 0) -> dict:
        cache_key = f"{pid}:{name}"
        if cache_key in self.process_cache:
            return self.process_cache[cache_key]
        results  = self._superposition_scan(name)
        susp_score = 0.0
        for p in SUSPICIOUS_PATTERNS:
            if p.search(name) or p.search(path):
                susp_score += 0.4
        if any(x in path.lower() for x in ['temp','tmp','cache','download']):
            susp_score += 0.3
        if susp_score > 0:
            results['SUSPICIOUS'] = {'interference': susp_score, 'phase': 0.0, 'probability': min(susp_score, 1.0), 'amplitude': susp_score}
        final_state = {}
        for cat, state in results.items():
            w = PROB_WEIGHTS.get(cat, 0.5)
            final_state[cat] = round(state['probability'] * w, 4)
        max_cat = max(final_state, key=final_state.get)
        max_prob = final_state[max_cat]
        if max_prob < 0.05:
            final_state['UNKNOWN'] = round(max(0.05 - max_prob, 0.05), 4)
        entanglement = {'pid': pid, 'name': name, 'state': dict(final_state), 'timestamp': datetime.now().isoformat()}
        self.entanglement_log.append(entanglement)
        self.phase_history.append({'name': name, 'max': max_cat, 'prob': max_prob})
        result = {'category': max_cat, 'confidence': max_prob, 'all_states': final_state, 'entanglement': entanglement}
        self.process_cache[cache_key] = result
        return result

# ── Parallel Scanner ───────────────────────────────────────────
def scan_proc(proc, classifier):
    try:
        pinfo = proc.as_dict(attrs=['pid','name','exe','create_time'])
        if pinfo['pid'] in (0, 4):
            return None
        return classifier.classify(pinfo['name'], pinfo.get('exe','') or '', pinfo['pid']), pinfo
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

def parallel_scan(processes, classifier, workers=16):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(scan_proc, p, classifier): p for p in processes}
        for future in as_completed(futures):
            r = future.result()
            if r:
                results.append(r)
    return results

# ── Entropy Tester ─────────────────────────────────────────────
def shannon_entropy(s: str) -> float:
    freq = [0.0] * 256
    for b in s.encode():
        freq[b] += 1
    entropy = 0.0
    n = len(s)
    for f in freq:
        if f > 0:
            p = f / n
            entropy -= p * (math.log2(p) if p > 0 else 0)
    return entropy

# ── Main ────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description='IMPGING Q-Engine')
    p.add_argument('--monitor',  action='store_true', help='Continuous monitoring')
    p.add_argument('--interval', type=float, default=2.0, help='Scan interval (s)')
    p.add_argument('--once',     action='store_true', help='Single snapshot')
    p.add_argument('--sigs',     action='store_true', help='Show signature database')
    p.add_argument('--entropy',  action='store_true', help='Run entropy stress-test')
    args = p.parse_args()
    classifier = QClassifier()

    if args.sigs:
        print(f"🃏 CASINO  ({len(CASINO_KW)}): {', '.join(sorted(CASINO_KW))}")
        print(f"🎮 GAMING  ({len(GAMING_KW)}): {', '.join(sorted(GAMING_KW))}")
        print(f"⚠️  MALWARE ({len(MALWARE_KW)}): {', '.join(sorted(MALWARE_KW))}")
        return

    if args.entropy:
        test_names = ["javaw", "svchost", "LsASS", "cmd", "~TM465xz", "xH4ck.exe", "FortniteLauncher", "bet365", "explorer"]
        print(f"\n  {'Process':<25} {'Entropy':>8}  Classification")
        print(f"  {'-'*25} {'-'*8}  {'-'*20}")
        for tn in test_names:
            r = classifier.classify(tn)
            print(f"  {tn:<25} {shannon_entropy(tn):>8.4f}  {r['category']} ({r['confidence']:.3f})")
        return

    stats = {'CASINO': 0, 'GAMING': 0, 'MALWARE': 0, 'SUSPICIOUS': 0, 'UNKNOWN': 0}
    seen_pids = set()
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║      ⚛️  IMPGING Q-ENGINE — Quantum Classifier          ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    def snapshot():
        nonlocal seen_pids, stats
        procs   = list(psutil.process_iter(['pid','name','exe','create_time']))
        results = parallel_scan(procs, classifier)
        new_found = []
        for res, info in results:
            if info['pid'] in seen_pids:
                continue
            seen_pids.add(info['pid'])
            cat  = res['category']
            conf = res['confidence']
            if conf >= 0.25:
                stats[cat] = stats.get(cat, 0) + 1
                new_found.append((cat, conf, info['name'], info['pid'], info.get('exe','')))
        if new_found:
            print(f"\n{'─'*62}")
            print(f"  🆕 PROCESS COLLAPSE — Quantum State Detection")
            for cat, conf, name, pid, exe in sorted(new_found, key=lambda x: -x[1]):
                bar  = '█' * int(conf * 20) + '░' * (20 - int(conf * 20))
                flag = '🔴' if cat in ('CASINO','MALWARE') else '🟡'
                print(f"  {flag} [{cat:12}] {bar} {conf:.2f}  {name} (PID:{pid})")
        print(f"\n  📊 Collapsed States — 🃏{stats['CASINO']}  🎮{stats['GAMING']}  ⚠️{stats['MALWARE']}  👁️{stats['SUSPICIOUS']}  ❓{stats['UNKNOWN']}")
        print(f"  🔗 Entanglement entries: {len(classifier.entanglement_log)}")

    if args.monitor or not args.once:
        print(f"[⚛️  MONITOR MODE] Interval: {args.interval}s | Press Ctrl+C to stop\n")
        try:
            while True:
                snapshot()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n[⬛] IMPGING Q-Engine collapsed. Shutdown complete.")
    else:
        snapshot()

if __name__ == '__main__':
    main()
