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
from viz.media_router import MediaRouter
from viz.models import LoopMode, MediaItem, MediaType, PlaybackState, PlaybackStatus
from viz.mounts import MountsManager
from viz.queue import PlaybackQueue
from viz.scanner import MediaScanner
from viz.screens.help import HelpScreen
from viz.screens.image_viewer import ImageViewerScreen
from viz.screens.video_player import VideoPlayerScreen
from viz.screens.audio_player import AudioPlayerScreen
from viz.screens.info import InfoScreen
from viz.screens.library_paths import LibraryPathsScreen
from viz.terminal import TerminalManager
from viz.widgets.details import DetailsWidget
from viz.widgets.footer import ContextualFooter
from viz.widgets.header import HeaderWidget
from viz.widgets.media_list import FolderListItem, MediaListItem, MediaListWidget
from viz.widgets.player_status import PlayerStatusWidget
from viz.widgets.sidebar import SidebarWidget


class VizApp(App):
    """
    Viz - Professional Offline Terminal Media Center.
    """

    CSS_PATH = "styles/app.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("enter", "select_action", "Play / Open", show=False),
        Binding("space", "toggle_play_pause", "Play/Pause", show=False),
        Binding("m", "toggle_mute", "Mute", show=False),
        Binding("up", "volume_up", "Vol +", show=False),
        Binding("down", "volume_down", "Vol -", show=False),
        Binding("left", "dismiss_action", "Parent Folder / Back", show=False),
        Binding("right", "select_action", "Open Folder", show=False),
        Binding("shift+left", "seek_left_large", "Seek -60s", show=False),
        Binding("shift+right", "seek_right_large", "Seek +60s", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("b", "prev_track", "Previous", show=False),
        Binding("z", "toggle_shuffle", "Shuffle", show=False),
        Binding("l", "cycle_loop", "Loop", show=False),
        Binding("f", "action_favorite_or_fullscreen", "Favorite", show=False),
        Binding("a", "cycle_audio_stream", "Audio Stream", show=False),
        Binding("s", "cycle_subtitle_stream", "Subtitles", show=False),
        Binding("i", "show_media_info", "Info", show=False),
        Binding("p", "action_manage_paths", "PATHS", show=True),
        Binding("1", "filter_all", "Filter All", show=False),
        Binding("2", "filter_videos", "Filter Videos", show=False),
        Binding("3", "filter_audio", "Filter Audio", show=False),
        Binding("4", "filter_images", "Filter Images", show=False),
        Binding("r", "refresh_library", "Refresh", show=False),
        Binding("question_mark", "show_help", "HELP", show=True),
        Binding("q", "quit_app", "QUIT", show=True),
        Binding("escape", "dismiss_action", "Back", show=False),
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
        self.active_category: str = "folder"
        self.is_scanning: bool = False
        self.selected_folder: Optional[FolderNode] = None
        self.folder_filter: str = "ALL"
        self.last_selected_item: Optional[MediaItem] = None
        self.last_selected_index: Optional[int] = None

    def compose(self) -> ComposeResult:
        yield HeaderWidget()

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
        """Handle terminal resize to maintain 3-column layout responsiveness."""
        try:
            details = self.query_one(DetailsWidget)
            details.display = True

            header = self.query_one(HeaderWidget)
            if event.size.height < 30:
                header.set_compact_mode(True)
            else:
                header.set_compact_mode(False)
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

        if not self.selected_folder and self.library.folder_roots:
            self.selected_folder = self.library.folder_roots[0]

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
            sidebar.update_tree_and_counts(self.library)

            footer = self.query_one(ContextualFooter)
            footer.set_mode_hint(self.active_category if not self.selected_folder else "folder")

            media_list = self.query_one(MediaListWidget)
            details = self.query_one(DetailsWidget)

            if self.is_scanning:
                media_list.render_scanning()
                details.show_empty("Scanning library directories...")
                return

            if self.selected_folder:
                media_list.render_folder(self.selected_folder, active_filter=self.folder_filter)
                if self.last_selected_item:
                    media_list.restore_selection(item=self.last_selected_item, index=self.last_selected_index)
                details.show_folder(self.selected_folder)
            elif self.active_category == "continue":
                media_list.render_media_items("CONTINUE WATCHING", self.library.get_continue_watching())
                details.show_empty("CONTINUE WATCHING")
            elif self.active_category == "recent":
                media_list.render_media_items("RECENTLY PLAYED", self.library.get_recently_played())
                details.show_empty("RECENTLY PLAYED")
            elif self.active_category == "favorites":
                media_list.render_media_items("FAVORITES", self.library.get_favorites())
                details.show_empty("FAVORITES")
            else:
                if self.library.folder_roots:
                    self.selected_folder = self.library.folder_roots[0]
                    media_list.render_folder(self.selected_folder, active_filter=self.folder_filter)
                    details.show_folder(self.selected_folder)
                else:
                    media_list.render_media_items("LIBRARY", self.library.all_items)
                    details.show_empty("LIBRARY")
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle selection of folder or media node in Filesystem Tree."""
        data = event.node.data
        if data:
            if data.get("type") == "folder":
                self.selected_folder = data["folder"]
                self.active_category = "folder"
                self.update_ui_views()
            elif data.get("type") == "media":
                self.play_media_item(data["media"])

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Real-time details update when navigating tree nodes (Folders & Media Files)."""
        data = event.node.data
        if data:
            try:
                details = self.query_one(DetailsWidget)
                if data.get("type") == "folder":
                    details.show_folder(data["folder"])
                elif data.get("type") == "media":
                    details.show_media_item(data["media"])
            except Exception:
                pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection in Personal views, Storage drives, System list, or Media list."""
        if event.list_view.id == "personal-views-list":
            item_id = (event.item.id or "") if event.item else ""
            if item_id.startswith("cat-"):
                self.active_category = item_id.replace("cat-", "")
                self.selected_folder = None
                self.update_ui_views()

        elif event.list_view.id == "storage-list":
            item_id = (event.item.id or "") if event.item else ""
            mounts = MountsManager.get_accessible_mounts()
            for mount_path, label_str in mounts:
                if f"drv-{hash(str(mount_path))}" == item_id:
                    for root in self.library.folder_roots:
                        if root.path == mount_path or root.path in mount_path.parents or mount_path in root.path.parents:
                            self.selected_folder = root
                            self.active_category = "folder"
                            self.update_ui_views()
                            break

        elif event.list_view.id == "system-list":
            item_id = (event.item.id or "") if event.item else ""
            if item_id == "sys-paths":
                self.action_manage_paths()
            elif item_id == "sys-refresh":
                self.action_refresh_library()
            elif item_id == "sys-help":
                self.action_show_help()

        elif event.list_view.id == "media-list":
            if isinstance(event.item, FolderListItem):
                self.selected_folder = event.item.folder_data
                self.active_category = "folder"
                self.update_ui_views()
            elif isinstance(event.item, MediaListItem):
                self.play_media_item(event.item.media_data)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Real-time details panel update when highlight changes in any ListView."""
        try:
            details = self.query_one(DetailsWidget)

            if event.list_view.id == "media-list":
                if isinstance(event.item, FolderListItem):
                    details.show_folder(event.item.folder_data)
                elif isinstance(event.item, MediaListItem):
                    details.show_media_item(event.item.media_data)
                elif isinstance(event.item, HeaderListItem) or not event.item:
                    if self.selected_folder:
                        details.show_folder(self.selected_folder)
                    else:
                        details.show_empty("LIBRARY")

            elif event.list_view.id == "personal-views-list":
                item_id = (event.item.id or "") if event.item else ""
                if item_id == "cat-continue":
                    details.show_empty("CONTINUE WATCHING")
                elif item_id == "cat-recent":
                    details.show_empty("RECENTLY PLAYED")
                elif item_id == "cat-favorites":
                    details.show_empty("FAVORITES")

            elif event.list_view.id == "storage-list":
                item_id = (event.item.id or "") if event.item else ""
                mounts = MountsManager.get_accessible_mounts()
                for mount_path, label_str in mounts:
                    if f"drv-{hash(str(mount_path))}" == item_id:
                        details.show_empty(f"STORAGE DRIVE: {label_str}\nPath: {mount_path}")
                        break
        except Exception:
            pass

    def action_select_action(self) -> None:
        """Handle Enter key action based on currently highlighted item in Media List."""
        try:
            media_list = self.query_one(MediaListWidget)
            list_view = media_list.query_one("#media-list", ListView)
            highlighted = list_view.highlighted_child
            if isinstance(highlighted, FolderListItem):
                self.selected_folder = highlighted.folder_data
                self.active_category = "folder"
                self.update_ui_views()
            elif isinstance(highlighted, MediaListItem):
                self.play_media_item(highlighted.media_data)
        except Exception:
            pass

    def play_media_item(self, item: MediaItem) -> None:
        """Play target MediaItem or launch Virtual Environment via MediaRouter."""
        self.last_selected_item = item
        try:
            media_list = self.query_one(MediaListWidget)
            self.last_selected_index = media_list.get_selected_index()
        except Exception:
            pass
        MediaRouter.open_media(self, item)



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
        try:
            media_list = self.query_one(MediaListWidget)
            list_view = media_list.query_one("#media-list", ListView)
            highlighted = list_view.highlighted_child
            if isinstance(highlighted, MediaListItem):
                is_fav = self.library.toggle_favorite(highlighted.media_data)
                self.notify("★ Added to Favorites" if is_fav else "Removed from Favorites", title="Favorites")
                self.update_ui_views()
        except Exception:
            pass

    def action_cycle_audio_stream(self) -> None:
        self.notify("Cycle Audio Stream", title="Audio")

    def action_cycle_subtitle_stream(self) -> None:
        self.notify("Cycle Subtitle Stream", title="Subtitles")

    def action_show_media_info(self) -> None:
        target_item = None
        try:
            media_list = self.query_one(MediaListWidget)
            list_view = media_list.query_one("#media-list", ListView)
            highlighted = list_view.highlighted_child
            if isinstance(highlighted, MediaListItem):
                target_item = highlighted.media_data
        except Exception:
            pass

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

    def action_refresh_library(self) -> None:
        self.notify("Rescanning library directories...", title="Refresh")
        self.refresh_library()

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_dismiss_action(self) -> None:
        if len(self.screen_stack) > 1:
            self.pop_screen()
            return

        if self.selected_folder:
            if self.selected_folder.parent:
                self.selected_folder = self.selected_folder.parent
            else:
                self.selected_folder = None
                if self.library.folder_roots:
                    self.selected_folder = self.library.folder_roots[0]
            self.update_ui_views()
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


