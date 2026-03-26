#!/usr/bin/env python3
"""
IMPGING - Status Checker
Shows current IMPGING optimization state
"""
import os
import sys
import psutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[IMPGING-STATUS] %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def check_tc_rules():
    """Check active traffic control rules"""
    try:
        import subprocess
        result = subprocess.run(['tc', 'qdisc', 'show'], capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            log.info("Active TC rules:")
            for line in result.stdout.strip().splitlines():
                log.info(f"  {line}")
            return True
        else:
            log.info("No active traffic shaping rules")
            return False
    except Exception:
        log.info("tc not available")
        return False

def check_cpu_affinity():
    """Check if any game processes have custom affinity"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_affinity']):
            try:
                if proc.info['cpu_affinity']:
                    log.info(f"PID {proc.info['pid']} ({proc.info['name']}): affinity={proc.info['cpu_affinity']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return True
    except Exception:
        return False

def check_game_processes():
    """List detected game processes"""
    KNOWN = ['VALORANT', 'cs2', 'csgo', 'apex', 'fortnite', 'League', 'Dota', 'Rocket', 
             'Genshin', 'Rust', 'Overwatch', 'PUBG', 'FIFA', 'NBA2K']
    found = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            name = proc.info['name'].lower()
            if any(g.lower() in name for g in KNOWN):
                found.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info.get('cpu_percent', 0),
                    'mem_mb': proc.info['memory_info'].rss / 1024 / 1024 if proc.info.get('memory_info') else 0
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if found:
        log.info("Active game processes:")
        for g in found:
            log.info(f"  PID {g['pid']}: {g['name']} (CPU: {g['cpu']:.1f}%, MEM: {g['mem_mb']:.0f}MB)")
    else:
        log.info("No game processes detected")
    
    return found

def check_dns():
    """Check current DNS settings"""
    resolv = Path('/etc/resolv.conf')
    if resolv.exists():
        log.info("Current DNS servers:")
        for line in resolv.read_text().splitlines():
            if line.strip() and not line.startswith('#'):
                log.info(f"  {line.strip()}")

def main():
    log.info("╔══════════════════════════════════════╗")
    log.info("║        IMPGING STATUS CENTER         ║")
    log.info("╚══════════════════════════════════════╝")
    
    log.info("\n── Game Processes ──")
    games = check_game_processes()
    
    log.info("\n── CPU Affinity ──")
    check_cpu_affinity()
    
    log.info("\n── Traffic Shaping ──")
    check_tc_rules()
    
    log.info("\n── DNS Settings ──")
    check_dns()
    
    log.info("\n── System Resources ──")
    log.info(f"CPU: {psutil.cpu_percent(interval=1):.1f}%")
    log.info(f"Memory: {psutil.virtual_memory().percent:.1f}% used")
    log.info(f"Network I/O: {psutil.net_io_counters().bytes_recv/1024/1024:.1f}MB in, {psutil.net_io_counters().bytes_sent/1024/1024:.1f}MB out")

if __name__ == "__main__":
    main()
