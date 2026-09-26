"""
Terminal Image Renderer Abstraction & Processing Pipeline for Viz Media Center.
Implements capability-aware renderer abstraction (Kitty, Sixel, Truecolor Half-Block, Text Fallback).
Preserves original source image files without modifying or permanently altering them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

from viz.terminal import TerminalManager


class ImageRenderer(ABC):
    """Abstract base class for terminal image renderers."""

    @abstractmethod
    def render(
        self,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        """Render target image file into string for terminal display."""
        pass


class KittyRenderer(ImageRenderer):
    """Kitty graphics protocol renderer fallback."""

    def render(
        self,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        # Fallback to high-quality block renderer within Textual app layout
        return BlockRenderer().render(path, max_w=max_w, max_h=max_h, rotation=rotation, zoom=zoom)


class SixelRenderer(ImageRenderer):
    """Sixel graphics protocol renderer fallback."""

    def render(
        self,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        return BlockRenderer().render(path, max_w=max_w, max_h=max_h, rotation=rotation, zoom=zoom)


class BlockRenderer(ImageRenderer):
    """High-quality truecolor RGB half-block (▀) renderer with aspect ratio preservation."""

    def render(
        self,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        try:
            from PIL import Image
            with Image.open(path) as img:
                # 1. Apply rotation
                if rotation in (90, 180, 270):
                    img = img.rotate(-rotation, expand=True)

                img = img.convert("RGB")
                orig_w, orig_h = img.size

                # 2. Aspect-ratio aware scaling (1 terminal char = ~2 vertical pixels)
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
            return f"     [ IMAGE RENDER ERROR: {err} ]"


class TextFallbackRenderer(ImageRenderer):
    """Textual fallback for low-color environments."""

    def render(
        self,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        return f"[ IMAGE FILE: {path.name} ]\n(Terminal graphics protocol unavailable)"


class ImageHelper:
    """Helper facade delegating to the best terminal-capability-aware image renderer."""

    @classmethod
    def get_renderer(cls) -> ImageRenderer:
        """Select best available renderer based on terminal capability detection."""
        if TerminalManager.supports_kitty_graphics():
            return KittyRenderer()
        elif TerminalManager.supports_sixel():
            return SixelRenderer()
        elif TerminalManager.supports_truecolor():
            return BlockRenderer()
        return TextFallbackRenderer()

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
        """Generate high-quality terminal preview using auto-selected renderer."""
        renderer = cls.get_renderer()
        return renderer.render(path, max_w=max_w, max_h=max_h, rotation=rotation, zoom=zoom)

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
        return cls.generate_rgb_preview(path, max_w=width, max_h=height, rotation=rotation, zoom=zoom)
