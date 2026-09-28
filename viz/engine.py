"""
High-Performance Media Engine Facade for Viz Media Center.
Coordinates modular viz.media package (MPV Subprocess, JSON-IPC, Kitty Graphics).

Provides distinct playback modes for:
- Video Virtual Environment: MPV process with Kitty terminal graphics output (--vo=kitty,gpu-next,gpu,auto)
- Audio Virtual Environment: MPV process with system default audio output (--no-video --vo=null)
- Image Virtual Environment: TerminalImageRenderer (Kitty graphics protocol)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from viz.media import (
    MPVAudioPlayer,
    MPVProcessManager,
    MPVVideoPlayer,
    TerminalGraphics,
    TerminalImageRenderer,
)
from viz.models import MediaItem, MediaType, PlaybackState, PlaybackStatus


class MediaEngine:
    """
    Dedicated Media Engine Facade for Viz.
    Coordinates player processes, IPC sync, seeking, volume, and event state.
    """

    def __init__(self, initial_volume: int = 80, initial_muted: bool = False) -> None:
        self.mgr = MPVProcessManager()
        self.video_player = MPVVideoPlayer(self.mgr)
        self.audio_player = MPVAudioPlayer(self.mgr)

        self.is_available: bool = True
        self.error_message: Optional[str] = None
        self.state = PlaybackState(volume=initial_volume, is_muted=initial_muted)
        self.on_state_change_callback: Optional[Callable[[PlaybackState], None]] = None
        self.active_media_type: Optional[MediaType] = None

    def play(self, media_item: MediaItem, start_position: float = 0.0) -> bool:
        """Route to appropriate playback engine based on media type."""
        if not media_item or not media_item.path.exists():
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = f"File not found: {media_item.path if media_item else 'None'}"
            return False

        if media_item.media_type == MediaType.VIDEO:
            return self.play_video(media_item, start_position=start_position)
        elif media_item.media_type == MediaType.AUDIO:
            return self.play_audio(media_item, start_position=start_position)
        elif media_item.media_type == MediaType.IMAGE:
            return self.play_image(media_item)
        return False

    def play_video(self, media_item: MediaItem, start_position: float = 0.0) -> bool:
        """Play video via MPV subprocess (--vo=kitty,gpu-next,gpu,auto)."""
        self.stop()
        success = self.video_player.play(
            item=media_item,
            start_position=start_position,
            volume=self.state.volume,
            muted=self.state.is_muted,
        )
        if success:
            self.active_media_type = MediaType.VIDEO
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING
            self.state.position = start_position
            self.sync_state()
            return True
        else:
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = "Failed to launch MPV video process"
            return False

    def play_audio(self, media_item: MediaItem, start_position: float = 0.0) -> bool:
        """Play audio via MPV subprocess (--no-video --vo=null)."""
        self.stop()
        success = self.audio_player.play(
            item=media_item,
            start_position=start_position,
            volume=self.state.volume,
            muted=self.state.is_muted,
        )
        if success:
            self.active_media_type = MediaType.AUDIO
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING
            self.state.position = start_position
            self.sync_state()
            return True
        else:
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = "Failed to launch MPV audio process"
            return False

    def play_image(self, media_item: MediaItem) -> bool:
        """Render image in native high-resolution Kitty raster protocol or native viewer."""
        self.stop()
        if not media_item or not media_item.path.exists():
            return False

        self.active_media_type = MediaType.IMAGE
        self.state.current_media = media_item
        self.state.status = PlaybackStatus.PLAYING
        return True

    def sync_state(self) -> None:
        """Query real MPV state via JSON IPC and update PlaybackState dataclass."""
        if self.active_media_type == MediaType.VIDEO:
            self.video_player.sync_to_state(self.state)
        elif self.active_media_type == MediaType.AUDIO:
            self.audio_player.sync_to_state(self.state)

        if self.on_state_change_callback:
            try:
                self.on_state_change_callback(self.state)
            except Exception:
                pass

    def toggle_pause(self) -> bool:
        if self.active_media_type == MediaType.VIDEO:
            res = self.video_player.toggle_pause()
            if res is not None:
                self.state.status = PlaybackStatus.PAUSED if res else PlaybackStatus.PLAYING
                return res
        elif self.active_media_type == MediaType.AUDIO:
            res = self.audio_player.toggle_pause()
            if res is not None:
                self.state.status = PlaybackStatus.PAUSED if res else PlaybackStatus.PLAYING
                return res
        return False

    def toggle_mute(self) -> bool:
        new_mute = not self.state.is_muted
        if self.active_media_type == MediaType.VIDEO:
            self.video_player.set_mute(new_mute)
        elif self.active_media_type == MediaType.AUDIO:
            self.audio_player.set_mute(new_mute)
        self.state.is_muted = new_mute
        return new_mute

    def set_volume(self, level: int) -> int:
        clamped = max(0, min(100, level))
        self.state.volume = clamped
        if self.active_media_type == MediaType.VIDEO:
            self.video_player.set_volume(clamped)
        elif self.active_media_type == MediaType.AUDIO:
            self.audio_player.set_volume(clamped)
        return clamped

    def change_volume(self, delta: int) -> int:
        return self.set_volume(self.state.volume + delta)

    def seek(self, seconds: float, relative: bool = True) -> float:
        if self.active_media_type == MediaType.VIDEO:
            self.video_player.seek(seconds, relative=relative)
            self.sync_state()
        elif self.active_media_type == MediaType.AUDIO:
            self.audio_player.seek(seconds, relative=relative)
            self.sync_state()
        return self.state.position

    def toggle_fullscreen(self) -> bool:
        if self.active_media_type == MediaType.VIDEO:
            res = self.video_player.toggle_fullscreen()
            self.state.is_fullscreen = res
            return res
        return False

    def stop(self) -> None:
        """Cleanly terminate playback process and clear terminal graphics."""
        self.mgr.stop()
        TerminalGraphics.clear_graphics()
        self.active_media_type = None
        self.state.status = PlaybackStatus.STOPPED
        self.state.position = 0.0

    def terminate(self) -> None:
        self.stop()


