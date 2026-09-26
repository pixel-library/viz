"""
Right-Column Media & Folder Details Widget for Viz Terminal Media Center.
Displays rich real-time metadata, pixel counts, real storage info, and library stats for selected files or folders.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import time
from typing import Optional, Union

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label

from viz.folder_tree import FolderNode
from viz.models import MediaItem, MediaType
from viz.widgets.player_status import PlayerStatusWidget


class DetailsWidget(Widget):
    """Details panel rendering detailed metadata for highlighted files/folders + real storage information."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="details-column"):
            yield Label("◆ INFORMATION", classes="column-header", id="details-header")
            yield Label("Select a file or folder\nto inspect details.", id="details-body")

    def _get_storage_section(self, target_path: Optional[Path] = None) -> str:
        try:
            check_path = target_path or Path.home()
            if not check_path.exists():
                check_path = Path.home()
            
            total, used, free = shutil.disk_usage(check_path)
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            pct = int((used / max(1, total)) * 100)
            bar_len = 10
            filled = int(bar_len * (pct / 100))
            bar_str = "█" * filled + "░" * (bar_len - filled)
            
            drive_name = "/" if check_path == Path("/") else check_path.anchor or "HOME"
            return (
                f"[bold orange]STORAGE[/bold orange]\n"
                f"─────────────────────────\n"
                f"[bold]DRIVE:[/bold]  {drive_name}\n"
                f"[bold]USED:[/bold]   {used_gb:.1f} GB\n"
                f"[bold]FREE:[/bold]   {free_gb:.1f} GB\n"
                f"[bold]TOTAL:[/bold]  {total_gb:.1f} GB\n"
                f"[bold]USAGE:[/bold]  [{bar_str}] {pct}%"
            )
        except Exception:
            return ""

    def _get_library_stats_section(self) -> str:
        try:
            lib = getattr(self.app, "library", None)
            if not lib:
                return ""
            return (
                f"[bold orange]MEDIA LIBRARY[/bold orange]\n"
                f"─────────────────────────\n"
                f"  Files:   {lib.all_count}\n"
                f"  Videos:  {lib.videos_count}\n"
                f"  Audio:   {lib.music_count}\n"
                f"  Images:  {lib.images_count}"
            )
        except Exception:
            return ""

    @staticmethod
    def _format_date(file_path: Path) -> str:
        try:
            mtime = os.path.getmtime(file_path)
            return time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
        except Exception:
            return "Unknown"

    def show_folder(self, folder: FolderNode) -> None:
        """Render details for a selected filesystem folder."""
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)

        header.update("◆ FOLDER INFORMATION")

        size_mb = folder.total_size_bytes / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
        mod_date = self._format_date(folder.path)

        storage_text = self._get_storage_section(folder.path)

        text = (
            f"[bold orange]{folder.name[:28]}[/bold orange]\n\n"
            f"[bold]TYPE:[/bold]      Folder\n"
            f"[bold]LOCATION:[/bold]  [dim]{str(folder.path)[:32]}[/dim]\n"
            f"[bold]MODIFIED:[/bold]  {mod_date}\n\n"
            f"[bold]CONTENTS:[/bold]\n"
            f"  Subfolders: {len(folder.subfolders)}\n"
            f"  Videos:     {folder.video_count}\n"
            f"  Audio:      {folder.audio_count}\n"
            f"  Images:     {folder.image_count}\n"
            f"  Total:      {folder.total_media_count} items\n"
            f"  Total Size: {size_str}\n\n"
            f"{storage_text}"
        )
        body.update(text)

    def show_media_item(self, item: MediaItem) -> None:
        """Render details for a selected media file (Video, Audio, Image)."""
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)

        header.update("◆ FILE INFORMATION")

        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
        if size_mb < 1.0:
            size_str = f"{int(item.file_size / 1024)} KB"
        fav_str = " ★" if item.favorite else ""
        mod_date = self._format_date(item.path)
        storage_text = self._get_storage_section(item.path)

        if item.media_type == MediaType.VIDEO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "Unknown"
            dim_str = f"{item.video_width} × {item.video_height}" if item.video_width > 0 else "Unknown"
            px_count = item.video_width * item.video_height if item.video_width > 0 else 0
            px_str = f"{px_count:,}" if px_count > 0 else "Unknown"

            text = (
                f"[bold orange]{item.name[:28]}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]       Video\n"
                f"[bold]FORMAT:[/bold]     {item.extension.upper().lstrip('.')}\n"
                f"[bold]DIMENSIONS:[/bold] {dim_str}\n"
                f"[bold]PIXELS:[/bold]     {px_str}\n"
                f"[bold]DURATION:[/bold]   {dur_str}\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{str(item.path.parent)[:32]}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}\n\n"
                f"{storage_text}"
            )

        elif item.media_type == MediaType.AUDIO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "Unknown"
            artist_str = f"{item.artist[:16]}" if item.artist else "Unknown Artist"
            album_str = f"{item.album[:16]}" if item.album else "Unknown Album"

            text = (
                f"[bold orange]{item.name[:28]}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]       Audio\n"
                f"[bold]FORMAT:[/bold]     {item.extension.upper().lstrip('.')}\n"
                f"[bold]ARTIST:[/bold]     {artist_str}\n"
                f"[bold]ALBUM:[/bold]      {album_str}\n"
                f"[bold]DURATION:[/bold]   {dur_str}\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{str(item.path.parent)[:32]}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}\n\n"
                f"{storage_text}"
            )

        elif item.media_type == MediaType.IMAGE:
            dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Unknown"
            fmt_str = item.image_format or item.extension.upper().lstrip('.')
            px_count = item.image_width * item.image_height if item.image_width > 0 else 0
            px_str = f"{px_count:,}" if px_count > 0 else "Unknown"

            text = (
                f"[bold orange]{item.name[:28]}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]       Image\n"
                f"[bold]FORMAT:[/bold]     {fmt_str}\n"
                f"[bold]DIMENSIONS:[/bold] {dim_str}\n"
                f"[bold]PIXELS:[/bold]     {px_str}\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{str(item.path.parent)[:32]}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}\n\n"
                f"{storage_text}"
            )
        else:
            text = (
                f"[bold orange]{item.name[:28]}[/bold orange]\n\n"
                f"[bold]TYPE:[/bold]       File\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{str(item.path.parent)[:32]}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}\n\n"
                f"{storage_text}"
            )

        body.update(text)

    def show_empty(self, message: str = "No item selected.") -> None:
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)
        header.update("◆ VIZ SYSTEM")
        storage_text = self._get_storage_section()
        lib_text = self._get_library_stats_section()
        body.update(f"{message}\n\n{lib_text}\n\n{storage_text}")

    show_media = show_media_item
