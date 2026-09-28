"""
Terminal Image Renderer Pipeline for Viz Media Center.

Implements direct raster pixel rendering:
1. Kitty Graphics Protocol  — full-resolution raster via escape sequences on compatible terminals
2. Native MPV Image Window — high-resolution hardware-accelerated raster window for Linux desktops

All renderers preserve original source files without modification.
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
    """Kitty Graphics Protocol renderer — sends real raster pixels via escape sequences."""

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

                cell_w, cell_h = 8, 16
                target_px_w = int(max_w * cell_w * zoom)
                target_px_h = int(max_h * cell_h * zoom)

                aspect = orig_w / max(1, orig_h)
                fit_w = target_px_w
                fit_h = int(fit_w / aspect)
                if fit_h > target_px_h:
                    fit_h = target_px_h
                    fit_w = int(fit_h * aspect)

                fit_w = max(64, min(fit_w, 4096))
                fit_h = max(64, min(fit_h, 4096))

                resized = img.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

                buf = io.BytesIO()
                resized.save(buf, format="PNG", optimize=True)
                png_data = buf.getvalue()

                b64_data = base64.standard_b64encode(png_data).decode("ascii")
                chunks = [b64_data[i:i + 4096] for i in range(0, len(b64_data), 4096)]
                escape_parts = []
                for idx, chunk in enumerate(chunks):
                    is_last = idx == len(chunks) - 1
                    more = 0 if is_last else 1
                    if idx == 0:
                        escape_parts.append(
                            f"\033_Ga=T,f=100,t=d,m={more},c={max_w},r={max_h};{chunk}\033\\"
                        )
                    else:
                        escape_parts.append(f"\033_Gm={more};{chunk}\033\\")

                return "".join(escape_parts)

        except Exception:
            return ""


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


class ImageHelper:
    """Helper facade delegating to terminal-capability-aware image renderers."""

    @classmethod
    def get_renderer(cls) -> ImageRenderer:
        """Select best available renderer based on terminal capability detection."""
        if TerminalCapabilities.has_kitty_graphics():
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
        """Generate high-quality raster preview if terminal supports Kitty graphics."""
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
        """Open image in a high-resolution native MPV window (for desktop environments)."""
        if not path.exists():
            return False

        if cls._active_proc and cls._active_proc.poll() is None:
            try:
                cls._active_proc.terminate()
            except Exception:
                pass

        try:
            cls._active_proc = subprocess.Popen(
                [
                    "mpv",
                    "--image-display-duration=inf",
                    "--loop-file=inf",
                    "--force-window=yes",
                    "--vo=gpu,gpu-next,auto",
                    "--title=Viz Image Viewer",
                    str(path.resolve()),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass

        return False

