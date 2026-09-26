"""
Right-Column Media & Folder Details Widget for Viz Terminal Media Center.
Displays rich real-time metadata for selected files or folders.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label

from viz.folder_tree import FolderNode
from viz.models import MediaItem, MediaType
from viz.widgets.player_status import PlayerStatusWidget


class DetailsWidget(Widget):
    """Details panel rendering detailed metadata for highlighted files and folders."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="details-column"):
            yield Label("◆ DETAILS", classes="column-header", id="details-header")
            yield Label("Select a file or folder\nto inspect details.", id="details-body")

    def show_folder(self, folder: FolderNode) -> None:
        """Render details for a selected filesystem folder."""
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)

        header.update("◆ FOLDER DETAILS")

        size_mb = folder.total_size_bytes / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"

        text = (
            f"[bold orange]{folder.name}[/bold orange]\n\n"
            f"[bold]LOCATION:[/bold]\n{folder.path}\n\n"
            f"[bold]CONTENTS:[/bold]\n"
            f"  Subfolders: {len(folder.subfolders)}\n"
            f"  Videos:     {folder.video_count}\n"
            f"  Audio:      {folder.audio_count}\n"
            f"  Images:     {folder.image_count}\n"
            f"  Total:      {folder.total_media_count} files\n\n"
            f"[bold]TOTAL SIZE:[/bold]\n  {size_str}\n\n"
            f"────────────────────────\n"
            f" [ENTER] Open Folder\n"
            f" [→] Expand  [←] Collapse"
        )
        body.update(text)

    def show_media_item(self, item: MediaItem) -> None:
        """Render details for a selected media file (Video, Audio, Image)."""
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)

        header.update("◆ FILE DETAILS")

        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
        fav_str = " ★ FAVORITE" if item.favorite else ""

        if item.media_type == MediaType.VIDEO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "Unknown"
            progress_str = f"{int(item.progress_pct * 100)}%" if item.progress_pct > 0 else "Not Started"
            if item.completed:
                progress_str = "Completed ✓"

            text = (
                f"[bold orange]{item.name}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]      Video ({item.extension.upper().lstrip('.')})\n"
                f"[bold]DURATION:[/bold]  {dur_str}\n"
                f"[bold]SIZE:[/bold]      {size_str}\n"
                f"[bold]PROGRESS:[/bold]  {progress_str}\n\n"
                f"[bold]LOCATION:[/bold]\n{item.path}\n\n"
                f"────────────────────────\n"
                f" [ENTER] Play Video\n"
                f" [F] Favorite  [I] Info Modal"
            )

        elif item.media_type == MediaType.AUDIO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "Unknown"
            title_str = item.title or item.display_name
            artist_str = item.artist or "Unknown Artist"
            album_str = item.album or "Unknown Album"

            text = (
                f"[bold orange]{title_str}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]      Audio ({item.extension.upper().lstrip('.')})\n"
                f"[bold]ARTIST:[/bold]    {artist_str}\n"
                f"[bold]ALBUM:[/bold]     {album_str}\n"
                f"[bold]DURATION:[/bold]  {dur_str}\n"
                f"[bold]SIZE:[/bold]      {size_str}\n\n"
                f"[bold]LOCATION:[/bold]\n{item.path}\n\n"
                f"────────────────────────\n"
                f" [ENTER] Play Track\n"
                f" [F] Favorite  [I] Info Modal"
            )

        elif item.media_type == MediaType.IMAGE:
            dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Unknown"
            fmt_str = item.image_format or item.extension.upper().lstrip('.')

            text = (
                f"[bold orange]{item.name}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]      Image ({fmt_str})\n"
                f"[bold]DIMENSIONS:[/bold] {dim_str}\n"
                f"[bold]SIZE:[/bold]      {size_str}\n\n"
                f"[bold]LOCATION:[/bold]\n{item.path}\n\n"
                f"────────────────────────\n"
                f" [ENTER] View Image\n"
                f" [F] Favorite  [I] Info Modal"
            )
        else:
            text = f"[bold orange]{item.name}[/bold orange]\n\nPath:\n{item.path}"

        body.update(text)

    def show_empty(self, message: str = "No item selected.") -> None:
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)
        header.update("◆ DETAILS")
        body.update(message)

    show_media = show_media_item

