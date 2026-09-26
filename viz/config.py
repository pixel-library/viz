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
        "library_paths": [],
        "volume": 80,
        "muted": False,
        "active_theme": "orange",
        "show_hidden_files": False,
        "sort_order": "name",
    }

    def __init__(self, config_file: Path = CONFIG_FILE) -> None:
        self.config_file = config_file.expanduser().resolve()
        self.config_dir = self.config_file.parent
        self.data: Dict[str, Any] = dict(self.DEFAULT_CONFIG)
        self.load()
        self._ensure_library_paths()

    def _ensure_library_paths(self) -> None:
        """Discover existing user media directories and mounted storage on first run."""
        paths = self.data.get("library_paths", [])
        if not paths:
            discovered = []
            home = Path.home()
            candidates = [
                home / "Desktop",
                home / "Documents",
                home / "Downloads",
                home / "Music",
                home / "Pictures",
                home / "Videos",
                home / "Movies",
                home / "Media",
                Path.cwd() / "media",
            ]
            for cand in candidates:
                if cand.exists() and cand.is_dir():
                    discovered.append(str(cand.resolve()))

            # Discover mounted secondary storage volumes
            try:
                from viz.mounts import MountsManager
                for m_path, _ in MountsManager.get_accessible_mounts():
                    if m_path.exists() and m_path.is_dir():
                        discovered.append(str(m_path.resolve()))
            except Exception:
                pass

            if not discovered and self.media_path.exists():
                discovered.append(str(self.media_path))

            self.data["library_paths"] = discovered or [str(Path.cwd())]
            self.save()

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
        p_str = str(Path(path).expanduser().resolve())
        self.set("media_path", p_str)
        paths = self.get_library_paths()
        if Path(p_str) not in paths:
            self.add_library_path(Path(p_str))

    def get_library_paths(self) -> list[Path]:
        raw_paths = self.get("library_paths", [])
        result = []
        for p in raw_paths:
            try:
                resolved = Path(p).expanduser().resolve()
                if resolved.exists() and resolved.is_dir() and resolved not in result:
                    result.append(resolved)
            except Exception:
                pass
        return result or [self.media_path]

    def add_library_path(self, path: Path | str) -> None:
        resolved = Path(path).expanduser().resolve()
        paths = self.get("library_paths", [])
        str_p = str(resolved)
        if str_p not in paths:
            paths.append(str_p)
            self.set("library_paths", paths)

    def remove_library_path(self, path: Path | str) -> None:
        resolved = Path(path).expanduser().resolve()
        paths = self.get("library_paths", [])
        str_p = str(resolved)
        if str_p in paths:
            paths.remove(str_p)
            self.set("library_paths", paths)

    @property
    def show_hidden_files(self) -> bool:
        return bool(self.get("show_hidden_files", False))

    @show_hidden_files.setter
    def show_hidden_files(self, val: bool) -> None:
        self.set("show_hidden_files", bool(val))

    @property
    def sort_order(self) -> str:
        return str(self.get("sort_order", "name"))

    @sort_order.setter
    def sort_order(self, val: str) -> None:
        self.set("sort_order", val)

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
