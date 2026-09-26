"""
Command-Line Interface entry point for Viz Media Player.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from viz.constants import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="viz",
        description="Viz - Terminal Media Player & Media Pipeline Engine",
    )
    parser.add_argument(
        "-p", "--path",
        type=str,
        default=None,
        help="Path to media directory to scan on launch",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Viz Terminal Media Player v{__version__}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging mode",
    )

    args = parser.parse_args()

    target_path = None
    if args.path:
        resolved = Path(args.path).expanduser().resolve()
        if not resolved.exists():
            print(f"[ERROR] Media directory does not exist:\n  {resolved}")
            sys.exit(1)
        if not resolved.is_dir():
            print(f"[ERROR] Specified path is not a directory:\n  {resolved}")
            sys.exit(1)
        target_path = resolved

    # Delayed import of VizApp after CLI validation
    from viz.app import VizApp

    app = VizApp(media_path_override=target_path)
    app.run()


if __name__ == "__main__":
    main()
