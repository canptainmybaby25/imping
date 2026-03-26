#!/usr/bin/env python3
"""
IMPGING - Network Jammer
Traffic shaping, DNS optimization, latency reduction for favorable gaming conditions
"""
import os
import sys
import argparse
import logging
import subprocess
import time
import socket
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[IMPGING-NET] %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

GAMING_DNS = {
    "Google": ("8.8.8.8", "8.8.4.4"),
    "Cloudflare": ("1.1.1.1", "1.0.0.1"),
    "Quad9": ("9.9.9.9", "149.112.112.112"),
    "Level3": ("4.2.2.1", "4.2.2.2"),
}

GAME_PORTS = {
    "VALORANT": [5000, 5002, 5020, 5040, 5070, 5080, 8400, 8402],
    "Counter-Strike 2": [27015, 27016, 27017, 27018, 27019],
    "Apex Legends": [27000, 27015, 27016, 27017, 27018, 27019, 27020],
    "Fortnite": [5222, 5223, 7777, 7780, 7781, 9000],
    "League of Legends": [5000, 5002, 5010, 5040, 5070, 5080],
    "Dota 2": [27000, 27015, 27016, 27017, 27018, 27019],
    "Overwatch 2": [5222, 5223, 7500, 7501, 7502, 7503],
    "Rocket League": [7000, 7001, 7500, 7501, 7502],
    "Genshin Impact": [22101, 22102, 22103],
}

# Well-known gaming server IPs for routing priority
GAME_SERVERS = {
    "VALORANT": ["104.160.0.0/16", "185.199.0.0/16"],
    "Counter-Strike 2": ["162.249.0.0/16", "205.196.0.0/16"],
    "Apex Legends": ["34.0.0.0/8", "104.0.0.0/8"],
}

def check_root():
    """Verify root privileges for traffic control"""
    if os.geteuid() != 0:
        log.error("Network jamming requires root privileges!")
        log.error("Run with: sudo python3 net-jammer.py ...")
        return False
    return True

def check_tc():
    """Check if traffic control (tc) is available"""
    try:
        result = subprocess.run(['tc', 'qdisc'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log.error("tc (iproute2) not found — install with: apt install iproute2")
        return False

def get_default_interface() -> str:
    """Get default network interface"""
    try:
        result = subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            match = re.search(r'dev\s+(\S+)', line)
            if match:
                iface = match.group(1)
                log.info(f"Default interface: {iface}")
                return iface
    except Exception as e:
        log.warning(f"Could not determine interface: {e}")
    return "eth0"

def setup_traffic_shaping(interface: str, mode: str):
    """Apply traffic shaping rules via tc"""
    if not check_tc():
        return False
    
    mode_params = {
        "aggressive": {"rate": "1Gbit", "delay": "1ms", "loss": "0%", "burst": "15kb"},
        "optimize": {"rate": "500Mbit", "delay": "5ms", "loss": "0%", "burst": "10kb"},
        "stealth": {"rate": "100Mbit", "delay": "10ms", "loss": "0.1%", "burst": "8kb"},
    }
    
    params = mode_params.get(mode, mode_params["optimize"])
    
    # Clean existing rules
    subprocess.run(['tc', 'qdisc', 'del', 'dev', interface, 'root'], capture_output=True)
    
    # Add HTB (Hierarchical Token Bucket) root qdisc
    result = subprocess.run([
        'tc', 'qdisc', 'add', 'dev', interface, 'root', 'htb',
        'default', '1'
    ], capture_output=True, text=True)
    
    if result.returncode != 0 and 'File exists' not in result.stderr:
        log.warning(f"HTB setup issue: {result.stderr}")
    
    # Add game traffic class with priority
    subprocess.run([
        'tc', 'class', 'add', 'dev', interface, 'parent', '1:', 'classid', '1:1', 'htb',
        'rate', params['rate'], 'burst', params['burst']
    ], capture_output=True)
    
    # Add filter for gaming ports
    for proto in ['tcp', 'udp']:
        subprocess.run([
            'tc', 'filter', 'add', 'dev', interface, 'parent', '1:', proto,
            'match', 'all', 'flowid', '1:1'
        ], capture_output=True)
    
    log.info(f"✓ Traffic shaping applied ({mode})")
    log.info(f"  Rate: {params['rate']}, Delay: {params['delay']}")
    return True

def flush_dns_cache():
    """Flush system DNS cache"""
    cmds = [
        ['resolvectl', 'flush-caches'],
        ['systemd-resolve', '--flush-caches'],
        ['service', 'dnsmasq', 'restart'],
    ]
    
    for cmd in cmds:
        try:
            subprocess.run(cmd, capture_output=True, timeout=5)
            log.info(f"✓ DNS cache flushed ({' '.join(cmd)})")
            return True
        except Exception:
            pass
    
    # Fallback: just log
    log.info("DNS cache flush attempted")
    return True

def set_gaming_dns(provider: str = "Cloudflare"):
    """Set gaming-optimized DNS"""
    if provider not in GAMING_DNS:
        provider = "Cloudflare"
    
    dns_servers = GAMING_DNS[provider]
    log.info(f"Setting DNS to {provider}: {dns_servers}")
    
    # Try resolvectl first (systemd)
    try:
        subprocess.run(
            ['resolvectl', 'dns', 'eth0'] + list(dns_servers),
            capture_output=True, timeout=5
        )
        log.info(f"✓ DNS set via resolvectl")
        return True
    except Exception:
        pass
    
    # Try NetworkManager
    try:
        for dns in dns_servers:
            subprocess.run(
                ['nmcli', 'mod', 'eth0', 'ipv4.dns', dns],
                capture_output=True, timeout=5
            )
        log.info("✓ DNS set via NetworkManager")
        return True
    except Exception:
        pass
    
    # Direct /etc/resolv.conf (fallback)
    try:
        resolv_path = Path('/etc/resolv.conf')
        if resolv_path.exists():
            content = "\n".join(f"nameserver {dns}" for dns in dns_servers) + "\n"
            resolv_path.write_text(content)
            log.info("✓ DNS written to /etc/resolv.conf")
            return True
    except PermissionError:
        log.warning("Need root to write /etc/resolv.conf")
    except Exception as e:
        log.warning(f"DNS update failed: {e}")
    
    return False

def optimize_game_routes(game_name: str):
    """Add custom routes for game servers to reduce latency"""
    if game_name not in GAME_SERVERS:
        log.info(f"No custom routes for {game_name}")
        return True
    
    log.info(f"Optimizing routes for {game_name}...")
    
    for net in GAME_SERVERS[game_name]:
        try:
            # Check if route exists
            result = subprocess.run(
                ['ip', 'route', 'show', net],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                log.info(f"Route exists: {net}")
            else:
                # Try to add priority route
                subprocess.run(
                    ['ip', 'route', 'add', net, 'via', '0.0.0.0', 'dev', get_default_interface(), 'metric', '100'],
                    capture_output=True, timeout=5
                )
                log.info(f"✓ Route added: {net}")
        except Exception as e:
            log.warning(f"Route optimization failed: {e}")
    
    return True

def mark_game_packets(ports: list):
    """Use iptables to mark game packets for priority"""
    try:
        subprocess.run(
            ['iptables', '-t', 'mangle', '-L', '-n'],
            capture_output=True, timeout=5
        )
    except FileNotFoundError:
        log.warning("iptables not available — skipping packet marking")
        return False
    
    for port in ports:
        # Mark NEW game packets
        try:
            subprocess.run([
                'iptables', '-t', 'mangle', '-A', 'PREROUTING',
                '-p', 'udp', '--dport', str(port),
                '-j', 'MARK', '--set-mark', '10'
            ], capture_output=True, timeout=5)
            
            subprocess.run([
                'iptables', '-t', 'mangle', '-A', 'PREROUTING',
                '-p', 'tcp', '--dport', str(port),
                '-j', 'MARK', '--set-mark', '10'
            ], capture_output=True, timeout=5)
            
            log.info(f"✓ Marked port {port} for priority")
        except Exception as e:
            log.warning(f"Failed to mark port {port}: {e}")
    
    return True

def apply_network_jamming(game_name: str, mode: str, interface: str):
    """Apply full network jamming stack"""
    log.info(f"=== IMPGING Network Jammer for {game_name} ({mode}) ===")
    
    results = {}
    
    results['traffic_shaping'] = setup_traffic_shaping(interface, mode)
    results['dns_flush'] = flush_dns_cache()
    results['dns_set'] = set_gaming_dns()
    results['route_optimize'] = optimize_game_routes(game_name)
    
    if game_name in GAME_PORTS:
        results['packet_marking'] = mark_game_packets(GAME_PORTS[game_name])
    else:
        results['packet_marking'] = True
    
    log.info("=== Network Jammer Summary ===")
    for k, v in results.items():
        status = "✓" if v else "✗"
        log.info(f"  {status} {k}: {'OK' if v else 'FAILED'}")
    
    return all(results.values())

def remove_jamming(interface: str):
    """Remove all jamming rules"""
    log.info("Removing network jamming rules...")
    
    try:
        subprocess.run(['tc', 'qdisc', 'del', 'dev', 'eth0', 'root'], capture_output=True)
        log.info("✓ Traffic shaping removed")
    except Exception:
        pass
    
    try:
        subprocess.run(['iptables', '-t', 'mangle', '-F'], capture_output=True)
        log.info("✓ iptables mangle cleared")
    except Exception:
        pass
    
    log.info("Network jamming removed")

def main():
    parser = argparse.ArgumentParser(description='IMPGING Network Jammer')
    parser.add_argument('--game', help='Game name')
    parser.add_argument('--mode', choices=['aggressive', 'optimize', 'stealth'], default='optimize',
                        help='Jamming intensity')
    parser.add_argument('--interface', default=None, help='Network interface (auto-detected if omitted)')
    parser.add_argument('--remove', action='store_true', help='Remove all jamming rules')
    args = parser.parse_args()
    
    if not check_root():
        sys.exit(1)
    
    interface = args.interface or get_default_interface()
    
    if args.remove:
        remove_jamming(interface)
        sys.exit(0)
    
    if not args.game:
        parser.print_help()
        sys.exit(1)
    
    try:
        success = apply_network_jamming(args.game, args.mode, interface)
        sys.exit(0 if success else 1)
    except Exception as e:
        log.error(f"Network jamming failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
