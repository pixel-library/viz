"""
Real Filesystem Folder Tree Builder for Viz Media Center.
Constructs hierarchical tree nodes from real scanned media directories and user library roots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from viz.models import MediaItem, MediaType


@dataclass
class FolderNode:
    """Represents a real filesystem directory containing media items and subfolders."""

    path: Path
    name: str
    parent: Optional[FolderNode] = None
    subfolders: List[FolderNode] = field(default_factory=list)
    media_files: List[MediaItem] = field(default_factory=list)

    # Recursive counts
    video_count: int = 0
    audio_count: int = 0
    image_count: int = 0
    total_media_count: int = 0
    total_size_bytes: int = 0

    def add_media(self, item: MediaItem) -> None:
        self.media_files.append(item)
        if item.media_type == MediaType.VIDEO:
            self.video_count += 1
        elif item.media_type == MediaType.AUDIO:
            self.audio_count += 1
        elif item.media_type == MediaType.IMAGE:
            self.image_count += 1
        self.total_media_count += 1
        self.total_size_bytes += item.file_size

    def prune_non_media_folders(self) -> None:
        """Prune child subfolders that contain zero media files."""
        pruned_subs = []
        for sf in self.subfolders:
            sf.prune_non_media_folders()
            if sf.total_media_count > 0 or sf.media_files:
                pruned_subs.append(sf)
        self.subfolders = pruned_subs

    def recalculate_counts(self) -> None:
        """Recursively recalculate total media counts and sizes from subfolders."""
        for sf in self.subfolders:
            sf.recalculate_counts()

        v = sum(sf.video_count for sf in self.subfolders) + sum(1 for m in self.media_files if m.media_type == MediaType.VIDEO)
        a = sum(sf.audio_count for sf in self.subfolders) + sum(1 for m in self.media_files if m.media_type == MediaType.AUDIO)
        img = sum(sf.image_count for sf in self.subfolders) + sum(1 for m in self.media_files if m.media_type == MediaType.IMAGE)
        sz = sum(sf.total_size_bytes for sf in self.subfolders) + sum(m.file_size for m in self.media_files)

        self.video_count = v
        self.audio_count = a
        self.image_count = img
        self.total_media_count = v + a + img
        self.total_size_bytes = sz


class FolderTreeBuilder:
    """Constructs real folder trees from discovered MediaItems and configured library roots."""

    @staticmethod
    def build_tree(library_roots: List[Path], items: List[MediaItem]) -> List[FolderNode]:
        """
        Build a list of root FolderNodes matching user library directories,
        populated recursively with actual filesystem subdirectories and files.
        Prunes non-media directories so tree only contains media-relevant folders.
        """
        roots: List[FolderNode] = []
        node_map: Dict[Path, FolderNode] = {}

        # 1. Initialize root nodes for configured library directories
        for root_path in library_roots:
            resolved_root = root_path.expanduser().resolve()
            if resolved_root not in node_map:
                name = "🏠 Home" if resolved_root == Path.home() else resolved_root.name or str(resolved_root)
                node = FolderNode(path=resolved_root, name=name)
                node_map[resolved_root] = node
                roots.append(node)

        # 2. Group items into folder nodes, dynamically building intermediate subfolders
        for item in items:
            item_dir = item.directory.resolve()

            # Find closest parent root
            matching_root: Optional[Path] = None
            for root_path in node_map:
                try:
                    item_dir.relative_to(root_path)
                    matching_root = root_path
                    break
                except ValueError:
                    continue

            if not matching_root:
                matching_root = item_dir
                if matching_root not in node_map:
                    node = FolderNode(path=matching_root, name=matching_root.name or str(matching_root))
                    node_map[matching_root] = node
                    roots.append(node)

            # Build folder chain from matching_root down to item_dir
            current_path = matching_root
            current_node = node_map[matching_root]

            try:
                rel_parts = item_dir.relative_to(matching_root).parts
            except ValueError:
                rel_parts = ()

            for part in rel_parts:
                current_path = current_path / part
                if current_path not in node_map:
                    sub_node = FolderNode(path=current_path, name=part, parent=current_node)
                    node_map[current_path] = sub_node
                    current_node.subfolders.append(sub_node)
                current_node = node_map[current_path]

            current_node.add_media(item)

        # 3. Recalculate recursive counts and prune non-media subfolders
        active_roots: List[FolderNode] = []
        for root_node in roots:
            root_node.recalculate_counts()
            root_node.prune_non_media_folders()
            if root_node.total_media_count > 0:
                active_roots.append(root_node)

        return active_roots
