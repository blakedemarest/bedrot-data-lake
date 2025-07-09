"""Cookie refresh automation system for BEDROT data ecosystem.

This package provides automated cookie refresh functionality to prevent
pipeline failures due to expired authentication.
"""

from .config import CookieRefreshConfig
from .storage import CookieStorageManager, AuthStateInfo, CookieInfo
from .notifier import CookieRefreshNotifier, NotificationLevel, NotificationEvent
from .refresher import CookieRefresher

__all__ = [
    'CookieRefreshConfig',
    'CookieStorageManager',
    'AuthStateInfo',
    'CookieInfo',
    'CookieRefreshNotifier',
    'NotificationLevel',
    'NotificationEvent',
    'CookieRefresher'
]

__version__ = '1.0.0'