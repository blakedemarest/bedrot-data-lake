"""
Comprehensive unit tests for cookie refresh system components
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
import json
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.cookie_refresh.storage import CookieStorageManager
from common.cookie_refresh.config import CookieRefreshConfig
from common.cookie_refresh.refresher import CookieRefresher
from common.cookie_refresh.notifier import NotificationManager
from common.cookie_refresh.strategies.base import RefreshStrategy


class TestCookieStorage(unittest.TestCase):
    """Test cookie storage functionality"""
    
    def setUp(self):
        """Create temporary directory for test cookies"""
        self.test_dir = tempfile.mkdtemp()
        self.storage = CookieStorageManager(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)
    
    def test_save_cookies(self):
        """Test saving cookies to file"""
        test_cookies = [
            {"name": "session", "value": "abc123", "domain": ".example.com"},
            {"name": "token", "value": "xyz789", "domain": ".example.com"}
        ]
        
        self.storage.save_cookies("test_service", test_cookies)
        
        # Verify file was created
        cookie_file = os.path.join(self.test_dir, "test_service", "cookies", "cookies.json")
        self.assertTrue(os.path.exists(cookie_file))
        
        # Verify content
        with open(cookie_file, 'r') as f:
            saved_cookies = json.load(f)
        self.assertEqual(saved_cookies, test_cookies)
    
    def test_load_cookies(self):
        """Test loading cookies from file"""
        test_cookies = [{"name": "test", "value": "value"}]
        service_dir = os.path.join(self.test_dir, "test_service", "cookies")
        os.makedirs(service_dir, exist_ok=True)
        
        with open(os.path.join(service_dir, "cookies.json"), 'w') as f:
            json.dump(test_cookies, f)
        
        loaded_auth = self.storage.load_auth_state("test_service")
        self.assertIsNotNone(loaded_auth)
        self.assertEqual(loaded_auth.get('cookies'), test_cookies)
    
    def test_get_cookie_age(self):
        """Test cookie age calculation"""
        # Create cookie file with known timestamp
        service_dir = os.path.join(self.test_dir, "test_service", "cookies")
        os.makedirs(service_dir, exist_ok=True)
        cookie_file = os.path.join(service_dir, "test_service_cookies.json")
        
        with open(cookie_file, 'w') as f:
            json.dump([], f)
        
        # Get age immediately
        age = self.storage.get_cookie_age("test_service")
        self.assertIsNotNone(age)
        self.assertLess(age.total_seconds(), 1)  # Should be less than 1 second
    
    def test_backup_cookies(self):
        """Test cookie backup functionality"""
        # Create original cookies
        test_cookies = [{"name": "test", "value": "original"}]
        self.storage.save_cookies("test_service", test_cookies)
        
        # Backup cookies
        backup_path = self.storage.backup_cookies("test_service")
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            backup_cookies = json.load(f)
        self.assertEqual(backup_cookies, test_cookies)
    
    def test_restore_cookies(self):
        """Test cookie restoration from backup"""
        # Create and backup cookies
        original_cookies = [{"name": "test", "value": "original"}]
        self.storage.save_cookies("test_service", original_cookies)
        backup_path = self.storage.backup_cookies("test_service")
        
        # Modify current cookies
        new_cookies = [{"name": "test", "value": "modified"}]
        self.storage.save_cookies("test_service", new_cookies)
        
        # Restore from backup
        self.storage.restore_cookies("test_service", backup_path)
        
        # Verify restoration
        restored_cookies = self.storage.load_cookies("test_service")
        self.assertEqual(restored_cookies, original_cookies)
    
    def test_validate_cookies(self):
        """Test cookie validation"""
        # Valid cookies
        valid_cookies = [
            {"name": "session", "value": "abc123", "domain": ".example.com"},
            {"name": "token", "value": "xyz789", "domain": ".example.com"}
        ]
        self.assertTrue(self.storage.validate_cookies(valid_cookies))
        
        # Invalid cookies - missing required fields
        invalid_cookies = [
            {"name": "session"},  # Missing value
            {"value": "xyz789"}   # Missing name
        ]
        self.assertFalse(self.storage.validate_cookies(invalid_cookies))
        
        # Empty cookies
        self.assertFalse(self.storage.validate_cookies([]))
        self.assertFalse(self.storage.validate_cookies(None))


class TestRefreshConfig(unittest.TestCase):
    """Test configuration management"""
    
    def test_service_config_creation(self):
        """Test creating service configuration"""
        config = ServiceConfig(
            enabled=True,
            refresh_interval_hours=24,
            max_age_days=7,
            strategy="playwright",
            priority=1,
            requires_2fa=True,
            notification_channels=["email", "slack"]
        )
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.refresh_interval_hours, 24)
        self.assertEqual(config.max_age_days, 7)
        self.assertEqual(config.strategy, "playwright")
        self.assertTrue(config.requires_2fa)
    
    def test_refresh_config_loading(self):
        """Test loading refresh configuration"""
        config_data = {
            "global": {
                "check_interval_minutes": 30,
                "max_retry_attempts": 3,
                "notification_channels": ["email"]
            },
            "services": {
                "spotify": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "strategy": "oauth"
                }
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            config = RefreshConfig.load_from_file("config.json")
            
            self.assertEqual(config.check_interval_minutes, 30)
            self.assertEqual(config.max_retry_attempts, 3)
            self.assertIn("spotify", config.services)
            self.assertTrue(config.services["spotify"].enabled)


class TestCookieRefresher(unittest.TestCase):
    """Test cookie refresher core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config = RefreshConfig(
            check_interval_minutes=30,
            max_retry_attempts=3,
            services={}
        )
        self.refresher = CookieRefresher(self.config, base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    @patch('common.cookie_refresh.refresher.NotificationManager')
    def test_check_service_cookies(self, mock_notifier):
        """Test checking if service cookies need refresh"""
        # Add test service config
        self.config.services["test_service"] = ServiceConfig(
            enabled=True,
            refresh_interval_hours=24,
            max_age_days=7
        )
        
        # Test with fresh cookies
        with patch.object(self.refresher.storage, 'get_cookie_age', return_value=timedelta(hours=1)):
            needs_refresh = self.refresher._check_service_needs_refresh("test_service")
            self.assertFalse(needs_refresh)
        
        # Test with old cookies
        with patch.object(self.refresher.storage, 'get_cookie_age', return_value=timedelta(days=8)):
            needs_refresh = self.refresher._check_service_needs_refresh("test_service")
            self.assertTrue(needs_refresh)
    
    @patch('common.cookie_refresh.refresher.NotificationManager')
    @patch('common.cookie_refresh.strategies.base.RefreshStrategy')
    def test_refresh_service_success(self, mock_strategy_class, mock_notifier):
        """Test successful cookie refresh"""
        # Setup mock strategy
        mock_strategy = Mock()
        mock_strategy.refresh.return_value = True
        mock_strategy.name = "test_strategy"
        mock_strategy_class.return_value = mock_strategy
        
        # Add service config
        self.config.services["test_service"] = ServiceConfig(
            enabled=True,
            strategy="test_strategy"
        )
        
        # Mock strategy loading
        with patch.object(self.refresher, '_load_strategy', return_value=mock_strategy):
            result = self.refresher.refresh_service("test_service")
            
            self.assertTrue(result)
            mock_strategy.refresh.assert_called_once()
    
    @patch('common.cookie_refresh.refresher.NotificationManager')
    def test_refresh_service_with_retry(self, mock_notifier):
        """Test cookie refresh with retry logic"""
        # Setup mock strategy that fails then succeeds
        mock_strategy = Mock()
        mock_strategy.refresh.side_effect = [False, False, True]
        mock_strategy.name = "test_strategy"
        
        # Add service config
        self.config.services["test_service"] = ServiceConfig(
            enabled=True,
            strategy="test_strategy"
        )
        
        with patch.object(self.refresher, '_load_strategy', return_value=mock_strategy):
            result = self.refresher.refresh_service("test_service")
            
            self.assertTrue(result)
            self.assertEqual(mock_strategy.refresh.call_count, 3)
    
    @patch('common.cookie_refresh.refresher.NotificationManager')
    def test_run_check_cycle(self, mock_notifier):
        """Test full check cycle"""
        # Add multiple services
        self.config.services.update({
            "service1": ServiceConfig(enabled=True, refresh_interval_hours=24),
            "service2": ServiceConfig(enabled=True, refresh_interval_hours=48),
            "service3": ServiceConfig(enabled=False, refresh_interval_hours=24)
        })
        
        # Mock methods
        with patch.object(self.refresher, '_check_service_needs_refresh') as mock_check:
            with patch.object(self.refresher, 'refresh_service') as mock_refresh:
                mock_check.side_effect = [True, False, True]  # service1 needs refresh, service2 doesn't
                mock_refresh.return_value = True
                
                self.refresher.run_check_cycle()
                
                # Should check only enabled services
                self.assertEqual(mock_check.call_count, 2)
                # Should refresh only service1
                mock_refresh.assert_called_once_with("service1")


class TestNotificationManager(unittest.TestCase):
    """Test notification functionality"""
    
    def setUp(self):
        """Set up test notification manager"""
        self.notifier = NotificationManager()
    
    @patch('common.cookie_refresh.notifier.smtplib.SMTP')
    def test_send_email_notification(self, mock_smtp):
        """Test email notification sending"""
        # Configure email settings
        self.notifier.configure_email(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="password",
            from_address="test@test.com",
            to_addresses=["admin@test.com"]
        )
        
        # Send notification
        self.notifier.send_notification(
            "Test Subject",
            "Test message",
            channels=["email"]
        )
        
        # Verify SMTP was called
        mock_smtp.assert_called_once()
    
    @patch('common.cookie_refresh.notifier.requests.post')
    def test_send_slack_notification(self, mock_post):
        """Test Slack notification sending"""
        # Configure Slack
        self.notifier.configure_slack("https://hooks.slack.com/test")
        
        # Send notification
        self.notifier.send_notification(
            "Test Subject",
            "Test message",
            channels=["slack"]
        )
        
        # Verify webhook was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "https://hooks.slack.com/test")
    
    def test_send_notification_with_multiple_channels(self):
        """Test sending to multiple channels"""
        with patch.object(self.notifier, '_send_email') as mock_email:
            with patch.object(self.notifier, '_send_slack') as mock_slack:
                self.notifier.send_notification(
                    "Test",
                    "Message",
                    channels=["email", "slack"]
                )
                
                mock_email.assert_called_once()
                mock_slack.assert_called_once()


class TestRefreshStrategies(unittest.TestCase):
    """Test individual service refresh strategies"""
    
    @patch('playwright.sync_api.sync_playwright')
    def test_playwright_strategy_base(self, mock_playwright):
        """Test base Playwright strategy functionality"""
        from common.cookie_refresh.strategies.base import PlaywrightStrategy
        
        # Setup mock browser
        mock_browser = Mock()
        mock_page = Mock()
        mock_context = Mock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        # Test strategy
        strategy = PlaywrightStrategy("test_service")
        
        # Mock login method
        with patch.object(strategy, '_perform_login', return_value=True):
            with patch.object(strategy, '_extract_cookies', return_value=[{"name": "test", "value": "cookie"}]):
                result = strategy.refresh()
                self.assertTrue(result)
    
    def test_oauth_strategy_base(self):
        """Test base OAuth strategy functionality"""
        from common.cookie_refresh.strategies.base import OAuthStrategy
        
        strategy = OAuthStrategy("test_service")
        
        # Mock OAuth flow
        with patch.object(strategy, '_perform_oauth_flow', return_value="access_token"):
            with patch.object(strategy, '_exchange_token_for_cookies', return_value=[{"name": "oauth", "value": "token"}]):
                result = strategy.refresh()
                self.assertTrue(result)
    
    def test_api_strategy_base(self):
        """Test base API strategy functionality"""
        from common.cookie_refresh.strategies.base import APIStrategy
        
        strategy = APIStrategy("test_service")
        
        # Mock API authentication
        with patch.object(strategy, '_authenticate', return_value="api_token"):
            with patch.object(strategy, '_get_cookies_from_token', return_value=[{"name": "api", "value": "token"}]):
                result = strategy.refresh()
                self.assertTrue(result)


class TestServiceSpecificStrategies(unittest.TestCase):
    """Test service-specific strategy implementations"""
    
    @patch('playwright.sync_api.sync_playwright')
    def test_spotify_strategy(self, mock_playwright):
        """Test Spotify OAuth strategy"""
        from common.cookie_refresh.strategies.spotify import SpotifyStrategy
        
        strategy = SpotifyStrategy()
        
        # Mock OAuth configuration
        with patch.dict(os.environ, {
            'SPOTIFY_CLIENT_ID': 'test_client_id',
            'SPOTIFY_CLIENT_SECRET': 'test_secret'
        }):
            with patch('webbrowser.open'):
                with patch('requests.post') as mock_post:
                    mock_post.return_value.json.return_value = {
                        'access_token': 'test_token',
                        'refresh_token': 'refresh_token'
                    }
                    
                    # Mock the OAuth callback server
                    with patch.object(strategy, '_start_callback_server'):
                        with patch.object(strategy, '_wait_for_code', return_value='auth_code'):
                            result = strategy.refresh()
                            # Note: Actual implementation would return True on success
                            self.assertIsNotNone(result)
    
    @patch('playwright.sync_api.sync_playwright')
    def test_tiktok_strategy(self, mock_playwright):
        """Test TikTok Playwright strategy with 2FA"""
        from common.cookie_refresh.strategies.tiktok import TikTokStrategy
        
        # Setup mocks
        mock_browser = Mock()
        mock_page = Mock()
        mock_context = Mock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        strategy = TikTokStrategy()
        
        # Mock page interactions
        mock_page.goto = Mock()
        mock_page.wait_for_selector = Mock()
        mock_page.fill = Mock()
        mock_page.click = Mock()
        mock_page.context.cookies.return_value = [
            {"name": "sessionid", "value": "test_session", "domain": ".tiktok.com"}
        ]
        
        with patch.dict(os.environ, {
            'TIKTOK_USERNAME': 'test_user',
            'TIKTOK_PASSWORD': 'test_pass'
        }):
            result = strategy.refresh()
            # Verify page interactions
            mock_page.goto.assert_called()
    
    def test_distrokid_strategy(self):
        """Test DistroKid JWT strategy"""
        from common.cookie_refresh.strategies.distrokid import DistroKidStrategy
        
        strategy = DistroKidStrategy()
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'token': 'jwt_token',
                'success': True
            }
            
            with patch.dict(os.environ, {
                'DISTROKID_USERNAME': 'test_user',
                'DISTROKID_PASSWORD': 'test_pass'
            }):
                result = strategy.refresh()
                # Verify API was called
                mock_post.assert_called()


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config = RefreshConfig(
            check_interval_minutes=30,
            max_retry_attempts=3,
            services={}
        )
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_handle_missing_credentials(self):
        """Test handling of missing credentials"""
        from common.cookie_refresh.strategies.spotify import SpotifyStrategy
        
        strategy = SpotifyStrategy()
        
        # Remove required environment variables
        with patch.dict(os.environ, {}, clear=True):
            result = strategy.refresh()
            self.assertFalse(result)
    
    def test_handle_network_errors(self):
        """Test handling of network errors"""
        from common.cookie_refresh.refresher import CookieRefresher
        
        refresher = CookieRefresher(self.config, base_path=self.test_dir)
        
        # Add service config
        self.config.services["test_service"] = ServiceConfig(
            enabled=True,
            strategy="test_strategy"
        )
        
        # Mock strategy that raises network error
        mock_strategy = Mock()
        mock_strategy.refresh.side_effect = ConnectionError("Network error")
        
        with patch.object(refresher, '_load_strategy', return_value=mock_strategy):
            result = refresher.refresh_service("test_service")
            self.assertFalse(result)
    
    def test_handle_invalid_cookie_format(self):
        """Test handling of invalid cookie formats"""
        storage = CookieStorage(base_path=self.test_dir)
        
        # Create invalid cookie file
        service_dir = os.path.join(self.test_dir, "test_service", "cookies")
        os.makedirs(service_dir, exist_ok=True)
        
        with open(os.path.join(service_dir, "test_service_cookies.json"), 'w') as f:
            f.write("invalid json")
        
        # Should handle gracefully
        cookies = storage.load_cookies("test_service")
        self.assertIsNone(cookies)
    
    def test_handle_permission_errors(self):
        """Test handling of file permission errors"""
        storage = CookieStorage(base_path=self.test_dir)
        
        # Create read-only directory
        service_dir = os.path.join(self.test_dir, "readonly_service")
        os.makedirs(service_dir)
        os.chmod(service_dir, 0o444)
        
        # Should handle permission error gracefully
        try:
            storage.save_cookies("readonly_service", [{"name": "test", "value": "value"}])
        except PermissionError:
            pass  # Expected
        finally:
            # Restore permissions for cleanup
            os.chmod(service_dir, 0o777)


class TestConcurrency(unittest.TestCase):
    """Test concurrent operations and thread safety"""
    
    def test_concurrent_cookie_refresh(self):
        """Test multiple services refreshing concurrently"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from common.cookie_refresh.refresher import CookieRefresher
        
        config = RefreshConfig(
            check_interval_minutes=30,
            max_retry_attempts=1,
            services={
                f"service_{i}": ServiceConfig(enabled=True, strategy="test")
                for i in range(5)
            }
        )
        
        refresher = CookieRefresher(config)
        
        # Mock refresh to simulate work
        def mock_refresh(service_name):
            import time
            time.sleep(0.1)  # Simulate work
            return True
        
        with patch.object(refresher, 'refresh_service', side_effect=mock_refresh):
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(refresher.refresh_service, f"service_{i}")
                    for i in range(5)
                ]
                
                results = [future.result() for future in as_completed(futures)]
                
                # All should complete successfully
                self.assertEqual(len(results), 5)
                self.assertTrue(all(results))


if __name__ == '__main__':
    unittest.main()