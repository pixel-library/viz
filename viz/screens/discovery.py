"""
Initial Library Discovery Screen for Viz Media Center.
Displays accessible home directories, mounted storage volumes, and indexed media summary.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from viz.library import LibraryManager
from viz.mounts import MountsManager


class DiscoveryScreen(ModalScreen):
    """Modal screen displaying initial filesystem storage discovery & media summary."""

    BINDINGS = [
        Binding("enter", "dismiss_screen", "Continue", show=True),
        Binding("escape", "dismiss_screen", "Continue", show=True),
        Binding("space", "dismiss_screen", "Continue", show=True),
    ]

    def __init__(self, library: LibraryManager, library_paths: List[Path]) -> None:
        super().__init__()
        self.library = library
        self.library_paths = library_paths

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog", id="discovery-dialog"):
            yield Label("VIZ // INITIAL LIBRARY DISCOVERY", classes="dialog-header")
            yield Label("", id="discovery-body")
            yield Label("[ENTER] Continue to Viz Media Center", classes="hint-label")

    def on_mount(self) -> None:
        mounts = MountsManager.get_accessible_mounts()
        home = Path.home()

        lines = [
            f"[bold orange]HOME DIRECTORY:[/bold orange]",
            f"  ✓ {home}\n",
            f"[bold orange]ACCESSIBLE MEDIA DIRECTORIES FOUND:[/bold orange]",
        ]

        for p in self.library_paths:
            if not any(p == m_path for m_path, _ in mounts):
                lines.append(f"  ✓ {p}")

        if mounts:
            lines.append(f"\n[bold orange]ACCESSIBLE MOUNTED STORAGE:[/bold orange]")
            for m_path, label in mounts:
                lines.append(f"  ✓ {label} ({m_path})")

        lines.extend([
            f"\n[bold orange]MEDIA DISCOVERED:[/bold orange]",
            f"  Videos: {self.library.videos_count}",
            f"  Audio:  {self.library.music_count}",
            f"  Images: {self.library.images_count}",
            f"  Total:  {self.library.all_count} files",
        ])

        body = self.query_one("#discovery-body", Label)
        body.update("\n".join(lines))

    def action_dismiss_screen(self) -> None:
        self.dismiss()
