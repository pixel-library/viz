"""
Centralized constants for Viz Terminal Media Player & Media Center.
Single source of truth for version, extension sets, theme colors, and paths.
"""

from __future__ import annotations

import os
from pathlib import Path

# Version Information
__version__ = "0.2.0"
APP_NAME = "Viz"
APP_TITLE = "Viz Terminal Media Center"

# Supported Video Extensions
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".webm",
    ".avi",
    ".mov",
    ".m4v",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".ts",
}

# Supported Audio Extensions
AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".ogg",
    ".opus",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
}

# Supported Image Extensions
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
}

SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | IMAGE_EXTENSIONS

# System Directories Excluded From Recursion
SYSTEM_EXCLUDE_PATHS = {
    "/proc",
    "/sys",
    "/dev",
    "/run",
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/var",
    "/tmp",
}

# XDG Compliant Storage Paths
CONFIG_DIR = Path.home() / ".config" / "viz"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
FAVORITES_FILE = CONFIG_DIR / "favorites.json"
PLAYLISTS_FILE = CONFIG_DIR / "playlists.json"
LOG_FILE = CONFIG_DIR / "viz.log"

# Orange + White Retro Palette
COLOR_ORANGE_PRIMARY = "#FF7A00"
COLOR_ORANGE_ACCENT = "#FF8C00"
COLOR_ORANGE_DEEP = "#E85D00"
COLOR_BG_LIGHT = "#FFFDF9"
COLOR_BG_PANEL = "#FFFFFF"
COLOR_BG_HEADER = "#FFF5E8"
COLOR_TEXT_PRIMARY = "#1A1A1A"
COLOR_TEXT_SECONDARY = "#666666"

# Retro Pixel Terminal Icons (Zero Emoji)
PIXEL_ICON_HOME = "[HOME]"
PIXEL_ICON_DRIVE = "[DRV]"
PIXEL_ICON_FOLDER = "[▰]"
PIXEL_ICON_FOLDER_OPEN = "[▰▼]"

# Compact ASCII Header Logo
ASCII_LOGO = (
    "██╗   ██╗██╗███████╗\n"
    "╚██╗ ██╔╝██║╚══███╔╝\n"
    " ╚████╔╝ ██║  ███╔╝ \n"
    "  ╚═══╝  ╚═╝  ╚══╝  "
)

