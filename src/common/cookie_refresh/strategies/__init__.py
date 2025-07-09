"""Cookie refresh strategies for different services.

Each service has its own strategy implementation that handles
the specific authentication flow and requirements.
"""

from .base import BaseRefreshStrategy, RefreshResult
from .distrokid import DistroKidRefreshStrategy
from .spotify import SpotifyRefreshStrategy
from .tiktok import TikTokRefreshStrategy
from .toolost import TooLostRefreshStrategy
from .linktree import LinktreeRefreshStrategy

__all__ = [
    'BaseRefreshStrategy',
    'RefreshResult',
    'DistroKidRefreshStrategy',
    'SpotifyRefreshStrategy',
    'TikTokRefreshStrategy',
    'TooLostRefreshStrategy',
    'LinktreeRefreshStrategy'
]