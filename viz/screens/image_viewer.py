"""
Dedicated Terminal Image Viewer Screen for Viz Media Center.

Two rendering modes:
1. NATIVE MODE (default on X11/Wayland): Opens image in native MPV window at full resolution.
   The terminal shows metadata, navigation controls, and file info.
2. TERMINAL MODE (fallback): Renders high-quality truecolor half-block art within the terminal.

Press 'v' to toggle between native and terminal preview modes.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from viz.images import ImageHelper
from viz.models import MediaItem
from viz.terminal import TerminalCapabilities


class ImageViewerScreen(ModalScreen):
    """Full-terminal screen for viewing images with native rendering support."""

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
        Binding("zero", "reset_zoom", "Reset Zoom", show=True),
        Binding("r", "rotate_image", "Rotate", show=True),
        Binding("f", "fit_zoom", "Fit", show=True),
        Binding("v", "open_native", "Native View", show=True),
        Binding("enter", "open_native", "Native View", show=False),
    ]

    def __init__(self, current_item: MediaItem, folder_images: List[MediaItem] = None) -> None:
        super().__init__()
        self.current_item = current_item
        self.folder_images = folder_images or [current_item]
        self.current_index = self.folder_images.index(current_item) if current_item in self.folder_images else 0
        self.zoom_level: float = 1.0
        self.rotation_angle: int = 0
        self.native_mode: bool = TerminalCapabilities.has_display()

    def compose(self) -> ComposeResult:
        with Vertical(id="image-screen-container"):
            yield Label("[IMG] VIZ // IMAGE VIEWER", classes="dialog-header", id="image-header")
            yield Label("", id="image-ascii-body")
            yield Label("", id="image-meta-body")
            yield Footer()

    def on_mount(self) -> None:
        self.update_display()

    def on_resize(self, event) -> None:
        self.update_display()

    def update_display(self) -> None:
        if not (0 <= self.current_index < len(self.folder_images)):
            return

        item = self.folder_images[self.current_index]

        header = self.query_one("#image-header", Label)
        header.update(f"VIZ // IMAGE VIEWER  [{self.current_index + 1}/{len(self.folder_images)}]")

        # Dynamic size calculation from terminal window
        term_w = getattr(self.app.size, "width", 80)
        term_h = getattr(self.app.size, "height", 24)

        max_w = max(30, term_w - 6)
        max_h = max(10, term_h - 9)

        ascii_body = self.query_one("#image-ascii-body", Label)

        if self.native_mode:
            # In native mode, show file info instead of terminal rendering
            dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Unknown"
            size_mb = item.file_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{int(item.file_size / 1024)} KB"
            fmt_str = item.image_format or item.extension.upper().lstrip(".")

            native_info = (
                "\n\n\n"
                "   ┌─────────────────────────────────────────────────────────────┐\n"
                f"   │          [bold orange]{item.name[:45]:<45}[/bold orange]  │\n"
                "   │                                                             │\n"
                f"   │          FORMAT: {fmt_str:<8}  DIMENSIONS: {dim_str:<15}  │\n"
                f"   │          FILE SIZE: {size_str:<12}                          │\n"
                "   │                                                             │\n"
                "   │        Press [bold]V[/bold] or [bold]ENTER[/bold] to open in native viewer        │\n"
                "   │        (Full resolution, hardware-accelerated MPV)          │\n"
                "   │                                                             │\n"
                "   │        Press [bold]T[/bold] for in-terminal preview                    │\n"
                "   └─────────────────────────────────────────────────────────────┘\n"
            )
            ascii_body.update(native_info)
        else:
            # Terminal rendering mode
            rgb_art = ImageHelper.generate_rgb_preview(
                item.path,
                max_w=max_w,
                max_h=max_h,
                rotation=self.rotation_angle,
                zoom=self.zoom_level,
            )
            ascii_body.update(rgb_art)

        meta_body = self.query_one("#image-meta-body", Label)
        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{int(item.file_size / 1024)} KB"
        dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Unknown"
        zoom_str = f"{int(self.zoom_level * 100)}%"
        rot_str = f"{self.rotation_angle}°"
        mode_str = "NATIVE" if self.native_mode else "TERMINAL"

        meta_text = (
            f"[bold orange]{item.name}[/bold orange]\n"
            f"[bold]{item.image_format or item.extension.upper()}[/bold] • {dim_str} • {size_str} • Zoom: {zoom_str} • Rotation: {rot_str} • Mode: {mode_str}\n"
            f"[dim]{item.path}[/dim]"
        )
        meta_body.update(meta_text)

    def action_open_native(self) -> None:
        """Open the current image in a native MPV viewer window."""
        if not (0 <= self.current_index < len(self.folder_images)):
            return
        item = self.folder_images[self.current_index]

        # Try engine's native image viewer first
        if hasattr(self.app, "engine"):
            if self.app.engine.play_image(item):
                self.app.notify(f"Opened in native viewer: {item.name}", title="Image Viewer")
                return

        # Fallback to ImageHelper
        if ImageHelper.open_native_viewer(item.path):
            self.app.notify(f"Opened in native viewer: {item.name}", title="Image Viewer")
        else:
            self.app.notify("No display server available for native viewing", title="Image Viewer", severity="warning")

    def action_prev_image(self) -> None:
        if len(self.folder_images) > 1:
            self.current_index = (self.current_index - 1) % len(self.folder_images)
            self.update_display()

    def action_next_image(self) -> None:
        if len(self.folder_images) > 1:
            self.current_index = (self.current_index + 1) % len(self.folder_images)
            self.update_display()

    def action_zoom_in(self) -> None:
        self.zoom_level = min(3.0, self.zoom_level + 0.25)
        self.update_display()

    def action_zoom_out(self) -> None:
        self.zoom_level = max(0.5, self.zoom_level - 0.25)
        self.update_display()

    def action_reset_zoom(self) -> None:
        self.zoom_level = 1.0
        self.rotation_angle = 0
        self.update_display()

    def action_rotate_image(self) -> None:
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.update_display()

    def action_fit_zoom(self) -> None:
        self.zoom_level = 1.0
        self.update_display()

    def action_dismiss_screen(self) -> None:
        self.dismiss()
