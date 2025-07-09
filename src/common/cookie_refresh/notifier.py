"""Notification system for cookie refresh events.

This module provides a flexible notification system that can send alerts
through various channels (console, file, email, etc.) when cookies need
refreshing or when refresh attempts succeed/fail.
"""

import logging
import smtplib
import json
import time
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import os

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class NotificationEvent:
    """Container for notification events."""
    
    def __init__(self, 
                 service: str,
                 level: NotificationLevel,
                 message: str,
                 details: Optional[Dict[str, Any]] = None,
                 account: Optional[str] = None):
        """Initialize notification event.
        
        Args:
            service: Service name
            level: Notification severity level
            message: Main notification message
            details: Additional details dictionary
            account: Optional account identifier
        """
        self.service = service
        self.level = level
        self.message = message
        self.details = details or {}
        self.account = account
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'service': self.service,
            'account': self.account,
            'level': self.level.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
    
    def format_message(self, include_details: bool = True) -> str:
        """Format notification message.
        
        Args:
            include_details: Whether to include detailed information
            
        Returns:
            Formatted message string
        """
        parts = [
            f"[{self.level.value}]",
            f"[{self.service}" + (f"/{self.account}" if self.account else "") + "]",
            self.message
        ]
        
        message = " ".join(parts)
        
        if include_details and self.details:
            detail_lines = [f"  - {k}: {v}" for k, v in self.details.items()]
            message += "\n" + "\n".join(detail_lines)
            
        return message


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""
    
    @abstractmethod
    def send(self, event: NotificationEvent) -> bool:
        """Send notification through this channel.
        
        Args:
            event: Notification event to send
            
        Returns:
            True if notification sent successfully
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this channel is available for sending.
        
        Returns:
            True if channel is configured and available
        """
        pass


class ConsoleNotificationChannel(NotificationChannel):
    """Console/terminal notification channel."""
    
    def __init__(self, min_level: NotificationLevel = NotificationLevel.INFO):
        """Initialize console channel.
        
        Args:
            min_level: Minimum level to display
        """
        self.min_level = min_level
        self._level_map = {
            NotificationLevel.INFO: logging.INFO,
            NotificationLevel.WARNING: logging.WARNING,
            NotificationLevel.CRITICAL: logging.ERROR,
            NotificationLevel.ERROR: logging.ERROR,
            NotificationLevel.SUCCESS: logging.INFO
        }
    
    def send(self, event: NotificationEvent) -> bool:
        """Send notification to console."""
        try:
            message = event.format_message()
            log_level = self._level_map.get(event.level, logging.INFO)
            
            # Use appropriate logging level
            logger.log(log_level, message)
            
            # Also print to console for immediate visibility
            if event.level in [NotificationLevel.WARNING, NotificationLevel.CRITICAL, NotificationLevel.ERROR]:
                print(f"\n{'='*60}")
                print(message)
                print(f"{'='*60}\n")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send console notification: {e}")
            return False
    
    def is_available(self) -> bool:
        """Console is always available."""
        return True


class FileNotificationChannel(NotificationChannel):
    """File-based notification channel."""
    
    def __init__(self, log_path: Path):
        """Initialize file channel.
        
        Args:
            log_path: Path to notification log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def send(self, event: NotificationEvent) -> bool:
        """Send notification to file."""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(f"{event.timestamp.isoformat()} {event.format_message()}\n")
            return True
        except Exception as e:
            logger.error(f"Failed to write notification to file: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if file path is writable."""
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False


class EmailNotificationChannel(NotificationChannel):
    """Enhanced email notification channel with HTML templates and retry logic."""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        """Initialize email channel.
        
        Args:
            smtp_config: SMTP configuration dictionary
        """
        self.smtp_host = smtp_config.get('smtp_host', os.getenv('SMTP_HOST', ''))
        self.smtp_port = int(smtp_config.get('smtp_port', os.getenv('SMTP_PORT', 587)))
        self.smtp_user = smtp_config.get('smtp_user', os.getenv('SMTP_USER', ''))
        self.smtp_password = smtp_config.get('smtp_password', os.getenv('SMTP_PASSWORD', ''))
        self.from_email = smtp_config.get('from_email', os.getenv('SMTP_FROM', ''))
        self.to_emails = smtp_config.get('to_emails', os.getenv('SMTP_TO', '').split(','))
        self.use_tls = smtp_config.get('use_tls', True)
        self.max_retries = smtp_config.get('max_retries', 3)
        self.retry_delay = smtp_config.get('retry_delay', 5)  # seconds
    
    def send(self, event: NotificationEvent) -> bool:
        """Send notification via email with retry logic."""
        if not self.is_available():
            logger.warning("Email notification channel not properly configured")
            return False
        
        # Attempt to send with retries
        for attempt in range(self.max_retries):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['From'] = self.from_email
                msg['To'] = ', '.join(self.to_emails)
                msg['Subject'] = self._get_subject(event)
                msg['X-Priority'] = '1' if event.level == NotificationLevel.CRITICAL else '3'
                
                # Create both plain text and HTML versions
                text_body = self._create_text_body(event)
                html_body = self._create_html_body(event)
                
                # Attach parts
                msg.attach(MIMEText(text_body, 'plain'))
                msg.attach(MIMEText(html_body, 'html'))
                
                # Send email
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    if self.use_tls:
                        server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Email notification sent for {event.service} (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                logger.warning(f"Email send attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to send email after {self.max_retries} attempts: {e}")
                    return False
        
        return False
    
    def _get_subject(self, event: NotificationEvent) -> str:
        """Generate email subject based on event level and service."""
        emoji_map = {
            NotificationLevel.SUCCESS: '✅',
            NotificationLevel.INFO: 'ℹ️',
            NotificationLevel.WARNING: '⚠️',
            NotificationLevel.CRITICAL: '🚨',
            NotificationLevel.ERROR: '❌'
        }
        
        emoji = emoji_map.get(event.level, '')
        return f"{emoji} [BEDROT Pipeline] {event.level.value}: {event.service} - {event.message[:50]}"
    
    def _create_text_body(self, event: NotificationEvent) -> str:
        """Create plain text email body."""
        body = f"""
BEDROT Pipeline Notification
{'=' * 50}

Service: {event.service}
Account: {event.account or 'N/A'}
Severity: {event.level.value}
Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{event.message}

"""
        
        if event.details:
            body += "Details:\n"
            for key, value in event.details.items():
                body += f"  • {key}: {value}\n"
        
        body += f"\n\nView full pipeline status:\nhttps://your-dashboard-url/health\n"
        
        return body
    
    def _create_html_body(self, event: NotificationEvent) -> str:
        """Create HTML email body with enhanced formatting."""
        # Color scheme based on severity
        color_map = {
            NotificationLevel.SUCCESS: '#28a745',
            NotificationLevel.INFO: '#17a2b8',
            NotificationLevel.WARNING: '#ffc107',
            NotificationLevel.CRITICAL: '#dc3545',
            NotificationLevel.ERROR: '#dc3545'
        }
        
        accent_color = color_map.get(event.level, '#6c757d')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: {accent_color};
            color: white;
            padding: 20px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .content {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0 0 8px 8px;
            padding: 20px;
        }}
        .level-badge {{
            display: inline-block;
            background: {accent_color};
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        .details {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
        }}
        .detail-item {{
            margin: 8px 0;
            padding-left: 20px;
            position: relative;
        }}
        .detail-item:before {{
            content: '•';
            position: absolute;
            left: 0;
            color: {accent_color};
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #6c757d;
        }}
        .action-button {{
            display: inline-block;
            background: {accent_color};
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 4px;
            margin: 10px 5px;
        }}
        .timestamp {{
            font-size: 14px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0;">BEDROT Pipeline Alert</h2>
    </div>
    
    <div class="content">
        <p><span class="level-badge">{event.level.value}</span></p>
        
        <h3>Service: {event.service}{f' / {event.account}' if event.account else ''}</h3>
        
        <p class="timestamp">Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="details">
            <strong>Message:</strong>
            <p>{event.message}</p>
        </div>
"""
        
        if event.details:
            html += """
        <div class="details">
            <strong>Additional Details:</strong>
"""
            for key, value in event.details.items():
                html += f'            <div class="detail-item">{key}: {value}</div>\n'
            html += "        </div>\n"
        
        # Add action buttons based on event type
        if event.level in [NotificationLevel.CRITICAL, NotificationLevel.ERROR]:
            html += """
        <div style="text-align: center; margin: 20px 0;">
            <a href="https://your-dashboard-url/health" class="action-button">View Dashboard</a>
            <a href="https://your-docs-url/troubleshooting" class="action-button">Troubleshooting Guide</a>
        </div>
"""
        
        html += """
    </div>
    
    <div class="footer">
        <p>This is an automated notification from the BEDROT Data Pipeline.</p>
        <p>To manage notification preferences, visit your dashboard settings.</p>
    </div>
</body>
</html>
"""
        
        return html
    
    def is_available(self) -> bool:
        """Check if email is properly configured."""
        return all([
            self.smtp_host,
            self.from_email,
            self.to_emails
        ])


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel for Discord, Slack, etc."""
    
    def __init__(self, webhook_config: Dict[str, Any]):
        """Initialize webhook channel.
        
        Args:
            webhook_config: Webhook configuration dictionary
        """
        self.webhook_url = webhook_config.get('url', os.getenv('WEBHOOK_URL', ''))
        self.webhook_type = webhook_config.get('type', 'generic')  # discord, slack, generic
        self.timeout = webhook_config.get('timeout', 10)
        self.max_retries = webhook_config.get('max_retries', 3)
        self.retry_delay = webhook_config.get('retry_delay', 2)
    
    def send(self, event: NotificationEvent) -> bool:
        """Send notification via webhook."""
        if not self.is_available():
            logger.warning("Webhook notification channel not configured")
            return False
        
        # Format payload based on webhook type
        if self.webhook_type == 'discord':
            payload = self._format_discord_payload(event)
        elif self.webhook_type == 'slack':
            payload = self._format_slack_payload(event)
        else:
            payload = self._format_generic_payload(event)
        
        # Send with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"Webhook notification sent for {event.service}")
                    return True
                else:
                    logger.warning(f"Webhook returned status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Webhook timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"Webhook error on attempt {attempt + 1}: {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        logger.error(f"Failed to send webhook notification after {self.max_retries} attempts")
        return False
    
    def is_available(self) -> bool:
        """Check if webhook URL is configured."""
        return bool(self.webhook_url)
    
    def _format_discord_payload(self, event: NotificationEvent) -> Dict[str, Any]:
        """Format payload for Discord webhook."""
        color_map = {
            NotificationLevel.SUCCESS: 0x28a745,
            NotificationLevel.INFO: 0x17a2b8,
            NotificationLevel.WARNING: 0xffc107,
            NotificationLevel.CRITICAL: 0xdc3545,
            NotificationLevel.ERROR: 0xdc3545
        }
        
        embed = {
            "title": f"Pipeline Alert: {event.service}",
            "description": event.message,
            "color": color_map.get(event.level, 0x6c757d),
            "timestamp": event.timestamp.isoformat(),
            "fields": [
                {
                    "name": "Service",
                    "value": event.service,
                    "inline": True
                },
                {
                    "name": "Level",
                    "value": event.level.value,
                    "inline": True
                }
            ]
        }
        
        if event.account:
            embed["fields"].append({
                "name": "Account",
                "value": event.account,
                "inline": True
            })
        
        if event.details:
            for key, value in event.details.items():
                embed["fields"].append({
                    "name": key.replace('_', ' ').title(),
                    "value": str(value),
                    "inline": False
                })
        
        return {"embeds": [embed]}
    
    def _format_slack_payload(self, event: NotificationEvent) -> Dict[str, Any]:
        """Format payload for Slack webhook."""
        emoji_map = {
            NotificationLevel.SUCCESS: ':white_check_mark:',
            NotificationLevel.INFO: ':information_source:',
            NotificationLevel.WARNING: ':warning:',
            NotificationLevel.CRITICAL: ':rotating_light:',
            NotificationLevel.ERROR: ':x:'
        }
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji_map.get(event.level, '')} Pipeline Alert: {event.service}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Level:* {event.level.value}\n*Message:* {event.message}\n*Time:* {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
        
        if event.details:
            detail_text = "\n".join([f"• *{k}:* {v}" for k, v in event.details.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n{detail_text}"
                }
            })
        
        return {"blocks": blocks}
    
    def _format_generic_payload(self, event: NotificationEvent) -> Dict[str, Any]:
        """Format generic webhook payload."""
        return event.to_dict()


class CookieRefreshNotifier:
    """Enhanced notification orchestrator with multi-channel support."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize notifier with configuration.
        
        Args:
            config: Notification configuration dictionary
        """
        self.config = config
        self.channels: List[NotificationChannel] = []
        self._notification_history: List[NotificationEvent] = []
        self._setup_channels()
    
    def _setup_channels(self):
        """Set up notification channels based on configuration."""
        # Console channel
        if self.config.get('console', {}).get('enabled', True):
            self.channels.append(ConsoleNotificationChannel())
        
        # File channel
        if self.config.get('file', {}).get('enabled', False):
            log_path = self.config['file'].get('log_path', 'logs/notifications.log')
            self.channels.append(FileNotificationChannel(Path(log_path)))
        
        # Email channel
        if self.config.get('email', {}).get('enabled', False):
            email_config = self.config['email']
            self.channels.append(EmailNotificationChannel(email_config))
        
        # Webhook channel
        if self.config.get('webhook', {}).get('enabled', False):
            webhook_config = self.config['webhook']
            self.channels.append(WebhookNotificationChannel(webhook_config))
        
        logger.info(f"Initialized {len(self.channels)} notification channels")
    
    def notify_expiration_warning(self, service: str, days_until_expiration: int,
                                 account: Optional[str] = None):
        """Send notification about upcoming cookie expiration.
        
        Args:
            service: Service name
            days_until_expiration: Days until cookies expire
            account: Optional account identifier
        """
        level = NotificationLevel.CRITICAL if days_until_expiration <= 3 else NotificationLevel.WARNING
        
        event = NotificationEvent(
            service=service,
            account=account,
            level=level,
            message=f"Cookies will expire in {days_until_expiration} days",
            details={
                'days_remaining': days_until_expiration,
                'action_required': 'Manual refresh may be needed'
            }
        )
        
        self._send_to_channels(event)
    
    def notify_refresh_started(self, service: str, account: Optional[str] = None):
        """Notify that cookie refresh has started.
        
        Args:
            service: Service name
            account: Optional account identifier
        """
        event = NotificationEvent(
            service=service,
            account=account,
            level=NotificationLevel.INFO,
            message="Cookie refresh started"
        )
        
        self._send_to_channels(event)
    
    def notify_refresh_success(self, service: str, account: Optional[str] = None,
                              details: Optional[Dict[str, Any]] = None):
        """Notify successful cookie refresh.
        
        Args:
            service: Service name
            account: Optional account identifier
            details: Additional success details
        """
        event = NotificationEvent(
            service=service,
            account=account,
            level=NotificationLevel.SUCCESS,
            message="Cookie refresh completed successfully",
            details=details
        )
        
        self._send_to_channels(event)
    
    def notify_refresh_failed(self, service: str, error: str,
                             account: Optional[str] = None,
                             details: Optional[Dict[str, Any]] = None):
        """Notify failed cookie refresh.
        
        Args:
            service: Service name
            error: Error message
            account: Optional account identifier
            details: Additional failure details
        """
        event = NotificationEvent(
            service=service,
            account=account,
            level=NotificationLevel.ERROR,
            message=f"Cookie refresh failed: {error}",
            details=details
        )
        
        self._send_to_channels(event)
    
    def notify_manual_intervention_required(self, service: str, reason: str,
                                          account: Optional[str] = None):
        """Notify that manual intervention is required.
        
        Args:
            service: Service name
            reason: Reason for manual intervention
            account: Optional account identifier
        """
        event = NotificationEvent(
            service=service,
            account=account,
            level=NotificationLevel.CRITICAL,
            message=f"Manual intervention required: {reason}",
            details={
                'action': 'Please refresh cookies manually',
                'reason': reason
            }
        )
        
        self._send_to_channels(event)
    
    def notify_all_services_status(self, status_list: List[Dict[str, Any]]):
        """Send summary notification of all services status.
        
        Args:
            status_list: List of service status dictionaries
        """
        expired_count = sum(1 for s in status_list if s.get('is_expired', False))
        warning_count = sum(1 for s in status_list if s.get('status') == 'WARNING')
        critical_count = sum(1 for s in status_list if s.get('status') == 'CRITICAL')
        
        level = NotificationLevel.INFO
        if expired_count > 0:
            level = NotificationLevel.ERROR
        elif critical_count > 0:
            level = NotificationLevel.CRITICAL
        elif warning_count > 0:
            level = NotificationLevel.WARNING
        
        event = NotificationEvent(
            service='SYSTEM',
            level=level,
            message=f"Cookie status summary: {expired_count} expired, {critical_count} critical, {warning_count} warnings",
            details={
                'total_services': len(status_list),
                'expired': expired_count,
                'critical': critical_count,
                'warnings': warning_count,
                'services': [s['service'] for s in status_list if s.get('is_expired', False)]
            }
        )
        
        self._send_to_channels(event)
    
    def _send_to_channels(self, event: NotificationEvent):
        """Send notification to all configured channels.
        
        Args:
            event: Notification event to send
        """
        # Add to history
        self._notification_history.append(event)
        
        # Limit history size
        if len(self._notification_history) > 1000:
            self._notification_history = self._notification_history[-500:]
        
        # Send to all channels
        success_count = 0
        for channel in self.channels:
            try:
                if channel.is_available():
                    if channel.send(event):
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending notification through {channel.__class__.__name__}: {e}")
        
        # Log summary
        if success_count == 0:
            logger.error(f"Failed to send notification through any channel for {event.service}")
        else:
            logger.info(f"Notification sent through {success_count}/{len(self.channels)} channels")
    
    def get_notification_history(self, service: Optional[str] = None, 
                               limit: int = 100) -> List[NotificationEvent]:
        """Get notification history.
        
        Args:
            service: Filter by service name (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of notification events
        """
        history = self._notification_history
        
        if service:
            history = [e for e in history if e.service == service]
        
        return history[-limit:]
    
    def send_custom_notification(self, level: NotificationLevel, message: str,
                               service: str = "SYSTEM", 
                               details: Optional[Dict[str, Any]] = None):
        """Send a custom notification.
        
        Args:
            level: Notification severity level
            message: Notification message
            service: Service name (defaults to SYSTEM)
            details: Additional details
        """
        event = NotificationEvent(
            service=service,
            level=level,
            message=message,
            details=details
        )
        
        self._send_to_channels(event)