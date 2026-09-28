"""
Backward compatibility module for Image Virtual Environment.
Re-exports ImageEnvironment as ImageViewerScreen.
"""

from viz.screens.image_environment import ImageEnvironment

ImageViewerScreen = ImageEnvironment

__all__ = ["ImageEnvironment", "ImageViewerScreen"]
