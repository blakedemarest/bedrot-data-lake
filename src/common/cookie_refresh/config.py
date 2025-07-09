"""Configuration loader for cookie refresh system.

This module handles loading configuration from YAML files and environment variables,
providing defaults for the cookie refresh automation system.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CookieRefreshConfig:
    """Configuration manager for cookie refresh system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to YAML configuration file. If None, uses default.
        """
        self.project_root = Path(os.environ.get('PROJECT_ROOT', os.getcwd()))
        self.data_lake_path = self.project_root / 'data_lake' if 'data_lake' not in str(self.project_root) else self.project_root
        
        # Default configuration path
        if config_path is None:
            config_path = self.data_lake_path / 'config' / 'cookie_refresh_config.yaml'
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with defaults."""
        defaults = self._get_defaults()
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f) or {}
                # Merge loaded config with defaults
                config = self._deep_merge(defaults, loaded_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config from {self.config_path}: {e}")
                config = defaults
        else:
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            config = defaults
            
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'general': {
                'check_interval_hours': 24,
                'expiration_warning_days': 7,
                'expiration_critical_days': 3,
                'backup_retention_days': 30,
                'max_refresh_attempts': 3,
                'browser_headless': False,  # Show browser for manual interventions
                'browser_timeout_seconds': 300,
                'screenshot_on_failure': True
            },
            'services': {
                'spotify': {
                    'enabled': True,
                    'refresh_strategy': 'spotify',
                    'expiration_days': 30,
                    'priority': 1,
                    'auth_url': 'https://accounts.spotify.com/login',
                    'requires_2fa': False
                },
                'distrokid': {
                    'enabled': True,
                    'refresh_strategy': 'distrokid',
                    'expiration_days': 90,
                    'priority': 2,
                    'auth_url': 'https://distrokid.com/signin',
                    'requires_2fa': False
                },
                'tiktok': {
                    'enabled': True,
                    'refresh_strategy': 'tiktok',
                    'expiration_days': 30,
                    'priority': 3,
                    'auth_url': 'https://www.tiktok.com/login',
                    'requires_2fa': True,
                    'accounts': ['pig1987', 'zone.a0']
                },
                'toolost': {
                    'enabled': True,
                    'refresh_strategy': 'toolost',
                    'expiration_days': 7,  # JWT expires weekly
                    'priority': 4,
                    'auth_url': 'https://app.toolost.com/login',
                    'requires_2fa': False
                },
                'linktree': {
                    'enabled': True,
                    'refresh_strategy': 'linktree',
                    'expiration_days': 30,
                    'priority': 5,
                    'auth_url': 'https://linktr.ee/login',
                    'requires_2fa': False
                },
                'metaads': {
                    'enabled': False,  # Not configured yet
                    'refresh_strategy': 'metaads',
                    'expiration_days': 90,
                    'priority': 6,
                    'auth_url': 'https://business.facebook.com',
                    'requires_2fa': True
                }
            },
            'notifications': {
                'enabled': True,
                'email': {
                    'enabled': False,
                    'smtp_host': os.environ.get('SMTP_HOST', ''),
                    'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
                    'smtp_user': os.environ.get('SMTP_USER', ''),
                    'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
                    'from_email': os.environ.get('NOTIFICATION_FROM_EMAIL', ''),
                    'to_emails': os.environ.get('NOTIFICATION_TO_EMAILS', '').split(',')
                },
                'console': {
                    'enabled': True,
                    'log_level': 'INFO'
                },
                'file': {
                    'enabled': True,
                    'log_path': str(self.data_lake_path / 'logs' / 'cookie_refresh.log')
                }
            },
            'paths': {
                'cookies_dir': str(self.data_lake_path / 'src'),
                'backup_dir': str(self.data_lake_path / 'backups' / 'cookies'),
                'logs_dir': str(self.data_lake_path / 'logs'),
                'screenshots_dir': str(self.data_lake_path / 'logs' / 'screenshots')
            }
        }
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # General settings
        if 'COOKIE_REFRESH_INTERVAL_HOURS' in os.environ:
            config['general']['check_interval_hours'] = int(os.environ['COOKIE_REFRESH_INTERVAL_HOURS'])
        
        if 'COOKIE_REFRESH_HEADLESS' in os.environ:
            config['general']['browser_headless'] = os.environ['COOKIE_REFRESH_HEADLESS'].lower() == 'true'
        
        # Service-specific overrides
        for service in config['services']:
            env_key = f'COOKIE_REFRESH_{service.upper()}_ENABLED'
            if env_key in os.environ:
                config['services'][service]['enabled'] = os.environ[env_key].lower() == 'true'
        
        return config
    
    def get_service_config(self, service: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service.
        
        Args:
            service: Service name (e.g., 'spotify', 'tiktok')
            
        Returns:
            Service configuration dict or None if not found
        """
        return self._config.get('services', {}).get(service)
    
    def get_enabled_services(self) -> List[str]:
        """Get list of enabled services sorted by priority.
        
        Returns:
            List of enabled service names
        """
        services = []
        for service, config in self._config.get('services', {}).items():
            if config.get('enabled', False):
                services.append((service, config.get('priority', 99)))
        
        # Sort by priority (lower number = higher priority)
        services.sort(key=lambda x: x[1])
        return [s[0] for s in services]
    
    def get_path(self, path_key: str) -> Path:
        """Get a configured path.
        
        Args:
            path_key: Key from paths configuration
            
        Returns:
            Path object
        """
        path_str = self._config.get('paths', {}).get(path_key, '')
        return Path(path_str) if path_str else self.data_lake_path
    
    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get a general configuration setting.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        return self._config.get('general', {}).get(key, default)
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration.
        
        Returns:
            Notification configuration dict
        """
        return self._config.get('notifications', {})
    
    @property
    def expiration_warning_timedelta(self) -> timedelta:
        """Get expiration warning threshold as timedelta."""
        days = self.get_general_setting('expiration_warning_days', 7)
        return timedelta(days=days)
    
    @property
    def expiration_critical_timedelta(self) -> timedelta:
        """Get critical expiration threshold as timedelta."""
        days = self.get_general_setting('expiration_critical_days', 3)
        return timedelta(days=days)


# Backward compatibility function
def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration in simplified format for backward compatibility.
    
    Args:
        config_path: Path to config file (optional)
        
    Returns:
        Configuration dictionary
    """
    config_manager = CookieRefreshConfig(config_path)
    return config_manager._config