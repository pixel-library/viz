"""
Terminal Graphics & Capability Detection Module for Viz Media Center.
Manages Kitty graphics protocol transmission, clearing escape sequences, and terminal state.
"""

from __future__ import annotations

import base64
import io
import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple


class TerminalGraphics:
    """Manages terminal graphics capabilities and Kitty escape sequences."""

    _kitty_supported: Optional[bool] = None

    @classmethod
    def is_kitty_supported(cls) -> bool:
        """Detect if active terminal supports Kitty graphics protocol."""
        if cls._kitty_supported is not None:
            return cls._kitty_supported

        kitty_id = os.getenv("KITTY_WINDOW_ID", "")
        term = os.getenv("TERM", "").lower()
        term_prog = os.getenv("TERM_PROGRAM", "").lower()

        cls._kitty_supported = bool(kitty_id) or "kitty" in term or "kitty" in term_prog
        return cls._kitty_supported

    @classmethod
    def clear_graphics(cls) -> None:
        """Send Kitty graphics protocol clear sequence to remove screen images/video frames."""
        try:
            # Delete all Kitty graphics from screen
            sys.stdout.write("\033_Ga=d\033\\")
            sys.stdout.flush()
        except Exception:
            pass

    @classmethod
    def encode_kitty_image(
        cls,
        image_path: Path,
        max_cols: int = 70,
        max_rows: int = 22,
        rotation: int = 0,
        zoom: float = 1.0,
    ) -> str:
        """Encode image file into Kitty graphics protocol escape sequence string."""
        if not image_path.exists():
            return ""

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                if rotation in (90, 180, 270):
                    img = img.rotate(-rotation, expand=True)

                img = img.convert("RGBA")
                orig_w, orig_h = img.size

                cell_w, cell_h = 8, 16
                target_px_w = int(max_cols * cell_w * zoom)
                target_px_h = int(max_rows * cell_h * zoom)

                aspect = orig_w / max(1, orig_h)
                fit_w = target_px_w
                fit_h = int(fit_w / aspect)
                if fit_h > target_px_h:
                    fit_h = target_px_h
                    fit_w = int(fit_h * aspect)

                fit_w = max(32, min(fit_w, 4096))
                fit_h = max(32, min(fit_h, 4096))

                resized = img.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

                buf = io.BytesIO()
                resized.save(buf, format="PNG", optimize=True)
                png_bytes = buf.getvalue()

                b64_str = base64.standard_b64encode(png_bytes).decode("ascii")
                chunks = [b64_str[i:i + 4096] for i in range(0, len(b64_str), 4096)]

                parts = []
                for idx, chunk in enumerate(chunks):
                    more = 0 if idx == len(chunks) - 1 else 1
                    if idx == 0:
                        parts.append(
                            f"\033_Ga=T,f=100,t=d,m={more},c={max_cols},r={max_rows};{chunk}\033\\"
                        )
                    else:
                        parts.append(f"\033_Gm={more};{chunk}\033\\")

                return "".join(parts)
        except Exception:
            return ""
