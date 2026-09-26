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
APP_TITLE = "VIZ // OFFLINE MEDIA TERMINAL"

# Supported Video Extensions (Requirement #2)
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
    ".m4v",
    ".mpeg",
    ".mpg",
    ".ts",
    ".m2ts",
    ".flv",
    ".wmv",
}

# Supported Audio Extensions (Requirement #2)
AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".opus",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
}

# Supported Image Extensions (Requirement #2)
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".svg",
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

# Professional Orange + White Theme Palette (Requirement #24)
COLOR_BG_PRIMARY = "#FFFDF8"
COLOR_BG_PANEL = "#FFFFFF"
COLOR_ORANGE_PRIMARY = "#FF8800"
COLOR_ORANGE_BRIGHT = "#FF9900"
COLOR_ORANGE_DARK = "#CC6600"
COLOR_TEXT_PRIMARY = "#1A1A1A"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_BORDER = "#FF8800"
COLOR_SELECTION = "#FFE1B8"

# Monochrome Folder Symbol & Pixel Icons (Requirement #5 & Backward Compatibility)
FOLDER_GLYPH_UNICODE = "🗀"
FOLDER_GLYPH_PIXEL = "[▰]"

PIXEL_ICON_HOME = "[HOME]"
PIXEL_ICON_DRIVE = "[DRV]"
PIXEL_ICON_FOLDER = "[▰]"
PIXEL_ICON_FOLDER_OPEN = "[▰▼]"

def get_folder_symbol(use_unicode: bool = True) -> str:
    """Return monochrome pixel/Unicode folder symbol abstraction."""
    return FOLDER_GLYPH_UNICODE if use_unicode else FOLDER_GLYPH_PIXEL


# Media Type Icons (Requirement #11)
ICON_VIDEO = "[VID]"
ICON_AUDIO = "[AUD]"
ICON_IMAGE = "[IMG]"

# Compact Header Text & ASCII Logo Constant
HEADER_TEXT = "VIZ // OFFLINE MEDIA TERMINAL"
ASCII_LOGO = "VIZ"



