"""vitools — kit de criação de vídeos verticais (Reels/Stories) com identidade de marca.

Fluxo: fotos + logo + um arquivo JSON de projeto  →  MP4 1080x1920 renderizado com ffmpeg.
"""
from .engine import render_project, load_project

__all__ = ["render_project", "load_project"]
__version__ = "1.0.0"
