"""
Playback Queue & Playlist Manager for Viz Media Player.
Manages up-next queue, playback sequence, shuffle, loop modes, next/previous navigation.
"""

from __future__ import annotations

import random
from typing import List, Optional

from viz.models import LoopMode, MediaItem


class PlaybackQueue:
    """Manages active playback queue and sequence logic."""

    def __init__(self) -> None:
        self.current_item: Optional[MediaItem] = None
        self.up_next: List[MediaItem] = []
        self.history: List[MediaItem] = []
        self._original_up_next: List[MediaItem] = []
        
        self.loop_mode: LoopMode = LoopMode.OFF
        self.is_shuffle: bool = False

    def set_current(self, item: MediaItem) -> None:
        """Set active item and add to history."""
        if self.current_item and self.current_item != item:
            self.history.append(self.current_item)
        self.current_item = item

    def add(self, item: MediaItem) -> None:
        """Append item to end of queue."""
        self.up_next.append(item)
        self._original_up_next.append(item)

    def add_next(self, item: MediaItem) -> None:
        """Insert item at front of queue."""
        self.up_next.insert(0, item)
        self._original_up_next.insert(0, item)

    def set_queue(self, items: List[MediaItem], start_index: int = 0) -> Optional[MediaItem]:
        """Set entire list as queue starting at start_index."""
        if not items or start_index < 0 or start_index >= len(items):
            return None

        self.current_item = items[start_index]
        self.up_next = items[start_index + 1 :]
        self.history = items[:start_index]
        self._original_up_next = list(self.up_next)

        if self.is_shuffle:
            random.shuffle(self.up_next)

        return self.current_item

    def remove(self, index: int) -> bool:
        """Remove item at index from queue."""
        if 0 <= index < len(self.up_next):
            item = self.up_next.pop(index)
            if item in self._original_up_next:
                self._original_up_next.remove(item)
            return True
        return False

    def clear(self) -> None:
        """Clear queue."""
        self.up_next.clear()
        self._original_up_next.clear()

    def get_next(self) -> Optional[MediaItem]:
        """
        Determine and return next MediaItem based on loop & shuffle modes.
        """
        # Loop Current File
        if self.loop_mode == LoopMode.ONE and self.current_item:
            return self.current_item

        # Up Next has items
        if self.up_next:
            next_item = self.up_next.pop(0)
            if self.current_item:
                self.history.append(self.current_item)
            self.current_item = next_item
            return next_item

        # Loop Queue
        if self.loop_mode == LoopMode.ALL and (self.history or self.current_item):
            all_items = list(self.history)
            if self.current_item:
                all_items.append(self.current_item)

            if all_items:
                if self.is_shuffle:
                    random.shuffle(all_items)
                
                self.current_item = all_items[0]
                self.up_next = all_items[1:]
                self.history.clear()
                return self.current_item

        return None

    def get_previous(self) -> Optional[MediaItem]:
        """Return previous MediaItem from history."""
        if self.history:
            prev_item = self.history.pop()
            if self.current_item:
                self.up_next.insert(0, self.current_item)
            self.current_item = prev_item
            return prev_item
        elif self.current_item:
            return self.current_item
        return None

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode on / off."""
        self.is_shuffle = not self.is_shuffle
        if self.is_shuffle:
            random.shuffle(self.up_next)
        else:
            self.up_next = list(self._original_up_next)
        return self.is_shuffle

    def cycle_loop(self) -> LoopMode:
        """Cycle loop mode: OFF -> ONE -> ALL -> OFF."""
        if self.loop_mode == LoopMode.OFF:
            self.loop_mode = LoopMode.ONE
        elif self.loop_mode == LoopMode.ONE:
            self.loop_mode = LoopMode.ALL
        else:
            self.loop_mode = LoopMode.OFF
        return self.loop_mode
