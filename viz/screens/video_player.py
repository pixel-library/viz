"""
Backward compatibility module for Video Virtual Environment.
Re-exports VideoEnvironment as VideoPlayerScreen.
"""

from viz.screens.video_environment import VideoEnvironment

VideoPlayerScreen = VideoEnvironment

__all__ = ["VideoEnvironment", "VideoPlayerScreen"]
