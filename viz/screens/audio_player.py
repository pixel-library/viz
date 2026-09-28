"""
Backward compatibility module for Audio Virtual Environment.
Re-exports AudioEnvironment as AudioPlayerScreen.
"""

from viz.screens.audio_environment import AudioEnvironment

AudioPlayerScreen = AudioEnvironment

__all__ = ["AudioEnvironment", "AudioPlayerScreen"]
