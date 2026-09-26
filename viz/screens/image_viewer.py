"""
Dedicated Terminal Image Viewer Screen for Viz Media Center.
Displays image metadata and high-contrast terminal art previews inside terminal.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from viz.images import ImageHelper
from viz.models import MediaItem


class ImageViewerScreen(ModalScreen):
    """Modal screen for viewing image metadata and terminal art previews inside terminal."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("q", "dismiss_screen", "Back", show=False),
        Binding("left", "prev_image", "Previous", show=True),
        Binding("right", "next_image", "Next", show=True),
        Binding("b", "prev_image", "Previous", show=False),
        Binding("n", "next_image", "Next", show=False),
        Binding("equals", "zoom_in", "Zoom +", show=True),
        Binding("plus", "zoom_in", "Zoom +", show=False),
        Binding("minus", "zoom_out", "Zoom -", show=True),
        Binding("r", "reset_zoom", "Reset Zoom", show=True),
        Binding("f", "fit_zoom", "Fit", show=True),
    ]

    def __init__(self, current_item: MediaItem, folder_images: List[MediaItem] = None) -> None:
        super().__init__()
        self.current_item = current_item
        self.folder_images = folder_images or [current_item]
        self.current_index = self.folder_images.index(current_item) if current_item in self.folder_images else 0
        self.zoom_level: float = 1.0

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog", id="image-dialog"):
            yield Label("[IMG] IMAGE VIEWER", classes="dialog-header", id="image-header")
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
        header.update(f"[IMG] IMAGE VIEWER [{self.current_index + 1}/{len(self.folder_images)}]")

        ascii_body = self.query_one("#image-ascii-body", Label)
        base_w = int(48 * self.zoom_level)
        base_h = int(18 * self.zoom_level)
        ascii_art = ImageHelper.generate_ascii_preview(item.path, width=base_w, height=base_h, use_blocks=True)
        ascii_body.update(ascii_art)

        meta_body = self.query_one("#image-meta-body", Label)
        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{int(item.file_size / 1024)} KB"
        dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Unknown"
        zoom_str = f"{int(self.zoom_level * 100)}%"

        meta_text = (
            f"[bold orange]{item.name}[/bold orange]  (Zoom: {zoom_str})\n"
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

    def action_zoom_in(self) -> None:
        self.zoom_level = min(2.5, self.zoom_level + 0.25)
        self.update_display()

    def action_zoom_out(self) -> None:
        self.zoom_level = max(0.5, self.zoom_level - 0.25)
        self.update_display()

    def action_reset_zoom(self) -> None:
        self.zoom_level = 1.0
        self.update_display()

    def action_fit_zoom(self) -> None:
        self.zoom_level = 1.0
        self.update_display()

    def action_dismiss_screen(self) -> None:
        self.dismiss()

