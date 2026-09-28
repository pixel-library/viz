"""
MPV Subprocess Lifecycle Manager for Viz Media Center.
Manages starting, monitoring, verifying, and terminating MPV subprocesses.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from viz.media.mpv_ipc import MPVIPCClient
from viz.media.terminal_graphics import TerminalGraphics


class MPVProcessManager:
    """Manages MPV subprocess lifecycle, socket creation, verification, and termination."""

    def __init__(self) -> None:
        self.proc: Optional[subprocess.Popen] = None
        self.socket_path: str = f"/tmp/viz_mpv_{os.getpid()}.sock"
        self.ipc: MPVIPCClient = MPVIPCClient(self.socket_path)
        self.is_video_mode: bool = False
        self.is_audio_mode: bool = False
        self.active_media_path: Optional[Path] = None

    def start_video_process(self, media_path: Path, volume: int = 80, muted: bool = False, start_position: float = 0.0) -> bool:
        """Start MPV subprocess in Video mode (--vo=kitty,gpu-next,gpu,auto)."""
        self.stop()
        self.active_media_path = media_path
        self.is_video_mode = True
        self.is_audio_mode = False

        self._cleanup_socket()

        # Build MPV command
        vo_mode = "kitty" if TerminalGraphics.is_kitty_supported() else "kitty,gpu-next,gpu,auto"
        cmd = [
            "mpv",
            f"--input-ipc-server={self.socket_path}",
            f"--vo={vo_mode}",
            "--hwdec=auto",
            "--force-window=no",
            "--keep-open=yes",
            f"--title=Viz // {media_path.name}",
            f"--volume={volume}",
        ]
        if muted:
            cmd.append("--mute=yes")
        if start_position > 0.0:
            cmd.append(f"--start={start_position:.2f}")
        cmd.append(str(media_path.resolve()))

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return self._wait_for_ipc()
        except Exception:
            return False

    def start_audio_process(self, media_path: Path, volume: int = 80, muted: bool = False, start_position: float = 0.0) -> bool:
        """Start MPV subprocess in Audio mode (--no-video --vo=null)."""
        self.stop()
        self.active_media_path = media_path
        self.is_video_mode = False
        self.is_audio_mode = True

        self._cleanup_socket()

        cmd = [
            "mpv",
            f"--input-ipc-server={self.socket_path}",
            "--no-video",
            "--vo=null",
            f"--title=Viz // {media_path.name}",
            f"--volume={volume}",
        ]
        if muted:
            cmd.append("--mute=yes")
        if start_position > 0.0:
            cmd.append(f"--start={start_position:.2f}")
        cmd.append(str(media_path.resolve()))

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return self._wait_for_ipc()
        except Exception:
            return False

    def _wait_for_ipc(self, timeout_sec: float = 1.0) -> bool:
        """Wait until the IPC socket is created and MPV process responds."""
        start_t = time.time()
        while time.time() - start_t < timeout_sec:
            if self.proc and self.proc.poll() is not None:
                return False
            if os.path.exists(self.socket_path):
                if self.ipc.is_connected():
                    return True
            time.sleep(0.05)
        return os.path.exists(self.socket_path)

    def is_alive(self) -> bool:
        """Return True if MPV process is alive and responsive."""
        if self.proc and self.proc.poll() is None:
            return True
        return False

    def _cleanup_socket(self) -> None:
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except Exception:
                pass

    def stop(self) -> None:
        """Cleanly quit MPV subprocess and remove temporary socket."""
        TerminalGraphics.clear_graphics()

        if self.proc and self.proc.poll() is None:
            try:
                self.ipc.quit()
            except Exception:
                pass
            try:
                self.proc.terminate()
                self.proc.wait(timeout=0.3)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.proc = None
        self._cleanup_socket()
        self.active_media_path = None
        self.is_video_mode = False
        self.is_audio_mode = False
