"""
Main Textual Application for Viz Terminal Media Center.
Coordinates Real Filesystem Tree, Library, Queue, Engine, Configuration, History, Views, and Contextual Keybindings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.events import Key
from textual.widgets import Footer, Input, Label, ListItem, ListView, Tree

from viz.config import ConfigManager
from viz.constants import APP_TITLE
from viz.engine import MediaEngine
from viz.folder_tree import FolderNode
from viz.history import HistoryManager
from viz.library import LibraryManager
from viz.models import LoopMode, MediaItem, MediaType, PlaybackState, PlaybackStatus
from viz.queue import PlaybackQueue
from viz.scanner import MediaScanner
from viz.screens.help import HelpScreen
from viz.screens.image_viewer import ImageViewerScreen
from viz.screens.info import InfoScreen
from viz.screens.library_paths import LibraryPathsScreen
from viz.series import SeriesEpisode, SeriesGroup
from viz.terminal import TerminalManager
from viz.widgets.details import DetailsWidget
from viz.widgets.footer import ContextualFooter
from viz.widgets.header import HeaderWidget
from viz.widgets.media_list import MediaListWidget
from viz.widgets.player_status import PlayerStatusWidget
from viz.widgets.search import SearchWidget
from viz.widgets.sidebar import SidebarWidget


class VizApp(App):
    """
    Viz - Professional Offline Terminal Media Center.
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
        Binding("p", "action_manage_paths", "PATHS", show=True),
        Binding("1", "filter_all", "Filter All", show=False),
        Binding("2", "filter_videos", "Filter Videos", show=False),
        Binding("3", "filter_audio", "Filter Audio", show=False),
        Binding("4", "filter_images", "Filter Images", show=False),
        Binding("ctrl+t", "toggle_tv_mode", "TV MODE", show=True),
        Binding("slash", "focus_search", "SEARCH", show=True),
        Binding("r", "refresh_library", "Refresh", show=False),
        Binding("question_mark", "show_help", "HELP", show=True),
        Binding("q", "quit_app", "QUIT", show=True),
        Binding("escape", "dismiss_action", "Dismiss", show=False),
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
        self.selected_folder: Optional[FolderNode] = None
        self.folder_filter: str = "ALL"

    def compose(self) -> ComposeResult:
        yield HeaderWidget()
        yield SearchWidget()

        with Horizontal(classes="main-box"):
            yield SidebarWidget()
            yield MediaListWidget()
            yield DetailsWidget()

        yield PlayerStatusWidget()
        yield ContextualFooter()

    def on_mount(self) -> None:
        """Initialize widgets, hide text cursor, and scan library."""
        TerminalManager.setup_terminal()
        self.title = f"Viz - {self.config.media_path.name}"
        self.engine.on_state_change_callback = self.on_engine_state_changed
        self.refresh_library()

        # Timer loop for state sync
        self.set_interval(0.5, self.sync_playback_loop)

    def on_resize(self, event) -> None:
        """Handle terminal resize to dynamically toggle Details panel for responsiveness."""
        try:
            details = self.query_one(DetailsWidget)
            if event.size.width < 120:
                details.display = False
            else:
                details.display = True
        except Exception:
            pass

    @work(thread=True)
    def refresh_library(self) -> None:
        """Background thread scan of all configured library directories."""
        self.is_scanning = True
        self.call_from_thread(self.update_ui_views)

        target_paths = self.config.get_library_paths()
        discovered = self.scanner.scan_directories(
            target_paths,
            show_hidden=self.config.show_hidden_files,
        )

        self.library.set_items_and_roots(discovered, target_paths)
        self.is_scanning = False
        self.call_from_thread(self.update_ui_views)

        # Show initial discovery summary on first run
        if not self.config.get("first_run_completed", False):
            self.config.set("first_run_completed", True)
            from viz.screens.discovery import DiscoveryScreen
            self.call_from_thread(self.push_screen, DiscoveryScreen(self.library, target_paths))

    def update_ui_views(self) -> None:
        """Update Sidebar Tree, counts, Middle Column view, and Details Panel."""
        try:
            sidebar = self.query_one(SidebarWidget)
            sidebar.update_tree_and_counts(self.library, queue_count=len(self.queue.up_next))

            footer = self.query_one(ContextualFooter)
            footer.set_mode_hint(self.active_category if not self.selected_folder else "folder")

            media_list = self.query_one(MediaListWidget)
            details = self.query_one(DetailsWidget)

            if self.is_scanning:
                media_list.render_scanning()
                details.show_empty("Scanning library directories...")
                return

            if self.active_search_query:
                query = self.active_search_query.lower()
                matching = [
                    m for m in self.library.all_items
                    if query in m.name.lower() or query in (m.title or "").lower() or query in (m.artist or "").lower()
                ]
                media_list.render_all_media(matching, query=self.active_search_query)
                details.show_empty(f"Search: '{self.active_search_query}' ({len(matching)} matches)")
                return

            if self.selected_folder:
                media_list.render_folder(self.selected_folder, active_filter=self.folder_filter)
                details.show_folder(self.selected_folder)

            elif self.active_category == "all":
                media_list.render_all_media(self.library.all_items)
                details.show_empty(f"ALL MEDIA ({len(self.library.all_items)} items)")

            elif self.active_category == "videos":
                media_list.render_videos(self.library.videos)
                details.show_empty(f"VIDEOS ({len(self.library.videos)} items)")

            elif self.active_category == "movies":
                media_list.render_movies(self.library.movies)
                details.show_empty(f"MOVIES ({len(self.library.movies)} items)")

            elif self.active_category == "series":
                if self.selected_series_name and self.selected_series_name in self.library.series_groups:
                    group = self.library.series_groups[self.selected_series_name]
                    all_eps = []
                    for season in group.seasons.values():
                        all_eps.extend(season)
                    media_list.render_episodes(self.selected_series_name, all_eps)
                    details.show_empty(f"SERIES: {self.selected_series_name}")
                else:
                    media_list.render_series(self.library.series_groups)
                    details.show_empty(f"SERIES ({len(self.library.series_groups)} shows)")

            elif self.active_category == "music":
                media_list.render_music(self.library.music)
                details.show_empty(f"MUSIC ({len(self.library.music)} tracks)")

            elif self.active_category == "images":
                media_list.render_images(self.library.images)
                details.show_empty(f"IMAGES ({len(self.library.images)} photos)")

            elif self.active_category == "continue":
                media_list.render_continue_watching(self.library.get_continue_watching())
                details.show_empty("CONTINUE WATCHING")

            elif self.active_category == "recent":
                media_list.render_all_media(self.library.get_recently_played())
                details.show_empty("RECENTLY PLAYED")

            elif self.active_category == "favorites":
                media_list.render_all_media(self.library.get_favorites())
                details.show_empty("FAVORITES")

            elif self.active_category == "completed":
                media_list.render_all_media(self.library.get_completed())
                details.show_empty("COMPLETED")

            elif self.active_category == "queue":
                media_list.render_queue(self.queue.current_item, self.queue.up_next)
                details.show_empty("PLAYBACK QUEUE")
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle selection of folder node in Filesystem Tree."""
        data = event.node.data
        if data and data.get("type") == "folder":
            self.selected_folder = data["folder"]
            self.active_category = "folder"
            self.update_ui_views()

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Real-time details update when navigating tree nodes."""
        data = event.node.data
        if data and data.get("type") == "folder":
            try:
                details = self.query_one(DetailsWidget)
                details.show_folder(data["folder"])
            except Exception:
                pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle real-time search typing."""
        self.active_search_query = event.value.strip()
        self.selected_folder = None
        self.update_ui_views()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection in Global Views list or System list."""
        if event.list_view.id == "global-views-list":
            item_id = (event.item.id or "") if event.item else ""
            if item_id.startswith("cat-"):
                self.active_category = item_id.replace("cat-", "")
                self.selected_folder = None
                self.selected_series_name = None
                self.update_ui_views()

        elif event.list_view.id == "system-list":
            item_id = (event.item.id or "") if event.item else ""
            if item_id == "sys-paths":
                self.action_manage_paths()
            elif item_id == "sys-refresh":
                self.action_refresh_library()
            elif item_id == "sys-help":
                self.action_show_help()

        elif event.list_view.id == "media-list":
            self.action_select_action()

    def get_item_at_index(self, idx: int) -> Optional[MediaItem]:
        """Resolve currently selected MediaItem from UI ListView index."""
        if idx is None or idx < 0:
            return None

        if self.selected_folder:
            filtered = self.selected_folder.media_files
            if self.folder_filter == "VIDEOS":
                filtered = [m for m in self.selected_folder.media_files if m.media_type == MediaType.VIDEO]
            elif self.folder_filter == "AUDIO":
                filtered = [m for m in self.selected_folder.media_files if m.media_type == MediaType.AUDIO]
            elif self.folder_filter == "IMAGES":
                filtered = [m for m in self.selected_folder.media_files if m.media_type == MediaType.IMAGE]

            offset = len(self.selected_folder.subfolders)
            file_idx = idx - offset
            if 0 <= file_idx < len(filtered):
                return filtered[file_idx]
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

        elif self.active_category == "videos":
            if 0 <= idx < len(self.library.videos):
                return self.library.videos[idx]

        elif self.active_category == "movies":
            if 0 <= idx < len(self.library.movies):
                return self.library.movies[idx]

        elif self.active_category == "images":
            if 0 <= idx < len(self.library.images):
                return self.library.images[idx]

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

        # Subfolder selection in Folder view
        if self.selected_folder:
            if 0 <= idx < len(self.selected_folder.subfolders):
                self.selected_folder = self.selected_folder.subfolders[idx]
                self.update_ui_views()
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
        """Play target MediaItem or launch Image Viewer."""
        if item.media_type == MediaType.IMAGE:
            folder_imgs = [m for m in (self.selected_folder.media_files if self.selected_folder else self.library.images) if m.media_type == MediaType.IMAGE]
            self.push_screen(ImageViewerScreen(item, folder_imgs))
            return

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

    def action_manage_paths(self) -> None:
        self.push_screen(LibraryPathsScreen(self.config))

    def action_filter_all(self) -> None:
        self.folder_filter = "ALL"
        self.update_ui_views()
        self.notify("Filter: ALL", title="Folder View")

    def action_filter_videos(self) -> None:
        self.folder_filter = "VIDEOS"
        self.update_ui_views()
        self.notify("Filter: VIDEOS", title="Folder View")

    def action_filter_audio(self) -> None:
        self.folder_filter = "AUDIO"
        self.update_ui_views()
        self.notify("Filter: AUDIO", title="Folder View")

    def action_filter_images(self) -> None:
        self.folder_filter = "IMAGES"
        self.update_ui_views()
        self.notify("Filter: IMAGES", title="Folder View")

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
        self.notify("Rescanning library directories...", title="Refresh")
        self.refresh_library()

    def action_toggle_tv_mode(self) -> None:
        self.notify("TV Mode Active", title="TV Mode (Ctrl+T)")

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_dismiss_action(self) -> None:
        if self.screen.__class__.__name__ in ("HelpScreen", "InfoScreen", "ImageViewerScreen", "LibraryPathsScreen", "DirectorySelectorModal"):
            self.pop_screen()
        elif self.selected_folder:
            if self.selected_folder.parent:
                self.selected_folder = self.selected_folder.parent
            else:
                self.selected_folder = None
                self.active_category = "all"
            self.update_ui_views()
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
        TerminalManager.restore_terminal()
        st = self.engine.state
        if st.current_media and st.position > 0:
            self.history.update_position(st.current_media.path, st.position, st.duration)

        self.config.save()
        self.history.save()
        self.library.save_favorites()
        self.engine.stop()
        self.engine.terminate()
        self.exit()
