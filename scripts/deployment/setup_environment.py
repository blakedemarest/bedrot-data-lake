#!/usr/bin/env python3
"""
Environment setup script for cookie refresh system
Sets up all required directories, configurations, and dependencies
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import platform

class EnvironmentSetup:
    """Sets up the complete environment for cookie refresh system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.setup_log = []
        self.errors = []
        
    def setup_all(self):
        """Run complete environment setup"""
        print("=" * 60)
        print("Cookie Refresh System - Environment Setup")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project Root: {self.project_root}")
        print(f"Platform: {platform.system()} {platform.version()}")
        print("=" * 60)
        print()
        
        # Run setup steps
        self.create_directory_structure()
        self.create_default_configs()
        self.setup_environment_file()
        self.install_dependencies()
        self.setup_logging()
        self.create_initial_backups()
        self.setup_scheduler_scripts()
        self.verify_setup()
        
        # Print summary
        self.print_summary()
        
        return len(self.errors) == 0
    
    def create_directory_structure(self):
        """Create all required directories"""
        print("Creating directory structure...")
        
        directories = [
            'config',
            'logs/cookie_refresh',
            'logs/cookie_refresh/services',
            'logs/cookie_refresh/errors',
            'backups/cookies',
            'backups/config',
            'data/metrics',
            'scripts/deployment',
            'scripts/maintenance',
            'monitoring/dashboards',
            'scheduler/tasks',
        ]
        
        for service in ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree', 'metaads']:
            directories.extend([
                f'src/{service}/cookies',
                f'backups/cookies/{service}',
                f'logs/cookie_refresh/services/{service}',
            ])
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                self.log_success(f"Created directory: {dir_path}")
            except Exception as e:
                self.log_error(f"Failed to create {dir_path}: {e}")
        
        print(f"  ✓ Created {len(directories)} directories\n")
    
    def create_default_configs(self):
        """Create default configuration files"""
        print("Creating default configurations...")
        
        # Main cookie refresh config
        config_file = self.project_root / 'config' / 'cookie_refresh_config.json'
        
        default_config = {
            "global": {
                "check_interval_minutes": 60,
                "max_retry_attempts": 3,
                "retry_delay_seconds": 300,
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
                    "max_age_days": 30,
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
                    "max_age_days": 30,
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
                    "refresh_interval_hours": 240,
                    "max_age_days": 12,
                    "strategy": "jwt",
                    "priority": 3,
                    "jwt_expiry_days": 12,
                    "credentials": {
                        "username_env": "DISTROKID_USERNAME",
                        "password_env": "DISTROKID_PASSWORD"
                    }
                },
                "toolost": {
                    "enabled": True,
                    "refresh_interval_hours": 120,
                    "max_age_days": 7,
                    "strategy": "jwt",
                    "priority": 4,
                    "jwt_expiry_days": 7,
                    "credentials": {
                        "username_env": "TOOLOST_USERNAME",
                        "password_env": "TOOLOST_PASSWORD"
                    }
                },
                "linktree": {
                    "enabled": True,
                    "refresh_interval_hours": 336,
                    "max_age_days": 30,
                    "strategy": "playwright",
                    "priority": 5,
                    "credentials": {
                        "username_env": "LINKTREE_USERNAME",
                        "password_env": "LINKTREE_PASSWORD"
                    }
                },
                "metaads": {
                    "enabled": False,
                    "refresh_interval_hours": 720,
                    "max_age_days": 60,
                    "strategy": "oauth",
                    "priority": 6,
                    "credentials": {
                        "access_token_env": "META_ACCESS_TOKEN"
                    }
                }
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "${SMTP_SERVER}",
                    "smtp_port": "${SMTP_PORT}",
                    "username": "${SMTP_USERNAME}",
                    "password": "${SMTP_PASSWORD}",
                    "from_address": "${SMTP_USERNAME}",
                    "to_addresses": ["${NOTIFICATION_EMAIL}"]
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "${SLACK_WEBHOOK_URL}"
                }
            },
            "monitoring": {
                "enabled": True,
                "port": 8080,
                "metrics_retention_days": 30,
                "dashboard_refresh_seconds": 30
            },
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 100,
                "backup_count": 10,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        if not config_file.exists():
            try:
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                self.log_success("Created default cookie_refresh_config.json")
            except Exception as e:
                self.log_error(f"Failed to create config: {e}")
        else:
            self.log_success("Config file already exists")
        
        # Create notification templates
        self.create_notification_templates()
        
        print("  ✓ Configuration files created\n")
    
    def create_notification_templates(self):
        """Create email and Slack notification templates"""
        templates_dir = self.project_root / 'config' / 'templates'
        templates_dir.mkdir(exist_ok=True)
        
        # Email template
        email_template = """Subject: BEDROT Cookie Refresh - {subject}

Hello,

This is an automated notification from the BEDROT Cookie Refresh System.

{message}

Service: {service}
Status: {status}
Timestamp: {timestamp}

{details}

--
BEDROT Data Ecosystem
Automated Cookie Management System
"""
        
        # Slack template
        slack_template = {
            "text": "BEDROT Cookie Refresh Alert",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "{subject}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "{message}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Service:* {'{service}'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {'{status}'}"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Timestamp: {'{timestamp}'}"
                        }
                    ]
                }
            ]
        }
        
        try:
            (templates_dir / 'email_template.txt').write_text(email_template)
            (templates_dir / 'slack_template.json').write_text(json.dumps(slack_template, indent=2))
            self.log_success("Created notification templates")
        except Exception as e:
            self.log_error(f"Failed to create templates: {e}")
    
    def setup_environment_file(self):
        """Create or update .env file with required variables"""
        print("Setting up environment variables...")
        
        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'
        
        # Create .env.example
        example_content = """# Cookie Refresh System Environment Variables

# Project Settings
PROJECT_ROOT=C:\\Users\\Earth\\BEDROT PRODUCTIONS\\bedrot-data-ecosystem\\data_lake
COOKIE_REFRESH_LOG_LEVEL=INFO
COOKIE_REFRESH_CONFIG_FILE=config/cookie_refresh_config.json

# Spotify OAuth
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# TikTok Credentials
TIKTOK_USERNAME=your_tiktok_username
TIKTOK_PASSWORD=your_tiktok_password

# DistroKid Credentials
DISTROKID_USERNAME=your_distrokid_username
DISTROKID_PASSWORD=your_distrokid_password

# TooLost Credentials
TOOLOST_USERNAME=your_toolost_username
TOOLOST_PASSWORD=your_toolost_password

# Linktree Credentials
LINKTREE_USERNAME=your_linktree_username
LINKTREE_PASSWORD=your_linktree_password

# Meta Ads (Optional)
META_ACCESS_TOKEN=your_meta_access_token

# Email Notifications (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=admin@company.com

# Slack Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Advanced Settings
COOKIE_REFRESH_DRY_RUN=false
COOKIE_REFRESH_HEADLESS=true
COOKIE_REFRESH_PARALLEL=true
"""
        
        try:
            env_example.write_text(example_content)
            self.log_success("Created .env.example")
            
            if not env_file.exists():
                shutil.copy(env_example, env_file)
                self.log_success("Created .env from example")
                print("  ⚠️  Please update .env with your actual credentials")
            else:
                self.log_success(".env file already exists")
        except Exception as e:
            self.log_error(f"Failed to setup environment: {e}")
        
        print("  ✓ Environment files configured\n")
    
    def install_dependencies(self):
        """Ensure all required packages are installed"""
        print("Checking dependencies...")
        
        try:
            # Check if in virtual environment
            if sys.prefix == sys.base_prefix:
                print("  ⚠️  Not in a virtual environment - skipping dependency check")
                print("     Run 'pip install -r requirements.txt' manually")
                return
            
            # Check for missing packages
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log_success("All dependencies satisfied")
            else:
                print("  ⚠️  Some dependencies may be missing")
                print("     Run 'pip install -r requirements.txt' to install")
                
        except Exception as e:
            self.log_error(f"Failed to check dependencies: {e}")
        
        print()
    
    def setup_logging(self):
        """Configure logging system"""
        print("Setting up logging...")
        
        # Create log config
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": "logs/cookie_refresh/cookie_refresh.log",
                    "maxBytes": 104857600,
                    "backupCount": 10
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": "logs/cookie_refresh/errors/errors.log",
                    "maxBytes": 10485760,
                    "backupCount": 5
                }
            },
            "loggers": {
                "cookie_refresh": {
                    "level": "DEBUG",
                    "handlers": ["console", "file", "error_file"],
                    "propagate": False
                }
            }
        }
        
        log_config_file = self.project_root / 'config' / 'logging_config.json'
        
        try:
            with open(log_config_file, 'w') as f:
                json.dump(log_config, f, indent=2)
            self.log_success("Created logging configuration")
        except Exception as e:
            self.log_error(f"Failed to setup logging: {e}")
        
        print("  ✓ Logging configured\n")
    
    def create_initial_backups(self):
        """Create initial backup of existing cookies"""
        print("Creating initial backups...")
        
        backup_count = 0
        
        for service in ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree']:
            cookie_dir = self.project_root / 'src' / service / 'cookies'
            if cookie_dir.exists():
                cookie_files = list(cookie_dir.glob('*.json'))
                for cookie_file in cookie_files:
                    if '_hashes' not in cookie_file.name:
                        backup_dir = self.project_root / 'backups' / 'cookies' / service
                        backup_name = f"{cookie_file.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        backup_path = backup_dir / backup_name
                        
                        try:
                            shutil.copy2(cookie_file, backup_path)
                            backup_count += 1
                        except Exception as e:
                            self.log_error(f"Failed to backup {cookie_file}: {e}")
        
        if backup_count > 0:
            self.log_success(f"Created {backup_count} cookie backups")
        else:
            self.log_success("No existing cookies to backup")
        
        print("  ✓ Backup complete\n")
    
    def setup_scheduler_scripts(self):
        """Create scheduler and maintenance scripts"""
        print("Creating scheduler scripts...")
        
        scripts_dir = self.project_root / 'scripts' / 'scheduler'
        scripts_dir.mkdir(exist_ok=True)
        
        # Windows batch file for manual refresh
        batch_content = """@echo off
echo Starting BEDROT Cookie Refresh...
echo.

cd /d "{project_root}"
call .venv\\Scripts\\activate

python src\\common\\cookie_refresh\\scheduler.py %*

echo.
echo Cookie refresh complete.
pause
""".format(project_root=self.project_root)
        
        # PowerShell script for Task Scheduler
        ps1_content = """# BEDROT Cookie Refresh Task
$projectRoot = "{project_root}"
$pythonPath = "$projectRoot\\.venv\\Scripts\\python.exe"
$scriptPath = "$projectRoot\\src\\common\\cookie_refresh\\scheduler.py"

# Change to project directory
Set-Location $projectRoot

# Run the scheduler
& $pythonPath $scriptPath --daemon

# Log completion
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "$projectRoot\\logs\\scheduler.log" -Value "$timestamp - Scheduler task completed"
""".format(project_root=self.project_root)
        
        # Daily maintenance script
        maintenance_content = """#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from common.cookie_refresh.maintenance import run_daily_maintenance

if __name__ == "__main__":
    run_daily_maintenance()
"""
        
        try:
            (scripts_dir / 'run_cookie_refresh.bat').write_text(batch_content)
            (scripts_dir / 'cookie_refresh_task.ps1').write_text(ps1_content)
            (scripts_dir / 'daily_maintenance.py').write_text(maintenance_content)
            
            self.log_success("Created scheduler scripts")
        except Exception as e:
            self.log_error(f"Failed to create scripts: {e}")
        
        print("  ✓ Scheduler scripts created\n")
    
    def verify_setup(self):
        """Verify the setup is complete"""
        print("Verifying setup...")
        
        checks = [
            ('config/cookie_refresh_config.json', 'Configuration file'),
            ('.env', 'Environment file'),
            ('logs/cookie_refresh', 'Log directory'),
            ('backups/cookies', 'Backup directory'),
            ('scripts/scheduler/run_cookie_refresh.bat', 'Scheduler script'),
        ]
        
        all_good = True
        
        for path, description in checks:
            full_path = self.project_root / path
            if full_path.exists():
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description} missing")
                all_good = False
        
        if all_good:
            self.log_success("Setup verification passed")
        else:
            self.log_error("Some components are missing")
        
        print()
    
    def log_success(self, message):
        """Log a successful operation"""
        self.setup_log.append(('SUCCESS', message))
    
    def log_error(self, message):
        """Log an error"""
        self.setup_log.append(('ERROR', message))
        self.errors.append(message)
    
    def print_summary(self):
        """Print setup summary"""
        print("=" * 60)
        print("SETUP SUMMARY")
        print("=" * 60)
        
        success_count = len([l for l in self.setup_log if l[0] == 'SUCCESS'])
        error_count = len(self.errors)
        
        print(f"Total operations: {len(self.setup_log)}")
        print(f"Successful: {success_count}")
        print(f"Errors: {error_count}")
        
        if error_count > 0:
            print("\nErrors encountered:")
            for error in self.errors:
                print(f"  - {error}")
            print("\n❌ Setup completed with errors")
        else:
            print("\n✅ Setup completed successfully!")
        
        print("\nNext steps:")
        print("1. Update .env file with your credentials")
        print("2. Run deployment validation: python scripts/deployment/validate_deployment.py")
        print("3. Test cookie refresh: python src/common/cookie_refresh/test_strategies.py")
        print("4. Start scheduler: python src/common/cookie_refresh/scheduler.py")
        
        # Save setup log
        log_file = self.project_root / f'setup_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(log_file, 'w') as f:
            f.write(f"Environment Setup Log\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            
            for status, message in self.setup_log:
                f.write(f"[{status}] {message}\n")
        
        print(f"\nSetup log saved to: {log_file.name}")


def main():
    """Run environment setup"""
    setup = EnvironmentSetup()
    success = setup.setup_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()