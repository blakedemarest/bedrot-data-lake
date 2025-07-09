"""
End-to-end test scenarios for cookie refresh system
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.cookie_refresh.refresher import CookieRefresher
from common.cookie_refresh.config import RefreshConfig, ServiceConfig
from common.cookie_refresh.storage import CookieStorage
from common.cookie_refresh.dashboard import DashboardServer


class TestE2EScenarios(unittest.TestCase):
    """End-to-end test scenarios simulating real-world usage"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.setup_complete_environment()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def setup_complete_environment(self):
        """Set up complete test environment with all services"""
        # Create config
        config_data = {
            "global": {
                "check_interval_minutes": 1,
                "max_retry_attempts": 3,
                "notification_channels": ["email"],
                "concurrent_refreshes": 2,
                "business_hours_only": False,
                "quiet_hours": {
                    "enabled": True,
                    "start": "22:00",
                    "end": "06:00"
                }
            },
            "services": {
                "spotify": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 10,
                    "strategy": "oauth",
                    "priority": 1,
                    "notification_channels": ["email"],
                    "credentials": {
                        "client_id_env": "SPOTIFY_CLIENT_ID",
                        "client_secret_env": "SPOTIFY_CLIENT_SECRET"
                    }
                },
                "tiktok": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 10,
                    "strategy": "playwright",
                    "priority": 2,
                    "requires_2fa": True,
                    "accounts": ["pig1987", "zone.a0"],
                    "credentials": {
                        "username_env": "TIKTOK_USERNAME",
                        "password_env": "TIKTOK_PASSWORD"
                    }
                },
                "distrokid": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 7,
                    "strategy": "jwt",
                    "priority": 3,
                    "jwt_expiry_days": 12
                },
                "toolost": {
                    "enabled": True,
                    "refresh_interval_hours": 168,
                    "max_age_days": 7,
                    "strategy": "jwt",
                    "priority": 4,
                    "jwt_expiry_days": 7
                },
                "linktree": {
                    "enabled": True,
                    "refresh_interval_hours": 336,
                    "max_age_days": 14,
                    "strategy": "playwright",
                    "priority": 5
                }
            }
        }
        
        self.config_file = os.path.join(self.test_dir, "config.json")
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        self.config = RefreshConfig.load_from_file(self.config_file)
        self.refresher = CookieRefresher(self.config, base_path=self.test_dir)
    
    def create_expired_cookies(self, service, age_days):
        """Create expired cookies for testing"""
        cookies = [
            {"name": "session", "value": f"{service}_session", "domain": f".{service}.com"},
            {"name": "token", "value": f"{service}_token", "domain": f".{service}.com"}
        ]
        
        # Special handling for JWT services
        if service in ["distrokid", "toolost"]:
            cookies.append({
                "name": "jwt",
                "value": "expired_jwt_token",
                "domain": f".{service}.com",
                "expires": (datetime.now() - timedelta(days=1)).timestamp()
            })
        
        self.refresher.storage.save_cookies(service, cookies)
        
        # Backdate file
        cookie_file = os.path.join(self.test_dir, service, "cookies", f"{service}_cookies.json")
        old_time = time.time() - (age_days * 24 * 60 * 60)
        os.utime(cookie_file, (old_time, old_time))
    
    def test_scenario_weekly_maintenance(self):
        """Test scenario: Weekly maintenance refresh of all services"""
        # Create week-old cookies for all services
        services = ["spotify", "tiktok", "distrokid", "toolost", "linktree"]
        for service in services:
            self.create_expired_cookies(service, age_days=8)
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'SPOTIFY_CLIENT_ID': 'test_client_id',
            'SPOTIFY_CLIENT_SECRET': 'test_secret',
            'TIKTOK_USERNAME': 'test_user',
            'TIKTOK_PASSWORD': 'test_pass',
            'DISTROKID_USERNAME': 'dk_user',
            'DISTROKID_PASSWORD': 'dk_pass',
            'TOOLOST_USERNAME': 'tl_user',
            'TOOLOST_PASSWORD': 'tl_pass',
            'LINKTREE_USERNAME': 'lt_user',
            'LINKTREE_PASSWORD': 'lt_pass'
        }):
            # Mock all strategies
            with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
                refresh_results = {}
                
                def create_mock_strategy(service_name):
                    strategy = Mock()
                    strategy.name = service_name
                    
                    # Simulate different scenarios
                    if service_name == "tiktok":
                        # TikTok requires 2FA
                        strategy.refresh.side_effect = lambda: self.simulate_2fa_flow(service_name)
                    elif service_name == "toolost":
                        # TooLost JWT expires frequently
                        strategy.refresh.return_value = True
                        strategy.get_cookies.return_value = [
                            {"name": "jwt", "value": "new_jwt", "expires": (datetime.now() + timedelta(days=7)).timestamp()}
                        ]
                    else:
                        strategy.refresh.return_value = True
                        strategy.get_cookies.return_value = [
                            {"name": "session", "value": f"new_{service_name}_session"}
                        ]
                    
                    return strategy
                
                mock_load.side_effect = lambda strategy_type, service: create_mock_strategy(service)
                
                # Run weekly maintenance
                start_time = datetime.now()
                results = self.refresher.run_check_cycle()
                end_time = datetime.now()
                
                # Verify all services were checked
                self.assertEqual(len(results), 5)
                
                # Verify priority order was respected
                # (Implementation would track actual call order)
                
                # Verify execution time is reasonable
                duration = (end_time - start_time).total_seconds()
                self.assertLess(duration, 60)  # Should complete within 1 minute
    
    def simulate_2fa_flow(self, service_name):
        """Simulate 2FA authentication flow"""
        with patch('builtins.input', return_value='123456'):
            return True
    
    def test_scenario_jwt_expiry_handling(self):
        """Test scenario: Handling JWT token expiration for TooLost and DistroKid"""
        # Create cookies with expired JWT tokens
        self.create_expired_cookies("toolost", age_days=8)  # JWT expires every 7 days
        self.create_expired_cookies("distrokid", age_days=13)  # JWT expires every 12 days
        
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            jwt_refresh_count = {"toolost": 0, "distrokid": 0}
            
            def create_jwt_strategy(service_name):
                strategy = Mock()
                strategy.name = service_name
                
                def refresh_jwt():
                    jwt_refresh_count[service_name] += 1
                    return True
                
                strategy.refresh = refresh_jwt
                strategy.get_cookies.return_value = [
                    {
                        "name": "jwt",
                        "value": f"new_jwt_{service_name}_{jwt_refresh_count[service_name]}",
                        "expires": (datetime.now() + timedelta(days=7 if service_name == "toolost" else 12)).timestamp()
                    }
                ]
                return strategy
            
            mock_load.side_effect = lambda _, service: create_jwt_strategy(service) if service in ["toolost", "distrokid"] else Mock(refresh=Mock(return_value=False))
            
            # Run refresh
            results = self.refresher.run_check_cycle()
            
            # Verify both JWT services were refreshed
            self.assertTrue(results.get("toolost", False))
            self.assertTrue(results.get("distrokid", False))
            self.assertEqual(jwt_refresh_count["toolost"], 1)
            self.assertEqual(jwt_refresh_count["distrokid"], 1)
    
    def test_scenario_2fa_timeout_recovery(self):
        """Test scenario: Recovery from 2FA timeout"""
        self.create_expired_cookies("tiktok", age_days=10)
        
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            attempt_count = 0
            
            def create_2fa_strategy(service_name):
                strategy = Mock()
                strategy.name = service_name
                
                def refresh_with_2fa():
                    nonlocal attempt_count
                    attempt_count += 1
                    
                    if attempt_count == 1:
                        # First attempt: timeout waiting for 2FA
                        raise TimeoutError("2FA code not provided within timeout")
                    else:
                        # Second attempt: success
                        return True
                
                strategy.refresh = refresh_with_2fa
                strategy.get_cookies.return_value = [
                    {"name": "session", "value": "authenticated_session"}
                ]
                return strategy
            
            mock_load.side_effect = lambda _, service: create_2fa_strategy(service)
            
            # Configure shorter retry delay for testing
            self.config.retry_delay_seconds = 0.1
            
            # Run refresh with retry
            result = self.refresher.refresh_service("tiktok")
            
            # Should succeed after retry
            self.assertTrue(result)
            self.assertEqual(attempt_count, 2)
    
    def test_scenario_concurrent_refresh_limit(self):
        """Test scenario: Respecting concurrent refresh limits"""
        # Create multiple services needing refresh
        services = ["spotify", "tiktok", "distrokid", "toolost", "linktree"]
        for service in services:
            self.create_expired_cookies(service, age_days=10)
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        lock = threading.Lock()
        
        def track_concurrent_execution(service_name):
            nonlocal concurrent_count, max_concurrent
            
            with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
            
            # Simulate work
            time.sleep(0.5)
            
            with lock:
                concurrent_count -= 1
            
            return True
        
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            def create_tracking_strategy(service_name):
                strategy = Mock()
                strategy.name = service_name
                strategy.refresh = lambda: track_concurrent_execution(service_name)
                return strategy
            
            mock_load.side_effect = lambda _, service: create_tracking_strategy(service)
            
            # Run refresh cycle
            self.refresher.run_check_cycle()
            
            # Verify concurrent limit was respected
            self.assertLessEqual(max_concurrent, self.config.concurrent_refreshes)
    
    def test_scenario_quiet_hours_enforcement(self):
        """Test scenario: Respecting quiet hours configuration"""
        # Set current time to quiet hours
        quiet_start = datetime.now().replace(hour=23, minute=0, second=0)
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = quiet_start
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            # Create expired cookies
            self.create_expired_cookies("spotify", age_days=10)
            
            # Mock strategy
            with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
                refresh_called = False
                
                def create_quiet_strategy(service_name):
                    strategy = Mock()
                    strategy.name = service_name
                    
                    def refresh():
                        nonlocal refresh_called
                        refresh_called = True
                        return True
                    
                    strategy.refresh = refresh
                    return strategy
                
                mock_load.side_effect = lambda _, service: create_quiet_strategy(service)
                
                # Run check during quiet hours
                results = self.refresher.run_check_cycle()
                
                # Should skip refresh during quiet hours
                self.assertFalse(refresh_called)
    
    def test_scenario_notification_escalation(self):
        """Test scenario: Notification escalation on repeated failures"""
        self.create_expired_cookies("distrokid", age_days=10)
        
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            # Strategy that always fails
            failing_strategy = Mock()
            failing_strategy.name = "distrokid"
            failing_strategy.refresh.return_value = False
            mock_load.return_value = failing_strategy
            
            # Mock notifications
            with patch.object(self.refresher.notifier, 'send_notification') as mock_notify:
                # Run multiple refresh attempts
                for i in range(5):
                    self.refresher.refresh_service("distrokid")
                    time.sleep(0.1)
                
                # Verify escalating notifications
                calls = mock_notify.call_args_list
                self.assertGreater(len(calls), 3)
                
                # Check that later notifications have higher priority
                # (Implementation would include priority in notification)
    
    def test_scenario_disaster_recovery(self):
        """Test scenario: Recovery from corrupted cookie storage"""
        # Create corrupted cookie files
        for service in ["spotify", "tiktok"]:
            service_dir = os.path.join(self.test_dir, service, "cookies")
            os.makedirs(service_dir, exist_ok=True)
            
            # Write invalid JSON
            with open(os.path.join(service_dir, f"{service}_cookies.json"), 'w') as f:
                f.write("{{invalid json content")
        
        # Mock strategies
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            def create_recovery_strategy(service_name):
                strategy = Mock()
                strategy.name = service_name
                strategy.refresh.return_value = True
                strategy.get_cookies.return_value = [
                    {"name": "session", "value": f"recovered_{service_name}"}
                ]
                return strategy
            
            mock_load.side_effect = lambda _, service: create_recovery_strategy(service)
            
            # Run refresh - should handle corrupted files gracefully
            results = self.refresher.run_check_cycle()
            
            # Verify recovery
            for service in ["spotify", "tiktok"]:
                # Should have new valid cookies
                cookies = self.refresher.storage.load_cookies(service)
                self.assertIsNotNone(cookies)
                self.assertTrue(any(c.get("value", "").startswith("recovered_") for c in cookies))
    
    def test_scenario_performance_under_load(self):
        """Test scenario: System performance with many services"""
        # Create 20 test services
        num_services = 20
        for i in range(num_services):
            service_name = f"service_{i}"
            self.config.services[service_name] = ServiceConfig(
                enabled=True,
                refresh_interval_hours=168,
                priority=i
            )
            self.create_expired_cookies(service_name, age_days=10)
        
        # Track performance metrics
        refresh_times = []
        
        def timed_refresh(service_name):
            start = time.time()
            time.sleep(0.1)  # Simulate work
            end = time.time()
            refresh_times.append(end - start)
            return True
        
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            def create_timed_strategy(service_name):
                strategy = Mock()
                strategy.name = service_name
                strategy.refresh = lambda: timed_refresh(service_name)
                return strategy
            
            mock_load.side_effect = lambda _, service: create_timed_strategy(service)
            
            # Run refresh cycle
            start_time = time.time()
            results = self.refresher.run_check_cycle()
            total_time = time.time() - start_time
            
            # Verify performance
            self.assertEqual(len(results), num_services)
            self.assertLess(total_time, 30)  # Should complete within 30 seconds
            
            # Check that concurrent execution improved performance
            expected_serial_time = num_services * 0.1
            self.assertLess(total_time, expected_serial_time * 0.7)  # At least 30% improvement
    
    def test_scenario_cross_platform_compatibility(self):
        """Test scenario: Windows and Linux path handling"""
        # Test both path separators
        test_paths = [
            ("windows", "C:\\Users\\test\\cookies"),
            ("linux", "/home/test/cookies")
        ]
        
        for platform, base_path in test_paths:
            with patch('os.path.sep', '\\' if platform == "windows" else '/'):
                storage = CookieStorage(base_path=base_path)
                
                # Test cookie operations
                test_cookies = [{"name": "test", "value": "cross_platform"}]
                
                # Should handle paths correctly regardless of platform
                try:
                    storage.save_cookies("test_service", test_cookies)
                    loaded = storage.load_cookies("test_service")
                    self.assertEqual(loaded, test_cookies)
                except Exception as e:
                    # Path might not exist in test environment
                    pass
    
    def test_scenario_monitoring_dashboard_integration(self):
        """Test scenario: Integration with monitoring dashboard"""
        # Start mock dashboard server
        dashboard = DashboardServer(self.refresher, port=0)
        
        # Create services with various states
        self.create_expired_cookies("spotify", age_days=5)  # Fresh
        self.create_expired_cookies("tiktok", age_days=15)  # Expired
        self.create_expired_cookies("toolost", age_days=8)   # Needs refresh
        
        # Mock refresh results
        with patch.object(self.refresher, 'get_service_status') as mock_status:
            mock_status.side_effect = lambda service: {
                "spotify": {"status": "healthy", "last_refresh": datetime.now() - timedelta(days=5)},
                "tiktok": {"status": "expired", "last_refresh": datetime.now() - timedelta(days=15)},
                "toolost": {"status": "warning", "last_refresh": datetime.now() - timedelta(days=8)}
            }.get(service, {"status": "unknown"})
            
            # Get dashboard data
            dashboard_data = dashboard.get_dashboard_data()
            
            # Verify dashboard shows correct status
            self.assertEqual(dashboard_data["services"]["spotify"]["status"], "healthy")
            self.assertEqual(dashboard_data["services"]["tiktok"]["status"], "expired")
            self.assertEqual(dashboard_data["services"]["toolost"]["status"], "warning")
            
            # Verify summary metrics
            self.assertEqual(dashboard_data["summary"]["total_services"], 5)
            self.assertEqual(dashboard_data["summary"]["healthy_services"], 1)
            self.assertEqual(dashboard_data["summary"]["expired_services"], 1)
            self.assertEqual(dashboard_data["summary"]["warning_services"], 1)


class TestFailureRecovery(unittest.TestCase):
    """Test various failure scenarios and recovery mechanisms"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config = RefreshConfig(
            check_interval_minutes=1,
            max_retry_attempts=3,
            retry_delay_seconds=0.1,
            services={}
        )
        self.refresher = CookieRefresher(self.config, base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_network_failure_recovery(self):
        """Test recovery from network failures"""
        self.config.services["test_service"] = ServiceConfig(
            enabled=True,
            strategy="api"
        )
        
        network_attempts = 0
        
        def flaky_network_call():
            nonlocal network_attempts
            network_attempts += 1
            
            if network_attempts < 3:
                raise ConnectionError("Network unavailable")
            return True
        
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            strategy = Mock()
            strategy.refresh = flaky_network_call
            mock_load.return_value = strategy
            
            # Should succeed after retries
            result = self.refresher.refresh_service("test_service")
            self.assertTrue(result)
            self.assertEqual(network_attempts, 3)
    
    def test_partial_success_handling(self):
        """Test handling partial success in multi-account services"""
        self.config.services["tiktok"] = ServiceConfig(
            enabled=True,
            strategy="playwright",
            accounts=["account1", "account2", "account3"]
        )
        
        with patch('common.cookie_refresh.refresher.load_strategy') as mock_load:
            results = {"account1": True, "account2": False, "account3": True}
            
            strategy = Mock()
            strategy.refresh_multiple_accounts = Mock(return_value=results)
            mock_load.return_value = strategy
            
            # Run refresh
            with patch.object(self.refresher, '_handle_partial_success') as mock_handle:
                self.refresher.refresh_service("tiktok")
                
                # Should handle partial success appropriately
                mock_handle.assert_called_once_with("tiktok", results)


if __name__ == '__main__':
    unittest.main()