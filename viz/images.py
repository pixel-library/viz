"""
Image Processing & Terminal Art Helper for Viz Media Center.
Uses Pillow to extract image metadata and generate clean terminal pixel art previews.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple


class ImageHelper:
    """Provides Pillow-based image metadata and terminal art preview generation."""

    ASCII_CHARS = " .:-=+*#%@"
    BLOCK_CHARS = "  ░▒▓█"

    @classmethod
    def get_image_dimensions(cls, path: Path) -> Tuple[int, int, str]:
        """Return (width, height, format) for an image file."""
        try:
            from PIL import Image
            with Image.open(path) as img:
                return img.width, img.height, img.format or path.suffix.lstrip(".").upper()
        except Exception:
            return 0, 0, path.suffix.lstrip(".").upper()

    @classmethod
    def generate_ascii_preview(
        cls,
        path: Path,
        width: int = 48,
        height: int = 18,
        use_blocks: bool = True,
    ) -> str:
        """Generate high-contrast pixel art preview of an image for terminal display."""
        try:
            from PIL import Image
            with Image.open(path) as img:
                img = img.convert("L")
                img = img.resize((max(10, width), max(5, height)))
                pixels = img.getdata()

                chars = cls.BLOCK_CHARS if use_blocks else cls.ASCII_CHARS
                lines = []
                for i in range(0, len(pixels), width):
                    row = pixels[i : i + width]
                    line = "".join(chars[pixel * (len(chars) - 1) // 255] for pixel in row)
                    lines.append(line)
                return "\n".join(lines)
        except Exception:
            return "     [ IMAGE PREVIEW UNAVAILABLE ]"

