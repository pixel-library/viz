"""
Centralized Media Router for Viz Terminal Media Center.
Determines media type and dispatches to dedicated Virtual Environments.

Architecture:
- Images → ImageEnvironment (immediate native raster image viewer)
- Videos → VideoEnvironment (hardware-accelerated GPU MPV window)
- Audio  → AudioEnvironment (high-fidelity audio player without video window)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from viz.models import MediaItem, MediaType
from viz.screens.audio_environment import AudioEnvironment
from viz.screens.image_environment import ImageEnvironment
from viz.screens.info import InfoScreen
from viz.screens.video_environment import VideoEnvironment


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

        # Guard against duplicate environment mounts on rapid or duplicate Enter keypress
        if len(app.screen_stack) > 1 and type(app.screen_stack[-1]).__name__ in (
            "ImageEnvironment", "VideoEnvironment", "AudioEnvironment",
            "ImageViewerScreen", "VideoPlayerScreen", "AudioPlayerScreen"
        ):
            return

        if item.media_type == MediaType.IMAGE:
            if hasattr(app, "last_selected_item"):
                app.last_selected_item = item
            folder_imgs = context_queue or cls._get_folder_media(app, MediaType.IMAGE)
            if item not in folder_imgs:
                folder_imgs.insert(0, item)
            app.push_screen(ImageEnvironment(item, folder_imgs))

        elif item.media_type == MediaType.VIDEO:
            if hasattr(app, "last_selected_item"):
                app.last_selected_item = item
            folder_vids = context_queue or cls._get_folder_media(app, MediaType.VIDEO)
            if item not in folder_vids:
                folder_vids.insert(0, item)
            app.push_screen(VideoEnvironment(item, folder_vids))

        elif item.media_type == MediaType.AUDIO:
            if hasattr(app, "last_selected_item"):
                app.last_selected_item = item
            folder_auds = context_queue or cls._get_folder_media(app, MediaType.AUDIO)
            if item not in folder_auds:
                folder_auds.insert(0, item)
            app.push_screen(AudioEnvironment(item, folder_auds))

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
