"""
Screens module for Viz Media Player.
"""

from viz.screens.discovery import DiscoveryScreen
from viz.screens.help import HelpScreen
from viz.screens.image_viewer import ImageViewerScreen
from viz.screens.video_player import VideoPlayerScreen
from viz.screens.audio_player import AudioPlayerScreen
from viz.screens.info import InfoScreen
from viz.screens.library_paths import DirectorySelectorModal, LibraryPathsScreen

__all__ = [
    "DiscoveryScreen",
    "HelpScreen",
    "InfoScreen",
    "ImageViewerScreen",
    "VideoPlayerScreen",
    "AudioPlayerScreen",
    "LibraryPathsScreen",
    "DirectorySelectorModal",
]

