"""
Left Sidebar Navigation Widget for Viz Terminal Media Center.
Implements Real Filesystem Tree navigation, Personal Views, and System commands.
Zero Unicode Emojis — 100% Pixel Terminal Art.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView, Tree
from textual.widgets.tree import TreeNode

from viz.constants import PIXEL_ICON_DRIVE, PIXEL_ICON_FOLDER, PIXEL_ICON_HOME
from viz.folder_tree import FolderNode
from viz.library import LibraryManager


class SidebarWidget(Widget):
    """Sidebar widget featuring real filesystem tree and personal views."""

    PERSONAL_CATEGORIES: List[Tuple[str, str]] = [
        ("continue", "CONTINUE WATCHING"),
        ("recent", "RECENTLY PLAYED"),
        ("favorites", "FAVORITES"),
    ]

    SYSTEM_CATEGORIES: List[Tuple[str, str]] = [
        ("paths", "LIBRARY PATHS"),
        ("refresh", "REFRESH LIBRARY"),
        ("help", "HELP"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="column", id="left-column"):
            yield Label("FILESYSTEM", classes="column-header", id="tree-header")
            tree: Tree[Dict] = Tree("LIBRARY ROOTS", id="folder-tree")
            tree.show_root = False
            yield tree

            yield Label("── PERSONAL ──", classes="section-header")
            with ListView(id="personal-views-list"):
                for cat_id, title in self.PERSONAL_CATEGORIES:
                    yield ListItem(Label(f"  {title}"), id=f"cat-{cat_id}")

            yield Label("── SYSTEM ──", classes="section-header")
            with ListView(id="system-list"):
                for cat_id, title in self.SYSTEM_CATEGORIES:
                    yield ListItem(Label(f"  {title}"), id=f"sys-{cat_id}")

    def update_tree_and_counts(self, library: LibraryManager) -> None:
        """Populate the filesystem Tree widget with real folder nodes and update personal counts."""
        tree: Tree[Dict] = self.query_one("#folder-tree", Tree)
        tree.clear()

        for root_folder in library.folder_roots:
            self._add_folder_to_tree(tree.root, root_folder)

        tree.root.expand()

        counts = {
            "continue": library.continue_count,
            "recent": library.recent_count,
            "favorites": library.favorites_count,
        }

        for cat_id, title in self.PERSONAL_CATEGORIES:
            try:
                item = self.query_one(f"#cat-{cat_id}", ListItem)
                label = item.query_one(Label)
                cnt = counts.get(cat_id, 0)
                label.update(f"  {title} ({cnt})")
            except Exception:
                pass

    def _add_folder_to_tree(self, parent_node: TreeNode[Dict], folder: FolderNode) -> None:
        """Recursively add FolderNode to Textual Tree using pixel terminal icons."""
        counts_parts = []
        if folder.video_count > 0:
            counts_parts.append(f"V:{folder.video_count}")
        if folder.audio_count > 0:
            counts_parts.append(f"A:{folder.audio_count}")
        if folder.image_count > 0:
            counts_parts.append(f"I:{folder.image_count}")

        breakdown = " ".join(counts_parts) if counts_parts else str(folder.total_media_count)
        count_tag = f"[{breakdown}]" if folder.total_media_count > 0 else ""

        # Remove emojis & set pixel icons
        clean_name = folder.name.replace("🏠", "").replace("💾", "").replace("📁", "").strip()

        if "Home" in folder.name or "home" in folder.name.lower():
            icon_str = f"{PIXEL_ICON_HOME} "
        elif "Volume" in folder.name or "GB" in folder.name:
            icon_str = f"{PIXEL_ICON_DRIVE} "
        else:
            icon_str = f"{PIXEL_ICON_FOLDER} "

        label_text = f"{icon_str}{clean_name} {count_tag}"

        node = parent_node.add(label_text, data={"type": "folder", "folder": folder})
        node.expand()

        for sf in folder.subfolders:
            self._add_folder_to_tree(node, sf)
