"""
Centralized Media Router for Viz Terminal Media Center.
Determines media type and routes to dedicated Virtual Environments.
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
            folder_imgs = context_queue or [m for m in (app.selected_folder.media_files if getattr(app, "selected_folder", None) else app.library.images) if m.media_type == MediaType.IMAGE]
            if item not in folder_imgs:
                folder_imgs.insert(0, item)
            app.push_screen(ImageViewerScreen(item, folder_imgs))

        elif item.media_type == MediaType.VIDEO:
            folder_vids = context_queue or [m for m in (app.selected_folder.media_files if getattr(app, "selected_folder", None) else app.library.videos) if m.media_type == MediaType.VIDEO]
            if item not in folder_vids:
                folder_vids.insert(0, item)
            app.push_screen(VideoPlayerScreen(item, folder_vids))

        elif item.media_type == MediaType.AUDIO:
            folder_auds = context_queue or [m for m in (app.selected_folder.media_files if getattr(app, "selected_folder", None) else app.library.audio) if m.media_type == MediaType.AUDIO]
            if item not in folder_auds:
                folder_auds.insert(0, item)
            app.push_screen(AudioPlayerScreen(item, folder_auds))

        else:
            app.push_screen(InfoScreen(item))
