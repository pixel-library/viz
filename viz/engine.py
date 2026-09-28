"""
Direct High-Performance Media Engine for Viz Terminal Media Center.
Coordinates native MPV playback via IPC socket process management and python-mpv fallback.

Provides distinct playback modes for:
- Video Virtual Environment: Hardware-accelerated GPU window (vo=gpu,gpu-next,auto / hwdec=auto)
- Audio Virtual Environment: High-fidelity audio playback without video window (vo=null / system default AO)
- Image Virtual Environment: High-resolution native display window (--image-display-duration=inf)
"""

from __future__ import annotations

import json
import os
import socket
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
    Manages player process lifecycle, real playback, seeking, volume, IPC socket sync, and event state.
    """

    def __init__(self, initial_volume: int = 80, initial_muted: bool = False) -> None:
        self.player: Optional[object] = None
        self.subprocess_proc: Optional[subprocess.Popen] = None
        self.ipc_socket_path: str = f"/tmp/viz_mpv_{os.getpid()}.sock"
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

    def _send_ipc_cmd(self, command: list) -> Optional[dict]:
        """Send JSON-IPC command to active MPV process socket."""
        if not os.path.exists(self.ipc_socket_path):
            return None
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.3)
            client.connect(self.ipc_socket_path)
            msg = json.dumps({"command": command}) + "\n"
            client.sendall(msg.encode("utf-8"))
            buf = b""
            while b"\n" not in buf:
                chunk = client.recv(1024)
                if not chunk:
                    break
                buf += chunk
            client.close()
            if buf:
                lines = buf.decode("utf-8", errors="replace").split("\n")
                for line in lines:
                    if line.strip():
                        data = json.loads(line)
                        if "error" in data:
                            return data
        except Exception:
            pass
        return None

    def play_video(self, media_item: MediaItem, start_position: float = 0.0) -> bool:
        """Play video in hardware-accelerated native MPV window."""
        self.stop()
        abs_path = str(media_item.path.resolve())

        # Cleanup socket file if left over
        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except Exception:
                pass

        cmd = [
            "mpv",
            f"--input-ipc-server={self.ipc_socket_path}",
            "--force-window=yes",
            "--vo=gpu,gpu-next,auto",
            "--hwdec=auto",
            "--keep-open=yes",
            f"--title=Viz // {media_item.name}",
            f"--volume={self.state.volume}",
        ]
        if self.state.is_muted:
            cmd.append("--mute=yes")
        if start_position > 0.0:
            cmd.append(f"--start={start_position:.2f}")
        cmd.append(abs_path)

        try:
            self.subprocess_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.active_media_type = MediaType.VIDEO
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING
            self.state.position = start_position

            # Wait briefly for socket creation
            for _ in range(10):
                if os.path.exists(self.ipc_socket_path):
                    break
                time.sleep(0.05)

            self.sync_state()
            return True
        except Exception as err:
            self.state.status = PlaybackStatus.ERROR
            self.state.error_message = f"Failed to start video player process: {err}"
            return False

    def play_audio(self, media_item: MediaItem, start_position: float = 0.0) -> bool:
        """Play audio using MPV engine without video window (vo=null)."""
        self.stop()
        abs_path = str(media_item.path.resolve())

        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except Exception:
                pass

        cmd = [
            "mpv",
            f"--input-ipc-server={self.ipc_socket_path}",
            "--no-video",
            "--vo=null",
            f"--title=Viz // {media_item.name}",
            f"--volume={self.state.volume}",
        ]
        if self.state.is_muted:
            cmd.append("--mute=yes")
        if start_position > 0.0:
            cmd.append(f"--start={start_position:.2f}")
        cmd.append(abs_path)

        try:
            self.subprocess_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.active_media_type = MediaType.AUDIO
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING
            self.state.position = start_position

            for _ in range(10):
                if os.path.exists(self.ipc_socket_path):
                    break
                time.sleep(0.05)

            self.sync_state()
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

        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except Exception:
                pass

        cmd = [
            "mpv",
            f"--input-ipc-server={self.ipc_socket_path}",
            "--image-display-duration=inf",
            "--loop-file=inf",
            "--force-window=yes",
            "--vo=gpu,gpu-next,auto",
            f"--title=Viz // {media_item.name}",
            abs_path,
        ]

        try:
            self.subprocess_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.active_media_type = MediaType.IMAGE
            self.state.current_media = media_item
            self.state.status = PlaybackStatus.PLAYING

            for _ in range(10):
                if os.path.exists(self.ipc_socket_path):
                    break
                time.sleep(0.05)

            return True
        except Exception:
            return False

    def sync_state(self) -> None:
        """Query real properties from MPV instance via IPC socket and update PlaybackState."""
        if self.subprocess_proc and self.subprocess_proc.poll() is not None:
            self.state.status = PlaybackStatus.STOPPED
            if self.on_state_change_callback:
                try:
                    self.on_state_change_callback(self.state)
                except Exception:
                    pass
            return

        if not os.path.exists(self.ipc_socket_path):
            return

        pos_resp = self._send_ipc_cmd(["get_property", "time-pos"])
        if pos_resp and "data" in pos_resp and pos_resp["data"] is not None:
            self.state.position = float(pos_resp["data"])

        dur_resp = self._send_ipc_cmd(["get_property", "duration"])
        if dur_resp and "data" in dur_resp and dur_resp["data"] is not None:
            self.state.duration = float(dur_resp["data"])

        pause_resp = self._send_ipc_cmd(["get_property", "pause"])
        if pause_resp and "data" in pause_resp and pause_resp["data"] is not None:
            is_p = bool(pause_resp["data"])
            self.state.status = PlaybackStatus.PAUSED if is_p else PlaybackStatus.PLAYING

        vol_resp = self._send_ipc_cmd(["get_property", "volume"])
        if vol_resp and "data" in vol_resp and vol_resp["data"] is not None:
            self.state.volume = int(vol_resp["data"])

        mute_resp = self._send_ipc_cmd(["get_property", "mute"])
        if mute_resp and "data" in mute_resp and mute_resp["data"] is not None:
            self.state.is_muted = bool(mute_resp["data"])

        eof_resp = self._send_ipc_cmd(["get_property", "eof-reached"])
        if eof_resp and "data" in eof_resp and eof_resp["data"]:
            self.state.status = PlaybackStatus.ENDED

        if self.on_state_change_callback:
            try:
                self.on_state_change_callback(self.state)
            except Exception:
                pass

    def toggle_pause(self) -> bool:
        if self.subprocess_proc and self.subprocess_proc.poll() is None:
            cur_pause = (self.state.status == PlaybackStatus.PAUSED)
            new_pause = not cur_pause
            self._send_ipc_cmd(["set_property", "pause", new_pause])
            self.state.status = PlaybackStatus.PAUSED if new_pause else PlaybackStatus.PLAYING
            return new_pause
        return False

    def toggle_mute(self) -> bool:
        if self.subprocess_proc and self.subprocess_proc.poll() is None:
            new_mute = not self.state.is_muted
            self._send_ipc_cmd(["set_property", "mute", new_mute])
            self.state.is_muted = new_mute
            return new_mute
        self.state.is_muted = not self.state.is_muted
        return self.state.is_muted

    def set_volume(self, level: int) -> int:
        clamped = max(0, min(100, level))
        self.state.volume = clamped
        if self.subprocess_proc and self.subprocess_proc.poll() is None:
            self._send_ipc_cmd(["set_property", "volume", clamped])
        return clamped

    def change_volume(self, delta: int) -> int:
        return self.set_volume(self.state.volume + delta)

    def seek(self, seconds: float, relative: bool = True) -> float:
        if self.subprocess_proc and self.subprocess_proc.poll() is None:
            mode = "relative" if relative else "absolute"
            self._send_ipc_cmd(["seek", seconds, mode])
            time.sleep(0.02)
            self.sync_state()
        return self.state.position

    def toggle_fullscreen(self) -> bool:
        if self.subprocess_proc and self.subprocess_proc.poll() is None:
            self._send_ipc_cmd(["cycle", "fullscreen"])
            self.state.is_fullscreen = not self.state.is_fullscreen
            return self.state.is_fullscreen
        return False

    def stop(self) -> None:
        """Cleanly terminate playback and release player process/window resources."""
        if self.subprocess_proc and self.subprocess_proc.poll() is None:
            try:
                self._send_ipc_cmd(["quit"])
            except Exception:
                pass
            try:
                self.subprocess_proc.terminate()
                self.subprocess_proc.wait(timeout=0.3)
            except Exception:
                pass
        self.subprocess_proc = None

        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except Exception:
                pass

        self.active_media_type = None
        self.state.status = PlaybackStatus.STOPPED
        self.state.position = 0.0

    def terminate(self) -> None:
        self.stop()

