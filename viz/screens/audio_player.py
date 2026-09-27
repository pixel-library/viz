"""
Dedicated Virtual Audio Player Screen for Viz Media Center.
Premium music and radio player UI inspired by modern audio environments.

Audio playback uses python-mpv engine with vo=null (no video window created).
"""

from __future__ import annotations

from typing import List, Optional
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from viz.metadata import MetadataExtractor
from viz.models import LoopMode, MediaItem, PlaybackState, PlaybackStatus
from viz.widgets.player_status import PlayerStatusWidget


class AudioPlayerScreen(ModalScreen):
    """Virtual Audio Player screen with real MPV audio playback integration."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("q", "dismiss_screen", "Back", show=False),
        Binding("space", "toggle_play_pause", "Play/Pause", show=True),
        Binding("left", "seek_back", "Seek -10s", show=True),
        Binding("right", "seek_forward", "Seek +10s", show=True),
        Binding("up", "volume_up", "Vol +", show=True),
        Binding("down", "volume_down", "Vol -", show=True),
        Binding("m", "toggle_mute", "Mute", show=True),
        Binding("n", "next_track", "Next Track", show=True),
        Binding("b", "prev_track", "Prev Track", show=True),
        Binding("l", "cycle_loop", "Loop Mode", show=True),
        Binding("z", "toggle_shuffle", "Shuffle", show=True),
    ]

    def __init__(self, current_item: MediaItem, playlist: Optional[List[MediaItem]] = None) -> None:
        super().__init__()
        self.current_item = MetadataExtractor.enrich_metadata(current_item)
        self.playlist = playlist or [current_item]
        self.current_index = self.playlist.index(current_item) if current_item in self.playlist else 0
        self.loop_mode: LoopMode = LoopMode.OFF
        self.is_shuffle: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="audio-screen-container"):
            with Horizontal(id="audio-header-bar"):
                yield Label("←  VIZ // MUSIC PLAYER", id="audio-brand")
                yield Label("", id="audio-queue-counter")

            with Horizontal(id="audio-hero"):
                yield Label("", id="audio-cover-art")
                with Vertical(id="audio-track-info"):
                    yield Label("... NOW PLAYING", id="audio-sub-label")
                    yield Label("", id="audio-track-title")
                    yield Label("", id="audio-artist-name")
                    yield Label("", id="audio-album-name")
                    yield Label("", id="audio-fmt-badge")

            with Horizontal(id="audio-scrubber-bar"):
                yield Label("00:00", id="audio-time-cur")
                yield Label("━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━", id="audio-scrubber-line")
                yield Label("00:00", id="audio-time-dur")

            with Horizontal(id="audio-sub-scrubber"):
                yield Label("ON AIR", id="audio-sub-left")
                yield Label("STEREO • HIGH-FIDELITY LIVE »", id="audio-sub-right")

            with Horizontal(id="audio-controls-bar"):
                yield Label("↶ [L] Loop: OFF", id="audio-loop-tag")
                yield Label("  ⏮ [B]    ( ⏸ ) [SPACE]    ⏭ [N]  ", id="audio-center-controls")
                yield Label("🔀 [Z] Shuffle: OFF", id="audio-shuffle-tag")

            with Horizontal(id="audio-footer-line"):
                yield Label("🔊 Volume 80%", id="audio-vol-tag")
                yield Label("Audio Output: System Default", id="audio-device-tag")
                yield Label("[ESC] Back to Filesystem", id="audio-esc-tag")

    def on_mount(self) -> None:
        self.start_playback()
        self.set_interval(0.25, self.update_display)

    def start_playback(self) -> None:
        if 0 <= self.current_index < len(self.playlist):
            self.current_item = MetadataExtractor.enrich_metadata(self.playlist[self.current_index])
            if hasattr(self.app, "last_selected_item"):
                self.app.last_selected_item = self.current_item
            if hasattr(self.app, "engine"):
                resume_pos = 0.0
                if hasattr(self.app, "history"):
                    resume_pos = self.app.history.get_resume_position(self.current_item.path)
                    if resume_pos > 0.0:
                        formatted_time = PlayerStatusWidget.format_time(resume_pos)
                        self.app.notify(f"Resuming at {formatted_time}", title="Resume Playback")
                self.app.engine.play(self.current_item, start_position=resume_pos)

    def update_display(self) -> None:
        engine = getattr(self.app, "engine", None)
        state: PlaybackState = engine.state if engine else PlaybackState()

        # Update history position periodically
        if hasattr(self.app, "history") and state.position > 5.0 and state.status == PlaybackStatus.PLAYING:
            self.app.history.update_position(self.current_item.path, state.position, state.duration)

        counter_lbl = self.query_one("#audio-queue-counter", Label)
        counter_lbl.update(f"[{self.current_index + 1}/{len(self.playlist)}]")

        # Track metadata display
        title_str = self.current_item.title or self.current_item.display_name
        artist_str = self.current_item.artist or "Unknown Artist"
        album_str = self.current_item.album or "Unknown Album"
        ext_str = self.current_item.extension.upper().lstrip(".")
        track_tag = f"Track {self.current_item.track_num}" if self.current_item.track_num else f"Track {self.current_index + 1}"

        self.query_one("#audio-track-title", Label).update(f"[bold white]{title_str}[/bold white]")
        self.query_one("#audio-artist-name", Label).update(f"[bold #b0b8c4]{artist_str}[/bold #b0b8c4]")
        self.query_one("#audio-album-name", Label).update(f"[dim #808a9d]{album_str}[/dim #808a9d]")
        self.query_one("#audio-fmt-badge", Label).update(f"[orange]{ext_str}[/orange] • [dim]{track_tag}[/dim]")

        # Cover art card
        cover_art = self.query_one("#audio-cover-art", Label)
        art_card = (
            " ┌─────────────────────┐ \n"
            " │                     │ \n"
            " │    ♫  AUDIO  ♫      │ \n"
            " │                     │ \n"
            " │    [ VIZ PLAYER ]   │ \n"
            " │                     │ \n"
            " └─────────────────────┘ "
        )
        cover_art.update(art_card)

        # Scrubber rendering
        pos_str = PlayerStatusWidget.format_time(state.position)
        dur_str = PlayerStatusWidget.format_time(state.duration)

        self.query_one("#audio-time-cur", Label).update(pos_str)
        self.query_one("#audio-time-dur", Label).update(dur_str)

        pct = (state.position / max(1.0, state.duration)) if state.duration > 0 else 0.0
        bar_len = max(10, getattr(self.app.size, "width", 80) - 30)
        filled = int(pct * bar_len)
        scrubber = "━" * filled + "●" + "─" * max(0, bar_len - filled - 1)
        self.query_one("#audio-scrubber-line", Label).update(f" {scrubber} ")

        # Controls & icons
        status_icon = "⏸" if state.status == PlaybackStatus.PLAYING else ("▶" if state.status == PlaybackStatus.PAUSED else "■")
        self.query_one("#audio-center-controls", Label).update(f"  ⏮ [B]   ( {status_icon} ) [SPACE]   ⏭ [N]  ")

        vol_str = "Muted" if state.is_muted else f"{state.volume}%"
        self.query_one("#audio-vol-tag", Label).update(f"🔊 Volume {vol_str}")
        self.query_one("#audio-loop-tag", Label).update(f"↶ [L] Loop: {self.loop_mode.value}")
        self.query_one("#audio-shuffle-tag", Label).update(f"🔀 [Z] Shuffle: {'ON' if self.is_shuffle else 'OFF'}")

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

    def action_next_track(self) -> None:
        if len(self.playlist) > 1:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.start_playback()

    def action_prev_track(self) -> None:
        if len(self.playlist) > 1:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.start_playback()

    def action_cycle_loop(self) -> None:
        if self.loop_mode == LoopMode.OFF:
            self.loop_mode = LoopMode.ONE
        elif self.loop_mode == LoopMode.ONE:
            self.loop_mode = LoopMode.ALL
        else:
            self.loop_mode = LoopMode.OFF
        self.update_display()

    def action_toggle_shuffle(self) -> None:
        self.is_shuffle = not self.is_shuffle
        self.update_display()

    def action_dismiss_screen(self) -> None:
        if hasattr(self.app, "engine"):
            state = self.app.engine.state
            if hasattr(self.app, "history") and state.position > 5.0 and state.current_media:
                self.app.history.update_position(state.current_media.path, state.position, state.duration)
            self.app.engine.stop()

        if hasattr(self.app, "update_ui_views"):
            self.app.update_ui_views()

        self.dismiss()
