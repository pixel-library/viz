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

SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

# XDG Compliant Storage Paths
CONFIG_DIR = Path.home() / ".config" / "viz"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
FAVORITES_FILE = CONFIG_DIR / "favorites.json"
PLAYLISTS_FILE = CONFIG_DIR / "playlists.json"
LOG_FILE = CONFIG_DIR / "viz.log"

# Orange Theme Palette
COLOR_ORANGE_PRIMARY = "#ff8800"
COLOR_ORANGE_ACCENT = "#ff9900"
COLOR_ORANGE_DARK = "#cc6600"
COLOR_BG_DARK = "#0c0905"
COLOR_BG_SURFACE = "#140d06"
COLOR_BG_PANEL = "#0f0a05"
COLOR_BG_HOVER = "#241407"

# ASCII Header Logo
ASCII_LOGO = (
    "██╗   ██╗██╗███████╗\n"
    "██║   ██║██║╚══███╔╝\n"
    "██║   ██║██║  ███╔╝ \n"
    "╚██╗ ██╔╝██║ ███╔╝  \n"
    " ╚████╔╝ ██║███████╗\n"
    "  ╚═══╝  ╚═╝╚══════╝"
)
