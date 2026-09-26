"""
Terminal State Manager & Graphics Capability Detection for Viz Media Center.
Detects Kitty Graphics Protocol, Sixel, native rendering tools, and truecolor support.
Provides clean cursor management and emergency exit hooks.
"""

from __future__ import annotations

import atexit
import os
import shutil
import signal
import sys
from pathlib import Path
from typing import Any, Optional


class TerminalCapabilities:
    """Cached terminal graphics capability detection results."""

    _detected: bool = False
    _kitty_graphics: bool = False
    _sixel: bool = False
    _truecolor: bool = False
    _timg_path: Optional[str] = None
    _chafa_path: Optional[str] = None
    _kitty_icat_path: Optional[str] = None
    _display_available: bool = False

    @classmethod
    def detect(cls) -> None:
        """Run full capability detection once, cache results."""
        if cls._detected:
            return

        # Kitty Graphics Protocol detection
        kitty_id = os.getenv("KITTY_WINDOW_ID", "")
        term = os.getenv("TERM", "").lower()
        term_prog = os.getenv("TERM_PROGRAM", "").lower()
        cls._kitty_graphics = bool(kitty_id) or "kitty" in term or "kitty" in term_prog

        # Sixel detection
        cls._sixel = term_prog in ("foot", "mlterm", "yaft", "wezterm", "contour") or "sixel" in term

        # Truecolor detection
        colorterm = os.getenv("COLORTERM", "").lower()
        cls._truecolor = colorterm in ("truecolor", "24bit") or cls._kitty_graphics

        # Display server availability (needed for native MPV window)
        cls._display_available = bool(os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"))

        # Discover native image rendering tools
        cls._timg_path = shutil.which("timg")
        cls._chafa_path = shutil.which("chafa")
        kitty_bin = shutil.which("kitty")
        if kitty_bin:
            icat_path = Path(kitty_bin).parent / "kitten"
            if icat_path.exists():
                cls._kitty_icat_path = str(icat_path)

        cls._detected = True

    @classmethod
    def has_kitty_graphics(cls) -> bool:
        cls.detect()
        return cls._kitty_graphics

    @classmethod
    def has_sixel(cls) -> bool:
        cls.detect()
        return cls._sixel

    @classmethod
    def has_truecolor(cls) -> bool:
        cls.detect()
        return cls._truecolor

    @classmethod
    def has_display(cls) -> bool:
        cls.detect()
        return cls._display_available

    @classmethod
    def get_timg_path(cls) -> Optional[str]:
        cls.detect()
        return cls._timg_path

    @classmethod
    def get_chafa_path(cls) -> Optional[str]:
        cls.detect()
        return cls._chafa_path

    @classmethod
    def best_image_method(cls) -> str:
        """Return the best available image rendering method string.

        Returns one of: 'kitty', 'sixel', 'timg', 'chafa', 'block', 'text'
        """
        cls.detect()
        if cls._kitty_graphics:
            return "kitty"
        if cls._sixel:
            return "sixel"
        if cls._timg_path:
            return "timg"
        if cls._chafa_path:
            return "chafa"
        if cls._truecolor:
            return "block"
        return "text"


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

        # Run capability detection at startup
        TerminalCapabilities.detect()
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

    # Backward-compatible static methods
    @staticmethod
    def supports_kitty_graphics() -> bool:
        return TerminalCapabilities.has_kitty_graphics()

    @staticmethod
    def supports_sixel() -> bool:
        return TerminalCapabilities.has_sixel()

    @staticmethod
    def supports_truecolor() -> bool:
        return TerminalCapabilities.has_truecolor()
