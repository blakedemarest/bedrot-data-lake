#!/usr/bin/env python3
"""
Pre-deployment readiness check script
Verifies all requirements are met before deployment
"""

import sys
import os
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime
import importlib.util
import socket
import shutil
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class DeploymentChecker:
    """Comprehensive deployment readiness checker"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []
        self.project_root = Path(__file__).parent.parent.parent
        
    def run_all_checks(self) -> bool:
        """Run all deployment checks"""
        print("=" * 60)
        print("BEDROT Cookie Refresh System - Deployment Readiness Check")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project Root: {self.project_root}")
        print("=" * 60)
        print()
        
        # Run checks
        self.check_python_version()
        self.check_operating_system()
        self.check_required_packages()
        self.check_playwright_browsers()
        self.check_environment_variables()
        self.check_directory_permissions()
        self.check_network_connectivity()
        self.check_disk_space()
        self.check_existing_installation()
        self.check_service_credentials()
        self.check_configuration_files()
        
        # Summary
        self.print_summary()
        
        return self.checks_failed == 0
    
    def check_python_version(self):
        """Check Python version compatibility"""
        print("Checking Python version...")
        required_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= required_version:
            self.check_passed(f"Python {sys.version.split()[0]} ✓")
        else:
            self.check_failed(f"Python {current_version} is below required {required_version}")
    
    def check_operating_system(self):
        """Check OS compatibility"""
        print("\nChecking operating system...")
        
        if platform.system() == "Windows":
            version = platform.version()
            self.check_passed(f"Windows {version} ✓")
            
            # Check for WSL
            if "Microsoft" in platform.release():
                self.add_warning("Running in WSL - some features may have limited functionality")
        else:
            self.add_warning(f"Non-Windows OS detected ({platform.system()}) - Task Scheduler integration unavailable")
    
    def check_required_packages(self):
        """Check if all required packages are installed"""
        print("\nChecking required packages...")
        
        required_packages = [
            ('playwright', '1.40.0'),
            ('requests', '2.31.0'),
            ('python-dotenv', '1.0.0'),
            ('cryptography', '41.0.0'),
            ('apscheduler', '3.10.0'),
            ('flask', '3.0.0'),
            ('pandas', '2.0.0'),
            ('pydantic', '2.0.0'),
            ('beautifulsoup4', '4.12.0'),
            ('selenium', '4.0.0'),
        ]
        
        missing_packages = []
        outdated_packages = []
        
        for package, min_version in required_packages:
            try:
                spec = importlib.util.find_spec(package.replace('-', '_'))
                if spec is None:
                    missing_packages.append(package)
                else:
                    # Try to check version
                    try:
                        module = importlib.import_module(package.replace('-', '_'))
                        if hasattr(module, '__version__'):
                            current = module.__version__
                            if self.compare_versions(current, min_version) < 0:
                                outdated_packages.append(f"{package} (current: {current}, required: {min_version})")
                    except:
                        pass  # Can't check version, assume OK
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.check_failed(f"Missing packages: {', '.join(missing_packages)}")
        elif outdated_packages:
            self.add_warning(f"Outdated packages: {', '.join(outdated_packages)}")
            self.check_passed("All required packages installed (some may need updates)")
        else:
            self.check_passed("All required packages installed with correct versions ✓")
    
    def check_playwright_browsers(self):
        """Check if Playwright browsers are installed"""
        print("\nChecking Playwright browsers...")
        
        try:
            result = subprocess.run(
                ["playwright", "install", "--dry-run"],
                capture_output=True,
                text=True
            )
            
            if "chromium" in result.stdout.lower() and "already installed" in result.stdout.lower():
                self.check_passed("Playwright Chromium browser installed ✓")
            else:
                self.check_failed("Playwright browsers not installed - run 'playwright install chromium'")
        except FileNotFoundError:
            self.check_failed("Playwright CLI not found - ensure playwright is installed")
    
    def check_environment_variables(self):
        """Check required environment variables"""
        print("\nChecking environment variables...")
        
        required_vars = {
            'PROJECT_ROOT': 'Project root directory',
            'SPOTIFY_CLIENT_ID': 'Spotify OAuth client ID',
            'SPOTIFY_CLIENT_SECRET': 'Spotify OAuth client secret',
        }
        
        recommended_vars = {
            'TIKTOK_USERNAME': 'TikTok username',
            'TIKTOK_PASSWORD': 'TikTok password',
            'DISTROKID_USERNAME': 'DistroKid username',
            'DISTROKID_PASSWORD': 'DistroKid password',
            'TOOLOST_USERNAME': 'TooLost username',
            'TOOLOST_PASSWORD': 'TooLost password',
            'LINKTREE_USERNAME': 'Linktree username',
            'LINKTREE_PASSWORD': 'Linktree password',
        }
        
        missing_required = []
        missing_recommended = []
        
        # Check .env file
        env_file = self.project_root / '.env'
        env_vars = {}
        
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # Check required variables
        for var, desc in required_vars.items():
            if var not in os.environ and var not in env_vars:
                missing_required.append(f"{var} ({desc})")
        
        # Check recommended variables
        for var, desc in recommended_vars.items():
            if var not in os.environ and var not in env_vars:
                missing_recommended.append(f"{var} ({desc})")
        
        if missing_required:
            self.check_failed(f"Missing required variables: {', '.join(missing_required)}")
        else:
            self.check_passed("All required environment variables set ✓")
            
        if missing_recommended:
            self.add_warning(f"Missing recommended variables: {', '.join(missing_recommended)}")
    
    def check_directory_permissions(self):
        """Check write permissions in required directories"""
        print("\nChecking directory permissions...")
        
        required_dirs = [
            'config',
            'logs',
            'backups',
            'src/spotify/cookies',
            'src/tiktok/cookies',
            'src/distrokid/cookies',
            'src/toolost/cookies',
            'src/linktree/cookies',
        ]
        
        permission_issues = []
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permission
            test_file = full_path / '.permission_test'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except Exception as e:
                permission_issues.append(f"{dir_path}: {str(e)}")
        
        if permission_issues:
            self.check_failed(f"Permission issues: {', '.join(permission_issues)}")
        else:
            self.check_passed("All directories have write permissions ✓")
    
    def check_network_connectivity(self):
        """Check network connectivity to required services"""
        print("\nChecking network connectivity...")
        
        endpoints = [
            ('spotify.com', 443, 'Spotify'),
            ('tiktok.com', 443, 'TikTok'),
            ('distrokid.com', 443, 'DistroKid'),
            ('toolost.com', 443, 'TooLost'),
            ('linktr.ee', 443, 'Linktree'),
            ('api.github.com', 443, 'GitHub (for updates)'),
        ]
        
        connection_issues = []
        
        for host, port, service in endpoints:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result != 0:
                    connection_issues.append(f"{service} ({host}:{port})")
            except Exception as e:
                connection_issues.append(f"{service} ({host}:{port}): {str(e)}")
        
        if connection_issues:
            self.check_failed(f"Cannot connect to: {', '.join(connection_issues)}")
        else:
            self.check_passed("Network connectivity verified ✓")
    
    def check_disk_space(self):
        """Check available disk space"""
        print("\nChecking disk space...")
        
        required_gb = 10
        
        if platform.system() == "Windows":
            import ctypes
            
            drive = str(self.project_root.drive) + '\\'
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(drive),
                ctypes.pointer(free_bytes),
                None,
                None
            )
            free_gb = free_bytes.value / (1024**3)
        else:
            stat = os.statvfs(self.project_root)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        
        if free_gb < required_gb:
            self.check_failed(f"Insufficient disk space: {free_gb:.1f}GB available, {required_gb}GB required")
        else:
            self.check_passed(f"Disk space: {free_gb:.1f}GB available ✓")
    
    def check_existing_installation(self):
        """Check for existing installation and backups"""
        print("\nChecking existing installation...")
        
        # Check for existing cookies
        cookie_dirs = list(self.project_root.glob("src/*/cookies/*.json"))
        if cookie_dirs:
            self.add_warning(f"Found {len(cookie_dirs)} existing cookie files - ensure backups are created")
            
            # Check for backups
            backup_dir = self.project_root / 'backups'
            if backup_dir.exists():
                backups = list(backup_dir.glob("*.json"))
                if backups:
                    latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
                    age_days = (datetime.now().timestamp() - latest_backup.stat().st_mtime) / (24 * 3600)
                    if age_days > 7:
                        self.add_warning(f"Latest backup is {age_days:.1f} days old - create fresh backup")
                    else:
                        self.check_passed(f"Recent backup found ({age_days:.1f} days old) ✓")
                else:
                    self.add_warning("No backups found - create backup before deployment")
            else:
                self.add_warning("Backup directory not found - will be created")
        else:
            self.check_passed("Clean installation - no existing cookies found ✓")
    
    def check_service_credentials(self):
        """Verify service credentials are valid format"""
        print("\nChecking service credentials format...")
        
        # Load .env file
        env_file = self.project_root / '.env'
        if not env_file.exists():
            self.add_warning("No .env file found - will need to create one")
            return
        
        issues = []
        
        with open(env_file) as f:
            env_content = f.read()
            
            # Check for common credential issues
            if 'your_' in env_content or 'xxx' in env_content.lower() or 'placeholder' in env_content.lower():
                issues.append("Placeholder values detected in .env file")
            
            # Check Spotify OAuth format
            if 'SPOTIFY_CLIENT_ID=' in env_content:
                for line in env_content.split('\n'):
                    if line.startswith('SPOTIFY_CLIENT_ID='):
                        client_id = line.split('=', 1)[1].strip()
                        if len(client_id) != 32:
                            issues.append("Spotify Client ID should be 32 characters")
            
            # Check for quotes in values (common mistake)
            if '"' in env_content or "'" in env_content:
                self.add_warning("Quotes detected in .env file - ensure values are unquoted")
        
        if issues:
            self.check_failed(f"Credential issues: {', '.join(issues)}")
        else:
            self.check_passed("Credential format appears valid ✓")
    
    def check_configuration_files(self):
        """Check for required configuration files"""
        print("\nChecking configuration files...")
        
        config_dir = self.project_root / 'config'
        config_file = config_dir / 'cookie_refresh_config.json'
        
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                self.check_passed("Configuration file valid ✓")
            except json.JSONDecodeError as e:
                self.check_failed(f"Invalid JSON in config file: {e}")
        else:
            self.add_warning("Configuration file not found - will use defaults")
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """Compare version strings"""
        def normalize(v):
            parts = [int(x) for x in v.split('.')]
            return parts + [0] * (3 - len(parts))
        
        v1_parts = normalize(v1)
        v2_parts = normalize(v2)
        
        for i in range(3):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        return 0
    
    def check_passed(self, message: str):
        """Record a passed check"""
        print(f"  ✓ {message}")
        self.checks_passed += 1
    
    def check_failed(self, message: str):
        """Record a failed check"""
        print(f"  ✗ {message}")
        self.checks_failed += 1
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning"""
        print(f"  ⚠ {message}")
        self.warnings.append(message)
    
    def print_summary(self):
        """Print summary of all checks"""
        print("\n" + "=" * 60)
        print("DEPLOYMENT READINESS SUMMARY")
        print("=" * 60)
        
        total_checks = self.checks_passed + self.checks_failed
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {self.checks_passed}")
        print(f"Failed: {self.checks_failed}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.checks_failed > 0:
            print("\n❌ DEPLOYMENT NOT READY")
            print("\nFailed Checks:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ DEPLOYMENT READY")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        print("\n" + "=" * 60)
        
        # Create readiness report
        report = {
            'timestamp': datetime.now().isoformat(),
            'ready': self.checks_failed == 0,
            'checks': {
                'total': total_checks,
                'passed': self.checks_passed,
                'failed': self.checks_failed
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'environment': {
                'python_version': sys.version,
                'platform': platform.platform(),
                'project_root': str(self.project_root)
            }
        }
        
        report_file = self.project_root / 'deployment_readiness_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")


def main():
    """Run deployment readiness check"""
    checker = DeploymentChecker()
    ready = checker.run_all_checks()
    
    if not ready:
        print("\n⚠️  Please address the failed checks before proceeding with deployment.")
        sys.exit(1)
    else:
        print("\n✅ System is ready for deployment!")
        print("\nNext steps:")
        print("1. Create a backup: python scripts/deployment/backup_existing_cookies.py")
        print("2. Run migration: python scripts/deployment/migrate_cookies.py")
        print("3. Validate deployment: python scripts/deployment/validate_deployment.py")
        sys.exit(0)


if __name__ == "__main__":
    main()