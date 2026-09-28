"""
Unit tests for Viz Media Virtual Environments (Image, Video, Audio).
"""

import pytest
from pathlib import Path
from textual.geometry import Size

from viz.app import VizApp
from viz.media_router import MediaRouter
from viz.models import MediaItem, MediaType
from viz.screens.image_environment import ImageEnvironment
from viz.screens.video_environment import VideoEnvironment
from viz.screens.audio_environment import AudioEnvironment
from viz.screens.image_viewer import ImageViewerScreen
from viz.screens.video_player import VideoPlayerScreen
from viz.screens.audio_player import AudioPlayerScreen


@pytest.fixture
def anyio_backend():
    return "asyncio"


def make_test_app() -> VizApp:
    app = VizApp()
    app.config.set("first_run_completed", True)
    app.refresh_library = lambda: None
    return app


@pytest.mark.anyio
async def test_image_environment_direct_routing(tmp_path):
    """Verify that opening an image routes directly to ImageEnvironment without intermediate modals."""
    app = make_test_app()
    img_path = tmp_path / "photo.png"
    img_path.write_bytes(b"\x00" * 1024)

    item = MediaItem(
        name="photo.png",
        display_name="photo",
        path=img_path,
        directory=tmp_path,
        extension=".png",
        media_type=MediaType.IMAGE,
        file_size=1024,
    )

    async with app.run_test(size=Size(120, 40)) as pilot:
        MediaRouter.open_media(app, item)
        await pilot.pause()
        assert len(app.screen_stack) == 2
        active_screen = app.screen_stack[-1]
        assert isinstance(active_screen, ImageEnvironment)
        assert isinstance(active_screen, ImageViewerScreen)
        assert active_screen.current_item.name == "photo.png"


@pytest.mark.anyio
async def test_video_environment_routing(tmp_path):
    """Verify that opening a video routes directly to VideoEnvironment."""
    app = make_test_app()
    vid_path = tmp_path / "movie.mp4"
    vid_path.write_bytes(b"\x00" * 1024)

    item = MediaItem(
        name="movie.mp4",
        display_name="movie",
        path=vid_path,
        directory=tmp_path,
        extension=".mp4",
        media_type=MediaType.VIDEO,
        file_size=1024,
    )

    async with app.run_test(size=Size(120, 40)) as pilot:
        MediaRouter.open_media(app, item)
        await pilot.pause()
        assert len(app.screen_stack) == 2
        active_screen = app.screen_stack[-1]
        assert isinstance(active_screen, VideoEnvironment)
        assert isinstance(active_screen, VideoPlayerScreen)
        assert active_screen.current_item.name == "movie.mp4"


@pytest.mark.anyio
async def test_audio_environment_routing(tmp_path):
    """Verify that opening an audio track routes directly to AudioEnvironment."""
    app = make_test_app()
    aud_path = tmp_path / "song.mp3"
    aud_path.write_bytes(b"\x00" * 1024)

    item = MediaItem(
        name="song.mp3",
        display_name="song",
        path=aud_path,
        directory=tmp_path,
        extension=".mp3",
        media_type=MediaType.AUDIO,
        file_size=1024,
    )

    async with app.run_test(size=Size(120, 40)) as pilot:
        MediaRouter.open_media(app, item)
        await pilot.pause()
        assert len(app.screen_stack) == 2
        active_screen = app.screen_stack[-1]
        assert isinstance(active_screen, AudioEnvironment)
        assert isinstance(active_screen, AudioPlayerScreen)
        assert active_screen.current_item.name == "song.mp3"


@pytest.mark.anyio
async def test_environment_esc_state_restoration(tmp_path):
    """Verify that dismissing an environment via ESC restores main filesystem view."""
    app = make_test_app()
    img_path = tmp_path / "pic.png"
    img_path.write_bytes(b"\x00" * 1024)

    item = MediaItem(
        name="pic.png",
        display_name="pic",
        path=img_path,
        directory=tmp_path,
        extension=".png",
        media_type=MediaType.IMAGE,
        file_size=1024,
    )

    async with app.run_test(size=Size(120, 40)) as pilot:
        MediaRouter.open_media(app, item)
        await pilot.pause()
        assert len(app.screen_stack) == 2

        await pilot.press("escape")
        await pilot.pause()
        assert len(app.screen_stack) == 1
        assert app.last_selected_item.path.resolve() == img_path.resolve()
