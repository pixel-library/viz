"""
Header Widget displaying professional VIZ branding and system status.
Uses a compact but distinctive single-line design with the VIZ identity.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from viz.constants import __version__
from viz.terminal import TerminalCapabilities


class HeaderWidget(Widget):
    """Compact Professional Header with VIZ branding and capability indicator."""

    def compose(self) -> ComposeResult:
        caps = []
        if TerminalCapabilities.has_display():
            caps.append("GPU")
        if TerminalCapabilities.has_kitty_graphics():
            caps.append("KITTY")
        if TerminalCapabilities.has_truecolor():
            caps.append("24BIT")
        cap_str = " | ".join(caps) if caps else "BASIC"

        yield Label(
            f"  ◆ VIZ  //  OFFLINE MEDIA TERMINAL  v{__version__}                    {cap_str}  ●  READY",
            id="top-status-line",
        )

    def set_status(self, status_str: str) -> None:
        lbl = self.query_one("#top-status-line", Label)
        caps = []
        if TerminalCapabilities.has_display():
            caps.append("GPU")
        if TerminalCapabilities.has_kitty_graphics():
            caps.append("KITTY")
        if TerminalCapabilities.has_truecolor():
            caps.append("24BIT")
        cap_str = " | ".join(caps) if caps else "BASIC"

        lbl.update(f"  ◆ VIZ  //  OFFLINE MEDIA TERMINAL  v{__version__}                    {cap_str}  ●  {status_str.upper()}")
