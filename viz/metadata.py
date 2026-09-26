"""
Local Media & Music Metadata Extractor for Viz Media Player.
Parses ID3 / Vorbis tags locally using mutagen if available, or falls back to clean filename parsing.
"""

from __future__ import annotations

import os
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
    """Extracts local audio and video metadata without external network calls."""

    @classmethod
    def enrich_metadata(cls, item: MediaItem) -> MediaItem:
        """Enrich MediaItem with local metadata (artist, album, title, duration)."""
        if not item or not item.path.exists():
            return item

        if item.media_type == MediaType.AUDIO:
            cls._enrich_audio(item)
        elif item.media_type == MediaType.VIDEO:
            cls._enrich_video(item)

        return item

    @classmethod
    def _enrich_audio(cls, item: MediaItem) -> None:
        """Enrich audio metadata using Mutagen or clean filename parsing."""
        if HAS_MUTAGEN:
            try:
                audio = mutagen.File(str(item.path.resolve()))
                if audio is not None:
                    if hasattr(audio, "info") and hasattr(audio.info, "length"):
                        item.duration = float(audio.info.length)

                    # Extract common tags (ID3 / Vorbis)
                    tags = getattr(audio, "tags", {}) or {}
                    
                    # Title
                    title = cls._get_tag(tags, ["TIT2", "title", "TITLE"])
                    if title:
                        item.title = str(title)

                    # Artist
                    artist = cls._get_tag(tags, ["TPE1", "artist", "ARTIST"])
                    if artist:
                        item.artist = str(artist)

                    # Album
                    album = cls._get_tag(tags, ["TALB", "album", "ALBUM"])
                    if album:
                        item.album = str(album)

                    # Track Number
                    track = cls._get_tag(tags, ["TRCK", "tracknumber", "TRACKNUMBER"])
                    if track:
                        try:
                            item.track_num = int(str(track).split("/")[0])
                        except ValueError:
                            pass
            except Exception:
                pass

        # Fallback to filename pattern parsing if metadata missing
        if not item.title:
            stem = item.path.stem
            if " - " in stem:
                parts = stem.split(" - ", 1)
                item.artist = item.artist or parts[0].strip()
                item.title = parts[1].strip()
            else:
                item.title = stem

        if not item.artist and item.directory.parent.name:
            item.artist = item.directory.parent.name
        if not item.album:
            item.album = item.directory.name

    @classmethod
    def _enrich_video(cls, item: MediaItem) -> None:
        """Enrich video metadata."""
        if not item.title:
            item.title = item.path.stem

    @staticmethod
    def _get_tag(tags: dict, keys: list[str]) -> Optional[str]:
        for k in keys:
            if k in tags:
                val = tags[k]
                if isinstance(val, list) and val:
                    return str(val[0])
                return str(val)
        return None
