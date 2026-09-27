"""
Middle Column Media Browser Widget for Viz Media Center.
Implements robust ListItems holding real FolderNode and MediaItem objects.
Zero index offset bugs, pure pixel art folder icons.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

from viz.constants import get_folder_symbol
from viz.folder_tree import FolderNode
from viz.models import MediaItem, MediaType
from viz.widgets.player_status import PlayerStatusWidget


class HeaderListItem(ListItem):
    """Disabled section header row in ListView."""

    def __init__(self, title: str) -> None:
        super().__init__(Label(f"── {title} ──"), disabled=True, classes="section-header")
        self.item_type = "header"


class FolderListItem(ListItem):
    """ListItem storing a real FolderNode object."""

    def __init__(self, label_text: str, folder: FolderNode) -> None:
        super().__init__(Label(label_text))
        self.folder_data = folder
        self.item_type = "folder"


class MediaListItem(ListItem):
    """ListItem storing a real MediaItem object."""

    def __init__(self, label_text: str, media_item: MediaItem) -> None:
        super().__init__(Label(label_text))
        self.media_data = media_item
        self.item_type = "media"


class MediaListWidget(Widget):
    """Main Content Media Browser displaying folders and classified media files."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="center-column"):
            yield Label("CONTENT / MEDIA", classes="column-header", id="browse-header")
            yield ListView(id="media-list")

    def render_scanning(self) -> None:
        """Render scanning status state."""
        self._update_header("SCANNING", 0)
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()
        list_view.append(ListItem(Label("[ SCANNING LIBRARY ]\n\nPlease wait...")))

    def update_list(self, media_items: Optional[List[MediaItem]] = None, is_scanning: bool = False, media_path_display: str = "") -> None:
        """Compatibility updater helper."""
        if is_scanning:
            self.render_scanning()
        elif media_items is not None:
            self.render_media_items("BROWSE", media_items)

    def render_folder(self, folder: FolderNode, active_filter: str = "ALL") -> None:
        """Render the contents of a real filesystem folder."""
        folder_sym = get_folder_symbol()
        self._update_header(f"{folder_sym} {folder.path}", folder.total_media_count)
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        # Filter media files
        filtered_files = folder.media_files
        if active_filter == "VIDEOS":
            filtered_files = [m for m in folder.media_files if m.media_type == MediaType.VIDEO]
        elif active_filter == "AUDIO":
            filtered_files = [m for m in folder.media_files if m.media_type == MediaType.AUDIO]
        elif active_filter == "IMAGES":
            filtered_files = [m for m in folder.media_files if m.media_type == MediaType.IMAGE]

        if not folder.subfolders and not filtered_files:
            list_view.append(ListItem(Label(f"[ EMPTY FOLDER ]\n\nNo supported media found in '{folder.name}'.")))
            return

        # 1. Subfolders first
        if folder.subfolders:
            list_view.append(HeaderListItem("FOLDERS"))
            for sf in folder.subfolders:
                cnt_tag = f"[{sf.total_media_count}]" if sf.total_media_count > 0 else ""
                clean_sf_name = sf.name.replace("📁", "").replace("🏠", "").replace("💾", "").strip()
                list_view.append(FolderListItem(f"{folder_sym} {clean_sf_name:<28} {cnt_tag}", folder=sf))

        # 2. Classified Files second
        if filtered_files:
            videos = [m for m in filtered_files if m.media_type == MediaType.VIDEO]
            audio = [m for m in filtered_files if m.media_type == MediaType.AUDIO]
            images = [m for m in filtered_files if m.media_type == MediaType.IMAGE]

            if videos:
                list_view.append(HeaderListItem("VIDEO"))
                for item in videos:
                    dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "--:--"
                    ext_str = item.extension.upper().lstrip(".")
                    fav_str = " ★" if item.favorite else ""
                    list_view.append(MediaListItem(f"[VID] {item.name[:26]:<26}  {ext_str:<5}  {dur_str}{fav_str}", media_item=item))

            if audio:
                list_view.append(HeaderListItem("AUDIO"))
                for item in audio:
                    dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "--:--"
                    ext_str = item.extension.upper().lstrip(".")
                    artist_str = f"{item.artist[:14]}" if item.artist else ""
                    fav_str = " ★" if item.favorite else ""
                    list_view.append(MediaListItem(f"[AUD] {item.name[:24]:<24}  {ext_str:<5}  {dur_str}{fav_str}", media_item=item))

            if images:
                list_view.append(HeaderListItem("IMAGES"))
                for item in images:
                    size_kb = f"{int(item.file_size / 1024)} KB"
                    ext_str = item.image_format or item.extension.upper().lstrip(".")
                    dim_str = f"{item.image_width}×{item.image_height}" if item.image_width > 0 else ""
                    fav_str = " ★" if item.favorite else ""
                    list_view.append(MediaListItem(f"[IMG] {item.name[:24]:<24}  {ext_str:<5}  {size_kb:<8}  {dim_str}{fav_str}", media_item=item))

    def render_media_items(self, title: str, items: List[MediaItem]) -> None:
        """Render a list of MediaItems (e.g. Recently Played, Favorites, Continue Watching)."""
        self._update_header(title, len(items))
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        if not items:
            list_view.append(ListItem(Label(f"[ {title} EMPTY ]\n\nNo items to display.")))
            return

        for item in items:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else ""
            fav_str = " ★" if item.favorite else ""
            icon = item.ascii_icon
            list_view.append(MediaListItem(f"{icon} {item.name[:28]:<28} {dur_str}{fav_str}", media_item=item))

    def _update_header(self, title: str, count: int) -> None:
        header_label = self.query_one("#browse-header", Label)
        display_title = title
        if len(display_title) > 22:
            display_title = f".../{display_title[-18:]}"
        header_label.update(f"CONTENT / MEDIA — {display_title} [{count}]")

    def get_selected_index(self) -> Optional[int]:
        list_view = self.query_one("#media-list", ListView)
        return list_view.index

    def restore_selection(self, item: Optional[MediaItem] = None, index: Optional[int] = None) -> None:
        """Highlight target item or index in ListView."""
        try:
            list_view = self.query_one("#media-list", ListView)
            if item:
                for idx, child in enumerate(list_view.children):
                    if isinstance(child, MediaListItem) and child.media_data.path == item.path:
                        list_view.index = idx
                        return
            if index is not None and 0 <= index < len(list_view.children):
                list_view.index = index
        except Exception:
            pass

