"""
Help Screen Modal for Viz Media Player.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class HelpScreen(ModalScreen):
    """Modal screen displaying keyboard shortcuts reference."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(12, 9, 5, 0.9);
    }

    #help-dialog {
        width: 68;
        height: auto;
        border: heavy #ff8800;
        background: #0f0a05;
        padding: 1 2;
    }

    #help-title {
        text-align: center;
        text-style: bold;
        color: #ff8800;
        margin-bottom: 1;
    }

    .help-row {
        height: 1;
        margin-bottom: 0;
    }

    .help-key {
        color: #ff8800;
        text-style: bold;
        width: 20;
    }

    .help-desc {
        color: #ffccaa;
    }

    #close-btn {
        margin-top: 1;
        horizontal-align: center;
        border: none;
        background: #ff8800;
        color: #0c0905;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("=== VIZ HELP & KEYBINDINGS ===", id="help-title")

            bindings = [
                ("Enter", "Play selected media file"),
                ("Spacebar", "Toggle Play / Pause"),
                ("M", "Toggle Mute / Unmute"),
                ("Up / Down Arrow", "Adjust Volume (+ / - 5%)"),
                ("Left / Right Arrow", "Seek relative (-10s / +10s)"),
                ("Shift + Left / Right", "Seek relative (-60s / +60s)"),
                ("F", "Toggle Fullscreen mode"),
                ("Ctrl + T", "Toggle TV Mode window"),
                ("/", "Focus Search bar"),
                ("R", "Refresh / Rescan library"),
                ("?", "Display Help Screen"),
                ("Esc", "Dismiss / Clear input"),
                ("Q", "Quit Viz Application"),
            ]

            for key, desc in bindings:
                with Horizontal(classes="help-row"):
                    yield Label(key, classes="help-key")
                    yield Label(desc, classes="help-desc")

            yield Button("Dismiss [ Esc ]", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
