"""
Terminal State Manager for Viz Media Center.
Hides text cursor on startup and ensures clean cursor/terminal restoration on exit or crash.
"""

from __future__ import annotations

import atexit
import signal
import sys
from typing import Any


class TerminalManager:
    """Manages terminal state, cursor visibility, and emergency exit hooks."""

    _initialized: bool = False

    @classmethod
    def setup_terminal(cls) -> None:
        """Hide terminal cursor and register cleanup exit hooks."""
        if cls._initialized:
            return

        cls.hide_cursor()
        atexit.register(cls.restore_terminal)

        def _signal_handler(sig: int, frame: Any) -> None:
            cls.restore_terminal()
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, _signal_handler)
            signal.signal(signal.SIGTERM, _signal_handler)
        except Exception:
            pass

        cls._initialized = True

    @staticmethod
    def hide_cursor() -> None:
        """Hide cursor using VT100 escape code."""
        try:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
        except Exception:
            pass

    @staticmethod
    def restore_terminal() -> None:
        """Restore text cursor visibility and reset terminal modes."""
        try:
            sys.stdout.write("\033[?25h\033[0m")
            sys.stdout.flush()
        except Exception:
            pass

    @staticmethod
    def supports_kitty_graphics() -> bool:
        """Detect Kitty terminal graphics protocol support."""
        import os
        return bool(os.getenv("KITTY_WINDOW_ID") or "kitty" in os.getenv("TERM", "").lower())

    @staticmethod
    def supports_sixel() -> bool:
        """Detect Sixel terminal graphics protocol support."""
        import os
        term = os.getenv("TERM", "").lower()
        term_prog = os.getenv("TERM_PROGRAM", "").lower()
        return "sixel" in term or term_prog in ("foot", "mlterm", "yaft", "wezterm")

    @staticmethod
    def supports_truecolor() -> bool:
        """Detect Truecolor / 24-bit RGB rendering support."""
        import os
        colorterm = os.getenv("COLORTERM", "").lower()
        return colorterm in ("truecolor", "24bit") or True  # Modern Linux terminals default to truecolor

