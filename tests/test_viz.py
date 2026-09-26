"""
Unit Test Suite for Viz Terminal Media Player.
"""

from pathlib import Path
import tempfile
import time

from viz.constants import AUDIO_EXTENSIONS, SUPPORTED_EXTENSIONS, VIDEO_EXTENSIONS
from viz.config import ConfigManager
from viz.history import HistoryManager
from viz.models import MediaItem, MediaType
from viz.scanner import MediaScanner
from viz.widgets.player_status import PlayerStatusWidget


def test_extension_constants():
    assert ".mp4" in VIDEO_EXTENSIONS
    assert ".mkv" in VIDEO_EXTENSIONS
    assert ".mp3" in AUDIO_EXTENSIONS
    assert ".flac" in AUDIO_EXTENSIONS
    assert ".mp4" in SUPPORTED_EXTENSIONS
    assert ".mp3" in SUPPORTED_EXTENSIONS


def test_media_type_detection():
    assert MediaType.from_path(Path("movie.MP4")) == MediaType.VIDEO
    assert MediaType.from_path(Path("movie.mkv")) == MediaType.VIDEO
    assert MediaType.from_path(Path("track.MP3")) == MediaType.AUDIO
    assert MediaType.from_path(Path("track.flac")) == MediaType.AUDIO
    assert MediaType.from_path(Path("file.txt")) == MediaType.UNKNOWN


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

        cfg.volume = 95
        cfg.muted = True

        cfg2 = ConfigManager(config_file=config_file)
        assert cfg2.volume == 95
        assert cfg2.muted


def test_config_corrupted_recovery():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        config_file.write_text("INVALID JSON DATA {{{", encoding="utf-8")

        cfg = ConfigManager(config_file=config_file)
        assert cfg.volume == 80
        assert not cfg.muted


def test_history_manager_resume_logic():
    with tempfile.TemporaryDirectory() as tmpdir:
        hist_file = Path(tmpdir) / "history.json"
        hist = HistoryManager(history_file=hist_file)

        test_path = Path(tmpdir) / "test_movie.mp4"
        test_path.write_text("dummy content")

        # Initial: no resume
        assert hist.get_resume_position(test_path) == 0.0

        # Save position at 100 seconds out of 500 seconds
        hist.update_position(test_path, position=100.0, duration=500.0)
        assert hist.get_resume_position(test_path) == 100.0

        # Near end of file: no resume
        hist.update_position(test_path, position=495.0, duration=500.0)
        assert hist.get_resume_position(test_path) == 0.0


def test_media_scanner():
    with tempfile.TemporaryDirectory() as tmpdir:
        media_dir = Path(tmpdir) / "media"
        media_dir.mkdir()

        (media_dir / "movie.mp4").write_text("dummy")
        (media_dir / "track.MP3").write_text("dummy")
        (media_dir / "readme.txt").write_text("dummy text")

        sub_dir = media_dir / "series"
        sub_dir.mkdir()
        (sub_dir / "episode.MKV").write_text("dummy")

        scanner = MediaScanner()
        discovered = scanner.scan_directory(media_dir)

        names = {item.name for item in discovered}
        assert "movie.mp4" in names
        assert "track.MP3" in names
        assert "episode.MKV" in names
        assert "readme.txt" not in names
