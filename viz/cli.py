"""
Command-Line Interface Entrypoint for Viz Media Player.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from viz import __version__
from viz.app import VizApp


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="viz",
        description="Viz - Terminal Media Player & Media Pipeline Engine",
    )
    parser.add_argument(
        "-p", "--path",
        type=str,
        default=None,
        help="Specify media directory to scan on launch",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Viz Terminal Media Player v{__version__}",
    )
    args = parser.parse_args()

    target_dir = args.path if args.path else None
    if target_dir and not Path(target_dir).exists():
        print(f"Error: Specified path '{target_dir}' does not exist.")
        sys.exit(1)

    app = VizApp(initial_dir=target_dir)
    app.run()


if __name__ == "__main__":
    main()
