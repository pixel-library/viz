"""
Data models and Enums for Viz Terminal Media Center.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from viz.constants import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


class MediaType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    UNKNOWN = "unknown"

    @classmethod
    def from_path(cls, path: Path) -> MediaType:
        ext = path.suffix.lower()
        if ext in VIDEO_EXTENSIONS:
            return cls.VIDEO
        elif ext in AUDIO_EXTENSIONS:
            return cls.AUDIO
        elif ext in IMAGE_EXTENSIONS:
            return cls.IMAGE
        return cls.UNKNOWN


class PlaybackStatus(Enum):
    STOPPED = auto()
    LOADING = auto()
    PLAYING = auto()
    PAUSED = auto()
    ENDED = auto()
    ERROR = auto()


class LoopMode(Enum):
    OFF = "No Loop"
    ONE = "Loop File"
    ALL = "Loop Queue"


@dataclass
class MediaItem:
    """Rich media model representing an audio, video, or image file."""

    path: Path
    name: str
    display_name: str
    extension: str
    media_type: MediaType
    directory: Path
    file_size: int = 0
    modified_time: float = 0.0
    duration: float = 0.0
    
    # User / Playback state
    favorite: bool = False
    play_count: int = 0
    last_played: float = 0.0
    last_position: float = 0.0
    completed: bool = False

    # Video / Series Metadata
    series_name: Optional[str] = None
    season_num: Optional[int] = None
    episode_num: Optional[int] = None
    episode_title: Optional[str] = None
    video_width: int = 0
    video_height: int = 0

    # Music Metadata
    artist: Optional[str] = None
    album: Optional[str] = None
    track_num: Optional[int] = None
    title: Optional[str] = None
    bitrate: int = 0

    # Image Metadata
    image_width: int = 0
    image_height: int = 0
    image_format: str = ""

    @classmethod
    def from_file(cls, path: Path) -> Optional[MediaItem]:
        """Safely instantiate MediaItem from filesystem Path."""
        try:
            resolved_path = path.expanduser().resolve()
            if not resolved_path.is_file():
                return None
            stat = resolved_path.stat()
            media_type = MediaType.from_path(resolved_path)
            if media_type == MediaType.UNKNOWN:
                return None

            item = cls(
                path=resolved_path,
                name=resolved_path.name,
                display_name=resolved_path.stem,
                extension=resolved_path.suffix.lower(),
                media_type=media_type,
                directory=resolved_path.parent,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
            )

            # Fast dimension extraction for images if Pillow is available
            if media_type == MediaType.IMAGE:
                try:
                    from PIL import Image
                    with Image.open(resolved_path) as img:
                        item.image_width, item.image_height = img.size
                        item.image_format = img.format or resolved_path.suffix.lstrip(".").upper()
                except Exception:
                    item.image_format = resolved_path.suffix.lstrip(".").upper()

            return item
        except (PermissionError, FileNotFoundError, OSError):
            return None

    @property
    def progress_pct(self) -> float:
        """Return progress percentage (0.0 to 1.0)."""
        if self.duration > 0 and self.last_position > 0:
            return min(1.0, max(0.0, self.last_position / self.duration))
        return 0.0

    @property
    def icon(self) -> str:
        return self.ascii_icon

    @property
    def ascii_icon(self) -> str:
        if self.media_type == MediaType.AUDIO:
            return "[AUD]"
        elif self.media_type == MediaType.VIDEO:
            return "[VID]"
        elif self.media_type == MediaType.IMAGE:
            return "[IMG]"
        return "[FILE]"


@dataclass
class PlaybackState:
    """State snapshot of active player engine."""

    current_media: Optional[MediaItem] = None
    status: PlaybackStatus = PlaybackStatus.STOPPED
    position: float = 0.0
    duration: float = 0.0
    volume: int = 80
    is_muted: bool = False
    speed: float = 1.0
    is_fullscreen: bool = False
    is_tv_mode: bool = False
    loop_mode: LoopMode = LoopMode.OFF
    is_shuffle: bool = False
    audio_track: int = 1
    sub_track: int = 0
    error_message: Optional[str] = None
