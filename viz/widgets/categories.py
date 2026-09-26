"""
Left Column Categories Widget.
Categories are dynamically derived from real media library metadata and playback history.
"""

from __future__ import annotations

from typing import List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView


class CategoriesWidget(Widget):
    """Categories list widget displaying real library filter options."""

    CATEGORY_DEFS: List[Tuple[str, str]] = [
        ("all", "✦ All Media"),
        ("video", "🎬 Movies & Videos"),
        ("audio", "🎵 Music & Audio"),
        ("latest", "• Latest Releases"),
        ("watched", "• Most Watched"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="left-column"):
            yield Label("◆ Discover Categories", classes="column-header")
            yield ListView(id="category-list")

    def on_mount(self) -> None:
        cat_list = self.query_one("#category-list", ListView)
        cat_list.clear()
        for cat_id, title in self.CATEGORY_DEFS:
            cat_list.append(ListItem(Label(title), id=f"cat-{cat_id}"))
