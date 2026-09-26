"""
Centralized Media Router for Viz Terminal Media Center.
Determines media type and routes to dedicated Virtual Environments.

Architecture:
- Images → ImageViewerScreen (terminal preview + native MPV viewer)
- Videos → VideoPlayerScreen (native MPV window + terminal controls)
- Audio  → AudioPlayerScreen (MPV audio-only + terminal controls)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from viz.models import MediaItem, MediaType
from viz.screens.audio_player import AudioPlayerScreen
from viz.screens.image_viewer import ImageViewerScreen
from viz.screens.info import InfoScreen
from viz.screens.video_player import VideoPlayerScreen


class MediaRouter:
    """Central router for opening media items or file paths in dedicated virtual environments."""

    @classmethod
    def open_media(
        cls,
        app,
        item_or_path: Union[MediaItem, Path, str],
        context_queue: Optional[List[MediaItem]] = None,
    ) -> None:
        """Route target media item to dedicated virtual environment screen."""
        if isinstance(item_or_path, (str, Path)):
            path = Path(item_or_path).expanduser().resolve()
            item = MediaItem.from_file(path)
            if not item:
                app.notify(f"Cannot open unsupported file: {path.name}", title="Media Router Error", severity="error")
                return
        else:
            item = item_or_path

        if item.media_type == MediaType.IMAGE:
            from viz.images import ImageHelper
            if hasattr(app, "last_selected_item"):
                app.last_selected_item = item

            if hasattr(app, "engine") and app.engine:
                if app.engine.play_image(item):
                    return

            ImageHelper.open_native_viewer(item.path)

        elif item.media_type == MediaType.VIDEO:
            folder_vids = context_queue or cls._get_folder_media(app, MediaType.VIDEO)
            if item not in folder_vids:
                folder_vids.insert(0, item)
            app.push_screen(VideoPlayerScreen(item, folder_vids))

        elif item.media_type == MediaType.AUDIO:
            folder_auds = context_queue or cls._get_folder_media(app, MediaType.AUDIO)
            if item not in folder_auds:
                folder_auds.insert(0, item)
            app.push_screen(AudioPlayerScreen(item, folder_auds))

        else:
            app.push_screen(InfoScreen(item))

    @classmethod
    def _get_folder_media(cls, app, media_type: MediaType) -> List[MediaItem]:
        """Get media items of given type from the currently selected folder or library."""
        try:
            selected = getattr(app, "selected_folder", None)
            if selected and hasattr(selected, "media_files"):
                items = [m for m in selected.media_files if m.media_type == media_type]
                if items:
                    return items

            library = getattr(app, "library", None)
            if library:
                if media_type == MediaType.IMAGE:
                    return list(library.images)
                elif media_type == MediaType.VIDEO:
                    return list(library.videos)
                elif media_type == MediaType.AUDIO:
                    return list(library.music)
        except Exception:
            pass
        return []
