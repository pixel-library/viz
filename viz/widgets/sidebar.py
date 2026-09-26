"""
Left Sidebar Navigation Widget.
Organizes Media Center navigation into LIBRARY, PERSONAL, PLAYBACK, and SYSTEM with real media counts.
"""

from __future__ import annotations

from typing import List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

from viz.library import LibraryManager


class SidebarWidget(Widget):
    """Compact navigation sidebar with sections and live counts."""

    # Category definitions: (id, label, section)
    CATEGORIES: List[Tuple[str, str, str]] = [
        # LIBRARY
        ("all", "ALL MEDIA", "LIBRARY"),
        ("movies", "MOVIES", "LIBRARY"),
        ("series", "SERIES", "LIBRARY"),
        ("music", "MUSIC", "LIBRARY"),
        # PERSONAL
        ("continue", "CONTINUE WATCHING", "PERSONAL"),
        ("recent", "RECENTLY PLAYED", "PERSONAL"),
        ("favorites", "FAVORITES", "PERSONAL"),
        ("completed", "COMPLETED", "PERSONAL"),
        # PLAYBACK
        ("queue", "PLAYBACK QUEUE", "PLAYBACK"),
        # SYSTEM
        ("refresh", "REFRESH LIBRARY", "SYSTEM"),
        ("help", "HELP", "SYSTEM"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="left-column"):
            yield Label("◆ MEDIA CENTER", classes="column-header")
            with ListView(id="category-list"):
                current_section = ""
                for cat_id, title, section in self.CATEGORIES:
                    if section != current_section:
                        current_section = section
                        yield ListItem(Label(f"── {section} ──"), classes="section-header")
                    yield ListItem(Label(f"  {title}"), id=f"cat-{cat_id}")

    def update_counts(self, library: LibraryManager, queue_count: int = 0) -> None:
        """Update navigation items with real media counts in-place."""
        counts = {
            "all": library.all_count,
            "movies": library.movies_count,
            "series": library.series_count,
            "music": library.music_count,
            "continue": library.continue_count,
            "recent": library.recent_count,
            "favorites": library.favorites_count,
            "completed": len(library.get_completed()),
            "queue": queue_count,
        }

        for cat_id, title, _ in self.CATEGORIES:
            try:
                item = self.query_one(f"#cat-{cat_id}", ListItem)
                label = item.query_one(Label)
                cnt = counts.get(cat_id)
                cnt_str = f" ({cnt})" if cnt is not None and cat_id not in ("refresh", "help") else ""
                label.update(f"  {title}{cnt_str}")
            except Exception:
                pass
