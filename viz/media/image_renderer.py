"""
Terminal Image Renderer for Viz Media Center.
Renders real raster images via Kitty Graphics protocol.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from viz.media.terminal_graphics import TerminalGraphics


class TerminalImageRenderer:
    """Dedicated Terminal Raster Image Renderer."""

    @classmethod
    def is_kitty_supported(cls) -> bool:
        """Return True if Kitty graphics protocol is supported."""
        return TerminalGraphics.is_kitty_supported()

    @classmethod
    def render_image(
        cls,
        image_path: Path,
        max_cols: int = 70,
        max_rows: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        """Render image into Kitty graphics protocol escape sequence or clean fallback message."""
        if not image_path.exists():
            return ""

        if cls.is_kitty_supported():
            return TerminalGraphics.encode_kitty_image(
                image_path,
                max_cols=max_cols,
                max_rows=max_rows,
                rotation=rotation,
                zoom=zoom,
            )

        # Clear error explaining missing Kitty protocol capability without fake text-art
        return "[ Kitty graphics output is unavailable in this terminal session ]"

    @classmethod
    def clear(cls) -> None:
        """Clear active terminal graphics."""
        TerminalGraphics.clear_graphics()
