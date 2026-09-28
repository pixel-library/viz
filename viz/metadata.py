"""
Local Media & Music Metadata Extractor for Viz Media Player.
Parses ID3 / Vorbis tags, ffprobe stream data, and Pillow image headers locally.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from viz.models import MediaItem, MediaType

# Attempt to import mutagen safely for audio tags
HAS_MUTAGEN = False
try:
    import mutagen
    HAS_MUTAGEN = True
except Exception:
    HAS_MUTAGEN = False


class MetadataExtractor:
    """Extracts local audio, video, and image metadata without external network calls."""

    @classmethod
    def enrich_metadata(cls, item: MediaItem) -> MediaItem:
        """Enrich MediaItem with local metadata (resolution, bitrate, artist, album, title, duration)."""
        if not item or not item.path.exists():
            return item

        if item.media_type == MediaType.AUDIO:
            cls._enrich_audio(item)
        elif item.media_type == MediaType.VIDEO:
            cls._enrich_video(item)
        elif item.media_type == MediaType.IMAGE:
            cls._enrich_image(item)

        return item

    @classmethod
    def _enrich_audio(cls, item: MediaItem) -> None:
        """Enrich audio metadata using Mutagen, ffprobe, or clean filename parsing."""
        if HAS_MUTAGEN:
            try:
                audio = mutagen.File(str(item.path.resolve()))
                if audio is not None:
                    if hasattr(audio, "info") and hasattr(audio.info, "length"):
                        item.duration = float(audio.info.length)
                    if hasattr(audio, "info") and hasattr(audio.info, "bitrate"):
                        item.bitrate = int(audio.info.bitrate)

                    tags = getattr(audio, "tags", {}) or {}
                    title = cls._get_tag(tags, ["TIT2", "title", "TITLE"])
                    if title:
                        item.title = str(title)

                    artist = cls._get_tag(tags, ["TPE1", "artist", "ARTIST"])
                    if artist:
                        item.artist = str(artist)

                    album = cls._get_tag(tags, ["TALB", "album", "ALBUM"])
                    if album:
                        item.album = str(album)

                    track = cls._get_tag(tags, ["TRCK", "tracknumber", "TRACKNUMBER"])
                    if track:
                        try:
                            item.track_num = int(str(track).split("/")[0])
                        except ValueError:
                            pass
            except Exception:
                pass

        # Use ffprobe if duration or bitrate still unpopulated
        if item.duration == 0.0:
            info = cls._probe_ffprobe(item.path)
            if info:
                fmt = info.get("format", {})
                if "duration" in fmt:
                    try:
                        item.duration = float(fmt["duration"])
                    except ValueError:
                        pass
                if "bit_rate" in fmt:
                    try:
                        item.bitrate = int(fmt["bit_rate"])
                    except ValueError:
                        pass

        if not item.title:
            stem = item.path.stem
            if " - " in stem:
                parts = stem.split(" - ", 1)
                item.artist = item.artist or parts[0].strip()
                item.title = parts[1].strip()
            else:
                item.title = stem

        if not item.artist and item.directory and item.directory.parent and item.directory.parent.name:
            item.artist = item.directory.parent.name
        if not item.album and item.directory:
            item.album = item.directory.name

    @classmethod
    def _enrich_video(cls, item: MediaItem) -> None:
        """Enrich video metadata using ffprobe."""
        if not item.title:
            item.title = item.path.stem

        if item.video_width == 0 or item.duration == 0.0:
            info = cls._probe_ffprobe(item.path)
            if info:
                fmt = info.get("format", {})
                if "duration" in fmt:
                    try:
                        item.duration = float(fmt["duration"])
                    except ValueError:
                        pass

                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "video":
                        if "width" in stream and "height" in stream:
                            item.video_width = int(stream["width"])
                            item.video_height = int(stream["height"])
                        break

    @classmethod
    def _enrich_image(cls, item: MediaItem) -> None:
        """Enrich image metadata using Pillow."""
        if item.image_width == 0:
            try:
                from PIL import Image
                with Image.open(item.path) as img:
                    item.image_width = img.width
                    item.image_height = img.height
                    item.image_format = img.format or item.extension.upper().lstrip(".")
            except Exception:
                pass

    @classmethod
    def _probe_ffprobe(cls, path: Path) -> dict:
        """Query file metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(path.resolve()),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0:
                return json.loads(res.stdout)
        except Exception:
            pass
        return {}

    @staticmethod
    def _get_tag(tags: dict, keys: list[str]) -> Optional[str]:
        for k in keys:
            if k in tags:
                val = tags[k]
                if isinstance(val, list) and val:
                    return str(val[0])
                return str(val)
        return None

