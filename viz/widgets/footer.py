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

    DEFAULT_HINT = "↑↓ Navigate   → Expand   ← Back   ENTER Open   I Info   F Favorite   R Refresh   ? Help   Q Quit"

    def compose(self) -> ComposeResult:
        yield Label(self.DEFAULT_HINT, id="notification-bar")

    def set_hint(self, hint_text: str) -> None:
        """Update active contextual shortcut hint line."""
        lbl = self.query_one("#notification-bar", Label)
        lbl.update(hint_text)

    def set_mode_hint(self, mode: str) -> None:
        if mode == "folder":
            text = "↑↓ Navigate   → Expand   ← Parent Folder   ENTER Open   I Info   F Favorite   ESC Back"
        elif mode == "music":
            text = "↑↓ Navigate   ENTER Play Track   SPACE Pause   Z Shuffle   L Loop   ESC Back"
        else:
            text = self.DEFAULT_HINT

        self.set_hint(text)

