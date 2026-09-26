"""
Header Widget displaying centered ASCII title logo for Viz.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from viz.constants import ASCII_LOGO


class HeaderWidget(Widget):
    """Centered ASCII Header Component."""

    def compose(self) -> ComposeResult:
        yield Static(ASCII_LOGO, id="ascii-header")
