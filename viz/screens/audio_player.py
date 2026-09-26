"""
Dedicated Virtual Audio Player Screen for Viz Media Center.
Provides full-terminal audio player controls, track metadata, waveform status, and MPV integration.
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
    ]

    def __init__(self, current_item: MediaItem, playlist: Optional[List[MediaItem]] = None) -> None:
        super().__init__()
        self.current_item = current_item
        self.playlist = playlist or [current_item]
        self.current_index = self.playlist.index(current_item) if current_item in self.playlist else 0

    def compose(self) -> ComposeResult:
        with Vertical(id="audio-screen-container"):
            yield Label("VIZ // AUDIO PLAYER", classes="dialog-header", id="audio-header")
            yield Label("", id="audio-display-body")
            yield Label("", id="audio-info-footer")
            yield Footer()

    def on_mount(self) -> None:
        self.start_playback()
        self.set_interval(0.5, self.update_display)

    def start_playback(self) -> None:
        if 0 <= self.current_index < len(self.playlist):
            self.current_item = self.playlist[self.current_index]
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

        header = self.query_one("#audio-header", Label)
        header.update(f"VIZ // AUDIO PLAYER  [{self.current_index + 1}/{len(self.playlist)}]")


        pos_str = PlayerStatusWidget.format_time(state.position)
        dur_str = PlayerStatusWidget.format_time(state.duration)
        pct = (state.position / max(1.0, state.duration)) if state.duration > 0 else 0.0
        bar_len = 36
        filled = int(pct * bar_len)
        scrubber = "━" * filled + "●" + "─" * max(0, bar_len - filled - 1)

        artist_str = f"By {self.current_item.artist}" if self.current_item.artist else ""
        album_str = f"Album: {self.current_item.album}" if self.current_item.album else ""
        status_text = "▶ PLAYING" if state.status == PlaybackStatus.PLAYING else ("⏸ PAUSED" if state.status == PlaybackStatus.PAUSED else "■ STOPPED")

        audio_ascii_card = (
            "\n\n"
            "                 [ AUDIO ]                \n\n"
            f"          {self.current_item.title or self.current_item.name}          \n"
            f"          {artist_str}  {album_str}          \n\n"
            f"               {pos_str} / {dur_str}               \n"
            f"       {scrubber}       \n\n"
            f"               {status_text}               \n"
        )

        display_body = self.query_one("#audio-display-body", Label)
        display_body.update(audio_ascii_card)

        info_footer = self.query_one("#audio-info-footer", Label)
        vol_str = "Muted" if state.is_muted else f"Volume {state.volume}%"
        info_footer.update(f" {vol_str}       Speed {state.speed}x       Repeat {state.loop_mode.value}")

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

    def action_dismiss_screen(self) -> None:
        self.dismiss()
