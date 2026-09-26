"""
Main Textual Application for Viz Terminal Media Player.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.events import Key
from textual.widgets import Footer, Input, Label, ListItem, ListView

from viz.config import ConfigManager
from viz.constants import APP_TITLE, COLOR_PRIMARY_ORANGE
from viz.engine import MediaEngine
from viz.history import HistoryManager
from viz.models import MediaItem, MediaType, PlaybackState, PlaybackStatus
from viz.scanner import MediaScanner
from viz.screens.help import HelpScreen
from viz.widgets.categories import CategoriesWidget
from viz.widgets.header import HeaderWidget
from viz.widgets.media_list import MediaListWidget
from viz.widgets.player_status import PlayerStatusWidget
from viz.widgets.search import SearchWidget


class VizApp(App):
    """
    Viz - Terminal Media Player Application.
    """

    CSS_PATH = "styles/app.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("enter", "select_media", "Play", show=False),
        Binding("space", "toggle_play_pause", "Play/Pause", show=False),
        Binding("m", "toggle_mute", "Mute", show=False),
        Binding("up", "volume_up", "Vol +", show=False),
        Binding("down", "volume_down", "Vol -", show=False),
        Binding("left", "seek_left", "Seek -10s", show=False),
        Binding("right", "seek_right", "Seek +10s", show=False),
        Binding("shift+left", "seek_left_large", "Seek -60s", show=False),
        Binding("shift+right", "seek_right_large", "Seek +60s", show=False),
        Binding("f", "toggle_fullscreen", "Fullscreen", show=False),
        Binding("ctrl+t", "toggle_tv_mode", "TV MODE", show=True),
        Binding("slash", "focus_search", "SEARCH", show=True),
        Binding("r", "refresh_library", "Refresh", show=False),
        Binding("question_mark", "show_help", "HELP", show=True),
        Binding("q", "quit_app", "QUIT", show=True),
        Binding("escape", "dismiss_action", "Dismiss", show=False),
    ]

    def __init__(self, media_path_override: Optional[Path | str] = None) -> None:
        super().__init__()
        self.title = APP_TITLE
        
        # Core Architecture Modules
        self.config = ConfigManager()
        if media_path_override:
            self.config.media_path = Path(media_path_override)

        self.history = HistoryManager()
        self.scanner = MediaScanner()
        self.engine = MediaEngine(
            initial_volume=self.config.volume,
            initial_muted=self.config.muted,
        )

        # Application State
        self.all_media_items: List[MediaItem] = []
        self.filtered_media_items: List[MediaItem] = []
        self.active_category: str = "all"
        self.active_search_query: str = ""
        self.is_scanning: bool = False
        self.current_selected_media: Optional[MediaItem] = None

    def compose(self) -> ComposeResult:
        yield HeaderWidget()
        yield SearchWidget()

        with Horizontal(classes="main-box"):
            yield CategoriesWidget()
            yield MediaListWidget()

        yield PlayerStatusWidget()
        yield Footer()

    def on_mount(self) -> None:
        """Initialize and trigger background scanner."""
        self.title = f"Viz - {self.config.media_path.name}"
        self.engine.on_state_change_callback = self.on_engine_state_changed
        self.refresh_library()

        # Update loop for time progress & auto history saving
        self.set_interval(0.5, self.sync_playback_loop)

    @work(thread=True)
    def refresh_library(self) -> None:
        """Run media directory scanner in background thread."""
        self.is_scanning = True
        self.call_from_thread(self.update_media_list_ui)

        target_dir = self.config.media_path
        discovered = self.scanner.scan_directory(target_dir)

        self.all_media_items = discovered
        self.is_scanning = False
        self.call_from_thread(self.filter_and_update_library)

    def filter_and_update_library(self) -> None:
        """Filter media items based on active category & search query."""
        items = list(self.all_media_items)

        # Apply category filter
        if self.active_category == "video":
            items = [m for m in items if m.media_type == MediaType.VIDEO]
        elif self.active_category == "audio":
            items = [m for m in items if m.media_type == MediaType.AUDIO]
        elif self.active_category == "latest":
            items = sorted(items, key=lambda m: m.modified_time, reverse=True)
        elif self.active_category == "watched":
            history_entries = self.history.get_recent_history()
            watched_paths = {e["path"] for e in history_entries}
            items = [m for m in items if str(m.path.resolve()) in watched_paths]

        # Apply search query filter
        if self.active_search_query:
            query = self.active_search_query.lower()
            items = [
                m for m in items if query in m.name.lower() or query in str(m.path).lower()
            ]

        self.filtered_media_items = items
        self.update_media_list_ui()

    def update_media_list_ui(self) -> None:
        """Update MediaListWidget view."""
        try:
            media_widget = self.query_one(MediaListWidget)
            media_widget.update_list(
                media_items=self.filtered_media_items,
                active_search_query=self.active_search_query,
                is_scanning=self.is_scanning,
                media_path_display=str(self.config.media_path),
            )
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle real-time search input typing."""
        self.active_search_query = event.value.strip()
        self.filter_and_update_library()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list selection for category or media file list."""
        if event.list_view.id == "category-list":
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(CategoriesWidget.CATEGORY_DEFS):
                cat_id = CategoriesWidget.CATEGORY_DEFS[idx][0]
                self.active_category = cat_id
                self.filter_and_update_library()
        elif event.list_view.id == "media-list":
            idx = event.list_view.index
            if idx is None and event.item is not None:
                try:
                    idx = list(event.list_view.children).index(event.item)
                except ValueError:
                    idx = None

            if idx is not None and 0 <= idx < len(self.filtered_media_items):
                target_media = self.filtered_media_items[idx]
                self.play_media_item(target_media)

    def play_media_item(self, media_item: MediaItem) -> None:
        """Play media item with automatic position resume logic."""
        resume_pos = self.history.get_resume_position(media_item.path)
        if resume_pos > 0.0:
            formatted_time = PlayerStatusWidget.format_time(resume_pos)
            self.notify(f"Resuming at {formatted_time}", title="Resume Playback")

        success = self.engine.play(media_item, start_position=resume_pos)
        if success:
            self.current_selected_media = media_item
            self.notify(f"Playing: {media_item.name}", title="Viz Engine")
        else:
            err = self.engine.state.error_message or "Could not open file"
            self.notify(err, title="Playback Error", severity="error")

    def on_engine_state_changed(self, state: PlaybackState) -> None:
        """Callback from MediaEngine when playback state changes."""
        try:
            status_widget = self.query_one(PlayerStatusWidget)
            status_widget.update_state(state)
        except Exception:
            pass

    def sync_playback_loop(self) -> None:
        """Periodic sync loop to save position and update status bar."""
        st = self.engine.state
        if st.status == PlaybackStatus.PLAYING and st.current_media:
            # Periodically save position to history
            if st.position > 5.0:
                self.history.update_position(
                    st.current_media.path, st.position, st.duration
                )

        try:
            status_widget = self.query_one(PlayerStatusWidget)
            status_widget.update_state(st)
        except Exception:
            pass

    # Keybinding Handlers
    def action_toggle_play_pause(self) -> None:
        is_paused = self.engine.toggle_pause()
        self.notify("PAUSED" if is_paused else "PLAYING", title="Playback")

    def action_toggle_mute(self) -> None:
        is_muted = self.engine.toggle_mute()
        self.config.muted = is_muted
        self.notify("MUTED" if is_muted else "UNMUTED", title="Audio")

    def action_volume_up(self) -> None:
        new_vol = self.engine.change_volume(5)
        self.config.volume = new_vol
        self.notify(f"Volume: {new_vol}%", title="Volume")

    def action_volume_down(self) -> None:
        new_vol = self.engine.change_volume(-5)
        self.config.volume = new_vol
        self.notify(f"Volume: {new_vol}%", title="Volume")

    def action_seek_left(self) -> None:
        pos = self.engine.seek(-10.0)
        self.notify("-10s", title="Seek")

    def action_seek_right(self) -> None:
        pos = self.engine.seek(10.0)
        self.notify("+10s", title="Seek")

    def action_seek_left_large(self) -> None:
        pos = self.engine.seek(-60.0)
        self.notify("-60s", title="Seek")

    def action_seek_right_large(self) -> None:
        pos = self.engine.seek(60.0)
        self.notify("+60s", title="Seek")

    def action_toggle_fullscreen(self) -> None:
        self.notify("Fullscreen toggled", title="Window")

    def action_toggle_tv_mode(self) -> None:
        self.notify("TV Mode: Native Window Active", title="TV Mode (Ctrl+T)")

    def action_focus_search(self) -> None:
        search_w = self.query_one(SearchWidget)
        search_w.focus_input()

    def action_refresh_library(self) -> None:
        self.notify("Rescanning media directory...", title="Refresh")
        self.refresh_library()

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_dismiss_action(self) -> None:
        if self.screen.__class__.__name__ == "HelpScreen":
            self.pop_screen()
        else:
            search_w = self.query_one(SearchWidget)
            search_w.clear_input()
            self.set_focus(None)

    def action_quit_app(self) -> None:
        """Clean shutdown saving state and terminating MPV engine."""
        st = self.engine.state
        if st.current_media and st.position > 0:
            self.history.update_position(
                st.current_media.path, st.position, st.duration
            )

        self.config.save()
        self.history.save()
        self.engine.stop()
        self.engine.terminate()
        self.exit()
