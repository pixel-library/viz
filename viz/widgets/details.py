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


class DetailsWidget(Vertical):
    """Details panel rendering detailed metadata for highlighted files/folders + real storage information."""

    def compose(self) -> ComposeResult:
        yield Label("INFORMATION", classes="column-header", id="details-header")
        yield Label("Select a file or folder\nto inspect details.", id="details-body")
        yield Label("STORAGE", classes="section-header", id="storage-header")
        yield Label("Loading storage...", id="storage-body")

    @staticmethod
    def _truncate_name(name: str, max_len: int = 22) -> str:
        if len(name) <= max_len:
            return name
        return name[: max_len - 3] + "..."

    @staticmethod
    def _truncate_path(path: Path | str, max_len: int = 22) -> str:
        p_str = str(path)
        if len(p_str) <= max_len:
            return p_str
        p = Path(path)
        return f".../{p.name}"

    def update_storage(self, target_path: Optional[Path] = None) -> None:
        """Update the permanent STORAGE section using real disk_usage for target_path."""
        try:
            check_path = target_path or Path.home()
            if not check_path.exists():
                check_path = Path.home()

            resolved = check_path.resolve()
            total, used, free = shutil.disk_usage(resolved)

            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)

            pct = (used / max(1, total)) * 100.0
            bar_len = 8
            filled = int(bar_len * (pct / 100.0))
            bar_str = "█" * filled + "░" * (bar_len - filled)

            drive_name = str(resolved)
            home_str = str(Path.home().resolve())
            if resolved == Path.home().resolve() or drive_name.startswith(home_str):
                drive_name = "HOME (~)"
            elif len(drive_name) > 18:
                drive_name = f".../{resolved.name}"

            text = (
                f"[bold]DRIVE:[/bold]  [dim]{drive_name}[/dim]\n"
                f"[bold]USED:[/bold]   {used_gb:.1f} GB\n"
                f"[bold]FREE:[/bold]   {free_gb:.1f} GB\n"
                f"[bold]TOTAL:[/bold]  {total_gb:.1f} GB\n"
                f"[bold]USAGE:[/bold]  [{bar_str}] {pct:.1f}%"
            )
            self.query_one("#storage-body", Label).update(text)
        except Exception:
            self.query_one("#storage-body", Label).update("Storage stats unavailable")

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

        header.update("INFORMATION")

        size_mb = folder.total_size_bytes / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
        mod_date = self._format_date(folder.path)

        folder_name = self._truncate_name(folder.name, 22)
        loc_str = self._truncate_path(folder.path, 22)

        text = (
            f"[bold orange]{folder_name}[/bold orange]\n\n"
            f"[bold]TYPE:[/bold]      Folder\n"
            f"[bold]LOCATION:[/bold]  [dim]{loc_str}[/dim]\n"
            f"[bold]MODIFIED:[/bold]  {mod_date}\n\n"
            f"[bold]CONTENTS:[/bold]\n"
            f"  Subfolders: {len(folder.subfolders)}\n"
            f"  Videos:     {folder.video_count}\n"
            f"  Audio:      {folder.audio_count}\n"
            f"  Images:     {folder.image_count}\n"
            f"  Total:      {folder.total_media_count} items\n"
            f"  Total Size: {size_str}"
        )
        body.update(text)
        self.update_storage(folder.path)

    def show_media_item(self, item: MediaItem) -> None:
        """Render details for a selected media file (Video, Audio, Image)."""
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)

        header.update("INFORMATION")

        from viz.metadata import MetadataExtractor
        item = MetadataExtractor.enrich_metadata(item)

        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
        if size_mb < 1.0:
            size_str = f"{int(item.file_size / 1024)} KB"
        fav_str = " ★" if item.favorite else ""
        mod_date = self._format_date(item.path)

        item_name = self._truncate_name(item.name, 22)
        loc_str = self._truncate_path(item.path.parent, 22)

        if item.media_type == MediaType.VIDEO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "N/A"
            dim_str = f"{item.video_width} × {item.video_height}" if item.video_width > 0 else "N/A"
            px_count = item.video_width * item.video_height if item.video_width > 0 else 0
            px_str = f"{px_count:,}" if px_count > 0 else "N/A"

            text = (
                f"[bold orange]{item_name}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]       Video\n"
                f"[bold]FORMAT:[/bold]     {item.extension.upper().lstrip('.')}\n"
                f"[bold]DIMENSIONS:[/bold] {dim_str}\n"
                f"[bold]PIXELS:[/bold]     {px_str}\n"
                f"[bold]DURATION:[/bold]   {dur_str}\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{loc_str}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}"
            )

        elif item.media_type == MediaType.AUDIO:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else "N/A"
            artist_str = self._truncate_name(item.artist, 14) if item.artist else "N/A"
            album_str = self._truncate_name(item.album, 14) if item.album else "N/A"

            text = (
                f"[bold orange]{item_name}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]       Audio\n"
                f"[bold]FORMAT:[/bold]     {item.extension.upper().lstrip('.')}\n"
                f"[bold]ARTIST:[/bold]     {artist_str}\n"
                f"[bold]ALBUM:[/bold]      {album_str}\n"
                f"[bold]DURATION:[/bold]   {dur_str}\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{loc_str}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}"
            )

        elif item.media_type == MediaType.IMAGE:
            dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "N/A"
            fmt_str = item.image_format or item.extension.upper().lstrip('.')
            px_count = item.image_width * item.image_height if item.image_width > 0 else 0
            px_str = f"{px_count:,}" if px_count > 0 else "N/A"

            text = (
                f"[bold orange]{item_name}[/bold orange]{fav_str}\n\n"
                f"[bold]TYPE:[/bold]       Image\n"
                f"[bold]FORMAT:[/bold]     {fmt_str}\n"
                f"[bold]DIMENSIONS:[/bold] {dim_str}\n"
                f"[bold]PIXELS:[/bold]     {px_str}\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{loc_str}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}"
            )
        else:
            text = (
                f"[bold orange]{item_name}[/bold orange]\n\n"
                f"[bold]TYPE:[/bold]       File\n"
                f"[bold]SIZE:[/bold]       {size_str}\n"
                f"[bold]LOCATION:[/bold]   [dim]{loc_str}[/dim]\n"
                f"[bold]MODIFIED:[/bold]   {mod_date}"
            )

        body.update(text)
        self.update_storage(item.path)

    def show_empty(self, message: str = "No item selected.") -> None:
        header = self.query_one("#details-header", Label)
        body = self.query_one("#details-body", Label)
        header.update("INFORMATION")
        lib = getattr(self.app, "library", None)
        lib_str = ""
        if lib:
            lib_str = (
                f"\n\n[bold orange]MEDIA LIBRARY[/bold orange]\n"
                f"─────────────────────────\n"
                f"  Total Files: {lib.all_count}\n"
                f"  Videos:      {lib.videos_count}\n"
                f"  Audio:       {lib.music_count}\n"
                f"  Images:      {lib.images_count}"
            )
        body.update(f"{message}{lib_str}")
        self.update_storage(Path.home())

    show_media = show_media_item

