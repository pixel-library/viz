"""
MPV JSON-IPC Protocol Client for Viz Media Center.
Sends structured JSON-IPC commands over Unix domain sockets to control MPV process.
"""

from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from typing import Any, Dict, Optional, List


class MPVIPCClient:
    """Robust JSON-IPC Client for controlling MPV subprocess via socket."""

    def __init__(self, socket_path: str) -> None:
        self.socket_path = socket_path

    def is_connected(self) -> bool:
        """Check if socket file exists and responds to ping."""
        if not os.path.exists(self.socket_path):
            return False
        res = self.send_command(["get_property", "idle"])
        return res is not None

    def send_command(self, command: List[Any], request_id: int = 1) -> Optional[Dict[str, Any]]:
        """Send a JSON IPC command array to the MPV socket and parse response."""
        if not os.path.exists(self.socket_path):
            return None

        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.3)
            client.connect(self.socket_path)

            payload = json.dumps({"command": command, "request_id": request_id}) + "\n"
            client.sendall(payload.encode("utf-8"))

            buf = b""
            while b"\n" not in buf:
                chunk = client.recv(2048)
                if not chunk:
                    break
                buf += chunk

            client.close()

            if buf:
                lines = buf.decode("utf-8", errors="replace").split("\n")
                for line in lines:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        if "error" in data:
                            return data
        except Exception:
            pass
        return None

    def load_file(self, path: Path) -> bool:
        """Load target media file into MPV."""
        res = self.send_command(["loadfile", str(path.resolve())])
        return res is not None and res.get("error") == "success"

    def play(self) -> bool:
        """Resume playback."""
        res = self.send_command(["set_property", "pause", False])
        return res is not None and res.get("error") == "success"

    def pause(self) -> bool:
        """Pause playback."""
        res = self.send_command(["set_property", "pause", True])
        return res is not None and res.get("error") == "success"

    def toggle_pause(self) -> Optional[bool]:
        """Toggle pause state and return new state."""
        cur_pause = self.get_property("pause")
        if cur_pause is not None:
            new_pause = not bool(cur_pause)
            self.send_command(["set_property", "pause", new_pause])
            return new_pause
        return None

    def seek(self, seconds: float, mode: str = "relative") -> Optional[float]:
        """Seek forward or backward by seconds."""
        self.send_command(["seek", seconds, mode])
        time.sleep(0.02)
        pos = self.get_property("time-pos")
        return float(pos) if pos is not None else None

    def set_volume(self, level: int) -> int:
        """Set volume level (0-100)."""
        clamped = max(0, min(100, level))
        self.send_command(["set_property", "volume", clamped])
        return clamped

    def set_mute(self, muted: bool) -> bool:
        """Set mute state."""
        self.send_command(["set_property", "mute", muted])
        return muted

    def toggle_fullscreen(self) -> bool:
        """Toggle fullscreen mode."""
        self.send_command(["cycle", "fullscreen"])
        fs = self.get_property("fullscreen")
        return bool(fs) if fs is not None else False

    def get_property(self, prop_name: str) -> Any:
        """Query property value from MPV via JSON IPC."""
        res = self.send_command(["get_property", prop_name])
        if res and res.get("error") == "success":
            return res.get("data")
        return None

    def get_playback_state(self) -> Dict[str, Any]:
        """Query comprehensive playback status snapshot."""
        return {
            "time_pos": self.get_property("time-pos"),
            "duration": self.get_property("duration"),
            "pause": self.get_property("pause"),
            "volume": self.get_property("volume"),
            "mute": self.get_property("mute"),
            "fullscreen": self.get_property("fullscreen"),
            "filename": self.get_property("filename"),
            "width": self.get_property("width"),
            "height": self.get_property("height"),
            "video_format": self.get_property("video-format"),
            "eof_reached": self.get_property("eof-reached"),
        }

    def quit(self) -> None:
        """Send quit command to MPV process."""
        self.send_command(["quit"])
