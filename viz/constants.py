"""
Centralized constants for Viz Terminal Media Player.
Single source of truth for version, media extensions, paths, and default configurations.
"""

from __future__ import annotations

import os
from pathlib import Path

# Version Information
__version__ = "0.1.0"
APP_NAME = "Viz"
APP_TITLE = "Viz Terminal Media Player"

# Supported Media Extensions (Case-Insensitive Sets)
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".m4v",
    ".avi",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".ogg",
    ".oga",
    ".aac",
    ".m4a",
}

SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

# Persistent Storage Paths (XDG compliant: ~/.config/viz)
CONFIG_DIR = Path.home() / ".config" / "viz"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
LOG_FILE = CONFIG_DIR / "viz.log"

# UI Aesthetics
COLOR_PRIMARY_ORANGE = "#ff8800"
COLOR_ACCENT_ORANGE = "#ff9900"
COLOR_DARK_ORANGE = "#cc6600"
COLOR_BG_DARK = "#0c0905"
COLOR_CONTAINER_BG = "#0f0a05"
COLOR_BAR_BG = "#140e07"

# ASCII Header Logo
ASCII_LOGO = (
    "██╗   ██╗██╗███████╗\n"
    "██║   ██║██║╚══███╔╝\n"
    "██║   ██║██║  ███╔╝ \n"
    "╚██╗ ██╔╝██║ ███╔╝  \n"
    " ╚████╔╝ ██║███████╗\n"
    "  ╚═══╝  ╚═╝╚══════╝"
)
