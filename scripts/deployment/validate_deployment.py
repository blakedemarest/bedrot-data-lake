#!/usr/bin/env python3
"""
Post-deployment validation script
Ensures the cookie refresh system is properly deployed and functional
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import socket
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class DeploymentValidator:
    """Validates successful deployment of cookie refresh system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.validation_results = {
            'configuration': {'passed': 0, 'failed': 0, 'tests': []},
            'services': {'passed': 0, 'failed': 0, 'tests': []},
            'scheduler': {'passed': 0, 'failed': 0, 'tests': []},
            'monitoring': {'passed': 0, 'failed': 0, 'tests': []},
            'notifications': {'passed': 0, 'failed': 0, 'tests': []},
            'performance': {'passed': 0, 'failed': 0, 'tests': []},
        }
        self.start_time = datetime.now()
        
    def run_validation(self, full: bool = False) -> bool:
        """Run all validation tests"""
        print("=" * 70)
        print("Cookie Refresh System - Deployment Validation")
        print("=" * 70)
        print(f"Mode: {'FULL VALIDATION' if full else 'QUICK VALIDATION'}")
        print(f"Timestamp: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project Root: {self.project_root}")
        print("=" * 70)
        print()
        
        # Run validation tests
        self.validate_configuration()
        self.validate_services()
        self.validate_scheduler()
        self.validate_monitoring()
        
        if full:
            self.validate_notifications()
            self.validate_performance()
        
        # Print results
        self.print_results()
        
        # Determine overall success
        total_failed = sum(category['failed'] for category in self.validation_results.values())
        
        return total_failed == 0
    
    def validate_configuration(self):
        """Validate configuration files and settings"""
        print("Validating Configuration...")
        print("-" * 40)
        
        # Check main config file
        config_file = self.project_root / 'config' / 'cookie_refresh_config.json'
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                
                # Validate structure
                required_sections = ['global', 'services', 'notifications']
                for section in required_sections:
                    if section in config:
                        self.add_test_result('configuration', f"Config section '{section}'", True)
                    else:
                        self.add_test_result('configuration', f"Config section '{section}'", False, 
                                           f"Missing required section: {section}")
                
                # Validate service configurations
                if 'services' in config:
                    for service, service_config in config['services'].items():
                        if self.validate_service_config(service, service_config):
                            self.add_test_result('configuration', f"Service config '{service}'", True)
                        else:
                            self.add_test_result('configuration', f"Service config '{service}'", False,
                                               "Invalid service configuration")
                
            except json.JSONDecodeError as e:
                self.add_test_result('configuration', 'Config file JSON', False, f"Invalid JSON: {e}")
        else:
            self.add_test_result('configuration', 'Config file exists', False, "Configuration file not found")
        
        # Check environment variables
        env_file = self.project_root / '.env'
        if env_file.exists():
            self.add_test_result('configuration', 'Environment file', True)
            
            # Check specific variables
            with open(env_file) as f:
                env_content = f.read()
                
            critical_vars = ['PROJECT_ROOT', 'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET']
            for var in critical_vars:
                if f'{var}=' in env_content:
                    self.add_test_result('configuration', f"Env var '{var}'", True)
                else:
                    self.add_test_result('configuration', f"Env var '{var}'", False, "Not found in .env")
        else:
            self.add_test_result('configuration', 'Environment file', False, ".env file not found")
        
        # Check directory structure
        required_dirs = [
            'config',
            'logs',
            'backups',
            'src/common/cookie_refresh',
            'src/common/cookie_refresh/strategies',
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                self.add_test_result('configuration', f"Directory '{dir_path}'", True)
            else:
                self.add_test_result('configuration', f"Directory '{dir_path}'", False, "Directory not found")
        
        print()
    
    def validate_services(self):
        """Validate service-specific components"""
        print("Validating Services...")
        print("-" * 40)
        
        services = ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree']
        
        for service in services:
            # Check cookie directory
            cookie_dir = self.project_root / 'src' / service / 'cookies'
            if cookie_dir.exists():
                self.add_test_result('services', f"{service} cookie directory", True)
                
                # Check for existing cookies
                cookie_files = list(cookie_dir.glob('*.json'))
                if cookie_files:
                    # Validate cookie age
                    for cookie_file in cookie_files:
                        age_days = (datetime.now().timestamp() - cookie_file.stat().st_mtime) / (24 * 3600)
                        if age_days < 30:
                            self.add_test_result('services', f"{service} cookie freshness", True,
                                               f"Cookies are {age_days:.1f} days old")
                        else:
                            self.add_test_result('services', f"{service} cookie freshness", False,
                                               f"Cookies are {age_days:.1f} days old (>30 days)")
                else:
                    self.add_test_result('services', f"{service} cookies exist", False, "No cookie files found")
            else:
                self.add_test_result('services', f"{service} cookie directory", False, "Directory not found")
            
            # Check strategy file
            strategy_file = self.project_root / 'src' / 'common' / 'cookie_refresh' / 'strategies' / f'{service}.py'
            if strategy_file.exists():
                self.add_test_result('services', f"{service} strategy", True)
            else:
                self.add_test_result('services', f"{service} strategy", False, "Strategy file not found")
        
        print()
    
    def validate_scheduler(self):
        """Validate Windows Task Scheduler setup"""
        print("Validating Scheduler...")
        print("-" * 40)
        
        if sys.platform != 'win32':
            self.add_test_result('scheduler', 'Platform check', False, 
                               "Not running on Windows - Task Scheduler unavailable")
            print()
            return
        
        # Check for scheduled tasks
        try:
            # Main refresh task
            result = subprocess.run(
                ['schtasks', '/query', '/tn', 'BEDROT Cookie Refresh', '/fo', 'list'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.add_test_result('scheduler', 'Main refresh task', True)
                
                # Parse task details
                output = result.stdout
                if 'Status:' in output:
                    status_line = [line for line in output.split('\n') if 'Status:' in line][0]
                    status = status_line.split(':', 1)[1].strip()
                    
                    if status == 'Ready':
                        self.add_test_result('scheduler', 'Task status', True, f"Status: {status}")
                    else:
                        self.add_test_result('scheduler', 'Task status', False, f"Status: {status}")
                
                # Check last run time
                if 'Last Run Time:' in output:
                    last_run_line = [line for line in output.split('\n') if 'Last Run Time:' in line][0]
                    last_run = last_run_line.split(':', 1)[1].strip()
                    
                    if 'N/A' not in last_run:
                        self.add_test_result('scheduler', 'Task has run', True, f"Last run: {last_run}")
                    else:
                        self.add_test_result('scheduler', 'Task has run', False, "Task has never run")
            else:
                self.add_test_result('scheduler', 'Main refresh task', False, "Task not found")
            
            # Health check task
            result = subprocess.run(
                ['schtasks', '/query', '/tn', 'BEDROT Cookie Refresh Health Check', '/fo', 'list'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.add_test_result('scheduler', 'Health check task', True)
            else:
                self.add_test_result('scheduler', 'Health check task', False, "Task not found")
                
        except Exception as e:
            self.add_test_result('scheduler', 'Task Scheduler access', False, f"Error: {e}")
        
        print()
    
    def validate_monitoring(self):
        """Validate monitoring components"""
        print("Validating Monitoring...")
        print("-" * 40)
        
        # Check if monitoring is enabled in config
        config_file = self.project_root / 'config' / 'cookie_refresh_config.json'
        monitoring_enabled = False
        monitoring_port = 8080
        
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                if 'monitoring' in config:
                    monitoring_enabled = config['monitoring'].get('enabled', False)
                    monitoring_port = config['monitoring'].get('port', 8080)
        
        if not monitoring_enabled:
            self.add_test_result('monitoring', 'Monitoring enabled', False, "Monitoring disabled in config")
            print()
            return
        
        # Check if dashboard is accessible
        try:
            response = requests.get(f'http://localhost:{monitoring_port}/health', timeout=5)
            if response.status_code == 200:
                self.add_test_result('monitoring', 'Dashboard accessible', True)
                
                # Check health endpoint response
                try:
                    health_data = response.json()
                    if 'status' in health_data:
                        self.add_test_result('monitoring', 'Health endpoint', True, 
                                           f"Status: {health_data['status']}")
                    
                    if 'services' in health_data:
                        service_count = len(health_data['services'])
                        self.add_test_result('monitoring', 'Service monitoring', True,
                                           f"Monitoring {service_count} services")
                except:
                    self.add_test_result('monitoring', 'Health data format', False, "Invalid JSON response")
            else:
                self.add_test_result('monitoring', 'Dashboard accessible', False, 
                                   f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.add_test_result('monitoring', 'Dashboard accessible', False, 
                               f"Cannot connect to port {monitoring_port}")
        except Exception as e:
            self.add_test_result('monitoring', 'Dashboard accessible', False, f"Error: {e}")
        
        # Check metrics database
        metrics_db = self.project_root / 'data' / 'metrics.db'
        if metrics_db.exists():
            self.add_test_result('monitoring', 'Metrics database', True)
        else:
            self.add_test_result('monitoring', 'Metrics database', False, "Database not found")
        
        # Check log files
        log_dir = self.project_root / 'logs' / 'cookie_refresh'
        if log_dir.exists():
            log_files = list(log_dir.glob('*.log'))
            if log_files:
                recent_logs = [f for f in log_files if 
                             (datetime.now().timestamp() - f.stat().st_mtime) < 24*3600]
                if recent_logs:
                    self.add_test_result('monitoring', 'Recent logs', True, 
                                       f"Found {len(recent_logs)} logs from last 24h")
                else:
                    self.add_test_result('monitoring', 'Recent logs', False, "No recent logs found")
            else:
                self.add_test_result('monitoring', 'Log files', False, "No log files found")
        else:
            self.add_test_result('monitoring', 'Log directory', False, "Log directory not found")
        
        print()
    
    def validate_notifications(self):
        """Validate notification system (full validation only)"""
        print("Validating Notifications...")
        print("-" * 40)
        
        config_file = self.project_root / 'config' / 'cookie_refresh_config.json'
        if not config_file.exists():
            self.add_test_result('notifications', 'Config available', False, "Config file not found")
            print()
            return
        
        with open(config_file) as f:
            config = json.load(f)
        
        # Check email configuration
        if 'notifications' in config and 'email' in config['notifications']:
            email_config = config['notifications']['email']
            if email_config.get('enabled', False):
                # Test email connection
                smtp_server = os.getenv('SMTP_SERVER', email_config.get('smtp_server'))
                smtp_port = int(os.getenv('SMTP_PORT', email_config.get('smtp_port', 587)))
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((smtp_server, smtp_port))
                    sock.close()
                    
                    if result == 0:
                        self.add_test_result('notifications', 'Email server connection', True,
                                           f"Connected to {smtp_server}:{smtp_port}")
                    else:
                        self.add_test_result('notifications', 'Email server connection', False,
                                           f"Cannot connect to {smtp_server}:{smtp_port}")
                except Exception as e:
                    self.add_test_result('notifications', 'Email server connection', False, f"Error: {e}")
            else:
                self.add_test_result('notifications', 'Email notifications', False, "Disabled in config")
        
        # Check Slack configuration
        if 'notifications' in config and 'slack' in config['notifications']:
            slack_config = config['notifications']['slack']
            if slack_config.get('enabled', False):
                webhook_url = os.getenv('SLACK_WEBHOOK_URL', slack_config.get('webhook_url'))
                if webhook_url and webhook_url.startswith('https://hooks.slack.com/'):
                    self.add_test_result('notifications', 'Slack webhook format', True)
                else:
                    self.add_test_result('notifications', 'Slack webhook format', False, 
                                       "Invalid webhook URL")
            else:
                self.add_test_result('notifications', 'Slack notifications', False, "Disabled in config")
        
        print()
    
    def validate_performance(self):
        """Validate system performance (full validation only)"""
        print("Validating Performance...")
        print("-" * 40)
        
        # Test cookie refresh speed
        print("Testing refresh performance...")
        
        # Simulate a dry-run refresh
        start_time = time.time()
        
        try:
            # Import and test strategy loading
            from common.cookie_refresh.strategies import load_strategy
            
            test_services = ['spotify', 'tiktok', 'distrokid']
            load_times = []
            
            for service in test_services:
                service_start = time.time()
                try:
                    strategy = load_strategy('base', service)
                    load_time = time.time() - service_start
                    load_times.append(load_time)
                    
                    if load_time < 1.0:
                        self.add_test_result('performance', f"{service} strategy load", True,
                                           f"Loaded in {load_time:.3f}s")
                    else:
                        self.add_test_result('performance', f"{service} strategy load", False,
                                           f"Slow load: {load_time:.3f}s")
                except Exception as e:
                    self.add_test_result('performance', f"{service} strategy load", False, f"Error: {e}")
            
            total_time = time.time() - start_time
            avg_load_time = sum(load_times) / len(load_times) if load_times else 0
            
            if total_time < 5.0:
                self.add_test_result('performance', 'Overall load time', True,
                                   f"Total: {total_time:.3f}s, Avg: {avg_load_time:.3f}s")
            else:
                self.add_test_result('performance', 'Overall load time', False,
                                   f"Slow: {total_time:.3f}s")
            
        except Exception as e:
            self.add_test_result('performance', 'Performance test', False, f"Error: {e}")
        
        # Check resource usage
        try:
            import psutil
            
            # Get current process
            process = psutil.Process()
            
            # Memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb < 500:
                self.add_test_result('performance', 'Memory usage', True, f"{memory_mb:.1f} MB")
            else:
                self.add_test_result('performance', 'Memory usage', False, f"High: {memory_mb:.1f} MB")
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent < 50:
                self.add_test_result('performance', 'CPU usage', True, f"{cpu_percent:.1f}%")
            else:
                self.add_test_result('performance', 'CPU usage', False, f"High: {cpu_percent:.1f}%")
                
        except ImportError:
            self.add_test_result('performance', 'Resource monitoring', False, "psutil not installed")
        except Exception as e:
            self.add_test_result('performance', 'Resource monitoring', False, f"Error: {e}")
        
        print()
    
    def validate_service_config(self, service: str, config: Dict) -> bool:
        """Validate individual service configuration"""
        required_fields = ['enabled', 'refresh_interval_hours', 'strategy']
        
        for field in required_fields:
            if field not in config:
                return False
        
        # Validate field values
        if not isinstance(config['enabled'], bool):
            return False
        
        if not isinstance(config['refresh_interval_hours'], (int, float)):
            return False
        
        if config['strategy'] not in ['oauth', 'playwright', 'jwt', 'api']:
            return False
        
        return True
    
    def add_test_result(self, category: str, test_name: str, passed: bool, details: str = ""):
        """Add a test result"""
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.validation_results[category]['tests'].append(result)
        
        if passed:
            self.validation_results[category]['passed'] += 1
            print(f"  ✓ {test_name}")
        else:
            self.validation_results[category]['failed'] += 1
            print(f"  ✗ {test_name}")
        
        if details:
            print(f"    → {details}")
    
    def print_results(self):
        """Print validation results summary"""
        print("\n" + "=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.validation_results.items():
            if results['tests']:  # Only show categories with tests
                passed = results['passed']
                failed = results['failed']
                total = passed + failed
                
                total_passed += passed
                total_failed += failed
                
                status = "✓" if failed == 0 else "✗"
                print(f"\n{status} {category.upper()}: {passed}/{total} passed")
                
                if failed > 0:
                    # Show failed tests
                    for test in results['tests']:
                        if not test['passed']:
                            print(f"  - {test['test']}: {test['details']}")
        
        # Overall summary
        print("\n" + "-" * 70)
        print("OVERALL SUMMARY")
        print("-" * 70)
        
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"\nValidation completed in {duration:.1f} seconds")
        
        if total_failed == 0:
            print("\n✅ DEPLOYMENT VALIDATION SUCCESSFUL!")
            print("\nThe cookie refresh system is properly deployed and ready for use.")
        else:
            print(f"\n❌ DEPLOYMENT VALIDATION FAILED")
            print(f"\n{total_failed} issues need to be resolved before the system is fully operational.")
            print("\nRefer to the failed tests above and consult the troubleshooting guide.")
        
        # Save detailed report
        report_file = self.project_root / f'deployment_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report_data = {
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': duration,
            'summary': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'success_rate': success_rate
            },
            'results': self.validation_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file.name}")


def main():
    """Run deployment validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate cookie refresh system deployment')
    parser.add_argument('--full', action='store_true', help='Run full validation including notifications and performance')
    
    args = parser.parse_args()
    
    validator = DeploymentValidator()
    success = validator.run_validation(full=args.full)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()