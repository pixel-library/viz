#!/usr/bin/env python3
"""
===============================================================================
 VIZ - Terminal Media Player (Single Entrypoint Launcher)
===============================================================================

Usage:
    python main.py
    python main.py --path ~/Videos
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add local repository directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from viz.cli import main

if __name__ == "__main__":
    main()
