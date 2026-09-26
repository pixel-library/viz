"""
Library Manager for Viz Media Player.
Organizes scanned MediaItems into Movies, Series, Music, Continue Watching, History, and Favorites.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from viz.constants import FAVORITES_FILE
from viz.history import HistoryManager
from viz.metadata import MetadataExtractor
from viz.models import MediaItem, MediaType
from viz.series import SeriesDetector, SeriesGroup


class LibraryManager:
    """Central repository for scanned media, classification, and favorites."""

    def __init__(self, history: HistoryManager, favorites_file: Path = FAVORITES_FILE) -> None:
        self.history = history
        self.favorites_file = favorites_file.expanduser().resolve()
        
        self.all_items: List[MediaItem] = []
        self.movies: List[MediaItem] = []
        self.series_groups: Dict[str, SeriesGroup] = {}
        self.series_episodes: List[MediaItem] = []
        self.music: List[MediaItem] = []
        self.favorites: Set[str] = set()

        self.load_favorites()

    def load_favorites(self) -> None:
        """Load favorite file paths from JSON."""
        if not self.favorites_file.exists():
            return
        try:
            content = self.favorites_file.read_text(encoding="utf-8")
            loaded = json.loads(content)
            if isinstance(loaded, list):
                self.favorites = set(loaded)
        except Exception as err:
            print(f"[Library Warning] Could not load favorites: {err}")

    def save_favorites(self) -> None:
        """Atomic write favorites to JSON."""
        try:
            self.favorites_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = self.favorites_file.parent / f"{self.favorites_file.name}.tmp"
            tmp_file.write_text(json.dumps(list(self.favorites), indent=2), encoding="utf-8")
            tmp_file.replace(self.favorites_file)
        except Exception as err:
            print(f"[Library Warning] Could not save favorites: {err}")

    def toggle_favorite(self, item: MediaItem) -> bool:
        """Toggle favorite status for MediaItem."""
        if not item:
            return False
        
        key = str(item.path.resolve())
        if key in self.favorites:
            self.favorites.remove(key)
            item.favorite = False
        else:
            self.favorites.add(key)
            item.favorite = True

        self.save_favorites()
        return item.favorite

    def set_items(self, discovered_items: List[MediaItem]) -> None:
        """Categorize and enrich scanned MediaItems."""
        self.all_items = discovered_items
        self.movies = []
        self.music = []
        self.series_episodes = []

        # Detect series episodes
        self.series_groups = SeriesDetector.group_series(discovered_items)
        series_item_paths = set()
        for group in self.series_groups.values():
            for season in group.seasons.values():
                for ep in season:
                    series_item_paths.add(ep.media_item.path.resolve())
                    self.series_episodes.append(ep.media_item)

        # Categorize Movies vs Music vs Series
        for item in discovered_items:
            # Sync favorite & history status
            resolved_key = str(item.path.resolve())
            item.favorite = resolved_key in self.favorites

            entry = self.history.entries.get(resolved_key)
            if entry:
                item.last_position = float(entry.get("position", 0.0))
                item.duration = float(entry.get("duration", 0.0))
                item.last_played = float(entry.get("last_played", 0.0))
                item.completed = bool(entry.get("completed", False))

            # Enrich metadata
            MetadataExtractor.enrich_metadata(item)

            if item.media_type == MediaType.AUDIO:
                self.music.append(item)
            elif item.media_type == MediaType.VIDEO:
                if resolved_key not in {str(p) for p in series_item_paths}:
                    self.movies.append(item)

    # Category Collection Getters
    def get_continue_watching(self) -> List[MediaItem]:
        """Return unfinished video items with saved progress > 10s."""
        unfinished = []
        for item in self.all_items:
            if item.media_type == MediaType.VIDEO and not item.completed:
                pos = self.history.get_resume_position(item.path)
                if pos > 10.0:
                    item.last_position = pos
                    unfinished.append(item)
        return sorted(unfinished, key=lambda m: m.last_played, reverse=True)

    def get_recently_played(self) -> List[MediaItem]:
        """Return recently played items sorted by last_played timestamp."""
        history_entries = self.history.get_recent_history()
        history_map = {e["path"]: e for e in history_entries}

        recent = []
        for item in self.all_items:
            key = str(item.path.resolve())
            if key in history_map:
                item.last_played = history_map[key].get("last_played", 0)
                recent.append(item)

        return sorted(recent, key=lambda m: m.last_played, reverse=True)

    def get_favorites(self) -> List[MediaItem]:
        """Return favorited items."""
        return [item for item in self.all_items if item.favorite]

    def get_completed(self) -> List[MediaItem]:
        """Return completed items."""
        return [item for item in self.all_items if item.completed]

    # Sidebar Counts
    @property
    def all_count(self) -> int:
        return len(self.all_items)

    @property
    def movies_count(self) -> int:
        return len(self.movies)

    @property
    def series_count(self) -> int:
        return len(self.series_groups)

    @property
    def music_count(self) -> int:
        return len(self.music)

    @property
    def favorites_count(self) -> int:
        return len(self.get_favorites())

    @property
    def recent_count(self) -> int:
        return len(self.get_recently_played())

    @property
    def continue_count(self) -> int:
        return len(self.get_continue_watching())
