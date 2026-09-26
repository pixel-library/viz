"""
Main Textual Application for Viz Terminal Media Center.
Coordinates Library, Queue, Engine, Configuration, History, Views, and Contextual Keybindings.
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
from viz.constants import APP_TITLE
from viz.engine import MediaEngine
from viz.history import HistoryManager
from viz.library import LibraryManager
from viz.models import LoopMode, MediaItem, MediaType, PlaybackState, PlaybackStatus
from viz.queue import PlaybackQueue
from viz.scanner import MediaScanner
from viz.screens.help import HelpScreen
from viz.screens.info import InfoScreen
from viz.series import SeriesEpisode, SeriesGroup
from viz.widgets.footer import ContextualFooter
from viz.widgets.header import HeaderWidget
from viz.widgets.media_list import MediaListWidget
from viz.widgets.player_status import PlayerStatusWidget
from viz.widgets.search import SearchWidget
from viz.widgets.sidebar import SidebarWidget


class VizApp(App):
    """
    Viz - Terminal Media Center Application.
    """

    CSS_PATH = "styles/app.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("enter", "select_action", "Play / Select", show=False),
        Binding("space", "toggle_play_pause", "Play/Pause", show=False),
        Binding("m", "toggle_mute", "Mute", show=False),
        Binding("up", "volume_up", "Vol +", show=False),
        Binding("down", "volume_down", "Vol -", show=False),
        Binding("left", "seek_left", "Seek -10s", show=False),
        Binding("right", "seek_right", "Seek +10s", show=False),
        Binding("shift+left", "seek_left_large", "Seek -60s", show=False),
        Binding("shift+right", "seek_right_large", "Seek +60s", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("b", "prev_track", "Previous", show=False),
        Binding("z", "toggle_shuffle", "Shuffle", show=False),
        Binding("l", "cycle_loop", "Loop", show=False),
        Binding("f", "action_favorite_or_fullscreen", "Favorite / Fullscreen", show=False),
        Binding("a", "cycle_audio_stream", "Audio Stream", show=False),
        Binding("s", "cycle_subtitle_stream", "Subtitles", show=False),
        Binding("i", "show_media_info", "Info", show=False),
        Binding("ctrl+t", "toggle_tv_mode", "TV MODE", show=True),
        Binding("slash", "focus_search", "SEARCH", show=True),
        Binding("r", "refresh_library", "Refresh", show=False),
        Binding("question_mark", "show_help", "HELP", show=True),
        Binding("q", "quit_app", "QUIT", show=True),
        Binding("escape", "dismiss_action", "Dismiss", show=False),
        # Queue actions
        Binding("d", "remove_from_queue", "Remove", show=False),
        Binding("c", "clear_queue", "Clear Queue", show=False),
    ]

    def __init__(self, media_path_override: Optional[Path | str] = None) -> None:
        super().__init__()
        self.title = APP_TITLE

        # Core Manager Layer
        self.config = ConfigManager()
        if media_path_override:
            self.config.media_path = Path(media_path_override)

        self.history = HistoryManager()
        self.library = LibraryManager(history=self.history)
        self.queue = PlaybackQueue()
        self.scanner = MediaScanner()
        self.engine = MediaEngine(
            initial_volume=self.config.volume,
            initial_muted=self.config.muted,
        )

        # Application State
        self.active_category: str = "all"
        self.active_search_query: str = ""
        self.is_scanning: bool = False
        self.selected_series_name: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield HeaderWidget()
        yield SearchWidget()

        with Horizontal(classes="main-box"):
            yield SidebarWidget()
            yield MediaListWidget()

        yield PlayerStatusWidget()
        yield ContextualFooter()

    def on_mount(self) -> None:
        """Initialize widgets and scan library."""
        self.title = f"Viz - {self.config.media_path.name}"
        self.engine.on_state_change_callback = self.on_engine_state_changed
        self.refresh_library()

        # Update loop for timer & playback position saving
        self.set_interval(0.5, self.sync_playback_loop)

    @work(thread=True)
    def refresh_library(self) -> None:
        """Background thread scan of configured media directory."""
        self.is_scanning = True
        self.call_from_thread(self.update_ui_views)

        target_dir = self.config.media_path
        discovered = self.scanner.scan_directory(target_dir)

        self.library.set_items(discovered)
        self.is_scanning = False
        self.call_from_thread(self.update_ui_views)

    def update_ui_views(self) -> None:
        """Update Sidebar counts and Right Column view based on active category."""
        sidebar = self.query_one(SidebarWidget)
        sidebar.update_counts(self.library, queue_count=len(self.queue.up_next))

        footer = self.query_one(ContextualFooter)
        footer.set_mode_hint(self.active_category)

        media_list = self.query_one(MediaListWidget)

        if self.is_scanning:
            media_list.update_list(
                media_items=[],
                is_scanning=True,
                media_path_display=str(self.config.media_path),
            )
            return

        if self.active_search_query:
            query = self.active_search_query.lower()
            matching = [
                m for m in self.library.all_items
                if query in m.name.lower() or query in (m.title or "").lower() or query in (m.artist or "").lower()
            ]
            media_list.render_all_media(matching, query=self.active_search_query)
            return

        if self.active_category == "all":
            media_list.render_all_media(self.library.all_items)

        elif self.active_category == "movies":
            media_list.render_movies(self.library.movies)

        elif self.active_category == "series":
            if self.selected_series_name and self.selected_series_name in self.library.series_groups:
                group = self.library.series_groups[self.selected_series_name]
                all_eps = []
                for season in group.seasons.values():
                    all_eps.extend(season)
                media_list.render_episodes(self.selected_series_name, all_eps)
            else:
                media_list.render_series(self.library.series_groups)

        elif self.active_category == "music":
            media_list.render_music(self.library.music)

        elif self.active_category == "continue":
            media_list.render_continue_watching(self.library.get_continue_watching())

        elif self.active_category == "recent":
            media_list.render_all_media(self.library.get_recently_played())

        elif self.active_category == "favorites":
            media_list.render_all_media(self.library.get_favorites())

        elif self.active_category == "completed":
            media_list.render_all_media(self.library.get_completed())

        elif self.active_category == "queue":
            media_list.render_queue(self.queue.current_item, self.queue.up_next)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle real-time search typing."""
        self.active_search_query = event.value.strip()
        self.update_ui_views()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list row selection."""
        if event.list_view.id == "category-list":
            item_id = (event.item.id or "") if event.item else ""
            if item_id.startswith("cat-"):
                cat_id = item_id.replace("cat-", "")
                if cat_id == "refresh":
                    self.action_refresh_library()
                elif cat_id == "help":
                    self.action_show_help()
                else:
                    self.active_category = cat_id
                    self.selected_series_name = None
                    self.update_ui_views()

        elif event.list_view.id == "media-list":
            self.action_select_action()

    def get_item_at_index(self, idx: int) -> Optional[MediaItem]:
        """Resolve currently selected MediaItem from UI ListView index."""
        if idx is None or idx < 0:
            return None

        if self.active_search_query:
            query = self.active_search_query.lower()
            matching = [
                m for m in self.library.all_items
                if query in m.name.lower() or query in (m.title or "").lower() or query in (m.artist or "").lower()
            ]
            if 0 <= idx < len(matching):
                return matching[idx]
            return None

        if self.active_category == "all":
            if 0 <= idx < len(self.library.all_items):
                return self.library.all_items[idx]

        elif self.active_category == "movies":
            if 0 <= idx < len(self.library.movies):
                return self.library.movies[idx]

        elif self.active_category == "series" and self.selected_series_name:
            group = self.library.series_groups.get(self.selected_series_name)
            if group:
                all_eps = []
                for season in group.seasons.values():
                    all_eps.extend(season)
                if 0 <= idx < len(all_eps):
                    return all_eps[idx].media_item

        elif self.active_category == "music":
            if 0 <= idx < len(self.library.music):
                return self.library.music[idx]

        elif self.active_category == "continue":
            cont_items = self.library.get_continue_watching()
            if 0 <= idx < len(cont_items):
                return cont_items[idx]

        elif self.active_category in ("recent", "favorites", "completed"):
            items = (
                self.library.get_recently_played()
                if self.active_category == "recent"
                else (self.library.get_favorites() if self.active_category == "favorites" else self.library.get_completed())
            )
            if 0 <= idx < len(items):
                return items[idx]

        elif self.active_category == "queue":
            if idx == 0 and self.queue.current_item:
                return self.queue.current_item
            elif self.queue.up_next:
                q_idx = idx - (2 if self.queue.current_item else 1)
                if 0 <= q_idx < len(self.queue.up_next):
                    return self.queue.up_next[q_idx]

        return None

    def action_select_action(self) -> None:
        """Handle Enter key action based on current view."""
        media_list = self.query_one(MediaListWidget)
        idx = media_list.get_selected_index()
        if idx is None:
            return

        if self.active_category == "series" and not self.selected_series_name:
            series_names = list(self.library.series_groups.keys())
            if 0 <= idx < len(series_names):
                self.selected_series_name = series_names[idx]
                self.update_ui_views()
            return

        target_item = self.get_item_at_index(idx)
        if target_item:
            self.play_media_item(target_item)

    def play_media_item(self, item: MediaItem) -> None:
        """Play target MediaItem with resume position checking."""
        resume_pos = self.history.get_resume_position(item.path)
        if resume_pos > 0.0:
            formatted_time = PlayerStatusWidget.format_time(resume_pos)
            self.notify(f"Resuming at {formatted_time}", title="Resume Playback")

        self.queue.set_current(item)
        success = self.engine.play(item, start_position=resume_pos)
        if success:
            self.notify(f"Playing: {item.name}", title="Viz Media Engine")
        else:
            err = self.engine.state.error_message or "Playback failed"
            self.notify(err, title="Playback Error", severity="error")

    def on_engine_state_changed(self, state: PlaybackState) -> None:
        """Engine observer callback when playback state changes."""
        try:
            status_widget = self.query_one(PlayerStatusWidget)
            status_widget.update_state(state)

            if state.status == PlaybackStatus.ENDED:
                next_item = self.queue.get_next()
                if next_item:
                    self.play_media_item(next_item)
        except Exception:
            pass

    def sync_playback_loop(self) -> None:
        """Timer loop saving position and syncing UI."""
        st = self.engine.state
        if st.status == PlaybackStatus.PLAYING and st.current_media:
            if st.position > 5.0:
                self.history.update_position(st.current_media.path, st.position, st.duration)

        try:
            status_widget = self.query_one(PlayerStatusWidget)
            status_widget.update_state(st)
        except Exception:
            pass

    # Playback Control Actions
    def action_toggle_play_pause(self) -> None:
        is_paused = self.engine.toggle_pause()
        self.notify("PAUSED" if is_paused else "PLAYING", title="Playback")

    def action_toggle_mute(self) -> None:
        is_muted = self.engine.toggle_mute()
        self.config.muted = is_muted
        self.notify("MUTED" if is_muted else "UNMUTED", title="Audio")

    def action_volume_up(self) -> None:
        vol = self.engine.change_volume(5)
        self.config.volume = vol
        self.notify(f"Volume: {vol}%", title="Volume")

    def action_volume_down(self) -> None:
        vol = self.engine.change_volume(-5)
        self.config.volume = vol
        self.notify(f"Volume: {vol}%", title="Volume")

    def action_seek_left(self) -> None:
        self.engine.seek(-10.0)
        self.notify("-10s", title="Seek")

    def action_seek_right(self) -> None:
        self.engine.seek(10.0)
        self.notify("+10s", title="Seek")

    def action_seek_left_large(self) -> None:
        self.engine.seek(-60.0)
        self.notify("-60s", title="Seek")

    def action_seek_right_large(self) -> None:
        self.engine.seek(60.0)
        self.notify("+60s", title="Seek")

    def action_next_track(self) -> None:
        next_item = self.queue.get_next()
        if next_item:
            self.play_media_item(next_item)
            self.notify(f"Next: {next_item.name}", title="Queue")

    def action_prev_track(self) -> None:
        prev_item = self.queue.get_previous()
        if prev_item:
            self.play_media_item(prev_item)
            self.notify(f"Previous: {prev_item.name}", title="Queue")

    def action_toggle_shuffle(self) -> None:
        shuffled = self.queue.toggle_shuffle()
        self.notify("Shuffle On" if shuffled else "Shuffle Off", title="Playback")

    def action_cycle_loop(self) -> None:
        mode = self.queue.cycle_loop()
        self.notify(f"Loop Mode: {mode.value}", title="Playback")

    def action_favorite_or_fullscreen(self) -> None:
        media_list = self.query_one(MediaListWidget)
        idx = media_list.get_selected_index()
        item = self.get_item_at_index(idx) if idx is not None else None
        if item:
            is_fav = self.library.toggle_favorite(item)
            self.notify("★ Added to Favorites" if is_fav else "Removed from Favorites", title="Favorites")
            self.update_ui_views()
        else:
            self.notify("Fullscreen toggled", title="Window")

    def action_cycle_audio_stream(self) -> None:
        self.notify("Cycle Audio Stream", title="Audio")

    def action_cycle_subtitle_stream(self) -> None:
        self.notify("Cycle Subtitle Stream", title="Subtitles")

    def action_show_media_info(self) -> None:
        media_list = self.query_one(MediaListWidget)
        idx = media_list.get_selected_index()
        target_item = self.get_item_at_index(idx) if idx is not None else None
        if not target_item and self.engine.state.current_media:
            target_item = self.engine.state.current_media

        if target_item:
            self.push_screen(InfoScreen(target_item))

    def action_remove_from_queue(self) -> None:
        if self.active_category == "queue":
            media_list = self.query_one(MediaListWidget)
            idx = media_list.get_selected_index()
            if idx is not None:
                q_idx = idx - (2 if self.queue.current_item else 1)
                if self.queue.remove(q_idx):
                    self.notify("Removed from queue", title="Queue")
                    self.update_ui_views()

    def action_clear_queue(self) -> None:
        if self.active_category == "queue":
            self.queue.clear()
            self.notify("Queue cleared", title="Queue")
            self.update_ui_views()

    def action_focus_search(self) -> None:
        search_w = self.query_one(SearchWidget)
        search_w.focus_input()
        footer = self.query_one(ContextualFooter)
        footer.set_mode_hint("search")

    def action_refresh_library(self) -> None:
        self.notify("Rescanning media directory...", title="Refresh")
        self.refresh_library()

    def action_toggle_tv_mode(self) -> None:
        self.notify("TV Mode Active", title="TV Mode (Ctrl+T)")

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_dismiss_action(self) -> None:
        if self.screen.__class__.__name__ in ("HelpScreen", "InfoScreen"):
            self.pop_screen()
        elif self.selected_series_name:
            self.selected_series_name = None
            self.update_ui_views()
        elif self.active_search_query:
            search_w = self.query_one(SearchWidget)
            search_w.clear_input()
            self.active_search_query = ""
            self.update_ui_views()
            self.set_focus(None)
        else:
            self.set_focus(None)

    def action_quit_app(self) -> None:
        st = self.engine.state
        if st.current_media and st.position > 0:
            self.history.update_position(st.current_media.path, st.position, st.duration)

        self.config.save()
        self.history.save()
        self.library.save_favorites()
        self.engine.stop()
        self.engine.terminate()
        self.exit()
