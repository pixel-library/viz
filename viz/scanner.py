"""
Non-blocking directory scanner for Viz Media Player.
Scans target media directory recursively for supported video/audio files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, List, Optional, Set

from viz.constants import SUPPORTED_EXTENSIONS
from viz.models import MediaItem


class MediaScanner:
    """
    Scans filesystem directories recursively for supported media items.
    Handles permission errors and nested subdirectories cleanly.
    """

    def __init__(self, supported_extensions: Set[str] = SUPPORTED_EXTENSIONS) -> None:
        self.supported_extensions = {ext.lower() for ext in supported_extensions}

    def scan_directory(
        self,
        directory: Path,
        progress_callback: Optional[Callable[[int, Path], None]] = None,
    ) -> List[MediaItem]:
        """
        Recursively scan target directory for supported files.
        Executes safely with individual file/directory exception handling.
        """
        resolved_dir = directory.expanduser().resolve()
        if not resolved_dir.exists() or not resolved_dir.is_dir():
            return []

        discovered: List[MediaItem] = []
        count = 0

        try:
            # Iterative walk to safely catch permission errors on subdirectories
            for root, dirs, files in os.walk(resolved_dir, followlinks=False):
                # Filter out hidden directories in place
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                root_path = Path(root)
                for filename in files:
                    if filename.startswith("."):
                        continue

                    ext = os.path.splitext(filename)[1].lower()
                    if ext in self.supported_extensions:
                        file_path = root_path / filename
                        media_item = MediaItem.from_file(file_path)
                        if media_item:
                            discovered.append(media_item)
                            count += 1
                            if progress_callback and count % 10 == 0:
                                progress_callback(count, file_path)
        except (PermissionError, OSError) as err:
            print(f"[Scanner Warning] Scan interrupted in {resolved_dir}: {err}")

        # Deterministic sorting by display name
        return sorted(discovered, key=lambda m: m.name.lower())
