"""
Mounted Storage Discovery Module for Viz Media Center.
Discovers accessible mounted secondary storage volumes on Linux and macOS.
"""

from __future__ import annotations

import getpass
import os
from pathlib import Path
import shutil
from typing import List, Tuple


class MountsManager:
    """Discovers accessible mounted storage volumes on Linux and macOS."""

    @classmethod
    def get_accessible_mounts(cls) -> List[Tuple[Path, str]]:
        """
        Discover accessible mounted storage directories for the current user.
        Returns a list of (mount_path, display_label) tuples.
        """
        user = getpass.getuser()
        candidates = [
            Path(f"/run/media/{user}"),
            Path(f"/media/{user}"),
            Path("/Volumes"),
            Path("/mnt"),
        ]

        discovered: List[Tuple[Path, str]] = []
        seen_paths = set()

        for base in candidates:
            if not base.exists() or not base.is_dir():
                continue

            try:
                for entry in base.iterdir():
                    try:
                        resolved = entry.resolve()
                        if not entry.is_dir() or resolved in seen_paths:
                            continue

                        # Check read permission
                        if not os.access(resolved, os.R_OK):
                            continue

                        # Filter out root filesystem mount loops if any
                        if resolved == Path("/"):
                            continue

                        seen_paths.add(resolved)
                        label = cls._get_volume_label(resolved)
                        discovered.append((resolved, label))
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                continue

        return discovered

    @classmethod
    def _get_volume_label(cls, path: Path) -> str:
        """Calculate human-readable label with disk size for a mounted volume."""
        try:
            usage = shutil.disk_usage(path)
            total_gb = int(usage.total / (1024 ** 3))
            if total_gb > 0:
                return f"{total_gb} GB Volume ({path.name})"
            return f"Volume ({path.name})"
        except Exception:
            return f"Storage ({path.name})"
