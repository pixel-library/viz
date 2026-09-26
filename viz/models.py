"""
Data models and Enums for Viz Terminal Media Player.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from viz.constants import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS


class MediaType(Enum):
    AUDIO = auto()
    VIDEO = auto()
    UNKNOWN = auto()

    @classmethod
    def from_path(cls, path: Path) -> MediaType:
        ext = path.suffix.lower()
        if ext in VIDEO_EXTENSIONS:
            return cls.VIDEO
        elif ext in AUDIO_EXTENSIONS:
            return cls.AUDIO
        return cls.UNKNOWN


class PlaybackStatus(Enum):
    STOPPED = auto()
    LOADING = auto()
    PLAYING = auto()
    PAUSED = auto()
    ENDED = auto()
    ERROR = auto()


@dataclass
class MediaItem:
    """Represents a media file discovered on disk."""

    path: Path
    name: str
    display_name: str
    extension: str
    media_type: MediaType
    file_size: int = 0
    modified_time: float = 0.0
    duration: float = 0.0

    @classmethod
    def from_file(cls, path: Path) -> Optional[MediaItem]:
        """Create MediaItem from Path safely."""
        try:
            resolved_path = path.resolve()
            if not resolved_path.is_file():
                return None
            stat = resolved_path.stat()
            media_type = MediaType.from_path(resolved_path)
            return cls(
                path=resolved_path,
                name=resolved_path.name,
                display_name=resolved_path.stem,
                extension=resolved_path.suffix.lower(),
                media_type=media_type,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
                duration=0.0,
            )
        except (PermissionError, FileNotFoundError, OSError):
            return None

    @property
    def icon(self) -> str:
        if self.media_type == MediaType.AUDIO:
            return "🎵"
        elif self.media_type == MediaType.VIDEO:
            return "🎬"
        return "📄"

    @property
    def ascii_icon(self) -> str:
        if self.media_type == MediaType.AUDIO:
            return "[A]"
        elif self.media_type == MediaType.VIDEO:
            return "[V]"
        return "[?]"


@dataclass
class PlaybackState:
    """State of the media engine playback."""

    current_media: Optional[MediaItem] = None
    status: PlaybackStatus = PlaybackStatus.STOPPED
    position: float = 0.0
    duration: float = 0.0
    volume: int = 80
    is_muted: bool = False
    is_fullscreen: bool = False
    is_tv_mode: bool = False
    error_message: Optional[str] = None
