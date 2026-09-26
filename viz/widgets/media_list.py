"""
Right Column Media List Widget for Viz Media Center.
Implements custom terminal representations for Movies, Series, Music, Continue Watching, and Queue.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

from viz.models import MediaItem, MediaType
from viz.series import SeriesEpisode, SeriesGroup
from viz.widgets.player_status import PlayerStatusWidget


class MediaListWidget(Widget):
    """Media list container rendering custom rows for Movies, Series, Music, and Queue."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="right-column"):
            yield Label("[ /Browse ]", classes="column-header", id="browse-header")
            yield ListView(id="media-list")

    def render_scanning(self) -> None:
        """Render scanning status state."""
        self._update_header("SCANNING", 0)
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()
        list_view.append(ListItem(Label("[ SCANNING LIBRARY ]\n\nPlease wait...")))

    def update_list(self, media_items: Optional[List[MediaItem]] = None, is_scanning: bool = False, media_path_display: str = "") -> None:
        """Update list view (compatibility helper)."""
        if is_scanning:
            self.render_scanning()
        elif media_items is not None:
            self.render_all_media(media_items)

    def render_movies(self, movies: List[MediaItem], title_suffix: str = "") -> None:
        """Render Movies view with duration and completion progress bars."""
        self._update_header(f"MOVIES {title_suffix}", len(movies))
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        if not movies:
            list_view.append(ListItem(Label("[ MOVIES ]\n\nNo movie files found in library.\nPress R to rescan.")))
            return

        for item in movies:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else ""
            fav_str = " ★" if item.favorite else ""
            
            # Progress bar
            progress_str = ""
            if item.progress_pct > 0.05 and not item.completed:
                filled = int(item.progress_pct * 12)
                scrubber = "█" * filled + "░" * (12 - filled)
                progress_str = f"\n    [{scrubber}] {int(item.progress_pct * 100)}%"
            elif item.completed:
                progress_str = "\n    [✓ COMPLETED]"

            text = f"[V] {item.display_name}{fav_str}\n    {dur_str}{progress_str}"
            list_view.append(ListItem(Label(text)))

    def render_series(self, series_groups: Dict[str, SeriesGroup]) -> None:
        """Render Series view grouped by TV Show."""
        self._update_header("SERIES", len(series_groups))
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        if not series_groups:
            list_view.append(ListItem(Label("[ SERIES ]\n\nNo TV series detected in library.")))
            return

        for s_name, group in series_groups.items():
            text = f"📺 {group.name}\n    {group.season_count} Season(s) · {group.total_episodes} Episode(s)"
            list_view.append(ListItem(Label(text)))

    def render_episodes(self, series_name: str, episodes: List[SeriesEpisode]) -> None:
        """Render episode list for a selected TV series."""
        self._update_header(f"SERIES // {series_name.upper()}", len(episodes))
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        for ep in episodes:
            item = ep.media_item
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else ""
            
            progress_str = ""
            if item.progress_pct > 0.05 and not item.completed:
                filled = int(item.progress_pct * 10)
                scrubber = "█" * filled + "░" * (10 - filled)
                progress_str = f" [{scrubber}] {int(item.progress_pct * 100)}%"

            text = f"S{ep.season_num:02d}E{ep.episode_num:02d} - {ep.title} ({dur_str}){progress_str}"
            list_view.append(ListItem(Label(text)))

    def render_music(self, music_items: List[MediaItem]) -> None:
        """Render Music view with Track Title, Artist, Album, and Duration."""
        self._update_header("MUSIC", len(music_items))
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        if not music_items:
            list_view.append(ListItem(Label("[ MUSIC ]\n\nNo audio files found in library.\nPress R to rescan.")))
            return

        for item in music_items:
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else ""
            artist_str = f" - {item.artist}" if item.artist else ""
            album_str = f" · {item.album}" if item.album else ""
            fav_str = " ★" if item.favorite else ""

            text = f"[♪] {item.title or item.display_name}{fav_str}\n    {artist_str}{album_str} ({dur_str})"
            list_view.append(ListItem(Label(text)))

    def render_all_media(self, items: List[MediaItem], query: str = "") -> None:
        """Render combined All Media list."""
        suffix = f" - Query: '{query}'" if query else ""
        self._update_header(f"ALL MEDIA{suffix}", len(items))
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        if not items:
            msg = f"No media matching > '{query}'" if query else "No media files found."
            list_view.append(ListItem(Label(f"[ NO RESULTS ]\n\n{msg}")))
            return

        for item in items:
            icon = item.ascii_icon
            dur_str = PlayerStatusWidget.format_time(item.duration) if item.duration > 0 else ""
            text = f"{icon} {item.name} ({dur_str})"
            list_view.append(ListItem(Label(text)))

    def render_continue_watching(self, items: List[MediaItem]) -> None:
        """Render Continue Watching section for unfinished videos."""
        self._update_header("CONTINUE WATCHING", len(items))
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        if not items:
            list_view.append(ListItem(Label("[ CONTINUE WATCHING ]\n\nNo unfinished videos.")))
            return

        for item in items:
            dur_str = PlayerStatusWidget.format_time(item.duration)
            curr_str = PlayerStatusWidget.format_time(item.last_position)
            filled = int(item.progress_pct * 14)
            scrubber = "█" * filled + "░" * (14 - filled)

            text = f"[V] {item.display_name}\n    {curr_str} / {dur_str} [{scrubber}] {int(item.progress_pct * 100)}%"
            list_view.append(ListItem(Label(text)))

    def render_queue(self, current: Optional[MediaItem], up_next: List[MediaItem]) -> None:
        """Render active Playback Queue."""
        total = (1 if current else 0) + len(up_next)
        self._update_header("PLAYBACK QUEUE", total)
        list_view = self.query_one("#media-list", ListView)
        list_view.clear()

        if current:
            dur_str = PlayerStatusWidget.format_time(current.duration)
            list_view.append(ListItem(Label(f"▶ NOW PLAYING\n  {current.ascii_icon} {current.name} ({dur_str})\n")))

        if not up_next:
            if not current:
                list_view.append(ListItem(Label("[ QUEUE EMPTY ]\n\nNo items in playback queue.")))
            return

        list_view.append(ListItem(Label("── UP NEXT ──")))
        for idx, item in enumerate(up_next, start=1):
            dur_str = PlayerStatusWidget.format_time(item.duration)
            list_view.append(ListItem(Label(f"{idx}. {item.ascii_icon} {item.name} ({dur_str})")))

    def _update_header(self, title: str, count: int) -> None:
        header_label = self.query_one("#browse-header", Label)
        header_label.update(f"[ {title} ({count}) ]")

    def get_selected_index(self) -> Optional[int]:
        list_view = self.query_one("#media-list", ListView)
        return list_view.index
