"""
Dedicated Virtual Image Environment Screen for Viz Media Center.
Image-focused gallery UI for full-resolution image viewing.

Direct rendering via native MPV image display process or Kitty graphics protocol.
ONE ENTER ONLY - Bypasses intermediate preview steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from viz.images import ImageHelper
from viz.models import MediaItem
from viz.terminal import TerminalCapabilities


class ImageViewerScreen(ModalScreen):
    """Full-terminal screen for viewing images with direct native rendering."""

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
    ]

    def __init__(self, current_item: MediaItem, folder_images: Optional[List[MediaItem]] = None) -> None:
        super().__init__()
        self.current_item = current_item
        self.folder_images = folder_images or [current_item]
        self.current_index = self.folder_images.index(current_item) if current_item in self.folder_images else 0
        self.zoom_level: float = 1.0
        self.rotation_angle: int = 0
        self.native_mode: bool = TerminalCapabilities.has_display()

    def compose(self) -> ComposeResult:
        with Vertical(id="image-screen-container"):
            with Horizontal(id="image-header-bar"):
                yield Label("←  VIZ // IMAGE ENVIRONMENT", id="image-brand")
                yield Label("", id="image-title-label")
                yield Label("", id="image-queue-counter")

            yield Label("", id="image-viewport")
            yield Label("", id="image-meta-bar")
            yield Label("", id="image-controls-bar")

    def on_mount(self) -> None:
        try:
            self.update_display()
            self.render_image_media()
        except Exception as err:
            print(f"IMAGE VIEWER ON MOUNT ERROR: {err}")
            import traceback
            traceback.print_exc()

    def render_image_media(self) -> None:
        """Launch high-resolution image rendering directly via engine or native viewer."""
        if not (0 <= self.current_index < len(self.folder_images)):
            return
        item = self.folder_images[self.current_index]
        self.current_item = item

        if hasattr(self.app, "last_selected_item"):
            self.app.last_selected_item = self.current_item

        # Launch native engine image viewer (MPV --image-display-duration=inf)
        if hasattr(self.app, "engine") and self.app.engine:
            if self.app.engine.play_image(item):
                return

        # Fallback to ImageHelper native viewer
        ImageHelper.open_native_viewer(item.path)

    def update_display(self) -> None:
        if not (0 <= self.current_index < len(self.folder_images)):
            return

        item = self.folder_images[self.current_index]

        title_lbl = self.query_one("#image-title-label", Label)
        title_lbl.update(f"[bold white]{item.name}[/bold white]")

        counter_lbl = self.query_one("#image-queue-counter", Label)
        counter_lbl.update(f"[{self.current_index + 1}/{len(self.folder_images)}]")

        size_mb = item.file_size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{int(item.file_size / 1024)} KB"
        dim_str = f"{item.image_width} × {item.image_height}" if item.image_width > 0 else "Full Resolution"
        fmt_str = item.image_format or item.extension.upper().lstrip(".")
        zoom_str = f"{int(self.zoom_level * 100)}%"
        rot_str = f"{self.rotation_angle}°"

        meta_text = (
            f"  [bold orange]{item.name}[/bold orange]  •  "
            f"[bold]{fmt_str}[/bold]  •  {dim_str}  •  {size_str}  •  "
            f"Zoom: {zoom_str}  •  Rotation: {rot_str}"
        )
        self.query_one("#image-meta-bar", Label).update(meta_text)

        controls_text = (
            "  ← Prev [B/LEFT]   |   + Zoom In   |   - Zoom Out   |   "
            "0 Reset   |   R Rotate   |   F Fit   |   Next [N/RIGHT] →   |   [ESC] Exit  "
        )
        self.query_one("#image-controls-bar", Label).update(controls_text)

        # Viewport Card Text
        viewport = self.query_one("#image-viewport", Label)

        # Try Kitty protocol rendering directly if Kitty terminal is supported
        term_w = getattr(self.app.size, "width", 80)
        term_h = getattr(self.app.size, "height", 24)
        max_w = max(30, term_w - 6)
        max_h = max(10, term_h - 10)

        rgb_art = ImageHelper.generate_rgb_preview(
            item.path,
            max_w=max_w,
            max_h=max_h,
            rotation=self.rotation_angle,
            zoom=self.zoom_level,
        )

        if rgb_art:
            viewport.update(rgb_art)
        else:
            card_content = (
                "\n\n\n"
                "   ┌────────────────────────────────────────────────────────────────────────┐\n"
                "   │                       [ VIZ IMAGE ENVIRONMENT ]                        │\n"
                "   │                                                                        │\n"
                f"   │     ACTIVE IMAGE:  [bold white]{item.name[:48]:<48}[/bold white]│\n"
                f"   │     FORMAT:        {fmt_str:<8}  DIMENSIONS: {dim_str:<14}            │\n"
                f"   │     FILE SIZE:     {size_str:<12}                                           │\n"
                "   │                                                                        │\n"
                "   │     [ High-Quality Raster Viewport Active in Native Window ]           │\n"
                "   │                                                                        │\n"
                "   │     [ N Next  •  B Prev  •  + Zoom In  •  - Zoom Out  •  ESC Back ]     │\n"
                "   └────────────────────────────────────────────────────────────────────────┘\n"
            )
            viewport.update(card_content)

    def action_prev_image(self) -> None:
        if len(self.folder_images) > 1:
            self.current_index = (self.current_index - 1) % len(self.folder_images)
            self.update_display()
            self.render_image_media()

    def action_next_image(self) -> None:
        if len(self.folder_images) > 1:
            self.current_index = (self.current_index + 1) % len(self.folder_images)
            self.update_display()
            self.render_image_media()

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
        if hasattr(self.app, "engine"):
            self.app.engine.stop()

        if hasattr(self.app, "update_ui_views"):
            self.app.update_ui_views()

        self.dismiss()
