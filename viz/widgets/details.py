"""
Right-Column Media & Folder Details Widget for Viz Terminal Media Center.
Displays rich real-time metadata, real storage info, and library stats for selected files or folders.
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
            yield Label("◆ FILE DETAILS", classes="column-header", id="details-header")
            yield Label("Select a file or folder\nto inspect details.", id="details-body")

    def _get_storage_section(self) -> str:
        try:
            total, used, free = shutil.disk_usage(Path.home())
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            pct = int((used / max(1, total)) * 100)
            bar_len = 10
            filled = int(bar_len * (pct / 100))
            bar_str = "█" * filled + "░" * (bar_len - filled)
            return (
                f"[bold]STORAGE[/bold]\n"
                f"─────────────────────────\n"
                f"HOME [{bar_str}] {pct}%\n"
                f"  Used:  {used_gb:.1f} GB\n"
                f"  Free:  {free_gb:.1f} GB\n"
                f"  Total: {total_gb:.1f} GB"
            )
        except Exception:
            return ""

    def _get_library_stats_section(self) -> str:
        try:
            lib = getattr(self.app, "library", None)
            if not lib:
                return ""
            return (
                f"[bold]MEDIA LIBRARY[/bold]\n"
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
            return time.strftime("%b %d, %Y %H:%M", time.localtime(mtime))
        except Exception:
            return "Unknown"

    def show_folder(self, folder: FolderNode) -> None:
        """Render details for a selected filesystem folder."""
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)

        header.update("◆ FOLDER DETAILS")

        size_mb = folder.total_size_bytes / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
        mod_date = self._format_date(folder.path)

        storage_text = self._get_storage_section()
        lib_text = self._get_library_stats_section()

        text = (
            f"[bold orange]{folder.name[:28]}[/bold orange]\n\n"
            f"[bold]LOCATION:[/bold]\n[dim]{str(folder.path)[:34]}[/dim]\n\n"
            f"[bold]CONTENTS:[/bold]\n"
            f"  Subfolders: {len(folder.subfolders)}\n"
            f"  Videos:     {folder.video_count}\n"
            f"  Audio:      {folder.audio_count}\n"
            f"  Images:     {folder.image_count}\n"
            f"  Total:      {folder.total_media_count} files\n\n"
            f"[bold]TOTAL SIZE:[/bold] {size_str}\n"
            f"[bold]MODIFIED:[/bold]   {mod_date}\n\n"
            f"{storage_text}\n\n"
            f"{lib_text}"
        )
        body.update(text)

    def show_media_item(self, item: MediaItem) -> None:
        """Render details for a selected media file (Video, Audio, Image)."""
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)

        header.update("◆ FILE DETAILS")

        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
        if size_mb < 1.0:
            size_str = f"{int(item.file_size / 1024)} KB"
        fav_str = " ★" if item.favorite else ""
        mod_date = self._format_date(item.path)

        storage_text = self._get_storage_section()
        lib_text = self._get_library_stats_section()

        if item.media_type == MediaType.VIDEO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "Unknown"
            text = (
                f"[bold orange]{item.name[:28]}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]      Video ({item.extension.upper().lstrip('.')})\n"
                f"[bold]DURATION:[/bold]  {dur_str}\n"
                f"[bold]SIZE:[/bold]      {size_str}\n"
                f"[bold]MODIFIED:[/bold]  {mod_date}\n\n"
                f"[bold]LOCATION:[/bold]\n[dim]{str(item.path)[:34]}[/dim]\n\n"
                f"{storage_text}\n\n"
                f"{lib_text}"
            )

        elif item.media_type == MediaType.AUDIO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "Unknown"
            artist_str = f"{item.artist[:16]}" if item.artist else "Unknown Artist"
            album_str = f"{item.album[:16]}" if item.album else "Unknown Album"

            text = (
                f"[bold orange]{item.name[:28]}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]      Audio ({item.extension.upper().lstrip('.')})\n"
                f"[bold]ARTIST:[/bold]    {artist_str}\n"
                f"[bold]ALBUM:[/bold]     {album_str}\n"
                f"[bold]DURATION:[/bold]  {dur_str}\n"
                f"[bold]SIZE:[/bold]      {size_str}\n"
                f"[bold]MODIFIED:[/bold]  {mod_date}\n\n"
                f"[bold]LOCATION:[/bold]\n[dim]{str(item.path)[:34]}[/dim]\n\n"
                f"{storage_text}\n\n"
                f"{lib_text}"
            )

        elif item.media_type == MediaType.IMAGE:
            dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Unknown"
            fmt_str = item.image_format or item.extension.upper().lstrip('.')

            text = (
                f"[bold orange]{item.name[:28]}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]      Image ({fmt_str})\n"
                f"[bold]DIMENSIONS:[/bold] {dim_str}\n"
                f"[bold]SIZE:[/bold]      {size_str}\n"
                f"[bold]MODIFIED:[/bold]  {mod_date}\n\n"
                f"[bold]LOCATION:[/bold]\n[dim]{str(item.path)[:34]}[/dim]\n\n"
                f"{storage_text}\n\n"
                f"{lib_text}"
            )
        else:
            text = f"[bold orange]{item.name[:28]}[/bold orange]\n\nPath:\n{item.path}\n\n{storage_text}"

        body.update(text)

    def show_empty(self, message: str = "No item selected.") -> None:
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)
        header.update("◆ FILE DETAILS")
        storage_text = self._get_storage_section()
        lib_text = self._get_library_stats_section()
        body.update(f"{message}\n\n{storage_text}\n\n{lib_text}")

    show_media = show_media_item
