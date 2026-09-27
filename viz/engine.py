"""
Isolated Media Engine Abstraction for MPV / libmpv Integration.
Handles player lifecycle, playback state, seeking, audio/video controls, and event mapping.

Key architectural decisions:
- Uses hwdec=auto for hardware-accelerated video decoding
- Creates a separate MPV window for video playback (vo=gpu)
- Audio-only playback uses vo=null to prevent window creation
- Image viewing uses --image-display-duration=inf for proper display
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Optional

from viz.models import MediaItem, MediaType, PlaybackState, PlaybackStatus
from viz.terminal import TerminalCapabilities

# Attempt to import python-mpv cleanly
HAS_MPV = False
MPV_INIT_ERROR = ""
try:
    import mpv
    HAS_MPV = True
except Exception as err:
    HAS_MPV = False
    MPV_INIT_ERROR = str(err)


class MediaEngine:
    """
    Dedicated media engine encapsulating python-mpv native player.
    Keeps MPV backend logic completely decoupled from UI widgets.

    Video: Opens in a native hardware-accelerated MPV window.
    Audio: Plays audio-only without creating a window.
    Images: Opened via separate MPV process with image display mode.
    """

    def __init__(self, initial_volume: int = 80, initial_muted: bool = False) -> None:
        self.player: Optional[mpv.MPV] = None
        self.is_available: bool = False
        self.error_message: Optional[str] = None
        self.state = PlaybackState(volume=initial_volume, is_muted=initial_muted)
        self.on_state_change_callback: Optional[Callable[[PlaybackState], None]] = None
        self._image_process: Optional[subprocess.Popen] = None

        if HAS_MPV:
            try:
                self.player = mpv.MPV(
                    keep_open=True,
                    osc=True,
                    title="Viz Media Player",
                    volume=initial_volume,
                    mute=initial_muted,
                    hwdec="auto",
                )
                self.is_available = True
                self._setup_event_observers()
            except Exception as err:
                self.is_available = False
                self.error_message = f"libmpv initialization failed: {err}"
        else:
            self.is_available = False
            self.error_message = (
                f"MPV / libmpv unavailable ({MPV_INIT_ERROR}). "
                "Please install system package: 'sudo apt install mpv libmpv-dev'"
            )

    def _setup_event_observers(self) -> None:
        """Register observers on MPV properties."""
        if not self.player:
            return

        @self.player.property_observer("time-pos")
        def _on_time_pos(_name, value):
            if value is not None:
                self.state.position = float(value)
                self._notify_state_change()

        @self.player.property_observer("duration")
        def _on_duration(_name, value):
            if value is not None:
                self.state.duration = float(value)
                self._notify_state_change()

        @self.player.property_observer("pause")
        def _on_pause(_name, value):
            if value is not None:
                if value and self.state.status == PlaybackStatus.PLAYING:
                    self.state.status = PlaybackStatus.PAUSED
                elif not value and self.state.status == PlaybackStatus.PAUSED:
                    self.state.status = PlaybackStatus.PLAYING
                self._notify_state_change()

        @self.player.property_observer("idle-active")
        def _on_idle(_name, value):
            if value:
                if self.state.status in (PlaybackStatus.PLAYING, PlaybackStatus.PAUSED):
                    self.state.status = PlaybackStatus.ENDED
                    self._notify_state_change()

    def _notify_state_change(self) -> None:
        if self.on_state_change_callback:
            try:
                self.on_state_change_callback(self.state)
            except Exception:
                pass

    def play(self, media_item: MediaItem, start_position: float = 0.0) -> bool:
        """Trigger playback for media item.

        For video files: Opens in native MPV window with hardware decoding.
        For audio files: Plays audio-only without creating a window.
        """
        if not self.is_available or not self.player:
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = self.error_message or "MPV engine unavailable"
            return False

        abs_path = str(media_item.path.resolve())
        try:
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.LOADING
            self.state.position = start_position
            self.state.duration = 0.0

            # Configure video output based on media type
            if media_item.media_type == MediaType.AUDIO:
                # Audio-only: no video window
                try:
                    self.player.vo = "null"
                except Exception:
                    pass
            else:
                # Video: use hardware-accelerated rendering in native window
                try:
                    if TerminalCapabilities.has_display():
                        self.player.vo = "gpu"
                    else:
                        self.player.vo = "null"
                except Exception:
                    pass

            if start_position > 0.0:
                self.player.play(abs_path, start=f"{start_position}")
            else:
                self.player.play(abs_path)

            self.state.status = PlaybackStatus.PLAYING
            self._notify_state_change()
            return True
        except Exception as err:
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = f"Playback error: {err}"
            self._notify_state_change()
            return False

    def play_image(self, media_item: MediaItem) -> bool:
        """Open image in a dedicated MPV process with native rendering.

        This launches a separate MPV process specifically for image viewing,
        using --image-display-duration=inf to keep the image displayed.
        The image is rendered at full native resolution in its own window.
        """
        if not TerminalCapabilities.has_display():
            return False

        if not media_item.path.exists():
            return False

        if self._image_process and self._image_process.poll() is None:
            try:
                self._image_process.terminate()
            except Exception:
                pass

        try:
            abs_path = str(media_item.path.resolve())
            self._image_process = subprocess.Popen(
                [
                    "mpv",
                    "--image-display-duration=inf",
                    "--force-window=yes",
                    f"--title=Viz // {media_item.name}",
                    "--no-terminal",
                    "--keep-open=yes",
                    "--loop-file=inf",
                    "--hwdec=auto",
                    abs_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def toggle_pause(self) -> bool:
        """Toggle pause / resume state."""
        if not self.player or not self.state.current_media:
            return False
        try:
            new_pause = not bool(getattr(self.player, "pause", False))
            self.player.pause = new_pause
            self.state.status = PlaybackStatus.PAUSED if new_pause else PlaybackStatus.PLAYING
            self._notify_state_change()
            return new_pause
        except Exception:
            return False

    def toggle_mute(self) -> bool:
        """Toggle mute state."""
        if not self.player:
            return False
        try:
            new_mute = not bool(getattr(self.player, "mute", False))
            self.player.mute = new_mute
            self.state.is_muted = new_mute
            self._notify_state_change()
            return new_mute
        except Exception:
            return False

    def set_volume(self, level: int) -> int:
        """Set volume level clamped to 0..100."""
        clamped = max(0, min(100, level))
        self.state.volume = clamped
        if self.player:
            try:
                self.player.volume = clamped
            except Exception:
                pass
        self._notify_state_change()
        return clamped

    def change_volume(self, delta: int) -> int:
        """Change volume by relative delta."""
        return self.set_volume(self.state.volume + delta)

    def seek(self, seconds: float, relative: bool = True) -> float:
        """Seek relative or absolute seconds."""
        if not self.player or not self.state.current_media:
            return 0.0
        try:
            mode = "relative" if relative else "absolute"
            self.player.seek(seconds, reference=mode)
            pos = float(getattr(self.player, "time_pos", 0.0) or 0.0)
            self.state.position = pos
            self._notify_state_change()
            return pos
        except Exception:
            return 0.0

    def stop(self) -> None:
        """Stop current playback."""
        if self._image_process and self._image_process.poll() is None:
            try:
                self._image_process.terminate()
            except Exception:
                pass
            self._image_process = None

        if self.player:
            try:
                self.player.stop()
            except Exception:
                pass
        self.state.status = PlaybackStatus.STOPPED
        self.state.position = 0.0
        self._notify_state_change()

    def terminate(self) -> None:
        """Cleanly terminate MPV instance on application quit."""
        if self._image_process and self._image_process.poll() is None:
            try:
                self._image_process.terminate()
            except Exception:
                pass
            self._image_process = None

        if self.player:
            try:
                self.player.stop()
                self.player.terminate()
            except Exception:
                pass
            self.player = None
