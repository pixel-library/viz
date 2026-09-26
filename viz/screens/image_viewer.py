"""
Dedicated Image Viewer Screen for Viz Media Center.
Displays image metadata and high-contrast ASCII image previews in terminal.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label

from viz.images import ImageHelper
from viz.models import MediaItem


class ImageViewerScreen(ModalScreen):
    """Modal screen for viewing image metadata and terminal ASCII art previews."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("left", "prev_image", "Previous", show=True),
        Binding("right", "next_image", "Next", show=True),
        Binding("f", "dismiss_screen", "Back", show=False),
    ]

    def __init__(self, current_item: MediaItem, folder_images: List[MediaItem] = None) -> None:
        super().__init__()
        self.current_item = current_item
        self.folder_images = folder_images or [current_item]
        self.current_index = self.folder_images.index(current_item) if current_item in self.folder_images else 0

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog", id="image-dialog"):
            yield Label("🖼️ IMAGE VIEWER", classes="dialog-header", id="image-header")
            yield Label("", id="image-ascii-body")
            yield Label("", id="image-meta-body")
            yield Footer()

    def on_mount(self) -> None:
        self.update_display()

    def update_display(self) -> None:
        if not (0 <= self.current_index < len(self.folder_images)):
            return

        item = self.folder_images[self.current_index]

        header = self.query_one("#image-header", Label)
        header.update(f"🖼️ IMAGE VIEWER [{self.current_index + 1}/{len(self.folder_images)}]")

        ascii_body = self.query_one("#image-ascii-body", Label)
        ascii_art = ImageHelper.generate_ascii_preview(item.path, width=44, height=14)
        ascii_body.update(ascii_art)

        meta_body = self.query_one("#image-meta-body", Label)
        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{int(item.file_size / 1024)} KB"
        dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Unknown"

        meta_text = (
            f"[bold orange]{item.name}[/bold orange]\n"
            f"Format: {item.image_format or item.extension.upper()}  |  "
            f"Resolution: {dim_str}  |  "
            f"Size: {size_str}\n"
            f"[dim]{item.path}[/dim]"
        )
        meta_body.update(meta_text)

    def action_prev_image(self) -> None:
        if len(self.folder_images) > 1:
            self.current_index = (self.current_index - 1) % len(self.folder_images)
            self.update_display()

    def action_next_image(self) -> None:
        if len(self.folder_images) > 1:
            self.current_index = (self.current_index + 1) % len(self.folder_images)
            self.update_display()

    def action_dismiss_screen(self) -> None:
        self.dismiss()
