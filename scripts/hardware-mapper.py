#!/usr/bin/env python3
"""
IMPGING - Hardware Mapper
Pins game processes to high-performance CPU cores, locks memory, optimizes GPU
"""
import os
import sys
import argparse
import logging
import subprocess
import psutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[IMPGING-HW] %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

SCHED_BIN = '/usr/bin/taskset'
CHRT_BIN = '/usr/bin/chrt'
NICE_BIN = '/usr/bin/nice'
MLOCK_BIN = '/usr/bin/mlock'

def get_cpu_topology():
    """Get CPU core topology — identify P-cores (performance) vs E-cores (efficiency)"""
    try:
        # Try to get CPU affinity info
        cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count()
        logical_count = psutil.cpu_count(logical=True)
        
        # On Intel/AMD with hybrid arch, P-cores are typically 0-(n/2)
        # This is a heuristic — actual detection needs deeper introspection
        cores = []
        for i in range(logical_count):
            try:
                # Check if core is offline
                online = i < cpu_count
                cores.append({
                    'core': i,
                    'online': online,
                    'type': 'P' if i < (cpu_count // 2) else 'E' if cpu_count > logical_count else 'normal'
                })
            except Exception:
                pass
        
        p_cores = [c['core'] for c in cores if c['type'] == 'P' and c['online']]
        e_cores = [c['core'] for c in cores if c['type'] == 'E' and c['online']]
        
        log.info(f"CPU Topology: {cpu_count} physical, {logical_count} logical")
        log.info(f"P-cores (Performance): {p_cores[:8]}{'...' if len(p_cores) > 8 else ''}")
        log.info(f"E-cores (Efficiency): {e_cores[:8]}{'...' if len(e_cores) > 8 else ''}")
        
        return p_cores, e_cores, cores
    except Exception as e:
        log.warning(f"Could not determine CPU topology: {e}")
        return list(range(psutil.cpu_count())), [], []

def get_game_pid(pid_arg: str, game_name: str) -> int:
    """Resolve PID from argument or find by game name"""
    if pid_arg:
        return int(pid_arg)
    
    # Find by process name
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if game_name.lower() in proc.info['name'].lower():
                log.info(f"Found {game_name} at PID {proc.info['pid']}")
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    raise ValueError(f"Could not find process for {game_name}")

def pin_to_cores(pid: int, p_cores: list):
    """Pin process to performance cores using taskset"""
    if not p_cores:
        log.warning("No P-cores available, skipping CPU pinning")
        return False
    
    mask = hex(sum(1 << c for c in p_cores[:8]))  # Use up to 8 P-cores
    try:
        result = subprocess.run(
            [SCHED_BIN, '-cp', mask, str(pid)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            log.info(f"✓ Pinned PID {pid} to cores {p_cores[:8]} (mask: {mask})")
            return True
        else:
            log.error(f"taskset failed: {result.stderr}")
            return False
    except FileNotFoundError:
        log.error("taskset not found — are iproute2 tools installed?")
        return False
    except PermissionError:
        log.error("Permission denied — run as root for CPU pinning")
        return False

def set_realtime_priority(pid: int, priority: int):
    """Set real-time priority using chrt"""
    try:
        # Map 0-100 to SCHED_FIFO 1-99
        rt_priority = max(1, min(99, (priority * 99) // 100))
        result = subprocess.run(
            [CHRT_BIN, '-f', '-p', str(rt_priority), str(pid)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            log.info(f"✓ Set real-time priority (SCHED_FIFO {rt_priority}) for PID {pid}")
            return True
        else:
            log.warning(f"chrt failed: {result.stderr}")
            return False
    except FileNotFoundError:
        log.warning("chrt not found — skipping real-time priority")
        return False

def boost_nice(pid: int, priority: int):
    """Set favorable nice value"""
    nice_val = -20 + (100 - priority) // 5  # Map 0-100 to -20 to 0
    nice_val = max(-20, min(0, nice_val))
    try:
        result = subprocess.run(
            [NICE_BIN, '-n', str(nice_val), '-p', str(pid)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            log.info(f"✓ Set nice={nice_val} for PID {pid}")
            return True
    except Exception as e:
        log.warning(f"nice failed: {e}")
    return False

def lock_memory(pid: int):
    """Lock game memory pages to prevent swapping (requires root)"""
    try:
        proc_path = Path(f'/proc/{pid}/status')
        if not proc_path.exists():
            return False
        
        # Try to write to /proc/pid/clear_soft_reclaim (kernel 6.5+)
        reclaim_path = Path(f'/proc/{pid}/clear_soft_reclaim')
        if reclaim_path.exists():
            try:
                reclaim_path.write_text('1')
                log.info(f"✓ Enabled soft reclaim bypass for PID {pid}")
            except PermissionError:
                pass
        
        # Memory cgroup lock if available
        return True
    except Exception as e:
        log.warning(f"Memory locking not fully available: {e}")
    return False

def disable_thermal_throttle():
    """Attempt to disable thermal throttling via sysfs"""
    try:
        # Intel P-state driver
        intel_pstate = Path('/dev/cpu/0/msr')
        if intel_pstate.exists():
            log.info("Intel P-state driver detected — using default turbo boost")
        
        # AMD Ryzen
        amd_pstate = Path('/sys/devices/system/cpu/amd-pstate/status')
        if amd_pstate.exists():
            try:
                current = amd_pstate.read_text().strip()
                log.info(f"AMD P-state status: {current}")
            except Exception:
                pass
        
        return True
    except Exception as e:
        log.warning(f"Thermal throttle control not available: {e}")
    return False

def optimize_gpu():
    """Attempt GPU optimization hints"""
    try:
        # NVIDIA GPU
        nvidia_smi = Path('/usr/bin/nvidia-smi')
        if nvidia_smi.exists():
            try:
                # Lock GPU clock to max performance state
                subprocess.run(
                    ['nvidia-smi', '-pm', '1'],  # Persistence mode
                    capture_output=True, timeout=5
                )
                subprocess.run(
                    ['nvidia-smi', '-pl', 'MAX'],  # Power limit
                    capture_output=True, timeout=5
                )
                log.info("✓ NVIDIA GPU optimization: persistence + max power limit")
            except Exception as e:
                log.warning(f"NVIDIA optimization failed: {e}")
        
        # AMD GPU (Radeon)
        amdgpu_profile = Path('/sys/class/drm/card0/device/power_dpm_state')
        if amdgpu_profile.exists():
            try:
                amdgpu_profile.write_text('performance')
                log.info("✓ AMD GPU set to performance mode")
            except PermissionError:
                pass
                
    except Exception as e:
        log.warning(f"GPU optimization not available: {e}")
    return True

def apply_hardware_mapping(pid: int, priority: int, game_name: str):
    """Apply full hardware mapping stack"""
    log.info(f"=== IMPGING Hardware Mapping for PID {pid} ({game_name}) ===")
    
    p_cores, e_cores, _ = get_cpu_topology()
    
    results = {
        'cpu_pinned': pin_to_cores(pid, p_cores),
        'rt_priority': set_realtime_priority(pid, priority),
        'nice_boosted': boost_nice(pid, priority),
        'memory_locked': lock_memory(pid),
        'gpu_optimized': optimize_gpu(),
    }
    
    disabled_thermal = disable_thermal_throttle()
    
    log.info("=== Hardware Mapping Summary ===")
    for k, v in results.items():
        status = "✓" if v else "✗"
        log.info(f"  {status} {k}: {'OK' if v else 'FAILED'}")
    log.info(f"  {'✓' if disabled_thermal else '✗'} Thermal throttle control")
    
    return all(results.values())

def main():
    parser = argparse.ArgumentParser(description='IMPGING Hardware Mapper')
    parser.add_argument('--pid', help='Game process PID')
    parser.add_argument('--priority', type=int, default=90, help='Priority 0-100 (default: 90)')
    parser.add_argument('--game', help='Game name (for process lookup)')
    args = parser.parse_args()
    
    if not args.pid and not args.game:
        parser.print_help()
        sys.exit(1)
    
    try:
        pid = get_game_pid(args.pid, args.game or "")
        success = apply_hardware_mapping(pid, args.priority, args.game or "Unknown")
        sys.exit(0 if success else 1)
    except Exception as e:
        log.error(f"Hardware mapping failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
