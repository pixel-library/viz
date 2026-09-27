"""
Left Sidebar Navigation Widget for Viz Terminal Media Center.
Implements Real Filesystem Tree navigation (Folders + Media Files), Mounted Storage, and Personal Views.
Zero Unicode Emojis — 100% Pixel Terminal Art.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView, Tree
from textual.widgets.tree import TreeNode

from viz.constants import PIXEL_ICON_DRIVE, get_folder_symbol
from viz.folder_tree import FolderNode
from viz.library import LibraryManager
from viz.mounts import MountsManager


class SidebarWidget(Vertical):
    """Sidebar widget featuring real filesystem tree (folders + files), mounted drives, and personal views."""

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
        yield Label("MEDIA FILESYSTEM", classes="column-header", id="tree-header")
        tree: Tree[Dict] = Tree("LIBRARY ROOTS", id="folder-tree")
        tree.show_root = False
        yield tree

        yield Label("── STORAGE ──", classes="section-header")
        yield ListView(id="storage-list")

        yield Label("── PERSONAL ──", classes="section-header")
        with ListView(id="personal-views-list"):
            for cat_id, title in self.PERSONAL_CATEGORIES:
                yield ListItem(Label(f"  {title}"), id=f"cat-{cat_id}")

        yield Label("── SYSTEM ──", classes="section-header")
        with ListView(id="system-list"):
            for cat_id, title in self.SYSTEM_CATEGORIES:
                yield ListItem(Label(f"  {title}"), id=f"sys-{cat_id}")

    def update_tree_and_counts(self, library: LibraryManager) -> None:
        """Populate the filesystem Tree widget with real folders + media files, update drives and personal counts."""
        tree: Tree[Dict] = self.query_one("#folder-tree", Tree)
        tree.clear()

        for root_folder in library.folder_roots:
            self._add_folder_to_tree(tree.root, root_folder)

        tree.root.expand()

        # Update Mounted Storage Drives
        try:
            storage_list = self.query_one("#storage-list", ListView)
            storage_list.clear()
            mounts = MountsManager.get_accessible_mounts()
            folder_sym = get_folder_symbol()
            if mounts:
                for mount_path, label_str in mounts:
                    storage_list.append(ListItem(Label(f" {folder_sym} {label_str}"), id=f"drv-{hash(str(mount_path))}"))
            else:
                storage_list.append(ListItem(Label(f" {folder_sym} Local Disk"), disabled=True))
        except Exception:
            pass

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
        """Recursively add FolderNode and its MediaItems to Textual Tree using pixel terminal icons."""
        counts_parts = []
        type_count = sum(1 for c in (folder.image_count, folder.video_count, folder.audio_count) if c > 0)
        if type_count > 1:
            counts_parts.append(f"M:{folder.total_media_count}")
        if folder.image_count > 0:
            counts_parts.append(f"I:{folder.image_count}")
        if folder.video_count > 0:
            counts_parts.append(f"V:{folder.video_count}")
        if folder.audio_count > 0:
            counts_parts.append(f"A:{folder.audio_count}")

        breakdown = " ".join(counts_parts) if counts_parts else str(folder.total_media_count)
        count_tag = f"[{breakdown}]" if folder.total_media_count > 0 else ""


        clean_name = folder.name.replace("🏠", "").replace("💾", "").replace("📁", "").strip()

        folder_sym = get_folder_symbol()
        icon_str = f"{folder_sym} "

        label_text = f"{icon_str}{clean_name} {count_tag}".strip()

        node = parent_node.add(label_text, data={"type": "folder", "folder": folder})
        node.expand()

        # 1. Subfolders
        for sf in folder.subfolders:
            self._add_folder_to_tree(node, sf)

        # 2. Media Files inside folder
        for media_item in folder.media_files:
            icon = media_item.ascii_icon
            file_label = f"  {icon} {media_item.name}"
            node.add_leaf(file_label, data={"type": "media", "media": media_item})


