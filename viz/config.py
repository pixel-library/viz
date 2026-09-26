"""
Configuration & User Preferences Manager for Viz Media Player.
Persists volume settings, favorites, recent history, and selected theme.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class ConfigManager:
    """Manages persistent JSON configuration in ~/.config/viz/config.json"""

    def __init__(self) -> None:
        self.config_dir = Path.home() / ".config" / "viz"
        self.config_file = self.config_dir / "config.json"
        self._default_config: Dict[str, Any] = {
            "volume": 80,
            "theme": "cyberpunk",
            "favorites": [],
            "recent_history": [],
            "last_directory": str(Path.cwd()),
        }
        self.data: Dict[str, Any] = dict(self._default_config)
        self.load()

    def load(self) -> None:
        """Load configuration from disk."""
        try:
            if self.config_file.exists():
                content = self.config_file.read_text(encoding="utf-8")
                loaded = json.loads(content)
                if isinstance(loaded, dict):
                    self.data.update(loaded)
        except Exception as err:
            print(f"[Viz Config Warning] Could not load config: {err}")

    def save(self) -> None:
        """Save configuration to disk."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except Exception as err:
            print(f"[Viz Config Warning] Could not save config: {err}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default if default is not None else self._default_config.get(key))

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def add_favorite(self, file_path: str) -> bool:
        favs: List[str] = self.data.get("favorites", [])
        if file_path not in favs:
            favs.append(file_path)
            self.set("favorites", favs)
            return True
        return False

    def remove_favorite(self, file_path: str) -> bool:
        favs: List[str] = self.data.get("favorites", [])
        if file_path in favs:
            favs.remove(file_path)
            self.set("favorites", favs)
            return True
        return False

    def is_favorite(self, file_path: str) -> bool:
        return file_path in self.data.get("favorites", [])

    def add_recent(self, file_path: str) -> None:
        history: List[str] = self.data.get("recent_history", [])
        if file_path in history:
            history.remove(file_path)
        history.insert(0, file_path)
        # Keep top 50 recent items
        self.set("recent_history", history[:50])
