"""
Image Processing & Terminal RGB Pixel Art Helper for Viz Media Center.
Uses Pillow and Rich markup to render full-color image previews inside terminal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple


class ImageHelper:
    """Provides Pillow-based image metadata and terminal RGB pixel art preview generation."""

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
    def generate_rgb_preview(
        cls,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        """
        Generate full-color RGB terminal preview using half-block characters (▀).
        Supports rotation (0, 90, 180, 270 degrees) and zoom scaling while maintaining aspect ratio.
        """
        try:
            from PIL import Image
            with Image.open(path) as img:
                # 1. Apply rotation
                if rotation in (90, 180, 270):
                    img = img.rotate(-rotation, expand=True)

                img = img.convert("RGB")
                orig_w, orig_h = img.size

                # 2. Calculate aspect-ratio aware target dimensions
                # Terminal aspect ratio compensation: 1 char is ~ 2 vertical pixels high
                aspect = orig_w / max(1, orig_h)
                eff_max_w = max(10, int(max_w * zoom))
                eff_max_h = max(5, int(max_h * zoom))

                target_w = eff_max_w
                target_h = int(target_w / (aspect * 2.0))

                if target_h > eff_max_h:
                    target_h = eff_max_h
                    target_w = int(target_h * aspect * 2.0)

                target_w = max(8, target_w)
                target_h = max(4, target_h)

                # Resize image: width = target_w, height = target_h * 2 (top and bottom half pixels)
                pixel_h = target_h * 2
                resized = img.resize((target_w, pixel_h), Image.Resampling.BILINEAR)

                lines = []
                for y in range(0, pixel_h - 1, 2):
                    line_parts = []
                    for x in range(target_w):
                        top_r, top_g, top_b = resized.getpixel((x, y))
                        bot_r, bot_g, bot_b = resized.getpixel((x, y + 1))

                        fg_hex = f"{top_r:02x}{top_g:02x}{top_b:02x}"
                        bg_hex = f"{bot_r:02x}{bot_g:02x}{bot_b:02x}"
                        line_parts.append(f"[#{fg_hex} on #{bg_hex}]▀[/]")
                    lines.append("".join(line_parts))

                return "\n".join(lines)
        except Exception as err:
            return f"     [ IMAGE PREVIEW ERROR: {err} ]"

    @classmethod
    def generate_ascii_preview(
        cls,
        path: Path,
        width: int = 48,
        height: int = 18,
        use_blocks: bool = True,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        """Compatibility wrapper delegating to RGB half-block renderer."""
        return cls.generate_rgb_preview(path, max_w=width, max_h=height, rotation=rotation, zoom=zoom)


