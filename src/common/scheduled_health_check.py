#!/usr/bin/env python3
"""
Scheduled Health Check Script

Runs periodic health checks and takes automated actions:
- Monitors pipeline health every 30 minutes
- Sends notifications for critical issues
- Triggers automatic cookie refresh when needed
- Generates daily summary reports
"""

import os
import sys
import json
import schedule
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline_health_monitor import PipelineHealthMonitor, HealthStatus
from cookie_refresh.dashboard import CookieRefreshDashboard
from cookie_refresh.notifier import CookieRefreshNotifier, NotificationLevel
from cookie_refresh.config_loader import load_config
from logging_config import setup_logging, get_logger

# Set up logging
logger = get_logger('pipeline.health.scheduler')


class ScheduledHealthChecker:
    """Orchestrates scheduled health checks and automated actions."""
    
    def __init__(self, check_interval: int = 30, enable_auto_fix: bool = True):
        """Initialize health checker.
        
        Args:
            check_interval: Minutes between health checks
            enable_auto_fix: Enable automatic issue resolution
        """
        self.check_interval = check_interval
        self.enable_auto_fix = enable_auto_fix
        self.project_root = Path(os.environ.get('PROJECT_ROOT', Path(__file__).resolve().parents[2]))
        
        # Initialize components
        self.monitor = PipelineHealthMonitor(
            enable_auto_remediation=enable_auto_fix,
            enable_notifications=True
        )
        
        self.dashboard = CookieRefreshDashboard()
        
        # Load notification config
        config = load_config()
        self.notifier = CookieRefreshNotifier(config.get('notifications', {}))
        
        # Track state
        self.last_check_time = None
        self.last_report = None
        self.check_history = []
        self.daily_summary_sent = False
    
    def run_health_check(self):
        """Execute a health check cycle."""
        logger.info("Starting scheduled health check")
        
        try:
            # Generate health report
            report = self.monitor.generate_report()
            self.last_report = report
            self.last_check_time = datetime.now()
            
            # Store check result
            check_result = {
                'timestamp': report['timestamp'],
                'overall_status': report['overall_status'],
                'services_count': len(report['services']),
                'critical_count': sum(1 for s in report['services'].values() 
                                    if s['status'] in ['CRITICAL', 'FAILED']),
                'remediation_count': len(report.get('remediation_actions', []))
            }
            
            self.check_history.append(check_result)
            
            # Limit history size
            if len(self.check_history) > 100:
                self.check_history = self.check_history[-50:]
            
            # Log summary
            logger.info(
                f"Health check complete: {report['overall_status']} "
                f"({check_result['critical_count']} critical issues)"
            )
            
            # Handle critical issues
            if report['overall_status'] in [HealthStatus.CRITICAL.value, HealthStatus.FAILED.value]:
                self._handle_critical_status(report)
            elif report['overall_status'] == HealthStatus.WARNING.value:
                self._handle_warning_status(report)
            
            # Save report
            self._save_report(report)
            
            # Update dashboard
            self.dashboard.generate_dashboard(auto_open=False)
            
        except Exception as e:
            logger.error(f"Error during health check: {e}", exc_info=True)
            
            # Send error notification
            self.notifier.send_custom_notification(
                level=NotificationLevel.ERROR,
                message=f"Health check failed: {str(e)}",
                service="HEALTH_MONITOR",
                details={'error': str(e)}
            )
    
    def _handle_critical_status(self, report: Dict[str, Any]):
        """Handle critical pipeline status."""
        critical_services = [
            (name, data) for name, data in report['services'].items()
            if data['status'] in [HealthStatus.CRITICAL.value, HealthStatus.FAILED.value]
        ]
        
        # Build notification message
        message_parts = [f"{name} ({data['status']})" for name, data in critical_services]
        
        # Send critical notification
        self.notifier.send_custom_notification(
            level=NotificationLevel.CRITICAL,
            message=f"Pipeline critical: {', '.join(message_parts)}",
            service="HEALTH_MONITOR",
            details={
                'critical_services': [name for name, _ in critical_services],
                'overall_status': report['overall_status'],
                'auto_remediation': 'Enabled' if self.enable_auto_fix else 'Disabled'
            }
        )
        
        # Log critical issues
        for service_name, service_data in critical_services:
            logger.critical(
                f"Service {service_name} is {service_data['status']}: "
                f"Score={service_data['health_score']}, "
                f"Cookie={service_data['cookie_health']['status']}"
            )
    
    def _handle_warning_status(self, report: Dict[str, Any]):
        """Handle warning pipeline status."""
        warning_services = [
            name for name, data in report['services'].items()
            if data['status'] == HealthStatus.WARNING.value
        ]
        
        if warning_services:
            # Send warning notification
            self.notifier.send_custom_notification(
                level=NotificationLevel.WARNING,
                message=f"Pipeline warnings for: {', '.join(warning_services)}",
                service="HEALTH_MONITOR",
                details={
                    'warning_services': warning_services,
                    'overall_status': report['overall_status']
                }
            )
    
    def _save_report(self, report: Dict[str, Any]):
        """Save health report to file."""
        # Create reports directory
        reports_dir = self.project_root / 'reports' / 'health'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save timestamped report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f'health_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also save as latest
        latest_file = reports_dir / 'latest_health_report.json'
        with open(latest_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.debug(f"Health report saved to {report_file}")
    
    def generate_daily_summary(self):
        """Generate and send daily summary report."""
        logger.info("Generating daily summary report")
        
        try:
            # Get summary data
            summary_data = self._compile_daily_summary()
            
            # Generate dashboard summary
            dashboard_summary = self.dashboard.generate_summary_report('markdown')
            
            # Build email content
            email_content = f"""
# BEDROT Pipeline Daily Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Health Check Summary
- Total checks: {summary_data['total_checks']}
- Average health score: {summary_data['avg_health_score']:.1f}%
- Critical incidents: {summary_data['critical_incidents']}
- Warnings: {summary_data['warnings']}
- Auto-remediations: {summary_data['auto_remediations']}

## Current Status
{dashboard_summary}

## Recommendations
{self._generate_recommendations(summary_data)}

---
This is an automated daily summary from the BEDROT Pipeline Health Monitor.
"""
            
            # Send summary notification
            self.notifier.send_custom_notification(
                level=NotificationLevel.INFO,
                message="Daily Pipeline Summary",
                service="HEALTH_MONITOR",
                details={
                    'summary': email_content,
                    'stats': summary_data
                }
            )
            
            # Mark as sent
            self.daily_summary_sent = True
            logger.info("Daily summary sent successfully")
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}", exc_info=True)
    
    def _compile_daily_summary(self) -> Dict[str, Any]:
        """Compile statistics for daily summary."""
        # Get checks from last 24 hours
        cutoff_time = datetime.now() - timedelta(days=1)
        recent_checks = [
            check for check in self.check_history
            if datetime.fromisoformat(check['timestamp']) > cutoff_time
        ]
        
        if not recent_checks:
            return {
                'total_checks': 0,
                'avg_health_score': 0,
                'critical_incidents': 0,
                'warnings': 0,
                'auto_remediations': 0
            }
        
        # Calculate statistics
        total_checks = len(recent_checks)
        critical_incidents = sum(1 for c in recent_checks 
                               if c['overall_status'] in ['CRITICAL', 'FAILED'])
        warnings = sum(1 for c in recent_checks 
                      if c['overall_status'] == 'WARNING')
        auto_remediations = sum(c.get('remediation_count', 0) for c in recent_checks)
        
        # Calculate average health score from latest report
        avg_health_score = 0
        if self.last_report and 'services' in self.last_report:
            scores = [s['health_score'] for s in self.last_report['services'].values()]
            avg_health_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_checks': total_checks,
            'avg_health_score': avg_health_score,
            'critical_incidents': critical_incidents,
            'warnings': warnings,
            'auto_remediations': auto_remediations
        }
    
    def _generate_recommendations(self, summary_data: Dict[str, Any]) -> str:
        """Generate recommendations based on summary data."""
        recommendations = []
        
        if summary_data['critical_incidents'] > 5:
            recommendations.append(
                "- High number of critical incidents. Consider reviewing authentication "
                "procedures and increasing monitoring frequency."
            )
        
        if summary_data['avg_health_score'] < 70:
            recommendations.append(
                "- Overall health score is low. Review service configurations and "
                "ensure all extractors are running properly."
            )
        
        if summary_data['auto_remediations'] > 10:
            recommendations.append(
                "- Frequent auto-remediations suggest underlying issues. "
                "Manual investigation recommended."
            )
        
        if not recommendations:
            recommendations.append("- Pipeline is operating normally. No immediate actions required.")
        
        return "\n".join(recommendations)
    
    def start_scheduler(self):
        """Start the scheduled health checks."""
        logger.info(f"Starting health check scheduler (interval: {self.check_interval} minutes)")
        
        # Schedule periodic health checks
        schedule.every(self.check_interval).minutes.do(self.run_health_check)
        
        # Schedule daily summary at 9 AM
        schedule.every().day.at("09:00").do(self.generate_daily_summary)
        
        # Run initial check
        self.run_health_check()
        
        # Main scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Reset daily summary flag at midnight
                if datetime.now().hour == 0 and self.daily_summary_sent:
                    self.daily_summary_sent = False
                    
        except KeyboardInterrupt:
            logger.info("Health check scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            raise
    
    def run_once(self):
        """Run a single health check and exit."""
        logger.info("Running single health check")
        self.run_health_check()
        
        # Print summary to console
        if self.last_report:
            print("\n" + "="*60)
            print("HEALTH CHECK SUMMARY")
            print("="*60)
            print(f"Overall Status: {self.last_report['overall_status']}")
            print(f"Timestamp: {self.last_report['timestamp']}")
            
            # Service summary
            services = self.last_report['services']
            healthy = sum(1 for s in services.values() if s['status'] == 'HEALTHY')
            warning = sum(1 for s in services.values() if s['status'] == 'WARNING')
            critical = sum(1 for s in services.values() if s['status'] == 'CRITICAL')
            failed = sum(1 for s in services.values() if s['status'] == 'FAILED')
            
            print(f"\nServices: {len(services)} total")
            print(f"  Healthy: {healthy}")
            print(f"  Warning: {warning}")
            print(f"  Critical: {critical}")
            print(f"  Failed: {failed}")
            
            # Remediation summary
            if self.last_report.get('remediation_actions'):
                print(f"\nRemediation Actions: {len(self.last_report['remediation_actions'])}")
                for action in self.last_report['remediation_actions']:
                    if action.get('executed'):
                        status = "SUCCESS" if action['success'] else "FAILED"
                        print(f"  - [{status}] {action['message']}")
            
            print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BEDROT Pipeline Scheduled Health Checker"
    )
    
    parser.add_argument(
        '--interval', '-i', 
        type=int, 
        default=30,
        help='Minutes between health checks (default: 30)'
    )
    
    parser.add_argument(
        '--once', '-o',
        action='store_true',
        help='Run once and exit'
    )
    
    parser.add_argument(
        '--no-auto-fix',
        action='store_true',
        help='Disable automatic issue resolution'
    )
    
    parser.add_argument(
        '--daily-summary',
        action='store_true',
        help='Generate daily summary immediately'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(log_level=args.log_level, service_name='health_scheduler')
    
    # Create health checker
    checker = ScheduledHealthChecker(
        check_interval=args.interval,
        enable_auto_fix=not args.no_auto_fix
    )
    
    # Execute based on mode
    if args.daily_summary:
        checker.generate_daily_summary()
    elif args.once:
        checker.run_once()
    else:
        checker.start_scheduler()


if __name__ == "__main__":
    main()