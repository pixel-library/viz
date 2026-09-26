"""
Player Status Bar Widget.
Renders current playback status, track title, time scrubber, and volume/mute indicators.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Label

from viz.models import PlaybackState, PlaybackStatus


class PlayerStatusWidget(Widget):
    """Player Status Component with time scrubber."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="player-bar"):
            yield Label("[ STOPPED ]", id="status-label", classes="bar-status")
            yield Label(
                "No Media Selected - Highlight a file and press Enter",
                id="title-label",
                classes="bar-title",
            )
            yield Label(
                "00:00 ──────────────────── 00:00",
                id="time-label",
                classes="bar-scrubber",
            )

    def update_state(self, state: PlaybackState) -> None:
        """Synchronize UI widget with current PlaybackState."""
        status_lbl = self.query_one("#status-label", Label)
        title_lbl = self.query_one("#title-label", Label)
        time_lbl = self.query_one("#time-label", Label)

        if state.status == PlaybackStatus.STOPPED or not state.current_media:
            status_lbl.update("[ STOPPED ]")
            title_lbl.update("No Media Selected - Highlight a file and press Enter")
            time_lbl.update("00:00 ──────────────────── 00:00")
            return

        # Status Label
        if state.status == PlaybackStatus.PAUSED:
            st_text = "[ PAUSED ]"
        elif state.status == PlaybackStatus.PLAYING:
            st_text = "[ PLAYING ]"
        elif state.status == PlaybackStatus.LOADING:
            st_text = "[ LOADING ]"
        elif state.status == PlaybackStatus.ENDED:
            st_text = "[ ENDED ]"
        elif state.status == PlaybackStatus.ERROR:
            st_text = "[ ERROR ]"
        else:
            st_text = "[ STOPPED ]"

        if state.is_muted:
            st_text += " [MUTED]"

        status_lbl.update(st_text)

        # Title Label
        icon = state.current_media.icon if state.current_media else "▶"
        title_lbl.update(f"{icon} {state.current_media.name} (Vol: {state.volume}%)")

        # Time Scrubber
        curr_str = self.format_time(state.position)
        dur_str = self.format_time(state.duration) if state.duration > 0 else "--:--"

        pct = (state.position / state.duration) if state.duration > 0 else 0.0
        pct = max(0.0, min(1.0, pct))
        total_chars = 16
        filled = int(pct * total_chars)
        scrubber = "━" * filled + "●" + "─" * (total_chars - filled)

        time_lbl.update(f"{curr_str} {scrubber} {dur_str}")

    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds into HH:MM:SS or MM:SS string safely."""
        if seconds <= 0:
            return "00:00"
        total_sec = int(seconds)
        hours = total_sec // 3600
        mins = (total_sec % 3600) // 60
        secs = total_sec % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"
