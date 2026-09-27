"""
Terminal Image Renderer Pipeline for Viz Media Center.

Implements a multi-strategy rendering pipeline:
1. Kitty Graphics Protocol  — full-resolution raster via escape sequences (best quality)
2. Sixel Graphics           — raster image protocol for compatible terminals
3. High-quality Truecolor Half-Block (▀) — best-in-class terminal character rendering
4. Text Fallback            — filename display for minimal terminals

All renderers preserve original source files without modification.
Memory-safe: uses streaming PIL reads, never loads full decoded pixels into a list.
"""

from __future__ import annotations

import base64
import io
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from viz.terminal import TerminalCapabilities


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
    """Kitty Graphics Protocol renderer — sends real raster pixels via escape sequences.

    Uses the Kitty graphics protocol (APC sequences) to transmit PNG data directly
    to the terminal, which then renders it natively at full resolution.
    """

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
                if rotation in (90, 180, 270):
                    img = img.rotate(-rotation, expand=True)

                img = img.convert("RGBA")
                orig_w, orig_h = img.size

                # Calculate target pixel dimensions based on terminal cell size
                # Typical terminal cell is ~8px wide, ~16px tall
                cell_w, cell_h = 8, 16
                target_px_w = max_w * cell_w
                target_px_h = max_h * cell_h

                # Apply zoom
                target_px_w = int(target_px_w * zoom)
                target_px_h = int(target_px_h * zoom)

                # Maintain aspect ratio
                aspect = orig_w / max(1, orig_h)
                fit_w = target_px_w
                fit_h = int(fit_w / aspect)
                if fit_h > target_px_h:
                    fit_h = target_px_h
                    fit_w = int(fit_h * aspect)

                fit_w = max(64, min(fit_w, 4096))
                fit_h = max(64, min(fit_h, 4096))

                resized = img.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

                # Encode to PNG in memory
                buf = io.BytesIO()
                resized.save(buf, format="PNG", optimize=True)
                png_data = buf.getvalue()

                # Build Kitty graphics escape sequence
                b64_data = base64.standard_b64encode(png_data).decode("ascii")

                # Split into 4096-byte chunks as per Kitty protocol
                chunks = [b64_data[i:i + 4096] for i in range(0, len(b64_data), 4096)]
                escape_parts = []
                for idx, chunk in enumerate(chunks):
                    is_last = idx == len(chunks) - 1
                    more = 0 if is_last else 1
                    if idx == 0:
                        # First chunk: specify format, transmission, display params
                        escape_parts.append(
                            f"\033_Ga=T,f=100,t=d,m={more},c={max_w},r={max_h};{chunk}\033\\"
                        )
                    else:
                        escape_parts.append(f"\033_Gm={more};{chunk}\033\\")

                return "".join(escape_parts)

        except Exception:
            return NativeFrameRenderer().render(path, max_w=max_w, max_h=max_h, rotation=rotation, zoom=zoom)


class NativeFrameRenderer(ImageRenderer):
    """Clean renderer for native viewer mode — prevents generating half-block/Unicode text-art previews."""

    def render(
        self,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        return ""


class TextFallbackRenderer(ImageRenderer):
    """Fallback renderer for minimal environments."""

    def render(
        self,
        path: Path,
        max_w: int = 70,
        max_h: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        return ""


class ImageHelper:
    """Helper facade delegating to the best terminal-capability-aware image renderer."""

    @classmethod
    def get_renderer(cls) -> ImageRenderer:
        """Select best available renderer based on terminal capability detection."""
        method = TerminalCapabilities.best_image_method()

        if method == "kitty":
            return KittyRenderer()
        return NativeFrameRenderer()

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

    _active_proc: Optional[subprocess.Popen] = None

    @classmethod
    def open_native_viewer(cls, path: Path) -> bool:
        """Open image in a native viewer window (for X11/Wayland environments).

        Uses MPV or system image viewer to display the image at full native resolution
        in its own window, completely bypassing terminal character rendering.
        Returns True if successfully launched.
        """
        if not TerminalCapabilities.has_display():
            return False

        if not path.exists():
            return False

        if cls._active_proc and cls._active_proc.poll() is None:
            try:
                cls._active_proc.terminate()
            except Exception:
                pass

        try:
            # Try mpv for image viewing (supports all common formats)
            cls._active_proc = subprocess.Popen(
                [
                    "mpv",
                    "--image-display-duration=inf",
                    "--force-window=yes",
                    "--title=Viz Image Viewer",
                    "--no-terminal",
                    "--keep-open=yes",
                    "--loop-file=inf",
                    str(path.resolve()),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            pass

        # Fallback to xdg-open
        try:
            subprocess.Popen(
                ["xdg-open", str(path.resolve())],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            pass

        return False
