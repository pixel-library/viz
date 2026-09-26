"""
Smart TV Series Detection & Episode Grouping for Viz Media Player.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from viz.models import MediaItem, MediaType


@dataclass
class SeriesEpisode:
    media_item: MediaItem
    season_num: int
    episode_num: int
    title: str


@dataclass
class SeriesGroup:
    name: str
    seasons: Dict[int, List[SeriesEpisode]] = field(default_factory=dict)

    @property
    def total_episodes(self) -> int:
        return sum(len(episodes) for episodes in self.seasons.values())

    @property
    def season_count(self) -> int:
        return len(self.seasons)


class SeriesDetector:
    """Detects TV show episode naming patterns and groups files into series structures."""

    PATTERNS = [
        # S01E01 or s01e01
        re.compile(r"^(?P<show>.+?)[._\s-]+[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})(?:[._\s-]+(?P<title>.+))?$", re.IGNORECASE),
        # 1x01
        re.compile(r"^(?P<show>.+?)[._\s-]+(?P<season>\d{1,2})x(?P<episode>\d{1,2})(?:[._\s-]+(?P<title>.+))?$", re.IGNORECASE),
        # Season 01/Episode 01 or Ep01
        re.compile(r"^(?P<show>.+?)[._\s-]+[eE][pP]?(?P<episode>\d{1,2})(?:[._\s-]+(?P<title>.+))?$", re.IGNORECASE),
    ]

    @classmethod
    def parse_item(cls, item: MediaItem) -> Optional[SeriesEpisode]:
        """Attempt to parse SeriesEpisode metadata from filename or directory path."""
        if item.media_type != MediaType.VIDEO:
            return None

        filename = item.path.stem

        for pattern in cls.PATTERNS:
            match = pattern.match(filename)
            if match:
                groups = match.groupdict()
                raw_show = groups.get("show", "").replace(".", " ").replace("_", " ").strip()
                show_name = raw_show.title() if raw_show else item.directory.name.title()
                season_num = int(groups.get("season") or 1)
                episode_num = int(groups.get("episode") or 1)
                raw_title = groups.get("title")
                ep_title = raw_title.replace(".", " ").replace("_", " ").strip().title() if raw_title else f"Episode {episode_num}"

                item.series_name = show_name
                item.season_num = season_num
                item.episode_num = episode_num
                item.episode_title = ep_title

                return SeriesEpisode(
                    media_item=item,
                    season_num=season_num,
                    episode_num=episode_num,
                    title=ep_title,
                )

        # Fallback: Check parent folder name if named "Season 1" or "Season 01"
        parent_name = item.directory.name
        season_match = re.match(r"Season\s*(\d+)", parent_name, re.IGNORECASE)
        if season_match:
            season_num = int(season_match.group(1))
            show_name = item.directory.parent.name.title()
            
            # Try finding episode number in filename
            ep_match = re.search(r"\b(\d{1,2})\b", filename)
            episode_num = int(ep_match.group(1)) if ep_match else 1
            
            item.series_name = show_name
            item.season_num = season_num
            item.episode_num = episode_num
            item.episode_title = f"Episode {episode_num}"

            return SeriesEpisode(
                media_item=item,
                season_num=season_num,
                episode_num=episode_num,
                title=f"Episode {episode_num}",
            )

        return None

    @classmethod
    def group_series(cls, items: List[MediaItem]) -> Dict[str, SeriesGroup]:
        """Group list of MediaItems into SeriesGroup map."""
        groups: Dict[str, SeriesGroup] = {}

        for item in items:
            parsed = cls.parse_item(item)
            if parsed:
                show_name = item.series_name or "Unknown Series"
                if show_name not in groups:
                    groups[show_name] = SeriesGroup(name=show_name)

                s_group = groups[show_name]
                s_num = parsed.season_num
                if s_num not in s_group.seasons:
                    s_group.seasons[s_num] = []

                s_group.seasons[s_num].append(parsed)

        # Sort episodes within each season
        for s_group in groups.values():
            for s_num in s_group.seasons:
                s_group.seasons[s_num].sort(key=lambda ep: ep.episode_num)

        return groups
