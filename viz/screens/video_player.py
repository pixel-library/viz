"""
Dedicated Virtual Video Player Screen for Viz Media Center.
Provides full-terminal video playback controls, progress scrubber, volume, and MPV state observer integration.
"""

from __future__ import annotations

from typing import List, Optional
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from viz.models import MediaItem, PlaybackState, PlaybackStatus
from viz.widgets.player_status import PlayerStatusWidget


class VideoPlayerScreen(ModalScreen):
    """Virtual Video Player screen with real MPV playback integration."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("q", "dismiss_screen", "Back", show=False),
        Binding("space", "toggle_play_pause", "Play/Pause", show=True),
        Binding("left", "seek_back", "Seek -10s", show=True),
        Binding("right", "seek_forward", "Seek +10s", show=True),
        Binding("up", "volume_up", "Vol +", show=True),
        Binding("down", "volume_down", "Vol -", show=True),
        Binding("m", "toggle_mute", "Mute", show=True),
        Binding("n", "next_video", "Next", show=True),
        Binding("b", "prev_video", "Previous", show=True),
        Binding("f", "toggle_fullscreen", "Fullscreen", show=True),
    ]

    def __init__(self, current_item: MediaItem, queue_items: Optional[List[MediaItem]] = None) -> None:
        super().__init__()
        self.current_item = current_item
        self.queue_items = queue_items or [current_item]
        self.current_index = self.queue_items.index(current_item) if current_item in self.queue_items else 0

    def compose(self) -> ComposeResult:
        with Vertical(id="video-screen-container"):
            yield Label("VIZ // VIDEO PLAYER", classes="dialog-header", id="video-header")
            yield Label("", id="video-display-body")
            yield Label("", id="video-status-bar")
            yield Label("", id="video-progress-bar")
            yield Footer()

    def on_mount(self) -> None:
        self.start_playback()
        self.set_interval(0.5, self.update_display)

    def start_playback(self) -> None:
        if 0 <= self.current_index < len(self.queue_items):
            self.current_item = self.queue_items[self.current_index]
            if hasattr(self.app, "engine"):
                self.app.engine.play(self.current_item)

    def update_display(self) -> None:
        engine = getattr(self.app, "engine", None)
        state: PlaybackState = engine.state if engine else PlaybackState()

        header = self.query_one("#video-header", Label)
        header.update(f"VIZ // VIDEO PLAYER  [{self.current_index + 1}/{len(self.queue_items)}]")

        display_body = self.query_one("#video-display-body", Label)
        item_name = self.current_item.name
        res_str = f"{self.current_item.image_width}x{self.current_item.image_height}" if self.current_item.image_width > 0 else "1080p"
        ext_str = self.current_item.extension.upper().lstrip(".")

        video_ascii_card = (
            "\n\n\n"
            "   ┌─────────────────────────────────────────────────────────────┐\n"
            f"   │                ▶ PLAYING VIDEO: {item_name[:28]:<28} │\n"
            "   │                                                             │\n"
            f"   │                FORMAT: {ext_str:<8}   RES: {res_str:<12}       │\n"
            "   │                                                             │\n"
            "   │                [ MPV REAL-TIME ENGINE ACTIVE ]              │\n"
            "   └─────────────────────────────────────────────────────────────┘\n"
        )
        display_body.update(video_ascii_card)

        # Status Line
        status_bar = self.query_one("#video-status-bar", Label)
        status_symbol = "▶" if state.status == PlaybackStatus.PLAYING else ("⏸" if state.status == PlaybackStatus.PAUSED else "■")
        pos_str = PlayerStatusWidget.format_time(state.position)
        dur_str = PlayerStatusWidget.format_time(state.duration)
        vol_str = f"Muted" if state.is_muted else f"Volume {state.volume}%"

        status_bar.update(f" {status_symbol} {pos_str} / {dur_str}                                     {vol_str}")

        # Progress Scrubber
        progress_bar = self.query_one("#video-progress-bar", Label)
        pct = (state.position / max(1.0, state.duration)) if state.duration > 0 else 0.0
        bar_len = 50
        filled = int(pct * bar_len)
        scrubber = "━" * filled + "●" + "─" * max(0, bar_len - filled - 1)
        progress_bar.update(f" {scrubber}")

    def action_toggle_play_pause(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.toggle_pause()
            self.update_display()

    def action_seek_back(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.seek(-10.0)
            self.update_display()

    def action_seek_forward(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.seek(10.0)
            self.update_display()

    def action_volume_up(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.change_volume(5)
            self.update_display()

    def action_volume_down(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.change_volume(-5)
            self.update_display()

    def action_toggle_mute(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.toggle_mute()
            self.update_display()

    def action_next_video(self) -> None:
        if len(self.queue_items) > 1:
            self.current_index = (self.current_index + 1) % len(self.queue_items)
            self.start_playback()

    def action_prev_video(self) -> None:
        if len(self.queue_items) > 1:
            self.current_index = (self.current_index - 1) % len(self.queue_items)
            self.start_playback()

    def action_toggle_fullscreen(self) -> None:
        if hasattr(self.app, "engine") and self.app.engine.player:
            try:
                cur_fs = getattr(self.app.engine.player, "fs", False)
                self.app.engine.player.fs = not cur_fs
            except Exception:
                pass

    def action_dismiss_screen(self) -> None:
        self.dismiss()
