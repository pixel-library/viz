"""
Main Textual Application for Viz Terminal Media Player.
Features Hacker/VCR aesthetic, live ASCII equalizer animation, multi-theme engine,
interactive category navigation, directory browser, and persistent state.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import random
from typing import List, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    OptionList,
    Static,
)

from viz.config import ConfigManager
from viz.engine import MediaEngine

# =============================================================================
# THEME SPECIFICATIONS (CYBERPUNK, SYNTHWAVE, AMBER CRT, MONOKAI)
# =============================================================================

THEMES = {
    "cyberpunk": {
        "name": "Cyberpunk Cyan/Neon",
        "primary": "#00f0ff",
        "secondary": "#00ff66",
        "bg_screen": "#090a0f",
        "bg_box": "#0d0e15",
        "bg_bar": "#0f121d",
        "accent": "#ff0055",
    },
    "synthwave": {
        "name": "Retro Synthwave",
        "primary": "#ff79c6",
        "secondary": "#bd93f9",
        "bg_screen": "#120a1c",
        "bg_box": "#190e28",
        "bg_bar": "#211336",
        "accent": "#f1fa8c",
    },
    "amber": {
        "name": "Amber CRT Terminal",
        "primary": "#ffb86c",
        "secondary": "#ff9900",
        "bg_screen": "#100d08",
        "bg_box": "#18130a",
        "bg_bar": "#221b0e",
        "accent": "#ff5555",
    },
    "monokai": {
        "name": "Monokai Dark",
        "primary": "#66d9ef",
        "secondary": "#a6e22e",
        "bg_screen": "#141619",
        "bg_box": "#1e2227",
        "bg_bar": "#282c34",
        "accent": "#fd971f",
    },
}

# =============================================================================
# HELP MODAL SCREEN
# =============================================================================

class HelpScreen(ModalScreen):
    """Modal screen displaying keyboard shortcuts and app architecture info."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(10, 12, 20, 0.85);
    }

    #help-dialog {
        width: 70;
        height: auto;
        border: heavy #00f0ff;
        background: #0d0e15;
        padding: 1 2;
    }

    #help-title {
        text-align: center;
        text-style: bold;
        color: #00ff66;
        margin-bottom: 1;
    }

    .help-row {
        height: 1;
        margin-bottom: 0;
    }

    .help-key {
        color: #00f0ff;
        text-style: bold;
        width: 22;
    }

    .help-desc {
        color: #e0e0e0;
    }

    #close-btn {
        margin-top: 1;
        horizontal-align: center;
        border: none;
        background: #00f0ff;
        color: #0d0e15;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("=== VIZ MEDIA PLAYER SHORTCUTS ===", id="help-title")

            bindings = [
                ("Enter", "Play selected file / Open directory"),
                ("Spacebar", "Toggle Play / Pause"),
                ("M", "Toggle Mute / Unmute"),
                ("Up / Down Arrow", "Adjust Volume (+ / - 5%)"),
                ("Left / Right Arrow", "Seek relative (-10s / +10s)"),
                ("T", "Cycle Color Themes"),
                ("B", "Toggle Favorite / Bookmark (★)"),
                ("A / S", "Cycle Audio Stream / Subtitles"),
                ("Ctrl + T", "Toggle TV Mode / Window Frame"),
                ("?", "Show Help Screen"),
                ("Q", "Quit Viz Player"),
            ]

            for key, desc in bindings:
                with Horizontal(classes="help-row"):
                    yield Label(key, classes="help-key")
                    yield Label(desc, classes="help-desc")

            yield Button("Dismiss [ Esc ]", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


# =============================================================================
# MAIN VIZ TEXTUAL APP CLASS
# =============================================================================

class VizApp(App):
    """
    Viz - Terminal Media Player Application
    """

    CSS = """
    /* Main Theme & Base Rules */
    Screen {
        background: #090a0f;
        color: #e0e0e0;
    }

    /* Header ASCII Logo */
    #ascii-header {
        text-align: center;
        color: #00f0ff;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
        height: 6;
    }

    /* Search Component */
    #search-container {
        align: center top;
        height: 3;
        margin-top: 0;
        margin-bottom: 1;
    }

    #search-input {
        width: 72;
        border: tall #00ff66;
        background: #0f111a;
        color: #00ff66;
        padding: 0 1;
    }

    #search-input:focus {
        border: double #00f0ff;
        background: #141824;
    }

    /* Main Navigation UI (The Box) */
    .main-box {
        border: round white;
        height: 1fr;
        margin: 0 2;
        background: #0d0e15;
    }

    .column {
        width: 1fr;
        height: 100%;
        padding: 1 2;
    }

    #left-column {
        border-right: solid #2a2e3d;
    }

    .column-header {
        text-style: bold;
        color: #00f0ff;
        margin-bottom: 1;
        border-bottom: heavy #00f0ff;
    }

    /* Category List Widget */
    #category-list {
        height: 1fr;
        border: none;
        background: transparent;
    }

    #category-list > ListItem {
        padding: 0 1;
        color: #a0a5b5;
        background: transparent;
    }

    #category-list > ListItem:hover {
        background: #141824;
        color: #00ff66;
    }

    #category-list > ListItem.--highlight {
        background: #00f0ff;
        color: #090a0f;
        text-style: bold;
    }

    /* Dynamic File Browser (Right Column) */
    #file-list {
        height: 1fr;
        border: none;
        background: transparent;
    }

    #file-list > ListItem {
        padding: 0 1;
        color: #c0c5d5;
        background: transparent;
    }

    #file-list > ListItem:hover {
        background: #181c2b;
        color: #00ff66;
    }

    #file-list > ListItem.--highlight {
        background: #00f0ff;
        color: #090a0f;
        text-style: bold;
    }

    /* Player Status & Control Bar */
    #player-bar {
        height: 3;
        margin: 0 2;
        border: double #00ff66;
        background: #0f121d;
        padding: 0 2;
        align: center middle;
    }

    .bar-info {
        color: #00ff66;
        text-style: bold;
        width: 14;
    }

    .bar-title {
        color: #ffffff;
        text-style: bold;
        width: 1fr;
        text-align: center;
    }

    .bar-scrubber {
        color: #00f0ff;
        width: 32;
        text-align: right;
    }

    .eq-bar {
        color: #ff0055;
        text-style: bold;
        width: 14;
    }

    Footer {
        background: #05060a;
        color: #00f0ff;
    }
    """

    BINDINGS = [
        Binding("ctrl+t", "toggle_tv_mode", "TV Mode", show=True),
        Binding("t", "cycle_theme", "Theme", show=True),
        Binding("?", "show_help", "Help", show=True),
        Binding("q", "quit_app", "Quit", show=True),
        Binding("space", "toggle_play_pause", "Play/Pause", show=False),
        Binding("m", "toggle_mute", "Mute", show=False),
        Binding("b", "toggle_favorite", "Favorite", show=False),
        Binding("up", "volume_up", "Vol +", show=False),
        Binding("down", "volume_down", "Vol -", show=False),
        Binding("left", "seek_left", "Seek -10s", show=False),
        Binding("right", "seek_right", "Seek +10s", show=False),
        Binding("a", "cycle_audio", "Audio Stream", show=False),
        Binding("s", "cycle_sub", "Subtitles", show=False),
    ]

    ASCII_LOGO = (
        "██╗   ██╗██╗███████╗\n"
        "██║   ██║██║╚══███╔╝\n"
        "██║   ██║██║  ███╔╝ \n"
        "╚██╗ ██╔╝██║ ███╔╝  \n"
        " ╚████╔╝ ██║███████╗\n"
        "  ╚═══╝  ╚═╝╚══════╝"
    )

    CATEGORIES = [
        ("all", "✦ All Media Files"),
        ("video", "🎬 Movies & Videos"),
        ("audio", "🎵 Music & Audio"),
        ("favorites", "★ Favorites"),
        ("recent", "🕒 Recently Played"),
        ("folders", "📁 Directory Browser"),
    ]

    EQUALIZER_FRAMES = [
        " ▅ █ ▇ ▅ ▄ ▅ █",
        " ▄ ▅ █ ▇ ▅ ▄ ▅",
        " ▇ ▅ ▄ ▅ █ ▇ ▅",
        " █ ▇ ▅ ▄ ▅ █ ▇",
        " ▅ █ ▇ ▅ ▄ ▅ █",
    ]

    def __init__(self, initial_dir: Optional[str] = None) -> None:
        super().__init__()
        self.config = ConfigManager()
        if initial_dir:
            self.current_dir = Path(initial_dir).resolve()
        else:
            self.current_dir = Path(self.config.get("last_directory", str(Path.cwd()))).resolve()

        initial_vol = int(self.config.get("volume", 80))
        self.engine = MediaEngine(initial_volume=initial_vol)
        
        self.media_files: List[Path] = []
        self.filtered_files: List[Path] = []
        self.active_category: str = "all"
        self.active_theme_name: str = str(self.config.get("theme", "cyberpunk"))
        self.eq_frame_idx: int = 0

    def compose(self) -> ComposeResult:
        yield Static(self.ASCII_LOGO, id="ascii-header")

        with Horizontal(id="search-container"):
            yield Input(placeholder="> Search movies, series & anime...", id="search-input")

        with Horizontal(classes="main-box"):
            # Left Column (Category Selector)
            with Vertical(classes="column", id="left-column"):
                yield Label("◆ Discover Categories", classes="column-header")
                yield ListView(id="category-list")
                
                engine_type = "MPV (Native)" if self.engine.using_mpv else "Simulation Engine"
                yield Label(f"\n[ Engine Status ]\nBackend: {engine_type}\nTheme: {self.active_theme_name.capitalize()}", classes="category-item", id="engine-status")

            # Right Column (File Browser)
            with Vertical(classes="column", id="right-column"):
                yield Label(f"[ {self.current_dir.name or '/'} ]", classes="column-header", id="browse-header")
                yield ListView(id="file-list")

        # Player Controls Bar
        with Horizontal(id="player-bar"):
            yield Label("[ STOPPED ]", id="status-label", classes="bar-info")
            yield Label(" ▅ █ ▇ ▅ ▄ ▅", id="eq-label", classes="eq-bar")
            yield Label("No Media Selected - Press Enter on a file", id="title-label", classes="bar-title")
            yield Label("[░░░░░░░░░░] 00:00 / 00:00", id="time-label", classes="bar-scrubber")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize UI widgets and state on mount."""
        self.populate_categories()
        self.scan_media_files()
        self.populate_file_list()
        self.set_interval(0.4, self.update_player_ui)

    def populate_categories(self) -> None:
        """Populate the left column category list."""
        cat_widget = self.query_one("#category-list", ListView)
        cat_widget.clear()
        for cat_id, name in self.CATEGORIES:
            cat_widget.append(ListItem(Label(name), id=f"cat-{cat_id}"))

    def scan_media_files(self) -> None:
        """Scan target directory for media files using pathlib."""
        valid_video = {".mp4", ".mkv", ".webm", ".avi", ".mov"}
        valid_audio = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a"}
        found: List[Path] = []

        if self.current_dir.exists() and self.current_dir.is_dir():
            try:
                for p in self.current_dir.glob("*"):
                    if p.is_file() and (p.suffix.lower() in valid_video or p.suffix.lower() in valid_audio):
                        found.append(p)
                    elif p.is_dir() and not p.name.startswith("."):
                        found.append(p)  # Include directories for folder navigation
            except Exception as e:
                print(f"[Scan Error]: {e}")

        # Auto-create demo files if directory is empty
        if not found and self.current_dir == Path.cwd():
            demo_dir = self.current_dir / "Media"
            demo_dir.mkdir(exist_ok=True)
            demo_files = [
                demo_dir / "Cyberpunk_2077_NightCity_Trailer.mp4",
                demo_dir / "VCR_Synthwave_Theme_Track01.mp3",
                demo_dir / "Anime_Opening_Sequence_1080p.mkv",
                demo_dir / "SciFi_Short_Film_Master.mp4",
                demo_dir / "Retro_Arcade_Ambience.mp3",
            ]
            for df in demo_files:
                if not df.exists():
                    try:
                        df.write_text("VIZ DEMO MEDIA FILE PLACEHOLDER")
                    except Exception:
                        pass
                found.append(df)

        self.media_files = sorted(found, key=lambda f: (not f.is_dir(), f.name.lower()))
        self.filter_by_category()

    def filter_by_category(self) -> None:
        """Filter current file view based on active category."""
        video_exts = {".mp4", ".mkv", ".webm", ".avi", ".mov"}
        audio_exts = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a"}

        if self.active_category == "all":
            self.filtered_files = list(self.media_files)
        elif self.active_category == "video":
            self.filtered_files = [f for f in self.media_files if f.is_dir() or f.suffix.lower() in video_exts]
        elif self.active_category == "audio":
            self.filtered_files = [f for f in self.media_files if f.is_dir() or f.suffix.lower() in audio_exts]
        elif self.active_category == "favorites":
            favs = set(self.config.get("favorites", []))
            self.filtered_files = [f for f in self.media_files if str(f.resolve()) in favs]
        elif self.active_category == "recent":
            history = self.config.get("recent_history", [])
            recent_paths = [Path(p) for p in history if Path(p).exists()]
            self.filtered_files = recent_paths if recent_paths else list(self.media_files)
        elif self.active_category == "folders":
            self.filtered_files = [f for f in self.media_files if f.is_dir()]

    def populate_file_list(self) -> None:
        """Populate the Right Column file browser list."""
        file_list_widget = self.query_one("#file-list", ListView)
        file_list_widget.clear()

        for f in self.filtered_files:
            if f.is_dir():
                prefix = "📁 "
            elif f.suffix.lower() in [".mp3", ".flac", ".wav", ".aac"]:
                prefix = "🎵 "
            else:
                prefix = "🎬 "

            fav_marker = " ★" if self.config.is_favorite(str(f.resolve())) else ""
            file_list_widget.append(ListItem(Label(f"{prefix}{f.name}{fav_marker}")))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Real-time search filtering."""
        query = event.value.strip().lower()
        if query:
            self.filtered_files = [
                f for f in self.media_files if query in f.name.lower()
            ]
        else:
            self.filter_by_category()
        self.populate_file_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list selection for category list and file list."""
        if event.list_view.id == "category-list":
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(self.CATEGORIES):
                self.active_category = self.CATEGORIES[idx][0]
                self.filter_by_category()
                self.populate_file_list()
                self.notify(f"Category: {self.CATEGORIES[idx][1]}", title="Navigation")
        elif event.list_view.id == "file-list":
            idx = event.list_view.index
            if idx is None and event.item is not None:
                try:
                    idx = list(event.list_view.children).index(event.item)
                except ValueError:
                    idx = None
            if idx is not None and 0 <= idx < len(self.filtered_files):
                target = self.filtered_files[idx]
                if target.is_dir():
                    self.current_dir = target.resolve()
                    self.config.set("last_directory", str(self.current_dir))
                    self.query_one("#browse-header", Label).update(f"[ {self.current_dir.name} ]")
                    self.scan_media_files()
                    self.populate_file_list()
                else:
                    self.start_playback(target)

    @work(thread=True)
    def start_playback(self, file_path: Path) -> None:
        """Start playback non-blockingly."""
        self.engine.play_file(file_path)
        self.config.add_recent(str(file_path.resolve()))
        self.call_from_thread(self.notify, f"Playing: {file_path.name}", title="Viz Media Player")

    def action_toggle_play_pause(self) -> None:
        is_paused = self.engine.toggle_pause()
        self.notify("PAUSED" if is_paused else "PLAYING", title="Playback")

    def action_toggle_mute(self) -> None:
        is_muted = self.engine.toggle_mute()
        self.notify("MUTED" if is_muted else "UNMUTED", title="Audio")

    def action_volume_up(self) -> None:
        new_vol = self.engine.change_volume(5)
        self.config.set("volume", new_vol)
        self.notify(f"Volume: {new_vol}%", title="Audio Volume")

    def action_volume_down(self) -> None:
        new_vol = self.engine.change_volume(-5)
        self.config.set("volume", new_vol)
        self.notify(f"Volume: {new_vol}%", title="Audio Volume")

    def action_seek_left(self) -> None:
        pos = self.engine.seek(-10.0)
        self.notify(f"Seek -10s ({self.format_time(pos)})", title="Seek")

    def action_seek_right(self) -> None:
        pos = self.engine.seek(10.0)
        self.notify(f"Seek +10s ({self.format_time(pos)})", title="Seek")

    def action_cycle_theme(self) -> None:
        theme_keys = list(THEMES.keys())
        curr_idx = theme_keys.index(self.active_theme_name) if self.active_theme_name in theme_keys else 0
        next_theme = theme_keys[(curr_idx + 1) % len(theme_keys)]
        self.active_theme_name = next_theme
        self.config.set("theme", next_theme)
        
        status_lbl = self.query_one("#engine-status", Label)
        engine_type = "MPV (Native)" if self.engine.using_mpv else "Simulation Engine"
        status_lbl.update(f"\n[ Engine Status ]\nBackend: {engine_type}\nTheme: {next_theme.capitalize()}")
        
        self.notify(f"Theme Switched: {THEMES[next_theme]['name']}", title="Theme Switcher")

    def action_toggle_favorite(self) -> None:
        if self.engine.state.file_path:
            fpath = str(self.engine.state.file_path.resolve())
            if self.config.is_favorite(fpath):
                self.config.remove_favorite(fpath)
                self.notify(f"Removed from Favorites: {self.engine.state.title}", title="Favorites")
            else:
                self.config.add_favorite(fpath)
                self.notify(f"Added to Favorites ★: {self.engine.state.title}", title="Favorites")
            self.populate_file_list()

    def action_cycle_audio(self) -> None:
        track = self.engine.cycle_audio_track()
        self.notify(f"Audio Track: Stream #{track}", title="Audio Stream")

    def action_cycle_sub(self) -> None:
        sub = self.engine.cycle_sub_track()
        lbl = "Off" if sub == 0 else f"Track #{sub}"
        self.notify(f"Subtitles: {lbl}", title="Subtitle Control")

    def action_toggle_tv_mode(self) -> None:
        mode = "Native Window Overlay" if self.engine.using_mpv else "Terminal Frame Mode"
        self.notify(f"TV Mode Active: {mode}", title="TV Mode (Ctrl+T)")

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_quit_app(self) -> None:
        self.engine.stop()
        self.exit()

    def update_player_ui(self) -> None:
        st = self.engine.update_position()

        status_lbl = self.query_one("#status-label", Label)
        eq_lbl = self.query_one("#eq-label", Label)
        title_lbl = self.query_one("#title-label", Label)
        time_lbl = self.query_one("#time-label", Label)

        if not st.is_playing:
            status_lbl.update("[ STOPPED ]")
            eq_lbl.update(" ▅ █ ▇ ▅ ▄ ▅")
            title_lbl.update("No Media Selected - Select a file to play")
            time_lbl.update("[░░░░░░░░░░] 00:00 / 00:00")
        else:
            state_text = "[ PAUSED ]" if st.is_paused else "[ PLAYING ]"
            if st.is_muted:
                state_text += " (MUTED)"
            status_lbl.update(state_text)

            # Animate ASCII equalizer when playing
            if not st.is_paused:
                self.eq_frame_idx = (self.eq_frame_idx + 1) % len(self.EQUALIZER_FRAMES)
                eq_lbl.update(self.EQUALIZER_FRAMES[self.eq_frame_idx])
            else:
                eq_lbl.update(" ▄ ▄ ▄ ▄ ▄ ▄")

            fav = " ★" if (st.file_path and self.config.is_favorite(str(st.file_path.resolve()))) else ""
            title_lbl.update(f"▶ {st.title}{fav} | Vol: {st.volume}%")

            # Progress Bar Scrubber
            pct = (st.position / st.duration) if st.duration > 0 else 0.0
            filled = int(pct * 10)
            scrubber = "█" * filled + "░" * (10 - filled)
            
            curr_str = self.format_time(st.position)
            dur_str = self.format_time(st.duration)
            time_lbl.update(f"[{scrubber}] {curr_str} / {dur_str}")

    @staticmethod
    def format_time(seconds: float) -> str:
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins:02d}:{secs:02d}"
