"""
Library Path Management & Directory Browser Screen for Viz Media Center.
Enables adding, removing, and browsing media directories 100% via keyboard.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, ListItem, ListView

from viz.config import ConfigManager


class DirectorySelectorModal(ModalScreen[Optional[Path]]):
    """Keyboard-driven Directory Selector Modal."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "open_directory", "Open Folder", show=True),
        Binding("a", "select_directory", "Select Current Directory", show=True),
        Binding("backspace", "parent_directory", "Parent Directory", show=True),
    ]

    def __init__(self, start_path: Optional[Path] = None) -> None:
        super().__init__()
        self.current_path = (start_path or Path.home()).expanduser().resolve()
        self.subdirs: List[Path] = []

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog", id="dir-dialog"):
            yield Label("📁 SELECT MEDIA DIRECTORY", classes="dialog-header")
            yield Label("", id="current-dir-label")
            yield ListView(id="dir-list")
            yield Label("[A] Select Current Directory  [ENTER] Open Folder  [BACKSPACE] Parent  [ESC] Cancel", classes="hint-label")

    def on_mount(self) -> None:
        self.load_directory(self.current_path)

    def load_directory(self, target: Path) -> None:
        resolved = target.expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            return

        self.current_path = resolved
        lbl = self.query_one("#current-dir-label", Label)
        lbl.update(f"[bold orange]CURRENT:[/bold orange] {self.current_path}")

        dir_list = self.query_one("#dir-list", ListView)
        dir_list.clear()

        self.subdirs = []
        try:
            entries = sorted(list(self.current_path.iterdir()), key=lambda p: p.name.lower())
            for p in entries:
                if p.is_dir() and not p.name.startswith("."):
                    self.subdirs.append(p)
                    dir_list.append(ListItem(Label(f"📁 {p.name}")))
        except (PermissionError, OSError):
            dir_list.append(ListItem(Label("[!] Permission Denied")))

    def action_open_directory(self) -> None:
        dir_list = self.query_one("#dir-list", ListView)
        idx = dir_list.index
        if idx is not None and 0 <= idx < len(self.subdirs):
            self.load_directory(self.subdirs[idx])

    def action_parent_directory(self) -> None:
        if self.current_path.parent != self.current_path:
            self.load_directory(self.current_path.parent)

    def action_select_directory(self) -> None:
        self.dismiss(self.current_path)

    def action_cancel(self) -> None:
        self.dismiss(None)


class LibraryPathsScreen(ModalScreen):
    """Modal screen for inspecting, adding, and removing library root paths."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("a", "add_path", "Add Path", show=True),
        Binding("d", "remove_path", "Remove Path", show=True),
        Binding("r", "rescan_paths", "Rescan", show=True),
    ]

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog", id="paths-dialog"):
            yield Label("📁 LIBRARY PATH MANAGER", classes="dialog-header")
            yield ListView(id="paths-list")
            yield Label("[A] Add Path   [D] Remove Path   [R] Rescan Library   [ESC] Back", classes="hint-label")

    def on_mount(self) -> None:
        self.refresh_paths_list()

    def refresh_paths_list(self) -> None:
        paths_list = self.query_one("#paths-list", ListView)
        paths_list.clear()

        paths = self.config.get_library_paths()
        for p in paths:
            paths_list.append(ListItem(Label(f"📁 {p}")))

    def action_add_path(self) -> None:
        def on_selected(selected_path: Optional[Path]) -> None:
            if selected_path:
                self.config.add_library_path(selected_path)
                self.refresh_paths_list()
                self.app.refresh_library()

        self.app.push_screen(DirectorySelectorModal(Path.home()), on_selected)

    def action_remove_path(self) -> None:
        paths_list = self.query_one("#paths-list", ListView)
        idx = paths_list.index
        paths = self.config.get_library_paths()
        if idx is not None and 0 <= idx < len(paths):
            target = paths[idx]
            self.config.remove_library_path(target)
            self.refresh_paths_list()
            self.app.refresh_library()

    def action_rescan_paths(self) -> None:
        self.app.refresh_library()
        self.dismiss()

    def action_dismiss_screen(self) -> None:
        self.dismiss()
