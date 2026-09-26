"""
Viz App Module - Pure Native MPV & Strict Orange Aesthetic
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional
import mpv

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)


class HelpScreen(ModalScreen):
    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(15, 10, 5, 0.9);
    }
    #help-dialog {
        width: 65;
        height: auto;
        border: heavy orange;
        background: #0f0b06;
        padding: 1 2;
    }
    #help-title {
        text-align: center;
        text-style: bold;
        color: orange;
        margin-bottom: 1;
    }
    .help-row {
        height: 1;
        margin-bottom: 0;
    }
    .help-key {
        color: orange;
        text-style: bold;
        width: 18;
    }
    .help-desc {
        color: #ffccaa;
    }
    #close-btn {
        margin-top: 1;
        horizontal-align: center;
        border: none;
        background: orange;
        color: #0d0a05;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("=== VIZ MEDIA PLAYER HELP ===", id="help-title")
            bindings = [
                ("Enter", "Play highlighted media file"),
                ("Spacebar", "Toggle Play / Pause"),
                ("M", "Toggle Mute / Unmute"),
                ("Left Arrow", "Seek backward (-10 seconds)"),
                ("Right Arrow", "Seek forward (+10 seconds)"),
                ("Ctrl + T", "Toggle TV Mode info"),
                ("?", "Display Help Screen"),
                ("Q", "Quit Application"),
            ]
            for key, desc in bindings:
                with Horizontal(classes="help-row"):
                    yield Label(key, classes="help-key")
                    yield Label(desc, classes="help-desc")
            yield Button("Dismiss [ Esc ]", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class VizApp(App):
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        background: #0c0905;
        color: #ffccaa;
    }
    #ascii-header {
        text-align: center;
        color: orange;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
        height: 6;
    }
    #search-container {
        align: center top;
        height: 3;
        margin-top: 0;
        margin-bottom: 1;
    }
    #search-input {
        width: 68;
        border: tall orange;
        background: #140d06;
        color: orange;
        padding: 0 1;
    }
    #search-input:focus {
        border: double #ff9900;
        background: #1c1208;
    }
    .main-box {
        border: round orange;
        height: 1fr;
        margin: 0 2;
        background: #0f0a05;
    }
    .column {
        width: 1fr;
        height: 100%;
        padding: 1 2;
    }
    #left-column {
        border-right: solid #33200d;
    }
    .column-header {
        text-style: bold;
        color: orange;
        margin-bottom: 1;
        padding-bottom: 0;
        border-bottom: heavy orange;
    }
    .category-item {
        color: #d99966;
        padding: 0 1;
        margin-bottom: 1;
    }
    #file-list {
        height: 1fr;
        border: none;
        background: transparent;
    }
    #file-list > ListItem {
        padding: 0 1;
        color: #ffccaa;
        background: transparent;
    }
    #file-list > ListItem:hover {
        background: #241407;
        color: orange;
    }
    #file-list > ListItem.--highlight {
        background: orange;
        color: #000000;
        text-style: bold;
    }
    #player-bar {
        height: 3;
        margin: 0 2;
        border: double orange;
        background: #140e07;
        padding: 0 2;
        align: center middle;
    }
    .bar-info {
        color: orange;
        text-style: bold;
    }
    .bar-title {
        color: #ffffff;
        text-style: bold;
        width: 1fr;
        text-align: center;
    }
    .bar-time {
        color: orange;
    }
    Footer {
        background: #080503;
        color: orange;
    }
    """

    BINDINGS = [
        Binding("ctrl+t", "toggle_tv_mode", "TV Mode", show=True),
        Binding("?", "show_help", "Help", show=True),
        Binding("q", "quit_app", "Quit", show=True),
        Binding("space", "toggle_play_pause", "Play/Pause", show=False),
        Binding("m", "toggle_mute", "Mute", show=False),
        Binding("left", "seek_left", "Seek -10s", show=False),
        Binding("right", "seek_right", "Seek +10s", show=False),
    ]

    ASCII_LOGO = (
        "██╗   ██╗██╗███████╗\n"
        "██║   ██║██║╚══███╔╝\n"
        "██║   ██║██║  ███╔╝ \n"
        "╚██╗ ██╔╝██║ ███╔╝  \n"
        " ╚████╔╝ ██║███████╗\n"
        "  ╚═══╝  ╚═╝╚══════╝"
    )

    def __init__(self, initial_dir: Optional[str] = None) -> None:
        super().__init__()
        self.player = mpv.MPV(
            video=True,
            keep_open=True,
            input_default_key_bindings=False,
            osc=True,
            title="Viz Media Window",
        )
        self.target_dir = Path(initial_dir).resolve() if initial_dir else Path.cwd() / "media"
        self.media_files: List[Path] = []
        self.filtered_files: List[Path] = []
        self.current_playing_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        yield Static(self.ASCII_LOGO, id="ascii-header")
        with Horizontal(id="search-container"):
            yield Input(placeholder="> Search movies, series & anime...", id="search-input")
        with Horizontal(classes="main-box"):
            with Vertical(classes="column", id="left-column"):
                yield Label("◆ Discover Categories", classes="column-header")
                yield Label("  • Trending Now", classes="category-item")
                yield Label("  • Top Rated Series", classes="category-item")
                yield Label("  • Latest Releases", classes="category-item")
                yield Label("  • Most Watched", classes="category-item")
            with Vertical(classes="column", id="right-column"):
                yield Label("[ /Browse ]", classes="column-header")
                yield ListView(id="file-list")
        with Horizontal(id="player-bar"):
            yield Label("[ STOPPED ]", id="status-label", classes="bar-info")
            yield Label("No Media Selected - Highlight a file and press Enter", id="title-label", classes="bar-title")
            yield Label("00:00 / 00:00", id="time-label", classes="bar-time")
        yield Footer()

    def on_mount(self) -> None:
        self.scan_media_directory()
        self.populate_file_list()
        self.set_interval(0.5, self.update_player_ui)

    def scan_media_directory(self) -> None:
        self.target_dir.mkdir(parents=True, exist_ok=True)
        valid_extensions = {".mp4", ".mkv", ".mp3"}
        found: List[Path] = []
        if self.target_dir.exists() and self.target_dir.is_dir():
            for p in self.target_dir.glob("*"):
                if p.is_file() and p.suffix.lower() in valid_extensions:
                    found.append(p)
        self.media_files = sorted(found, key=lambda f: f.name.lower())
        self.filtered_files = list(self.media_files)

    def populate_file_list(self) -> None:
        file_list_widget = self.query_one("#file-list", ListView)
        file_list_widget.clear()
        for f in self.filtered_files:
            icon = "🎵 " if f.suffix.lower() == ".mp3" else "🎬 "
            file_list_widget.append(ListItem(Label(f"{icon}{f.name}")))

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.strip().lower()
        if query:
            self.filtered_files = [f for f in self.media_files if query in f.name.lower()]
        else:
            self.filtered_files = list(self.media_files)
        self.populate_file_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.list_view.index
        if index is None and event.item is not None:
            try:
                index = list(event.list_view.children).index(event.item)
            except ValueError:
                index = None
        if index is not None and 0 <= index < len(self.filtered_files):
            self.start_playback(self.filtered_files[index])

    @work(thread=True)
    def start_playback(self, file_path: Path) -> None:
        self.current_playing_file = file_path
        try:
            self.player.play(str(file_path.resolve()))
            self.call_from_thread(self.notify, f"Playing: {file_path.name}", title="MPV Engine")
        except Exception as err:
            self.call_from_thread(self.notify, f"Playback Error: {err}", title="MPV Error", severity="error")

    def action_toggle_play_pause(self) -> None:
        if self.current_playing_file:
            try:
                self.player.pause = not self.player.pause
                status = "PAUSED" if self.player.pause else "PLAYING"
                self.notify(f"Media {status}", title="Playback Control")
            except Exception:
                pass

    def action_toggle_mute(self) -> None:
        try:
            self.player.mute = not self.player.mute
            status = "MUTED" if self.player.mute else "UNMUTED"
            self.notify(f"Audio {status}", title="Audio Control")
        except Exception:
            pass

    def action_seek_left(self) -> None:
        if self.current_playing_file:
            try:
                self.player.seek(-10, reference="relative")
                self.notify("Seek -10s", title="Seek Control")
            except Exception:
                pass

    def action_seek_right(self) -> None:
        if self.current_playing_file:
            try:
                self.player.seek(10, reference="relative")
                self.notify("Seek +10s", title="Seek Control")
            except Exception:
                pass

    def action_toggle_tv_mode(self) -> None:
        self.notify("TV Mode Active", title="TV Mode (Ctrl+T)")

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_quit_app(self) -> None:
        try:
            self.player.stop()
            self.player.terminate()
        except Exception:
            pass
        self.exit()

    def update_player_ui(self) -> None:
        status_lbl = self.query_one("#status-label", Label)
        title_lbl = self.query_one("#title-label", Label)
        time_lbl = self.query_one("#time-label", Label)

        if not self.current_playing_file:
            status_lbl.update("[ STOPPED ]")
            title_lbl.update("No Media Selected - Highlight a file and press Enter")
            time_lbl.update("00:00 / 00:00")
        else:
            try:
                is_paused = bool(getattr(self.player, "pause", False))
                is_muted = bool(getattr(self.player, "mute", False))
                pos = float(getattr(self.player, "time_pos", 0.0) or 0.0)
                dur = float(getattr(self.player, "duration", 0.0) or 0.0)

                state_text = "[ PAUSED ]" if is_paused else "[ PLAYING ]"
                if is_muted:
                    state_text += " (MUTED)"
                status_lbl.update(state_text)
                title_lbl.update(f"▶ {self.current_playing_file.name}")
                time_lbl.update(f"{self.format_time(pos)} / {self.format_time(dur)}")
            except Exception:
                pass

    @staticmethod
    def format_time(seconds: float) -> str:
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins:02d}:{secs:02d}"
