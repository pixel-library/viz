"""
Async Media Engine Wrapper for MPV & Simulation Fallback Mode.
Handles playback, volume adjustment, seeking, track switching, and audio status.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

HAS_MPV = False
MPV_ERROR_MSG = ""
try:
    import mpv
    HAS_MPV = True
except Exception as e:
    HAS_MPV = False
    MPV_ERROR_MSG = str(e)


@dataclass
class PlaybackState:
    file_path: Optional[Path] = None
    title: str = "No Media Loaded"
    is_playing: bool = False
    is_paused: bool = False
    is_muted: bool = False
    duration: float = 0.0
    position: float = 0.0
    volume: int = 80
    audio_track: int = 1
    sub_track: int = 0


class MediaEngine:
    """
    Asynchronous wrapper for MPV media engine with fallback simulation support.
    Manages non-blocking calls to python-mpv.
    """

    def __init__(self, initial_volume: int = 80) -> None:
        self.mpv_instance = None
        self.using_mpv = False
        self.state = PlaybackState(volume=initial_volume)
        self.init_error: Optional[str] = None

        if HAS_MPV:
            try:
                self.mpv_instance = mpv.MPV(
                    video=True,
                    keep_open=True,
                    input_default_key_bindings=False,
                    osc=True,
                    volume=initial_volume,
                    title="Viz Media Output",
                )
                self.using_mpv = True
            except Exception as err:
                self.using_mpv = False
                self.init_error = f"libmpv init warning: {err}"
        else:
            self.init_error = MPV_ERROR_MSG or "python-mpv package or libmpv library not installed."

    def play_file(self, file_path: Path) -> None:
        """Trigger media playback for the specified path."""
        self.state.file_path = file_path
        self.state.title = file_path.name
        self.state.is_playing = True
        self.state.is_paused = False
        self.state.position = 0.0

        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.play(str(file_path.resolve()))
                dur = getattr(self.mpv_instance, "duration", None)
                if dur:
                    self.state.duration = float(dur)
                else:
                    self.state.duration = 180.0
            except Exception as e:
                print(f"[MPV Error] Failed to play {file_path}: {e}")
        else:
            self.state.duration = 240.0 if file_path.suffix.lower() in [".mp4", ".mkv"] else 180.0

    def toggle_pause(self) -> bool:
        """Toggle pause/play state."""
        if not self.state.is_playing:
            return False
        
        self.state.is_paused = not self.state.is_paused
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.pause = self.state.is_paused
            except Exception:
                pass
        return self.state.is_paused

    def toggle_mute(self) -> bool:
        """Toggle mute state."""
        self.state.is_muted = not self.state.is_muted
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.mute = self.state.is_muted
            except Exception:
                pass
        return self.state.is_muted

    def set_volume(self, level: int) -> int:
        """Set volume percentage (0-100)."""
        level = max(0, min(100, level))
        self.state.volume = level
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.volume = level
            except Exception:
                pass
        return level

    def change_volume(self, delta: int) -> int:
        """Change volume relative by delta."""
        return self.set_volume(self.state.volume + delta)

    def seek(self, seconds: float) -> float:
        """Seek relative seconds."""
        if not self.state.is_playing:
            return 0.0
        
        new_pos = max(0.0, min(self.state.duration, self.state.position + seconds))
        self.state.position = new_pos

        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.seek(seconds, reference="relative")
            except Exception:
                pass
        return new_pos

    def cycle_audio_track(self) -> int:
        """Cycle audio track stream."""
        self.state.audio_track = (self.state.audio_track % 3) + 1
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.aid = self.state.audio_track
            except Exception:
                pass
        return self.state.audio_track

    def cycle_sub_track(self) -> int:
        """Cycle subtitle track stream."""
        self.state.sub_track = (self.state.sub_track + 1) % 4
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.sid = "no" if self.state.sub_track == 0 else self.state.sub_track
            except Exception:
                pass
        return self.state.sub_track

    def update_position(self) -> PlaybackState:
        """Periodically sync state from MPV or simulate progress."""
        if self.using_mpv and self.mpv_instance and self.state.is_playing:
            try:
                pos = getattr(self.mpv_instance, "time_pos", None)
                if pos is not None:
                    self.state.position = float(pos)
                dur = getattr(self.mpv_instance, "duration", None)
                if dur is not None:
                    self.state.duration = float(dur)
                self.state.is_paused = bool(getattr(self.mpv_instance, "pause", False))
                self.state.is_muted = bool(getattr(self.mpv_instance, "mute", False))
            except Exception:
                pass
        elif self.state.is_playing and not self.state.is_paused:
            self.state.position += 1.0
            if self.state.position >= self.state.duration:
                self.state.position = self.state.duration

        return self.state

    def stop(self) -> None:
        """Stop playback and cleanup."""
        self.state.is_playing = False
        self.state.is_paused = False
        if self.using_mpv and self.mpv_instance:
            try:
                self.mpv_instance.stop()
                self.mpv_instance.terminate()
            except Exception:
                pass
