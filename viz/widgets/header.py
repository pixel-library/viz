"""
Header Widget displaying compact VIZ branding and system status line.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Static

from viz.constants import ASCII_LOGO


class HeaderWidget(Widget):
    """Compact Header Component with VIZ ASCII logo and system status line."""

    def compose(self) -> ComposeResult:
        yield Static(ASCII_LOGO, id="ascii-header")
        yield Label("VIZ // OFFLINE MEDIA TERMINAL                        ● SYSTEM READY", id="top-status-line")

    def set_status(self, status_str: str) -> None:
        lbl = self.query_one("#top-status-line", Label)
        lbl.update(f"VIZ // OFFLINE MEDIA TERMINAL                        ● {status_str.upper()}")


