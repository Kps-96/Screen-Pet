"""Configuration and persistent state management for Deckpet."""

import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict


CONFIG_DIR = Path.home() / ".config" / "deckpet"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATS_FILE = CONFIG_DIR / "stats.json"


DEFAULT_CONFIG: Dict[str, Any] = {
    "water_interval_minutes": 35,
    "daily_water_goal": 8,
    "posture_interval_minutes": 50,
    "idle_sleep_seconds": 300,  # 5 minutes to sleep
    "sound_enabled": True,
    "pet_scale": 1.0,
    "auto_hide_fullscreen": True,
    "window_x": 120,
    "window_y": 120,
    "theme_color": "cyan",  # cyan, green, amber, purple
}


class ConfigManager:
    """Manages application settings and daily statistics."""

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config: Dict[str, Any] = self._load_config()
        self.stats: Dict[str, Any] = self._load_stats()

    def _load_config(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {**DEFAULT_CONFIG, **data}
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    def save_config(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[Deckpet] Error saving config: {e}")

    def _load_stats(self) -> Dict[str, Any]:
        today_str = date.today().isoformat()
        default_stats = {
            "date": today_str,
            "water_count": 0,
            "postures_done": 0,
            "active_minutes": 0,
        }
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("date") == today_str:
                        return {**default_stats, **data}
            except Exception:
                pass
        return default_stats

    def save_stats(self) -> None:
        # Check if date rolled over
        today_str = date.today().isoformat()
        if self.stats.get("date") != today_str:
            self.stats["date"] = today_str
            self.stats["water_count"] = 0
            self.stats["postures_done"] = 0

        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"[Deckpet] Error saving stats: {e}")

    def increment_water(self) -> int:
        self.save_stats()  # ensure rollover check
        self.stats["water_count"] = self.stats.get("water_count", 0) + 1
        self.save_stats()
        return self.stats["water_count"]

    def increment_posture(self) -> int:
        self.save_stats()
        self.stats["postures_done"] = self.stats.get("postures_done", 0) + 1
        self.save_stats()
        return self.stats["postures_done"]

    def get_water_count(self) -> int:
        self.save_stats()
        return self.stats.get("water_count", 0)

    def get_water_goal(self) -> int:
        return int(self.config.get("daily_water_goal", 8))
