"""
Media Information Modal Screen for Viz Media Player.
Displays format, resolution, codec, duration, size, progress, and file path.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from viz.models import MediaItem, MediaType
from viz.widgets.player_status import PlayerStatusWidget


class InfoScreen(ModalScreen):
    """Modal screen displaying detailed media item metadata."""

    DEFAULT_CSS = """
    InfoScreen {
        align: center middle;
        background: rgba(12, 9, 5, 0.9);
    }

    #info-dialog {
        width: 72;
        height: auto;
        border: heavy #ff8800;
        background: #0f0a05;
        padding: 1 2;
    }

    #info-title {
        text-align: center;
        text-style: bold;
        color: #ff8800;
        margin-bottom: 1;
        border-bottom: heavy #ff8800;
    }

    .info-row {
        height: 1;
        margin-bottom: 0;
    }

    .info-label {
        color: #ff8800;
        text-style: bold;
        width: 16;
    }

    .info-val {
        color: #ffccaa;
        width: 1fr;
    }

    #close-btn {
        margin-top: 1;
        horizontal-align: center;
        border: none;
        background: #ff8800;
        color: #0c0905;
        text-style: bold;
    }
    """

    def __init__(self, media_item: MediaItem) -> None:
        super().__init__()
        self.item = media_item

    def compose(self) -> ComposeResult:
        with Vertical(id="info-dialog"):
            header_str = "TRACK INFORMATION" if self.item.media_type == MediaType.AUDIO else "VIDEO INFORMATION"
            yield Label(f"=== {header_str} ===", id="info-title")

            # Size calculation
            size_mb = self.item.file_size / (1024 * 1024)
            size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
            dur_str = PlayerStatusWidget.format_time(self.item.duration)
            pct_str = f"{int(self.item.progress_pct * 100)}%"

            info_fields = [
                ("Title", self.item.title or self.item.name),
                ("Type", self.item.media_type.name),
                ("Format", self.item.extension.upper().lstrip(".")),
                ("Duration", dur_str),
                ("File Size", size_str),
                ("Location", str(self.item.directory)),
                ("Progress", pct_str),
                ("Favorite", "★ Yes" if self.item.favorite else "No"),
                ("Completed", "✓ Yes" if self.item.completed else "No"),
            ]

            if self.item.media_type == MediaType.AUDIO:
                if self.item.artist:
                    info_fields.insert(1, ("Artist", self.item.artist))
                if self.item.album:
                    info_fields.insert(2, ("Album", self.item.album))

            elif self.item.media_type == MediaType.VIDEO and self.item.series_name:
                info_fields.insert(1, ("Series", self.item.series_name))
                info_fields.insert(2, ("Season / Ep", f"S{self.item.season_num:02d}E{self.item.episode_num:02d}"))

            for label, val in info_fields:
                with Horizontal(classes="info-row"):
                    yield Label(label, classes="info-label")
                    yield Label(str(val), classes="info-val")

            yield Button("Dismiss [ Esc ]", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
