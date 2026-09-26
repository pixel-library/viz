"""
Right Column Media Library List Widget.
Renders discovered MediaItems and manages empty / search empty state displays.
"""

from __future__ import annotations

from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

from viz.models import MediaItem


class MediaListWidget(Widget):
    """Dynamic Media List component for the Right Column."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="right-column"):
            yield Label("[ /Browse ]", classes="column-header", id="browse-header")
            yield ListView(id="media-list")

    def update_list(
        self,
        media_items: List[MediaItem],
        active_search_query: str = "",
        is_scanning: bool = False,
        media_path_display: str = "",
    ) -> None:
        """Update list view with items or show appropriate empty/scanning state."""
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        header_label = self.query_one("#browse-header", Label)

        if is_scanning:
            header_label.update("[ /Browse - SCANNING... ]")
            list_view.append(ListItem(Label("[ SCANNING MEDIA DIRECTORY... ]")))
            return

        header_label.update(f"[ /Browse ({len(media_items)}) ]")

        if not media_items:
            if active_search_query:
                list_view.append(
                    ListItem(
                        Label(
                            f"[ NO RESULTS ]\nNo media matches query: > '{active_search_query}'"
                        )
                    )
                )
            else:
                list_view.append(
                    ListItem(
                        Label(
                            f"[ LIBRARY EMPTY ]\nNo supported media files found in:\n{media_path_display}\n\nPress R to rescan."
                        )
                    )
                )
            return

        for item in media_items:
            icon = item.icon
            list_view.append(ListItem(Label(f"{icon} {item.name}")))

    def get_selected_index(self) -> Optional[int]:
        list_view = self.query_one("#media-list", ListView)
        return list_view.index
