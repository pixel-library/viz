"""
Persistent Configuration Manager for Viz Media Player.
Stores user settings in ~/.config/viz/config.json with atomic writes and recovery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from viz.constants import CONFIG_DIR, CONFIG_FILE


class ConfigManager:
    """Manages persistent JSON configuration with schema versioning and atomic writes."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "version": 1,
        "media_path": str(Path.cwd() / "media"),
        "volume": 80,
        "muted": False,
        "active_theme": "orange",
    }

    def __init__(self, config_file: Path = CONFIG_FILE) -> None:
        self.config_file = config_file.expanduser().resolve()
        self.config_dir = self.config_file.parent
        self.data: Dict[str, Any] = dict(self.DEFAULT_CONFIG)
        self.load()

    def load(self) -> None:
        """Load settings from JSON file. Recovers safely if corrupted."""
        if not self.config_file.exists():
            self.save()
            return

        try:
            content = self.config_file.read_text(encoding="utf-8")
            loaded = json.loads(content)
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except Exception as err:
            # Backup corrupted config and recreate default safely
            backup_path = self.config_dir / f"config.corrupted.{self.config_file.name}"
            try:
                if self.config_file.exists():
                    self.config_file.rename(backup_path)
            except Exception:
                pass
            print(f"[Config Warning] Corrupted config recovered. Error: {err}")
            self.data = dict(self.DEFAULT_CONFIG)
            self.save()

    def save(self) -> None:
        """Atomic write to config file to prevent corruption on crash."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self.config_dir / f"{self.config_file.name}.tmp"
            temp_file.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            temp_file.replace(self.config_file)
        except Exception as err:
            print(f"[Config Warning] Could not save config: {err}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default if default is not None else self.DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    @property
    def media_path(self) -> Path:
        return Path(self.get("media_path", str(Path.cwd() / "media"))).expanduser().resolve()

    @media_path.setter
    def media_path(self, path: Path | str) -> None:
        self.set("media_path", str(Path(path).expanduser().resolve()))

    @property
    def volume(self) -> int:
        return max(0, min(100, int(self.get("volume", 80))))

    @volume.setter
    def volume(self, val: int) -> None:
        self.set("volume", max(0, min(100, int(val))))

    @property
    def muted(self) -> bool:
        return bool(self.get("muted", False))

    @muted.setter
    def muted(self, val: bool) -> None:
        self.set("muted", bool(val))
