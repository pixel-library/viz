"""
Unit & UI Layout Tests for Viz Terminal Media Center.
Verifies three-column presence, visibility, responsivness, and metadata rendering.
"""

import pytest
from pathlib import Path
from textual.geometry import Size

from viz.app import VizApp
from viz.widgets.sidebar import SidebarWidget
from viz.widgets.media_list import MediaListWidget
from viz.widgets.details import DetailsWidget
from viz.folder_tree import FolderNode
from viz.models import MediaItem, MediaType


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_three_column_visibility_and_mounting():
    """Verify that all 3 panels (Left, Center, Right) are mounted and visible simultaneously."""
    app = VizApp()
    async with app.run_test(size=Size(120, 40)) as pilot:
        sidebar = app.query_one(SidebarWidget)
        media_list = app.query_one(MediaListWidget)
        details = app.query_one(DetailsWidget)

        assert sidebar is not None
        assert media_list is not None
        assert details is not None

        assert details.display is True
        assert sidebar.display is True
        assert media_list.display is True


@pytest.mark.anyio
async def test_details_panel_visible_at_small_terminal():
    """Verify that Details panel is visible at 80x24 terminal resolution."""
    app = VizApp()
    async with app.run_test(size=Size(80, 24)) as pilot:
        details = app.query_one(DetailsWidget)
        assert details.display is True


@pytest.mark.anyio
async def test_details_panel_renders_folder_and_storage_info(tmp_path):
    """Verify DetailsWidget updates information and storage for a folder."""
    app = VizApp()
    async with app.run_test(size=Size(120, 40)) as pilot:
        details = app.query_one(DetailsWidget)

        folder = FolderNode(name="TestFolder", path=tmp_path)
        folder.image_count = 5
        folder.total_media_count = 5

        details.show_folder(folder)

        body_lbl = details.query_one("#details-body")
        storage_lbl = details.query_one("#storage-body")

        body_str = str(body_lbl._renderable) if hasattr(body_lbl, "_renderable") else str(body_lbl.render())
        storage_str = str(storage_lbl._renderable) if hasattr(storage_lbl, "_renderable") else str(storage_lbl.render())

        assert "TestFolder" in body_str
        assert "Folder" in body_str
        assert "TOTAL:" in storage_str
        assert "USED:" in storage_str
        assert "FREE:" in storage_str


@pytest.mark.anyio
async def test_details_panel_renders_media_item(tmp_path):
    """Verify DetailsWidget updates metadata for an Image media item."""
    app = VizApp()
    async with app.run_test(size=Size(120, 40)) as pilot:
        details = app.query_one(DetailsWidget)

        img_path = tmp_path / "sample.png"
        img_path.write_bytes(b"\x00" * 1024)

        item = MediaItem(
            name="sample.png",
            display_name="sample",
            path=img_path,
            directory=tmp_path,
            extension=".png",
            media_type=MediaType.IMAGE,
            file_size=1024,
            image_width=1920,
            image_height=1080,
            image_format="PNG",
        )

        details.show_media_item(item)

        body_lbl = details.query_one("#details-body")
        body_str = str(body_lbl._renderable) if hasattr(body_lbl, "_renderable") else str(body_lbl.render())

        assert "sample.png" in body_str
        assert "Image" in body_str
        assert "1920 × 1080" in body_str
