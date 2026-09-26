#!/usr/bin/env python3
"""
===============================================================================
 VIZ - Offline Hacker/VCR Terminal Media Player & Media Pipeline Engine
===============================================================================

System Architecture & Concurrency Model:
----------------------------------------
1. Frontend (TUI): Built using Textual (async event loop). The TUI manages the 
   terminal viewport, responsive layout, search input, CSS styling, and keybindings.
2. Backend (Media Engine): Driven by python-mpv (C bindings to libmpv). MPV spawns
   its own native decoding and rendering C threads.
3. Threading Safety: Interactions with python-mpv are executed asynchronously or 
   offloaded via worker threads (`asyncio.to_thread` / Textual `@work`) to ensure
   playback actions (loading files, seeking, audio track changes) NEVER freeze 
   the Textual TUI event loop.
4. Fallback Architecture: If system `libmpv` is not detected, Viz seamlessly activates
   an internal simulated media engine to ensure full TUI preview stability.

Dependencies & Installation:
----------------------------
- Python 3.10+
- Install Python packages:
    pip install textual python-mpv
- Install System Media Engine (libmpv):
    - Ubuntu/Debian:  sudo apt update && sudo apt install -y mpv libmpv-dev
    - Arch Linux:     sudo pacman -S mpv
    - Fedora:         sudo dnf install mpv mpv-devel
    - macOS:          brew install mpv

Usage:
------
    python main.py
    # or install as package:
    pip install .
    viz --path ~/Videos
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add local package path if executing directly
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from viz.app import VizApp
from viz.cli import main

if __name__ == "__main__":
    main()
