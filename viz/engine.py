"""
Direct High-Performance Media Engine for Viz Terminal Media Center.
Coordinates python-mpv native libmpv bindings and fallback subprocess rendering.

Provides distinct playback modes for:
- Video Virtual Environment: Hardware-accelerated GPU window (vo=gpu / gpu_context=wayland,x11egl,auto)
- Audio Virtual Environment: High-fidelity audio playback without video window (vo=null)
- Image Virtual Environment: High-resolution native display window (--image-display-duration=inf)
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from viz.models import MediaItem, MediaType, PlaybackState, PlaybackStatus
from viz.terminal import TerminalCapabilities

try:
    import mpv
    HAS_PYTHON_MPV = True
except Exception:
    HAS_PYTHON_MPV = False


class MediaEngine:
    """
    Dedicated Media Engine for Viz.
    Manages player lifecycle, real playback, seeking, volume, and event state.
    """

    def __init__(self, initial_volume: int = 80, initial_muted: bool = False) -> None:
        self.player: Optional[object] = None
        self.subprocess_proc: Optional[subprocess.Popen] = None
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
        """Play video in hardware-accelerated native MPV window (vo=gpu / gpu_context=wayland,x11egl,auto)."""
        self.stop()
        abs_path = str(media_item.path.resolve())

        if HAS_PYTHON_MPV:
            try:
                self.player = mpv.MPV(
                    force_window="yes",
                    vo="gpu",
                    gpu_context="wayland,x11egl,auto",
                    hwdec="auto",
                    keep_open="yes",
                    title=f"Viz // {media_item.name}",
                    volume=self.state.volume,
                    mute=self.state.is_muted,
                )
                self.player.play(abs_path)
                if start_position > 0.0:
                    time.sleep(0.05)
                    try:
                        self.player.seek(start_position, "absolute")
                    except Exception:
                        pass

                self.active_media_type = MediaType.VIDEO
                self.state.current_media = media_item
                self.state.status = PlaybackStatus.PLAYING
                self.state.position = start_position
                self.sync_state()
                return True
            except Exception:
                try:
                    # Fallback python-mpv without explicit gpu_context
                    self.player = mpv.MPV(
                        force_window="yes",
                        vo="gpu",
                        hwdec="auto",
                        keep_open="yes",
                        title=f"Viz // {media_item.name}",
                        volume=self.state.volume,
                        mute=self.state.is_muted,
                    )
                    self.player.play(abs_path)
                    self.active_media_type = MediaType.VIDEO
                    self.state.current_media = media_item
                    self.state.status = PlaybackStatus.PLAYING
                    return True
                except Exception:
                    self.player = None

        # Fallback to subprocess MPV instance
        try:
            cmd = [
                "mpv",
                "--force-window=yes",
                "--vo=gpu",
                "--gpu-context=wayland,x11egl,auto",
                "--hwdec=auto",
                "--keep-open=yes",
                f"--volume={self.state.volume}",
                f"--title=Viz // {media_item.name}",
            ]
            if self.state.is_muted:
                cmd.append("--mute=yes")
            if start_position > 0.0:
                cmd.append(f"--start={start_position}")
            cmd.append(abs_path)

            self.subprocess_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.active_media_type = MediaType.VIDEO
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING
            self.state.position = start_position
            return True
        except Exception as err:
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = f"Failed to start video player process: {err}"
            return False

    def play_audio(self, media_item: MediaItem, start_position: float = 0.0) -> bool:
        """Play audio using MPV engine without video window (vo=null)."""
        self.stop()
        abs_path = str(media_item.path.resolve())

        if HAS_PYTHON_MPV:
            try:
                self.player = mpv.MPV(
                    vo="null",
                    video="no",
                    title=f"Viz // {media_item.name}",
                    volume=self.state.volume,
                    mute=self.state.is_muted,
                )
                self.player.play(abs_path)
                if start_position > 0.0:
                    time.sleep(0.05)
                    try:
                        self.player.seek(start_position, "absolute")
                    except Exception:
                        pass

                self.active_media_type = MediaType.AUDIO
                self.state.current_media = media_item
                self.state.status = PlaybackStatus.PLAYING
                self.state.position = start_position
                self.sync_state()
                return True
            except Exception:
                self.player = None

        # Fallback to subprocess MPV audio instance
        try:
            cmd = [
                "mpv",
                "--vo=null",
                "--video=no",
                f"--volume={self.state.volume}",
                f"--title=Viz // {media_item.name}",
            ]
            if self.state.is_muted:
                cmd.append("--mute=yes")
            if start_position > 0.0:
                cmd.append(f"--start={start_position}")
            cmd.append(abs_path)

            self.subprocess_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.active_media_type = MediaType.AUDIO
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING
            self.state.position = start_position
            return True
        except Exception as err:
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = f"Failed to start audio player process: {err}"
            return False

    def play_image(self, media_item: MediaItem) -> bool:
        """Render image in native high-resolution MPV window."""
        self.stop()
        if not media_item or not media_item.path.exists():
            return False

        abs_path = str(media_item.path.resolve())

        if HAS_PYTHON_MPV:
            try:
                self.player = mpv.MPV(
                    force_window="yes",
                    vo="gpu",
                    gpu_context="wayland,x11egl,auto",
                    image_display_duration="inf",
                    keep_open="yes",
                    loop_file="inf",
                    title=f"Viz // {media_item.name}",
                )
                self.player.play(abs_path)
                self.active_media_type = MediaType.IMAGE
                self.state.current_media = media_item
                self.state.status = PlaybackStatus.PLAYING
                return True
            except Exception:
                try:
                    self.player = mpv.MPV(
                        force_window="yes",
                        vo="gpu",
                        image_display_duration="inf",
                        keep_open="yes",
                        loop_file="inf",
                        title=f"Viz // {media_item.name}",
                    )
                    self.player.play(abs_path)
                    self.active_media_type = MediaType.IMAGE
                    self.state.current_media = media_item
                    self.state.status = PlaybackStatus.PLAYING
                    return True
                except Exception:
                    self.player = None

        # Fallback process
        try:
            cmd = [
                "mpv",
                "--image-display-duration=inf",
                "--force-window=yes",
                "--vo=gpu",
                "--gpu-context=wayland,x11egl,auto",
                "--keep-open=yes",
                "--loop-file=inf",
                f"--title=Viz // {media_item.name}",
                abs_path,
            ]
            self.subprocess_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.active_media_type = MediaType.IMAGE
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING
            return True
        except Exception:
            return False

    def sync_state(self) -> None:
        """Query properties from player instance and update PlaybackState."""
        if not self.player:
            return

        try:
            pos = getattr(self.player, "time_pos", None)
            if pos is not None:
                self.state.position = float(pos)

            dur = getattr(self.player, "duration", None)
            if dur is not None:
                self.state.duration = float(dur)

            pause = getattr(self.player, "pause", None)
            if pause is not None:
                self.state.status = PlaybackStatus.PAUSED if pause else PlaybackStatus.PLAYING

            vol = getattr(self.player, "volume", None)
            if vol is not None:
                self.state.volume = int(vol)

            mute = getattr(self.player, "mute", None)
            if mute is not None:
                self.state.is_muted = bool(mute)

            fs = getattr(self.player, "fs", None)
            if fs is not None:
                self.state.is_fullscreen = bool(fs)

            eof = getattr(self.player, "eof_reached", False)
            if eof:
                self.state.status = PlaybackStatus.ENDED

        except Exception:
            pass

        if self.on_state_change_callback:
            try:
                self.on_state_change_callback(self.state)
            except Exception:
                pass

    def toggle_pause(self) -> bool:
        if self.player:
            try:
                cur_pause = getattr(self.player, "pause", False)
                new_pause = not bool(cur_pause)
                self.player.pause = new_pause
                self.state.status = PlaybackStatus.PAUSED if new_pause else PlaybackStatus.PLAYING
                return new_pause
            except Exception:
                pass
        return False

    def toggle_mute(self) -> bool:
        if self.player:
            try:
                cur_mute = getattr(self.player, "mute", False)
                new_mute = not bool(cur_mute)
                self.player.mute = new_mute
                self.state.is_muted = new_mute
                return new_mute
            except Exception:
                pass
        self.state.is_muted = not self.state.is_muted
        return self.state.is_muted

    def set_volume(self, level: int) -> int:
        clamped = max(0, min(100, level))
        self.state.volume = clamped
        if self.player:
            try:
                self.player.volume = clamped
            except Exception:
                pass
        return clamped

    def change_volume(self, delta: int) -> int:
        return self.set_volume(self.state.volume + delta)

    def seek(self, seconds: float, relative: bool = True) -> float:
        if self.player:
            try:
                mode = "relative" if relative else "absolute"
                self.player.seek(seconds, mode)
                time.sleep(0.02)
                pos = getattr(self.player, "time_pos", 0.0)
                if pos is not None:
                    self.state.position = float(pos)
                    return float(pos)
            except Exception:
                pass
        return self.state.position

    def toggle_fullscreen(self) -> bool:
        if self.player:
            try:
                cur_fs = getattr(self.player, "fs", False)
                new_fs = not bool(cur_fs)
                self.player.fs = new_fs
                self.state.is_fullscreen = new_fs
                return new_fs
            except Exception:
                pass
        return False

    def stop(self) -> None:
        """Cleanly terminate playback and release player process/window resources."""
        if self.player:
            try:
                self.player.stop()
            except Exception:
                pass
            try:
                self.player.terminate()
            except Exception:
                pass
            self.player = None

        if self.subprocess_proc and self.subprocess_proc.poll() is None:
            try:
                self.subprocess_proc.terminate()
                self.subprocess_proc.wait(timeout=0.5)
            except Exception:
                pass
            self.subprocess_proc = None

        self.active_media_type = None
        self.state.status = PlaybackStatus.STOPPED
        self.state.position = 0.0

    def terminate(self) -> None:
        self.stop()
