"""
UI Widgets module for Viz Media Player.
"""

from viz.widgets.details import DetailsWidget
from viz.widgets.footer import ContextualFooter
from viz.widgets.header import HeaderWidget
from viz.widgets.media_list import MediaListWidget
from viz.widgets.player_status import PlayerStatusWidget
from viz.widgets.search import SearchWidget
from viz.widgets.sidebar import SidebarWidget

__all__ = [
    "HeaderWidget",
    "SearchWidget",
    "SidebarWidget",
    "MediaListWidget",
    "DetailsWidget",
    "PlayerStatusWidget",
    "ContextualFooter",
]
