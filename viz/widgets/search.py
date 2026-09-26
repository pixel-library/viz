"""
Search Component Stub (Search removed).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget


class SearchWidget(Widget):
    """Empty Search Stub."""

    def compose(self) -> ComposeResult:
        return []

    def focus_input(self) -> None:
        pass

    def clear_input(self) -> None:
        pass

