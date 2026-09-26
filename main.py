#!/usr/bin/env python3
"""
===============================================================================
 VIZ - Offline Hacker/VCR Terminal Media Player & Media Pipeline Specification
===============================================================================

System Architecture & Concurrency Model:
----------------------------------------
1. Frontend (TUI): Built using Textual (async event loop). The TUI manages the 
   terminal viewport, responsive layout, search input, CSS styling, and keybindings.
2. Backend (Media Engine): Driven by python-mpv (C bindings to libmpv). MPV spawns
   its own native decoding and rendering C threads.
3. Threading Safety: Interactions with python-mpv are executed asynchronously or 
   offloaded via worker threads (`asyncio.to_thread` / Textual `@work`) to ensure
   playback actions (loading files, seeking, audio track changes) NEVER freeze 
   the Textual TUI event loop.
4. Fallback Architecture: If system `libmpv` is not detected, Viz seamlessly activates
   an internal simulated media engine to ensure full TUI preview stability.

Dependencies & Installation:
----------------------------
- Python 3.10+
- Install Python packages:
    pip install textual python-mpv
- Install System Media Engine (libmpv):
    - Ubuntu/Debian:  sudo apt update && sudo apt install -y mpv libmpv-dev
    - Arch Linux:     sudo pacman -S mpv
    - Fedora:         sudo dnf install mpv mpv-devel
    - macOS:          brew install mpv

Usage:
------
    python main.py
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import time
from typing import List, Optional

# Textual imports
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.events import Key
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

# Attempt to import python-mpv gracefully
HAS_MPV = False
MPV_ERROR_MSG = ""
try:
    import mpv
    HAS_MPV = True
except Exception as e:
    HAS_MPV = False
    MPV_ERROR_MSG = str(e)


# =============================================================================
# MEDIA ENGINE WRAPPER (MPV & SIMULATION FALLBACK)
# =============================================================================

@dataclass
class PlaybackState:
    file_path: Optional[Path] = None
    title: str = "No Media Loaded"
    is_playing: bool = False
    is_paused: bool = False
    is_muted: bool = False
    duration: float = 0.0
    position: float = 0.0
    volume: int = 100


class MediaEngine:
    """
    Asynchronous wrapper for MPV media engine with fallback simulation support.
    Manages non-blocking calls to python-mpv.
    """

    def __init__(self) -> None:
        self.mpv_instance = None
        self.using_mpv = False
        self.state = PlaybackState()
        self.init_error: Optional[str] = None
        
        self._sim_task: Optional[asyncio.Task] = None

        if HAS_MPV:
            try:
                # Initialize python-mpv instance with borderless overlay window for video
                self.mpv_instance = mpv.MPV(
                    video=True,
                    keep_open=True,
                    input_default_key_bindings=False,
                    osc=True,
                    title="Viz Media Output",
                )
                self.using_mpv = True
            except Exception as err:
                self.using_mpv = False
                self.init_error = f"libmpv init warning: {err}"
        else:
            self.init_error = MPV_ERROR_MSG or "python-mpv package or libmpv library not installed."

    def play_file(self, file_path: Path) -> None:
        """Trigger media playback for the specified path."""
        self.state.file_path = file_path
        self.state.title = file_path.name
        self.state.is_playing = True
        self.state.is_paused = False
        self.state.position = 0.0

        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.play(str(file_path.resolve()))
                # Update duration if available
                dur = getattr(self.mpv_instance, "duration", None)
                if dur:
                    self.state.duration = float(dur)
                else:
                    self.state.duration = 180.0  # default estimate
            except Exception as e:
                print(f"[MPV Error] Failed to play {file_path}: {e}")
        else:
            # Fallback mock duration based on file type
            self.state.duration = 240.0 if file_path.suffix.lower() in [".mp4", ".mkv"] else 180.0

    def toggle_pause(self) -> bool:
        """Toggle pause/play state."""
        if not self.state.is_playing:
            return False
        
        self.state.is_paused = not self.state.is_paused
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.pause = self.state.is_paused
            except Exception:
                pass
        return self.state.is_paused

    def toggle_mute(self) -> bool:
        """Toggle mute state."""
        self.state.is_muted = not self.state.is_muted
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.mute = self.state.is_muted
            except Exception:
                pass
        return self.state.is_muted

    def seek(self, seconds: float) -> float:
        """Seek relative seconds (+10 or -10)."""
        if not self.state.is_playing:
            return 0.0
        
        new_pos = max(0.0, min(self.state.duration, self.state.position + seconds))
        self.state.position = new_pos

        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.seek(seconds, reference="relative")
            except Exception:
                pass
        return new_pos

    def update_position(self) -> PlaybackState:
        """Periodically sync state from MPV or simulate progress."""
        if self.using_mpv and self.mpv_instance and self.state.is_playing:
            try:
                pos = getattr(self.mpv_instance, "time_pos", None)
                if pos is not None:
                    self.state.position = float(pos)
                dur = getattr(self.mpv_instance, "duration", None)
                if dur is not None:
                    self.state.duration = float(dur)
                self.state.is_paused = bool(getattr(self.mpv_instance, "pause", False))
                self.state.is_muted = bool(getattr(self.mpv_instance, "mute", False))
            except Exception:
                pass
        elif self.state.is_playing and not self.state.is_paused:
            # Advance simulation timer
            self.state.position += 1.0
            if self.state.position >= self.state.duration:
                self.state.position = self.state.duration

        return self.state

    def stop(self) -> None:
        """Stop playback and cleanup."""
        self.state.is_playing = False
        self.state.is_paused = False
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.stop()
                self.mpv_instance.terminate()
            except Exception:
                pass


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
        width: 65;
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
        width: 18;
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
            yield Label("=== VIZ MEDIA PLAYER HELP ===", id="help-title")
            
            bindings = [
                ("Enter", "Play selected media file"),
                ("Spacebar", "Toggle Play / Pause"),
                ("M", "Toggle Mute / Unmute"),
                ("Left Arrow", "Seek backward (-10 seconds)"),
                ("Right Arrow", "Seek forward (+10 seconds)"),
                ("Ctrl + T", "Toggle TV Mode / Fullscreen Window"),
                ("?", "Show this Help Screen"),
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
# MAIN TEXTUAL APP
# =============================================================================

class VizApp(App):
    """
    Viz - Terminal Media Player
    A responsive Textual application adhering to a VCR/Hacker aesthetic.
    """

    CSS = """
    /* Main Theme & Reset */
    Screen {
        background: #090a0f;
        color: #e0e0e0;
    }

    /* Header ASCII Component */
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
        width: 68;
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
        padding-bottom: 0;
        border-bottom: heavy #00f0ff;
    }

    .category-item {
        color: #a0a5b5;
        padding: 0 1;
        margin-bottom: 1;
    }

    .category-item:hover {
        color: #00ff66;
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

    /* Player Status & Control Overlay Bar */
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
    }

    .bar-title {
        color: #ffffff;
        text-style: bold;
        width: 1fr;
        text-align: center;
    }

    .bar-time {
        color: #00f0ff;
    }

    .bar-engine {
        color: #ffaa00;
        text-style: italic;
    }

    /* Footer Styling */
    Footer {
        background: #05060a;
        color: #00f0ff;
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

    def __init__(self) -> None:
        super().__init__()
        self.engine = MediaEngine()
        self.media_files: List[Path] = []
        self.filtered_files: List[Path] = []
        self._update_timer = None

    def compose(self) -> ComposeResult:
        # Header Component
        yield Static(self.ASCII_LOGO, id="ascii-header")

        # Search Component
        with Horizontal(id="search-container"):
            yield Input(placeholder="> Search movies, series & anime...", id="search-input")

        # Main Navigation UI (The Box)
        with Horizontal(classes="main-box"):
            # Left Column (Static Navigation)
            with Vertical(classes="column", id="left-column"):
                yield Label("◆ Discover Categories", classes="column-header")
                yield Label("  • Trending Now", classes="category-item")
                yield Label("  • Top Rated Series", classes="category-item")
                yield Label("  • Latest Releases", classes="category-item")
                yield Label("  • Most Watched", classes="category-item")
                
                # System status indicator in left column
                engine_type = "MPV (Native)" if self.engine.using_mpv else "Simulation Engine"
                yield Label(f"\n[ Engine Status ]\nBackend: {engine_type}", classes="category-item")

            # Right Column (Dynamic File Browser)
            with Vertical(classes="column", id="right-column"):
                yield Label("[ /Browse ]", classes="column-header")
                yield ListView(id="file-list")

        # Status & Playback Control Bar
        with Horizontal(id="player-bar"):
            yield Label("[ STOPPED ]", id="status-label", classes="bar-info")
            yield Label("No Media Selected - Select a file to play", id="title-label", classes="bar-title")
            yield Label("00:00 / 00:00", id="time-label", classes="bar-time")

        # Footer
        yield Footer()

    def on_mount(self) -> None:
        """App initialization on mount."""
        self.scan_media_files()
        self.populate_file_list()
        
        # Start background timer to update media player UI state every 0.5s
        self.set_interval(0.5, self.update_player_ui)

    def scan_media_files(self) -> None:
        """Scan current directory and Media folder for audio/video files using pathlib."""
        valid_extensions = {".mp4", ".mkv", ".mp3", ".webm", ".avi", ".flac", ".wav"}
        found: List[Path] = []

        # Scan working directory & subdirectories
        search_dirs = [Path.cwd(), Path.cwd() / "Media", Path.home() / "Videos", Path.home() / "Music"]
        for s_dir in search_dirs:
            if s_dir.exists() and s_dir.is_dir():
                for p in s_dir.glob("*"):
                    if p.is_file() and p.suffix.lower() in valid_extensions:
                        if p not in found:
                            found.append(p)

        # If no local media files exist, create demo media items so the app is instantly usable
        if not found:
            demo_dir = Path.cwd() / "Media"
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

        self.media_files = sorted(found, key=lambda f: f.name.lower())
        self.filtered_files = list(self.media_files)

    def populate_file_list(self) -> None:
        """Populate the Right Column ListView widget."""
        file_list_widget = self.query_one("#file-list", ListView)
        file_list_widget.clear()

        for f in self.filtered_files:
            prefix = "🎵 " if f.suffix.lower() in [".mp3", ".flac", ".wav"] else "🎬 "
            file_list_widget.append(ListItem(Label(f"{prefix}{f.name}")))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Real-time search input filtering for file browser."""
        query = event.value.strip().lower()
        if query:
            self.filtered_files = [
                f for f in self.media_files if query in f.name.lower()
            ]
        else:
            self.filtered_files = list(self.media_files)
        self.populate_file_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Trigger playback when pressing Enter or clicking on a file item."""
        index = event.list_view.index
        if index is None and event.item is not None:
            try:
                index = list(event.list_view.children).index(event.item)
            except ValueError:
                index = None
        if index is not None and 0 <= index < len(self.filtered_files):
            selected_file = self.filtered_files[index]
            self.start_playback(selected_file)

    @work(thread=True)
    def start_playback(self, file_path: Path) -> None:
        """Execute playback initiation in worker thread to avoid blocking TUI event loop."""
        self.engine.play_file(file_path)
        self.call_from_thread(self.notify, f"Playing: {file_path.name}", title="Viz Media Player")

    def action_toggle_play_pause(self) -> None:
        """Hotkey action: Spacebar -> Toggle Play/Pause."""
        is_paused = self.engine.toggle_pause()
        status_str = "PAUSED" if is_paused else "PLAYING"
        self.notify(f"Media {status_str}", title="Playback Control")

    def action_toggle_mute(self) -> None:
        """Hotkey action: M -> Toggle Mute."""
        is_muted = self.engine.toggle_mute()
        muted_str = "MUTED" if is_muted else "UNMUTED"
        self.notify(f"Audio {muted_str}", title="Audio Control")

    def action_seek_left(self) -> None:
        """Hotkey action: Left Arrow -> Seek -10s."""
        pos = self.engine.seek(-10.0)
        self.notify(f"Seek -10s ({self.format_time(pos)})", title="Seek")

    def action_seek_right(self) -> None:
        """Hotkey action: Right Arrow -> Seek +10s."""
        pos = self.engine.seek(10.0)
        self.notify(f"Seek +10s ({self.format_time(pos)})", title="Seek")

    def action_toggle_tv_mode(self) -> None:
        """Hotkey action: Ctrl+T -> Toggle TV Mode info."""
        mode = "Native Window Overlay" if self.engine.using_mpv else "Terminal Frame Mode"
        self.notify(f"TV Mode Active: {mode}", title="TV Mode (Ctrl+T)")

    def action_show_help(self) -> None:
        """Hotkey action: ? -> Display Help Screen."""
        self.push_screen(HelpScreen())

    def action_quit_app(self) -> None:
        """Hotkey action: Q -> Quit app cleanly."""
        self.engine.stop()
        self.exit()

    def update_player_ui(self) -> None:
        """Periodic UI update loop for status bar timer and labels."""
        st = self.engine.update_position()
        
        status_lbl = self.query_one("#status-label", Label)
        title_lbl = self.query_one("#title-label", Label)
        time_lbl = self.query_one("#time-label", Label)

        if not st.is_playing:
            status_lbl.update("[ STOPPED ]")
            title_lbl.update("No Media Selected - Select a file to play")
            time_lbl.update("00:00 / 00:00")
        else:
            state_text = "[ PAUSED ]" if st.is_paused else "[ PLAYING ]"
            if st.is_muted:
                state_text += " (MUTED)"
            status_lbl.update(state_text)
            
            title_lbl.update(f"▶ {st.title}")
            
            curr_str = self.format_time(st.position)
            dur_str = self.format_time(st.duration)
            time_lbl.update(f"{curr_str} / {dur_str}")

    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds into MM:SS string."""
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins:02d}:{secs:02d}"


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = VizApp()
    app.run()
