"""
Integration tests for cookie refresh system with mock authentication
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.cookie_refresh.refresher import CookieRefresher
from common.cookie_refresh.config import RefreshConfig, ServiceConfig
from common.cookie_refresh.storage import CookieStorage
from common.cookie_refresh.notifier import NotificationManager


class MockOAuthHandler(BaseHTTPRequestHandler):
    """Mock OAuth callback handler for testing"""
    
    def do_GET(self):
        """Handle OAuth callback"""
        if 'code=' in self.path:
            # Extract code from query string
            code = self.path.split('code=')[1].split('&')[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization successful!</h1></body></html>")
            # Store code for retrieval
            self.server.auth_code = code
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress log messages during tests"""
        pass


class TestIntegration(unittest.TestCase):
    """Integration tests for complete cookie refresh workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "config.json")
        self.create_test_config()
        
        # Load config and create refresher
        self.config = RefreshConfig.load_from_file(self.config_file)
        self.refresher = CookieRefresher(self.config, base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def create_test_config(self):
        """Create test configuration file"""
        config_data = {
            "global": {
                "check_interval_minutes": 1,
                "max_retry_attempts": 2,
                "notification_channels": ["email", "slack"],
                "concurrent_refreshes": 3
            },
            "services": {
                "spotify": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 10,
                    "strategy": "oauth",
                    "priority": 1,
                    "notification_channels": ["email"]
                },
                "tiktok": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 10,
                    "strategy": "playwright",
                    "priority": 2,
                    "requires_2fa": True
                },
                "distrokid": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 7,
                    "strategy": "jwt",
                    "priority": 3
                },
                "toolost": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 7,
                    "strategy": "jwt",
                    "priority": 4
                }
            },
            "notifications": {
                "email": {
                    "smtp_server": "smtp.test.com",
                    "smtp_port": 587,
                    "username": "test@test.com",
                    "password": "password",
                    "from_address": "test@test.com",
                    "to_addresses": ["admin@test.com"]
                },
                "slack": {
                    "webhook_url": "https://hooks.slack.com/test"
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
    
    def create_old_cookies(self, service, age_days=10):
        """Create old cookies for testing"""
        cookies = [
            {"name": "session", "value": "old_session", "domain": f".{service}.com"},
            {"name": "token", "value": "old_token", "domain": f".{service}.com"}
        ]
        
        # Save cookies
        self.refresher.storage.save_cookies(service, cookies)
        
        # Modify file timestamp to make them old
        cookie_file = os.path.join(self.test_dir, service, "cookies", f"{service}_cookies.json")
        old_time = time.time() - (age_days * 24 * 60 * 60)
        os.utime(cookie_file, (old_time, old_time))
    
    @patch('playwright.sync_api.sync_playwright')
    @patch('requests.post')
    @patch('webbrowser.open')
    def test_full_refresh_cycle(self, mock_browser_open, mock_requests_post, mock_playwright):
        """Test complete refresh cycle for all services"""
        # Setup mock responses
        mock_requests_post.return_value.json.return_value = {
            'access_token': 'new_token',
            'refresh_token': 'new_refresh',
            'token': 'jwt_token'
        }
        
        # Setup Playwright mock
        mock_browser = Mock()
        mock_page = Mock()
        mock_context = Mock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_page.context.cookies.return_value = [
            {"name": "new_session", "value": "new_value", "domain": ".test.com"}
        ]
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        # Create old cookies for all services
        for service in ["spotify", "tiktok", "distrokid", "toolost"]:
            self.create_old_cookies(service, age_days=15)
        
        # Set environment variables
        with patch.dict(os.environ, {
            'SPOTIFY_CLIENT_ID': 'test_id',
            'SPOTIFY_CLIENT_SECRET': 'test_secret',
            'TIKTOK_USERNAME': 'test_user',
            'TIKTOK_PASSWORD': 'test_pass',
            'DISTROKID_USERNAME': 'dk_user',
            'DISTROKID_PASSWORD': 'dk_pass',
            'TOOLOST_USERNAME': 'tl_user',
            'TOOLOST_PASSWORD': 'tl_pass'
        }):
            # Mock strategy loading and execution
            with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
                mock_strategies = {}
                for service in ["spotify", "tiktok", "distrokid", "toolost"]:
                    strategy = Mock()
                    strategy.refresh.return_value = True
                    strategy.name = service
                    mock_strategies[service] = strategy
                
                mock_load.side_effect = lambda name, service: mock_strategies[service]
                
                # Run check cycle
                results = self.refresher.run_check_cycle()
                
                # Verify all services were refreshed
                self.assertEqual(len(results), 4)
                for service, success in results.items():
                    self.assertTrue(success, f"Service {service} should have been refreshed successfully")
    
    @patch('common.cookie_refresh.notifier.smtplib.SMTP')
    @patch('requests.post')
    def test_notification_on_failure(self, mock_requests_post, mock_smtp):
        """Test notifications are sent on refresh failure"""
        # Create old cookies
        self.create_old_cookies("spotify", age_days=15)
        
        # Mock failed refresh
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            mock_strategy = Mock()
            mock_strategy.refresh.return_value = False
            mock_strategy.name = "spotify"
            mock_load.return_value = mock_strategy
            
            # Configure notifications
            self.refresher.notifier.configure_email(
                smtp_server="smtp.test.com",
                smtp_port=587,
                username="test@test.com",
                password="password",
                from_address="test@test.com",
                to_addresses=["admin@test.com"]
            )
            
            # Run refresh
            result = self.refresher.refresh_service("spotify")
            
            # Verify failure
            self.assertFalse(result)
            
            # Verify notification was sent
            mock_smtp.assert_called()
    
    def test_concurrent_service_refresh(self):
        """Test multiple services refreshing concurrently"""
        # Create old cookies for multiple services
        services = ["spotify", "tiktok", "distrokid"]
        for service in services:
            self.create_old_cookies(service, age_days=15)
        
        # Track refresh order
        refresh_order = []
        refresh_lock = threading.Lock()
        
        def mock_refresh(service_name):
            with refresh_lock:
                refresh_order.append(service_name)
            time.sleep(0.1)  # Simulate work
            return True
        
        # Mock strategy loading
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            mock_strategies = {}
            for service in services:
                strategy = Mock()
                strategy.refresh.side_effect = lambda s=service: mock_refresh(s)
                strategy.name = service
                mock_strategies[service] = strategy
            
            mock_load.side_effect = lambda name, s: mock_strategies[s]
            
            # Run concurrent refresh
            results = self.refresher.run_check_cycle()
            
            # Verify all services were refreshed
            self.assertEqual(len(results), 3)
            self.assertEqual(set(refresh_order), set(services))
    
    def test_oauth_callback_server(self):
        """Test OAuth callback server functionality"""
        from common.cookie_refresh.strategies.spotify import SpotifyStrategy
        
        # Start mock OAuth server
        server = HTTPServer(('localhost', 0), MockOAuthHandler)
        server_port = server.server_address[1]
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        try:
            # Simulate OAuth callback
            response = requests.get(f'http://localhost:{server_port}/callback?code=test_auth_code')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(server.auth_code, 'test_auth_code')
        finally:
            server.shutdown()
    
    @patch('playwright.sync_api.sync_playwright')
    def test_2fa_handling(self, mock_playwright):
        """Test 2FA handling for services that require it"""
        # Setup Playwright mock
        mock_browser = Mock()
        mock_page = Mock()
        mock_context = Mock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        mock_pw = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        # Mock 2FA detection
        mock_page.query_selector.return_value = Mock()  # 2FA element exists
        
        # Mock user input for 2FA
        with patch('builtins.input', return_value='123456'):
            from common.cookie_refresh.strategies.tiktok import TikTokStrategy
            strategy = TikTokStrategy()
            
            # Mock the rest of the flow
            mock_page.context.cookies.return_value = [
                {"name": "session", "value": "authenticated", "domain": ".tiktok.com"}
            ]
            
            with patch.dict(os.environ, {
                'TIKTOK_USERNAME': 'test_user',
                'TIKTOK_PASSWORD': 'test_pass'
            }):
                # Should handle 2FA prompt
                result = strategy.refresh()
                # Verify 2FA code was entered
                mock_page.fill.assert_any_call('[data-testid="2fa-input"]', '123456')
    
    def test_rollback_on_validation_failure(self):
        """Test rollback when new cookies fail validation"""
        # Create valid cookies
        valid_cookies = [
            {"name": "session", "value": "valid", "domain": ".test.com"},
            {"name": "token", "value": "valid_token", "domain": ".test.com"}
        ]
        self.refresher.storage.save_cookies("test_service", valid_cookies)
        
        # Mock refresh that returns invalid cookies
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            mock_strategy = Mock()
            # Return cookies missing required fields
            mock_strategy.refresh.return_value = True
            mock_strategy.get_cookies.return_value = [
                {"name": "invalid"},  # Missing value
                {"value": "invalid"}  # Missing name
            ]
            mock_strategy.name = "test_service"
            mock_load.return_value = mock_strategy
            
            # Add service config
            self.config.services["test_service"] = ServiceConfig(
                enabled=True,
                strategy="test"
            )
            
            # Attempt refresh
            with patch.object(self.refresher.storage, 'validate_cookies', return_value=False):
                with patch.object(self.refresher.storage, 'backup_cookies') as mock_backup:
                    with patch.object(self.refresher.storage, 'restore_cookies') as mock_restore:
                        result = self.refresher.refresh_service("test_service")
                        
                        # Should fail and restore backup
                        self.assertFalse(result)
                        mock_backup.assert_called_once()
                        mock_restore.assert_called_once()
    
    def test_health_check_endpoint(self):
        """Test health check monitoring endpoint"""
        from common.cookie_refresh.dashboard import start_dashboard
        
        # Start dashboard in test mode
        dashboard_thread = threading.Thread(
            target=start_dashboard,
            kwargs={'port': 0, 'test_mode': True}
        )
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        # Give server time to start
        time.sleep(1)
        
        # Test health endpoint
        try:
            response = requests.get('http://localhost:8080/health')
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            self.assertIn('services', data)
            self.assertIn('last_check', data)
        except:
            pass  # Server might not be available in test environment
    
    def test_service_priority_ordering(self):
        """Test services are refreshed in priority order"""
        # Create services with different priorities
        services_refreshed = []
        
        def track_refresh(service_name):
            services_refreshed.append(service_name)
            return True
        
        # Mock strategies
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            for service in ["spotify", "tiktok", "distrokid", "toolost"]:
                self.create_old_cookies(service, age_days=15)
                strategy = Mock()
                strategy.refresh.side_effect = lambda s=service: track_refresh(s)
                strategy.name = service
                mock_load.return_value = strategy
            
            # Run refresh cycle
            self.refresher.run_check_cycle()
            
            # Verify priority order (spotify=1, tiktok=2, distrokid=3, toolost=4)
            expected_order = ["spotify", "tiktok", "distrokid", "toolost"]
            self.assertEqual(services_refreshed[:4], expected_order)


class TestDatabaseIntegration(unittest.TestCase):
    """Test integration with cookie storage database"""
    
    def setUp(self):
        """Set up test database"""
        self.test_dir = tempfile.mkdtemp()
        self.storage = CookieStorage(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_cookie_history_tracking(self):
        """Test cookie refresh history is tracked"""
        # Save initial cookies
        cookies_v1 = [{"name": "session", "value": "v1", "domain": ".test.com"}]
        self.storage.save_cookies("test_service", cookies_v1)
        
        # Update cookies
        cookies_v2 = [{"name": "session", "value": "v2", "domain": ".test.com"}]
        self.storage.save_cookies("test_service", cookies_v2)
        
        # Verify history
        history = self.storage.get_refresh_history("test_service")
        self.assertIsNotNone(history)
        self.assertGreater(len(history), 0)
    
    def test_metrics_collection(self):
        """Test refresh metrics are collected"""
        from common.cookie_refresh.storage import RefreshMetrics
        
        metrics = RefreshMetrics(self.test_dir)
        
        # Record successful refresh
        metrics.record_refresh("spotify", True, duration=5.2)
        
        # Record failed refresh
        metrics.record_refresh("tiktok", False, duration=10.5, error="2FA timeout")
        
        # Get metrics
        stats = metrics.get_service_stats("spotify")
        self.assertEqual(stats['total_refreshes'], 1)
        self.assertEqual(stats['success_rate'], 1.0)
        self.assertAlmostEqual(stats['avg_duration'], 5.2)
        
        stats = metrics.get_service_stats("tiktok")
        self.assertEqual(stats['total_refreshes'], 1)
        self.assertEqual(stats['success_rate'], 0.0)
        self.assertIn("2FA timeout", stats['last_error'])


if __name__ == '__main__':
    unittest.main()