"""
Unit Test Suite for Viz Terminal Media Center.
"""

from pathlib import Path
import tempfile
import time

from viz.constants import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, SUPPORTED_EXTENSIONS, VIDEO_EXTENSIONS
from viz.config import ConfigManager
from viz.folder_tree import FolderTreeBuilder
from viz.history import HistoryManager
from viz.library import LibraryManager
from viz.models import MediaItem, MediaType
from viz.queue import PlaybackQueue
from viz.scanner import MediaScanner
from viz.series import SeriesDetector
from viz.widgets.player_status import PlayerStatusWidget


def test_extension_constants():
    assert ".mp4" in VIDEO_EXTENSIONS
    assert ".mkv" in VIDEO_EXTENSIONS
    assert ".mp3" in AUDIO_EXTENSIONS
    assert ".flac" in AUDIO_EXTENSIONS
    assert ".jpg" in IMAGE_EXTENSIONS
    assert ".png" in IMAGE_EXTENSIONS
    assert ".mp4" in SUPPORTED_EXTENSIONS
    assert ".mp3" in SUPPORTED_EXTENSIONS
    assert ".jpg" in SUPPORTED_EXTENSIONS


def test_media_type_detection():
    assert MediaType.from_path(Path("movie.MP4")) == MediaType.VIDEO
    assert MediaType.from_path(Path("movie.mkv")) == MediaType.VIDEO
    assert MediaType.from_path(Path("track.MP3")) == MediaType.AUDIO
    assert MediaType.from_path(Path("photo.JPG")) == MediaType.IMAGE
    assert MediaType.from_path(Path("photo.png")) == MediaType.IMAGE
    assert MediaType.from_path(Path("file.txt")) == MediaType.UNKNOWN


def test_folder_tree_builder():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        sub1 = root / "Movies" / "Interstellar"
        sub1.mkdir(parents=True)
        m_file = sub1 / "Interstellar.mkv"
        m_file.write_text("video_content")

        item = MediaItem.from_file(m_file)
        assert item is not None

        roots = FolderTreeBuilder.build_tree([root], [item])
        assert len(roots) == 1
        assert roots[0].name == root.name
        assert len(roots[0].subfolders) == 1
        assert roots[0].subfolders[0].name == "Movies"
        assert roots[0].total_media_count == 1
        assert roots[0].video_count == 1


def test_series_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "Breaking.Bad.S01E03.mkv"
        p1.write_text("dummy")
        item1 = MediaItem.from_file(p1)
        assert item1 is not None

        episode = SeriesDetector.parse_item(item1)
        assert episode is not None
        assert episode.season_num == 1
        assert episode.episode_num == 3
        assert "Breaking Bad" in item1.series_name


def test_playback_queue():
    q = PlaybackQueue()
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "track1.mp3"
        p2 = Path(tmpdir) / "track2.mp3"
        p1.write_text("dummy")
        p2.write_text("dummy")

        m1 = MediaItem.from_file(p1)
        m2 = MediaItem.from_file(p2)

        q.set_queue([m1, m2], start_index=0)
        assert q.current_item == m1
        assert len(q.up_next) == 1

        next_track = q.get_next()
        assert next_track == m2


def test_time_formatting():
    assert PlayerStatusWidget.format_time(0) == "00:00"
    assert PlayerStatusWidget.format_time(45) == "00:45"
    assert PlayerStatusWidget.format_time(222) == "03:42"
    assert PlayerStatusWidget.format_time(5076) == "01:24:36"


def test_config_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        cfg = ConfigManager(config_file=config_file)
        assert cfg.volume == 80
        assert not cfg.muted

        cfg.add_library_path(Path(tmpdir))
        assert Path(tmpdir).resolve() in cfg.get_library_paths()


def test_non_media_folder_pruning():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        media_dir = root / "Downloads" / "Videos"
        empty_dir = root / "PythonCode" / "Project"
        media_dir.mkdir(parents=True)
        empty_dir.mkdir(parents=True)

        vid = media_dir / "clip.mp4"
        vid.write_text("video")

        item = MediaItem.from_file(vid)
        roots = FolderTreeBuilder.build_tree([root], [item])

        assert len(roots) == 1
        sub_names = [sf.name for sf in roots[0].subfolders]
        assert "Downloads" in sub_names
        assert "PythonCode" not in sub_names


def test_mounts_discovery():
    from viz.mounts import MountsManager
    mounts = MountsManager.get_accessible_mounts()
    assert isinstance(mounts, list)


def test_history_manager_resume_logic():
    with tempfile.TemporaryDirectory() as tmpdir:
        hist_file = Path(tmpdir) / "history.json"
        hist = HistoryManager(history_file=hist_file)

        test_path = Path(tmpdir) / "test_movie.mp4"
        test_path.write_text("dummy content")

        assert hist.get_resume_position(test_path) == 0.0

        hist.update_position(test_path, position=100.0, duration=500.0)
        assert hist.get_resume_position(test_path) == 100.0

        hist.update_position(test_path, position=495.0, duration=500.0)
        assert hist.get_resume_position(test_path) == 0.0
