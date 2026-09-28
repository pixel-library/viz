"""
Video Virtual Environment for Viz Media Center.
Dedicated environment for real video playback with hardware-accelerated GPU rendering.

Renders real video pixels in a native MPV window with full keyboard controls.
"""

from __future__ import annotations

from typing import List, Optional
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from viz.metadata import MetadataExtractor
from viz.models import MediaItem, PlaybackState, PlaybackStatus
from viz.widgets.player_status import PlayerStatusWidget


class VideoEnvironment(ModalScreen):
    """Video Virtual Environment with real hardware-accelerated MPV window playback."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("q", "dismiss_screen", "Back", show=False),
        Binding("space", "toggle_play_pause", "Play/Pause", show=True),
        Binding("left", "seek_back", "Seek -10s", show=True),
        Binding("right", "seek_forward", "Seek +10s", show=True),
        Binding("shift+left", "seek_back_large", "Seek -60s", show=False),
        Binding("shift+right", "seek_forward_large", "Seek +60s", show=False),
        Binding("up", "volume_up", "Vol +", show=True),
        Binding("down", "volume_down", "Vol -", show=True),
        Binding("m", "toggle_mute", "Mute", show=True),
        Binding("n", "next_video", "Next", show=True),
        Binding("b", "prev_video", "Previous", show=True),
        Binding("f", "toggle_fullscreen", "Fullscreen", show=True),
    ]

    def __init__(self, current_item: MediaItem, queue_items: Optional[List[MediaItem]] = None) -> None:
        super().__init__()
        self.current_item = MetadataExtractor.enrich_metadata(current_item)
        self.queue_items = queue_items or [current_item]
        self.current_index = self.queue_items.index(current_item) if current_item in self.queue_items else 0

    def compose(self) -> ComposeResult:
        with Vertical(id="video-screen-container"):
            with Horizontal(id="video-header-bar"):
                yield Label("←  VIZ // VIDEO ENVIRONMENT", id="video-brand")
                yield Label("", id="video-title-label")
                yield Label("", id="video-queue-counter")

            yield Label("", id="video-viewport")

            with Horizontal(id="video-scrubber-bar"):
                yield Label("00:00", id="video-time-cur")
                yield Label("━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━", id="video-scrubber-line")
                yield Label("00:00", id="video-time-dur")

            with Horizontal(id="video-controls-bar"):
                yield Label("MP4 • 1080p", id="video-fmt-tag")
                yield Label("  ⏮   ( ⏸ )   ⏭  ", id="video-center-controls")
                yield Label("🔊 80%    ⚙ GPU    ⛶ [F]    [ESC] Back", id="video-right-status")

    def on_mount(self) -> None:
        self.start_playback()
        self.set_interval(0.2, self.update_display)

    def start_playback(self) -> None:
        if 0 <= self.current_index < len(self.queue_items):
            self.current_item = MetadataExtractor.enrich_metadata(self.queue_items[self.current_index])
            if hasattr(self.app, "last_selected_item"):
                self.app.last_selected_item = self.current_item
            if hasattr(self.app, "engine"):
                resume_pos = 0.0
                if hasattr(self.app, "history"):
                    resume_pos = self.app.history.get_resume_position(self.current_item.path)
                    if resume_pos > 0.0:
                        formatted_time = PlayerStatusWidget.format_time(resume_pos)
                        self.app.notify(f"Resuming at {formatted_time}", title="Resume Playback")
                self.app.engine.play_video(self.current_item, start_position=resume_pos)

    def update_display(self) -> None:
        engine = getattr(self.app, "engine", None)
        if engine:
            engine.sync_state()
            state: PlaybackState = engine.state
        else:
            state = PlaybackState()

        if hasattr(self.app, "history") and state.position > 5.0 and state.status == PlaybackStatus.PLAYING:
            self.app.history.update_position(self.current_item.path, state.position, state.duration)

        title_lbl = self.query_one("#video-title-label", Label)
        title_lbl.update(f"[bold white]{self.current_item.name}[/bold white]")

        counter_lbl = self.query_one("#video-queue-counter", Label)
        counter_lbl.update(f"[{self.current_index + 1} / {len(self.queue_items)}]")

        pos_str = PlayerStatusWidget.format_time(state.position)
        dur_str = PlayerStatusWidget.format_time(state.duration)

        self.query_one("#video-time-cur", Label).update(pos_str)
        self.query_one("#video-time-dur", Label).update(dur_str)

        pct = (state.position / max(1.0, state.duration)) if state.duration > 0 else 0.0
        bar_len = max(10, getattr(self.app.size, "width", 80) - 30)
        filled = int(pct * bar_len)
        scrubber = "━" * filled + "●" + "─" * max(0, bar_len - filled - 1)
        self.query_one("#video-scrubber-line", Label).update(f" {scrubber} ")

        status_icon = "▶" if state.status == PlaybackStatus.PLAYING else ("⏸" if state.status == PlaybackStatus.PAUSED else "■")
        self.query_one("#video-center-controls", Label).update(f"  ⏮   ( {status_icon} )   ⏭  ")

        ext_str = self.current_item.extension.upper().lstrip(".")
        res_str = f"{self.current_item.video_width}x{self.current_item.video_height}" if self.current_item.video_width > 0 else "Full Native"
        self.query_one("#video-fmt-tag", Label).update(f"{ext_str} • {res_str}")

        vol_str = "Muted" if state.is_muted else f"{state.volume}%"
        fs_str = "⛶ [F] Fullscreen" if not state.is_fullscreen else "⛶ [F] Windowed"
        self.query_one("#video-right-status", Label).update(f"🔊 {vol_str}   ⚙ GPU   {fs_str}   [ESC] Back")

        viewport = self.query_one("#video-viewport", Label)
        status_text = "PLAYING" if state.status == PlaybackStatus.PLAYING else ("PAUSED" if state.status == PlaybackStatus.PAUSED else "STOPPED")

        status_banner = (
            "\n\n"
            f"                     [bold orange]{status_icon}  {status_text}[/bold orange]\n"
            f"        [bold white]{self.current_item.name}[/bold white]\n"
            f"        Format: {ext_str}   Resolution: {res_str}   Output: MPV Kitty Graphics (vo=kitty)\n"
            "        [ Real-time Terminal Video Active • Press ESC to Exit ]\n"
        )
        viewport.update(status_banner)

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

    def action_seek_back_large(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.seek(-60.0)
            self.update_display()

    def action_seek_forward_large(self) -> None:
        if hasattr(self.app, "engine"):
            self.app.engine.seek(60.0)
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
        if hasattr(self.app, "engine"):
            self.app.engine.toggle_fullscreen()

    def action_dismiss_screen(self) -> None:
        if hasattr(self.app, "engine"):
            state = self.app.engine.state
            if hasattr(self.app, "history") and state.position > 5.0 and state.current_media:
                self.app.history.update_position(state.current_media.path, state.position, state.duration)
            self.app.engine.stop()

        if hasattr(self.app, "update_ui_views"):
            self.app.update_ui_views()

        self.dismiss()

