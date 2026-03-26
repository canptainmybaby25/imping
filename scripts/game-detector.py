#!/usr/bin/env python3
"""
IMPGING - Game Process Auto-Detector
Automatically detects gaming processes and triggers IMPGING optimization stack
"""
import os
import sys
import signal
import time
import logging
import subprocess
import psutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[IMPGING-DETECTOR] %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

KNOWN_GAMES = {
    # FPS / Shooters
    "VALORANT": ["VALORANT", "Riot Vanguard", "ShooterGame"],
    "Counter-Strike 2": ["cs2", "csgo", "engine", "client"],
    "Apex Legends": ["apex", "r5apex", "EasyAntiCheat"],
    "Fortnite": ["Fortnite", "EpicGamesLauncher", "BE"],
    "Call of Duty": ["CoherentUI", "ModernWarfare", "IW8", "s1", "s2"],
    "Overwatch 2": ["Overwatch", "Overwatch- Retail", "GameParameters"],
    "PUBG": ["PUBG", "TslGame", "UES"],
    "Rust": ["Rust", "rust", "easyanticheat"],
    "Escape from Tarkov": ["EscapeFromTarkov", "BsgLauncher"],
    
    # MOBAs
    "League of Legends": ["League of Legends", "LeagueClient", "LoR", "RiotClientservices"],
    "Dota 2": ["dota2", "GameModule", "steamwebhelper"],
    "Heroes of the Storm": ["HeroesOfTheStorm", "StormUI", "Heroes"],
    
    # Battle Royale
    "Genshin Impact": ["GenshinImpact", "YuanShen", "Genshin"],
    "Honkai: Star Rail": ["StarRail", "崩坏", "Houkai"],
    "Wuthering Waves": ["WutheringWaves", "Waves", "Game"],
    
    # MMORPGs
    "World of Warcraft": ["Wow", "World of Warcraft", "azerothcore"],
    "Final Fantasy XIV": ["ffxiv", "ff14", "FINAL FANTASY XIV"],
    "Black Desert Online": ["BlackDesert", "BDO", "Game"],
    
    # Sports / Racing
    "EA FC (FIFA)": ["EA Sports FC", "FC", "EASW"],
    "NBA 2K": ["NBA2K", "2K", "nba2k"],
    "Rocket League": ["RocketLeague", "Rocket League", "UE4"],
    
    # Platforms
    "Steam": ["steamwebhelper", "Steam", "steam"],
    "Epic Games": ["EpicGamesLauncher", "EpicWebHelper", "EpicGames"],
    "Geforce Now": ["GeForceNOW", "Gfn", "nvidia"],
    
    # Casino / Gambling
    "Bet365": ["bet365", "bet365app"],
    "PokerStars": ["pokerstars", "poker"],
    "888 Casino": ["888casino", "888poker"],
    "DraftKings": ["draftkings"],
    "FanDuel": ["fanduel"],
    "William Hill": ["williamhill"],
    
    # Generic detection
    "Unknown Game": ["game", "Game", "Unity", "UE4", "UE5", "UnrealEngine"],
}

CPU_PRIORITY_MAP = {
    "VALORANT": 98,
    "Counter-Strike 2": 98,
    "Apex Legends": 98,
    "Call of Duty": 98,
    "Overwatch 2": 97,
    "PUBG": 97,
    "Rust": 96,
    "Escape from Tarkov": 98,
    "League of Legends": 95,
    "Dota 2": 95,
    "Rocket League": 96,
    "Genshin Impact": 96,
}

DETECTION_INTERVAL = 2.0  # seconds


class GameDetector:
    def __init__(self, interval=DETECTION_INTERVAL):
        self.interval = interval
        self._running = False
        self.active_games = {}
        self._callbacks = []
    
    def add_callback(self, callback):
        """Add callback(game_name, pid, game_info) when game detected"""
        self._callbacks.append(callback)
    
    def get_game_name(self, process_name: str) -> str:
        """Match process name to known game"""
        process_name_lower = process_name.lower()
        for game, keywords in KNOWN_GAMES.items():
            for kw in keywords:
                if kw.lower() in process_name_lower:
                    return game
        return None
    
    def find_gaming_processes(self) -> list:
        """Find all running game processes"""
        games_found = []
        seen_pids = set()
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                pinfo = proc.info
                pid = pinfo['pid']
                if pid in seen_pids:
                    continue
                seen_pids.add(pid)
                
                name = pinfo['name'] or ""
                game = self.get_game_name(name)
                if game:
                    games_found.append({
                        'pid': pid,
                        'name': name,
                        'game': game,
                        'cpu': pinfo.get('cpu_percent', 0),
                        'mem_mb': pinfo['memory_info'].rss / 1024 / 1024 if pinfo.get('memory_info') else 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return games_found
    
    def trigger_imping(self, game_name: str, pid: int):
        """Trigger IMPING optimization for detected game"""
        log.info(f"🎮 {game_name} detected (PID: {pid}) — Activating IMPING stack!")
        
        priority = CPU_PRIORITY_MAP.get(game_name, 90)
        
        # Try to trigger hardware mapper
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            hw_mapper = os.path.join(script_dir, "hardware-mapper.py")
            if os.path.exists(hw_mapper):
                subprocess.run(
                    ['python3', hw_mapper, '--pid', str(pid), '--priority', str(priority)],
                    capture_output=True, timeout=10
                )
                log.info(f"✓ Hardware mapping applied (priority: {priority})")
        except Exception as e:
            log.warning(f"Hardware mapper failed: {e}")
        
        # Try to trigger net jammer
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            net_jammer = os.path.join(script_dir, "net-jammer.py")
            if os.path.exists(net_jammer):
                subprocess.run(
                    ['python3', net_jammer, '--game', game_name, '--mode', 'optimize'],
                    capture_output=True, timeout=10
                )
                log.info(f"✓ Network jamming optimized")
        except Exception as e:
            log.warning(f"Net jammer failed: {e}")
        
        # Call registered callbacks
        for cb in self._callbacks:
            try:
                cb(game_name, pid, {'priority': priority})
            except Exception as e:
                log.warning(f"Callback error: {e}")
    
    def stop(self):
        self._running = False
    
    def start_monitoring(self):
        """Start continuous game detection"""
        log.info("IMPGING Game Detector started!")
        log.info(f"Monitoring for {len(KNOWN_GAMES)} known games...")
        log.info(f"Detection interval: {self.interval}s")
        log.info("Press Ctrl+C to stop")
        
        self._running = True
        
        def signal_handler(sig, frame):
            log.info("Shutting down game detector...")
            self._running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while self._running:
            try:
                games = self.find_gaming_processes()
                
                current_games = {g['game']: g['pid'] for g in games}
                
                # Detect new games
                for game, pid in current_games.items():
                    if game not in self.active_games:
                        log.info(f"✨ New game detected: {game} (PID: {pid})")
                        self.trigger_imping(game, pid)
                        self.active_games[game] = pid
                
                # Detect exited games
                for game in list(self.active_games.keys()):
                    if game not in current_games:
                        log.info(f"Game exited: {game}")
                        del self.active_games[game]
                
                time.sleep(self.interval)
                
            except Exception as e:
                log.error(f"Detection error: {e}")
                time.sleep(self.interval)
        
        log.info("Game detector stopped.")


def main():
    detector = GameDetector()
    detector.start_monitoring()


if __name__ == "__main__":
    main()