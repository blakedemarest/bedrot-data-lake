#!/usr/bin/env python3
"""
Simple configuration loader for backward compatibility.

This module provides a load_config() function that returns configuration
in the expected format for existing code.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Also try notification-specific env file
notif_env_path = Path(__file__).parent.parent.parent / '.env.notification'
if notif_env_path.exists():
    load_dotenv(notif_env_path)


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file with environment variable overrides.
    
    This function provides backward compatibility with the original config.py
    interface while adding environment variable support.
    
    Args:
        config_path: Path to config file (defaults to config/cookie_refresh_config.json)
        
    Returns:
        Configuration dictionary with environment overrides applied
    """
    # Default path
    if config_path is None:
        project_root = Path(os.environ.get('PROJECT_ROOT', os.getcwd()))
        data_lake_path = project_root / 'data_lake' if 'data_lake' not in str(project_root) else project_root
        config_path = data_lake_path / 'config' / 'cookie_refresh_config.json'
    
    # Create default config structure
    config = {
        'services': [],
        'notifications': {},
        'settings': {},
        'paths': {}
    }
    
    # Load from JSON if exists
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                for key, value in loaded_config.items():
                    if isinstance(value, dict) and key in config:
                        config[key].update(value)
                    else:
                        config[key] = value
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    # Apply environment variable overrides for notifications
    
    # Email configuration from environment
    if os.getenv('SMTP_HOST'):
        config['notifications']['email'] = {
            'enabled': True,
            'smtp_host': os.getenv('SMTP_HOST'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'smtp_user': os.getenv('SMTP_USER'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('SMTP_FROM'),
            'to_emails': os.getenv('SMTP_TO', '').split(',') if os.getenv('SMTP_TO') else [],
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            'max_retries': int(os.getenv('SMTP_MAX_RETRIES', 3)),
            'retry_delay': int(os.getenv('SMTP_RETRY_DELAY', 5))
        }
    
    # Webhook configuration from environment
    if os.getenv('WEBHOOK_URL'):
        config['notifications']['webhook'] = {
            'enabled': True,
            'url': os.getenv('WEBHOOK_URL'),
            'type': os.getenv('WEBHOOK_TYPE', 'generic'),
            'timeout': int(os.getenv('WEBHOOK_TIMEOUT', 10)),
            'max_retries': int(os.getenv('WEBHOOK_MAX_RETRIES', 3)),
            'retry_delay': int(os.getenv('WEBHOOK_RETRY_DELAY', 2))
        }
    
    # Console and file notifications
    if 'console' not in config['notifications']:
        config['notifications']['console'] = {}
    config['notifications']['console']['enabled'] = os.getenv('NOTIFY_CONSOLE', 'true').lower() == 'true'
    
    if 'file' not in config['notifications']:
        config['notifications']['file'] = {}
    config['notifications']['file']['enabled'] = os.getenv('NOTIFY_FILE', 'true').lower() == 'true'
    config['notifications']['file']['log_path'] = os.getenv('NOTIFY_LOG_PATH', 'logs/notifications.log')
    
    # Notification preferences
    config['notification_preferences'] = {
        'on_success': os.getenv('NOTIFY_ON_SUCCESS', 'false').lower() == 'true',
        'on_warning': os.getenv('NOTIFY_ON_WARNING', 'true').lower() == 'true',
        'on_critical': os.getenv('NOTIFY_ON_CRITICAL', 'true').lower() == 'true',
        'on_error': os.getenv('NOTIFY_ON_ERROR', 'true').lower() == 'true'
    }
    
    # Health monitor settings
    config['health_monitor'] = {
        'check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', 30)),
        'enable_auto_remediation': os.getenv('ENABLE_AUTO_REMEDIATION', 'true').lower() == 'true',
        'enable_daily_summary': os.getenv('ENABLE_DAILY_SUMMARY', 'true').lower() == 'true',
        'daily_summary_time': os.getenv('DAILY_SUMMARY_TIME', '09:00')
    }
    
    # Log settings
    config['logging'] = {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'retention_days': int(os.getenv('LOG_RETENTION_DAYS', 30)),
        'enable_structured': os.getenv('ENABLE_STRUCTURED_LOGS', 'true').lower() == 'true'
    }
    
    # If no services defined in config, use defaults
    if not config.get('services'):
        config['services'] = [
            {
                'name': 'spotify',
                'cookie_max_age_days': 30,
                'priority': 'high',
                'auto_refresh': False,
                'manual_login_url': 'https://accounts.spotify.com/login'
            },
            {
                'name': 'tiktok',
                'cookie_max_age_days': 30,
                'priority': 'high',
                'auto_refresh': False,
                'multi_account': True,
                'accounts': [
                    {'name': 'pig1987'},
                    {'name': 'zone.a0'}
                ],
                'manual_login_url': 'https://www.tiktok.com/login'
            },
            {
                'name': 'distrokid',
                'cookie_max_age_days': 30,
                'priority': 'medium',
                'auto_refresh': False,
                'manual_login_url': 'https://distrokid.com/signin'
            },
            {
                'name': 'toolost',
                'cookie_max_age_days': 7,
                'priority': 'critical',
                'auto_refresh': True,
                'manual_login_url': 'https://app.toolost.com/login'
            },
            {
                'name': 'linktree',
                'cookie_max_age_days': 30,
                'priority': 'medium',
                'auto_refresh': False,
                'manual_login_url': 'https://linktr.ee/login'
            },
            {
                'name': 'metaads',
                'cookie_max_age_days': 90,
                'priority': 'low',
                'auto_refresh': False,
                'manual_login_url': 'https://business.facebook.com'
            }
        ]
    
    return config