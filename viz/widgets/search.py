"""
Search Component wrapping Input widget.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input


class SearchWidget(Widget):
    """Search input component with placeholder."""

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="> Search movies, series & anime...",
            id="search-input",
        )

    def focus_input(self) -> None:
        self.query_one("#search-input", Input).focus()

    def clear_input(self) -> None:
        inp = self.query_one("#search-input", Input)
        inp.value = ""
