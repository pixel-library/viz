"""
Pure Native MPV Engine for Viz Media Player.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import mpv


class MediaEngine:
    """Pure native python-mpv player wrapper."""

    def __init__(self) -> None:
        self.player = mpv.MPV(
            keep_open=True,
            osc=True,
            title="Viz Media Output",
        )
        self.current_file: Optional[Path] = None

    def play_file(self, file_path: Path) -> None:
        self.current_file = file_path
        self.player.play(str(file_path.resolve()))

    def toggle_pause(self) -> bool:
        self.player.pause = not self.player.pause
        return bool(self.player.pause)

    def toggle_mute(self) -> bool:
        self.player.mute = not self.player.mute
        return bool(self.player.mute)

    def seek(self, seconds: float) -> None:
        self.player.seek(seconds, reference="relative")

    def stop(self) -> None:
        try:
            self.player.stop()
            self.player.terminate()
        except Exception:
            pass
