"""
Audio Player Facade for Viz Media Center.
Coordinates MPVProcessManager, MPVIPCClient, and Audio playback state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from viz.media.mpv_process import MPVProcessManager
from viz.models import MediaItem, PlaybackState, PlaybackStatus


class MPVAudioPlayer:
    """Facade for managing audio playback using MPV subprocess + JSON IPC."""

    def __init__(self, process_mgr: MPVProcessManager) -> None:
        self.mgr = process_mgr

    def play(self, item: MediaItem, start_position: float = 0.0, volume: int = 80, muted: bool = False) -> bool:
        """Start audio playback for MediaItem."""
        return self.mgr.start_audio_process(
            media_path=item.path,
            volume=volume,
            muted=muted,
            start_position=start_position,
        )

    def sync_to_state(self, state: PlaybackState) -> None:
        """Query real MPV audio state via JSON IPC and update PlaybackState dataclass."""
        if not self.mgr.is_alive():
            state.status = PlaybackStatus.STOPPED
            return

        snapshot = self.mgr.ipc.get_playback_state()

        if snapshot.get("time_pos") is not None:
            state.position = float(snapshot["time_pos"])

        if snapshot.get("duration") is not None:
            state.duration = float(snapshot["duration"])

        if snapshot.get("pause") is not None:
            is_p = bool(snapshot["pause"])
            state.status = PlaybackStatus.PAUSED if is_p else PlaybackStatus.PLAYING

        if snapshot.get("volume") is not None:
            state.volume = int(snapshot["volume"])

        if snapshot.get("mute") is not None:
            state.is_muted = bool(snapshot["mute"])

        if snapshot.get("eof_reached"):
            state.status = PlaybackStatus.ENDED

    def toggle_pause(self) -> Optional[bool]:
        """Toggle play/pause via IPC."""
        return self.mgr.ipc.toggle_pause()

    def seek(self, seconds: float, relative: bool = True) -> Optional[float]:
        """Seek forward/backward."""
        return self.mgr.ipc.seek(seconds, "relative" if relative else "absolute")

    def set_volume(self, level: int) -> int:
        """Set volume."""
        return self.mgr.ipc.set_volume(level)

    def set_mute(self, muted: bool) -> bool:
        """Set mute state."""
        return self.mgr.ipc.set_mute(muted)

    def stop(self) -> None:
        """Stop audio playback process."""
        self.mgr.stop()
