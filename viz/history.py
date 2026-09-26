"""
Playback History & Resume Manager for Viz Media Player.
Stores position, duration, and completion status in ~/.config/viz/history.json.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from viz.constants import CONFIG_DIR, HISTORY_FILE


class HistoryManager:
    """Manages persistent playback history, position saving, and resume points."""

    MAX_HISTORY_ENTRIES = 200

    def __init__(self, history_file: Path = HISTORY_FILE) -> None:
        self.history_file = history_file.expanduser().resolve()
        self.history_dir = self.history_file.parent
        self.entries: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load history entries from JSON safely."""
        if not self.history_file.exists():
            return

        try:
            content = self.history_file.read_text(encoding="utf-8")
            loaded = json.loads(content)
            if isinstance(loaded, dict):
                self.entries = loaded
        except Exception as err:
            print(f"[History Warning] Could not load history: {err}")
            self.entries = {}

    def save(self) -> None:
        """Atomic write history entries to disk."""
        try:
            self.history_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self.history_dir / f"{self.history_file.name}.tmp"
            temp_file.write_text(json.dumps(self.entries, indent=2), encoding="utf-8")
            temp_file.replace(self.history_file)
        except Exception as err:
            print(f"[History Warning] Could not save history: {err}")

    def update_position(self, file_path: Path, position: float, duration: float) -> None:
        """Save playback progress for media file."""
        if not file_path:
            return
        
        normalized_path = str(file_path.resolve())
        is_completed = (duration > 0) and (position >= duration - 15.0)

        self.entries[normalized_path] = {
            "path": normalized_path,
            "filename": file_path.name,
            "position": position if not is_completed else 0.0,
            "duration": duration,
            "last_played": time.time(),
            "completed": is_completed,
        }

        # Trim history size if exceeds limit
        if len(self.entries) > self.MAX_HISTORY_ENTRIES:
            sorted_items = sorted(
                self.entries.items(), key=lambda item: item[1].get("last_played", 0)
            )
            # Remove oldest items
            for key, _ in sorted_items[: len(self.entries) - self.MAX_HISTORY_ENTRIES]:
                del self.entries[key]

        self.save()

    def get_resume_position(self, file_path: Path) -> float:
        """
        Check if media file has a valid resume position.
        Returns position > 0 if media should be resumed, else 0.0.
        """
        if not file_path:
            return 0.0

        normalized_path = str(file_path.resolve())
        entry = self.entries.get(normalized_path)
        if not entry:
            return 0.0

        position = float(entry.get("position", 0.0))
        duration = float(entry.get("duration", 0.0))
        completed = bool(entry.get("completed", False))

        if completed:
            return 0.0

        # Resume if position > 10 seconds and not near end of file
        if position >= 10.0 and (duration == 0.0 or position < duration - 20.0):
            return position

        return 0.0

    def get_recent_history(self) -> List[Dict[str, Any]]:
        """Return recently played items sorted by last_played timestamp."""
        return sorted(
            list(self.entries.values()),
            key=lambda e: e.get("last_played", 0),
            reverse=True,
        )
