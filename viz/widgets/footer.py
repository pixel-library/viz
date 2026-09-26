"""
Contextual Footer Widget for Viz Media Center.
Changes keyboard hints dynamically based on active screen and mode.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label


class ContextualFooter(Widget):
    """Contextual Footer displaying mode-specific keyboard action hints."""

    DEFAULT_HINT = "↑↓ Navigate   ENTER Play   SPACE Pause   / Search   I Info   ? Help   Q Quit"

    def compose(self) -> ComposeResult:
        yield Label(self.DEFAULT_HINT, id="notification-bar")

    def set_hint(self, hint_text: str) -> None:
        """Update active contextual shortcut hint line."""
        lbl = self.query_one("#notification-bar", Label)
        lbl.update(hint_text)

    def set_mode_hint(self, mode: str) -> None:
        """Set hints tailored for Movies, Music, Series, Queue, or Player."""
        if mode == "movies":
            text = "↑↓ Navigate   ENTER Play   I Info   F Favorite   / Search   ESC Back"
        elif mode == "series":
            text = "↑↓ Select Series   ENTER Open Episodes   I Info   / Search   ESC Back"
        elif mode == "music":
            text = "↑↓ Navigate   ENTER Play   SPACE Pause   Z Shuffle   L Loop   ESC Back"
        elif mode == "queue":
            text = "ENTER Play   D Remove   C Clear   Z Shuffle   L Loop   ESC Back"
        elif mode == "search":
            text = "Type query   ENTER Select   ↑↓ Navigate   ESC Exit Search"
        else:
            text = self.DEFAULT_HINT

        self.set_hint(text)
