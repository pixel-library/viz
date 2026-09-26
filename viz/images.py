"""
Image Processing & ASCII Preview Helper for Viz Media Center.
Uses Pillow to extract image metadata and generate clean terminal ASCII previews.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple


class ImageHelper:
    """Provides Pillow-based image metadata and terminal preview generation."""

    ASCII_CHARS = " .:-=+*#%@"

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
    def generate_ascii_preview(cls, path: Path, width: int = 40, height: int = 15) -> str:
        """Generate high-contrast ASCII art preview of an image for terminal display."""
        try:
            from PIL import Image
            with Image.open(path) as img:
                img = img.convert("L")
                img = img.resize((width, height))
                pixels = img.getdata()

                lines = []
                for i in range(0, len(pixels), width):
                    row = pixels[i : i + width]
                    line = "".join(cls.ASCII_CHARS[pixel * (len(cls.ASCII_CHARS) - 1) // 255] for pixel in row)
                    lines.append(line)
                return "\n".join(lines)
        except Exception:
            return "     [ IMAGE PREVIEW UNAVAILABLE ]"
