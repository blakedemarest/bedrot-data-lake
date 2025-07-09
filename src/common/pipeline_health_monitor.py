#!/usr/bin/env python3
"""
Pipeline Health Monitoring and Active Management Tool

Transforms pipeline monitoring from passive reporting to active management:
- Automated cookie refresh triggers
- Real-time data freshness monitoring
- Intelligent bottleneck resolution
- Actionable remediation with auto-fixes
- HTML/JSON report generation
- Integration with notification system
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from enum import Enum
import time

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our cookie refresh system
sys.path.append(str(Path(__file__).parent.parent))
try:
    from cookie_refresh.refresher import CookieRefresher
    from cookie_refresh.notifier import CookieRefreshNotifier, NotificationLevel
    from cookie_refresh.config_loader import load_config
    COOKIE_REFRESH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Cookie refresh system not available: {e}")
    COOKIE_REFRESH_AVAILABLE = False
    # Define dummy classes to prevent errors
    class CookieRefresher:
        pass
    class CookieRefreshNotifier:
        pass
    class NotificationLevel:
        pass
    def load_config():
        return {}

PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    print("ERROR: PROJECT_ROOT environment variable must be set.")
    sys.exit(1)

PROJECT_ROOT = Path(PROJECT_ROOT)


class HealthStatus(Enum):
    """Health status levels for services and pipeline components."""
    HEALTHY = "HEALTHY"        # Everything is working perfectly
    WARNING = "WARNING"        # Minor issues, monitoring needed
    CRITICAL = "CRITICAL"      # Major issues, immediate action needed
    FAILED = "FAILED"          # Service is down or completely broken
    

class ServicePriority(Enum):
    """Service priority levels for determining remediation urgency."""
    CRITICAL = 1    # TooLost - requires weekly refresh
    HIGH = 2        # Spotify, TikTok - core revenue streams
    MEDIUM = 3      # DistroKid, Linktree - important but less frequent
    LOW = 4         # MetaAds - nice to have


class PipelineHealthMonitor:
    """Active pipeline health management system."""
    
    def __init__(self, enable_auto_remediation: bool = True, enable_notifications: bool = True):
        self.project_root = PROJECT_ROOT
        self.zones = ['landing', 'raw', 'staging', 'curated']
        self.services = ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree', 'metaads']
        self.health_report = {}
        self.enable_auto_remediation = enable_auto_remediation
        self.enable_notifications = enable_notifications
        
        # Service priority mapping for weighted scoring
        self.service_priority = {
            'toolost': ServicePriority.CRITICAL,
            'spotify': ServicePriority.HIGH,
            'tiktok': ServicePriority.HIGH,
            'distrokid': ServicePriority.MEDIUM,
            'linktree': ServicePriority.MEDIUM,
            'metaads': ServicePriority.LOW
        }
        
        # Initialize cookie refresh manager if auto-remediation is enabled
        if self.enable_auto_remediation and COOKIE_REFRESH_AVAILABLE:
            try:
                config = load_config()
                self.cookie_manager = CookieRefresher(config)
                self.notifier = CookieRefreshNotifier(config.get('notifications', {})) if self.enable_notifications else None
                logger.info("Cookie refresh manager initialized for auto-remediation")
            except Exception as e:
                logger.warning(f"Could not initialize cookie refresh manager: {e}")
                self.cookie_manager = None
                self.notifier = None
        else:
            if self.enable_auto_remediation and not COOKIE_REFRESH_AVAILABLE:
                logger.warning("Auto-remediation requested but cookie refresh system not available")
            self.cookie_manager = None
            self.notifier = None
            
        # Track remediation actions taken
        self.remediation_log = []
        
    def check_zone_freshness(self, service: str) -> Dict[str, Dict]:
        """Check data freshness in each zone for a service."""
        freshness = {}
        
        for zone in self.zones:
            zone_path = self.project_root / zone / service
            if not zone_path.exists():
                freshness[zone] = {
                    'exists': False,
                    'latest_file': None,
                    'latest_date': None,
                    'days_old': None
                }
                continue
                
            # Find most recent file
            all_files = []
            for ext in ['*.json', '*.csv', '*.ndjson', '*.parquet', '*.tsv', '*.html']:
                all_files.extend(zone_path.glob(ext))
            
            # Also check subdirectories (like toolost/streams)
            for subdir in zone_path.iterdir():
                if subdir.is_dir():
                    for ext in ['*.json', '*.csv', '*.ndjson', '*.parquet', '*.tsv']:
                        all_files.extend(subdir.glob(ext))
            
            if not all_files:
                freshness[zone] = {
                    'exists': True,
                    'latest_file': None,
                    'latest_date': None,
                    'days_old': None
                }
                continue
            
            latest_file = max(all_files, key=lambda p: p.stat().st_mtime)
            latest_date = datetime.fromtimestamp(latest_file.stat().st_mtime)
            days_old = (datetime.now() - latest_date).days
            
            freshness[zone] = {
                'exists': True,
                'latest_file': latest_file.name,
                'latest_date': latest_date.strftime('%Y-%m-%d %H:%M:%S'),
                'days_old': days_old,
                'full_path': str(latest_file.relative_to(self.project_root))
            }
            
        return freshness
    
    def check_cookie_health(self, service: str) -> Dict:
        """Check cookie status for a service."""
        cookie_patterns = {
            'spotify': 'src/spotify/cookies/spotify_cookies.json',
            'tiktok': 'src/tiktok/cookies/tiktok_cookies_*.json',
            'distrokid': 'src/distrokid/cookies/distrokid_cookies.json',
            'toolost': 'src/toolost/cookies/toolost_cookies.json',
            'linktree': 'src/linktree/cookies/linktree_cookies.json',
            'metaads': 'src/metaads/cookies/metaads_cookies.json'
        }
        
        pattern = cookie_patterns.get(service)
        if not pattern:
            return {'status': 'no_check', 'message': 'No cookie check configured'}
        
        # Handle wildcard patterns
        if '*' in pattern:
            cookie_dir = self.project_root / Path(pattern).parent
            if cookie_dir.exists():
                cookie_files = list(cookie_dir.glob(Path(pattern).name))
                if cookie_files:
                    # Check all cookie files
                    results = []
                    for cookie_file in cookie_files:
                        account = cookie_file.stem.replace(f'{service}_cookies_', '')
                        result = self._check_single_cookie(cookie_file, service)
                        result['account'] = account
                        results.append(result)
                    return {'status': 'multiple', 'cookies': results}
            return {'status': 'missing', 'message': 'No cookie files found'}
        else:
            cookie_path = self.project_root / pattern
            if cookie_path.exists():
                return self._check_single_cookie(cookie_path, service)
            return {'status': 'missing', 'message': 'Cookie file not found'}
    
    def _check_single_cookie(self, cookie_path: Path, service: str) -> Dict:
        """Check a single cookie file."""
        file_age = datetime.now() - datetime.fromtimestamp(cookie_path.stat().st_mtime)
        
        # Service-specific expiry times
        expiry_days = {
            'spotify': 30,
            'tiktok': 30,
            'distrokid': 30,
            'toolost': 7,
            'linktree': 30,
            'metaads': 90
        }
        
        max_age = expiry_days.get(service, 30)
        is_expired = file_age.days > max_age
        
        return {
            'status': 'expired' if is_expired else 'valid',
            'days_old': file_age.days,
            'max_age': max_age,
            'expires_in': max_age - file_age.days if not is_expired else 0,
            'file': cookie_path.name
        }
    
    def detect_pipeline_bottlenecks(self, service: str, freshness: Dict) -> List[str]:
        """Detect where data flow is blocked in the pipeline."""
        bottlenecks = []
        
        # Check if data exists in landing but not in subsequent zones
        if freshness['landing']['exists'] and freshness['landing']['latest_file']:
            landing_age = freshness['landing']['days_old']
            
            for next_zone in ['raw', 'staging', 'curated']:
                if not freshness[next_zone]['exists'] or not freshness[next_zone]['latest_file']:
                    bottlenecks.append(f"No data in {next_zone} zone")
                elif freshness[next_zone]['days_old'] > landing_age + 1:
                    bottlenecks.append(
                        f"{next_zone} zone is {freshness[next_zone]['days_old'] - landing_age} days behind landing"
                    )
        
        # Special check for TooLost directory issue
        if service == 'toolost':
            # Check both possible locations
            raw_streams = self.project_root / 'raw' / 'toolost' / 'streams'
            raw_direct = self.project_root / 'raw' / 'toolost'
            
            streams_files = list(raw_streams.glob('*.json')) if raw_streams.exists() else []
            direct_files = list(raw_direct.glob('*.json'))
            
            if direct_files and not streams_files:
                bottlenecks.append("TooLost files in raw/ but cleaner expects raw/streams/")
            elif streams_files and direct_files:
                # Check which has newer files
                latest_streams = max(streams_files, key=lambda p: p.stat().st_mtime) if streams_files else None
                latest_direct = max(direct_files, key=lambda p: p.stat().st_mtime) if direct_files else None
                
                if latest_direct and latest_streams:
                    if latest_direct.stat().st_mtime > latest_streams.stat().st_mtime:
                        bottlenecks.append("Newer TooLost files in raw/ not being processed")
        
        return bottlenecks
    
    def get_recommendations(self, service: str, freshness: Dict, cookie_health: Dict, bottlenecks: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Generate actionable recommendations and automatic remediation actions.
        
        Returns:
            recommendations: List of manual action items
            auto_actions: List of actions that can be taken automatically
        """
        recommendations = []
        auto_actions = []
        
        # Cookie recommendations with auto-remediation
        if cookie_health['status'] == 'missing':
            recommendations.append(f"Run manual authentication for {service}")
            auto_actions.append({
                'type': 'cookie_refresh',
                'service': service,
                'reason': 'missing_cookies',
                'priority': 'high'
            })
        elif cookie_health['status'] == 'expired':
            days_expired = cookie_health['days_old'] - cookie_health['max_age']
            recommendations.append(f"Refresh {service} cookies (expired {days_expired} days ago)")
            auto_actions.append({
                'type': 'cookie_refresh',
                'service': service,
                'reason': f'expired_{days_expired}_days_ago',
                'priority': 'critical' if days_expired > 7 else 'high'
            })
        elif cookie_health['status'] == 'valid' and cookie_health.get('expires_in', 0) <= 3:
            recommendations.append(f"Consider refreshing {service} cookies (expires in {cookie_health['expires_in']} days)")
            auto_actions.append({
                'type': 'cookie_refresh',
                'service': service,
                'reason': f'expiring_soon_{cookie_health["expires_in"]}_days',
                'priority': 'medium'
            })
        
        # Data freshness recommendations
        if freshness['landing']['exists'] and freshness['landing']['days_old'] is not None:
            if freshness['landing']['days_old'] > 7:
                recommendations.append(f"⚠️ URGENT: Run {service} extractor (last data: {freshness['landing']['days_old']} days ago)")
                auto_actions.append({
                    'type': 'run_extractor',
                    'service': service,
                    'reason': f'stale_data_{freshness["landing"]["days_old"]}_days',
                    'priority': 'high'
                })
            elif freshness['landing']['days_old'] > 3:
                recommendations.append(f"Run {service} extractor (last data: {freshness['landing']['days_old']} days ago)")
        
        # Bottleneck recommendations with auto-fixes
        if bottlenecks:
            if "TooLost files in raw/ but cleaner expects raw/streams/" in bottlenecks:
                recommendations.append("Update toolost_raw2staging.py to check both directories")
                auto_actions.append({
                    'type': 'fix_directory_mismatch',
                    'service': 'toolost',
                    'reason': 'directory_structure_issue',
                    'priority': 'critical'
                })
            if any("No data in" in b for b in bottlenecks):
                recommendations.append(f"Run cleaners for {service}")
                auto_actions.append({
                    'type': 'run_cleaners',
                    'service': service,
                    'reason': 'pipeline_blocked',
                    'priority': 'medium'
                })
        
        return recommendations, auto_actions
    
    def generate_report(self) -> Dict:
        """Generate comprehensive health report with auto-remediation."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': HealthStatus.HEALTHY,
            'remediation_actions': [],
            'auto_remediation_enabled': self.enable_auto_remediation
        }
        
        all_auto_actions = []
        overall_scores = []
        
        for service in self.services:
            logger.info(f"Checking {service}...")
            
            freshness = self.check_zone_freshness(service)
            cookie_health = self.check_cookie_health(service)
            bottlenecks = self.detect_pipeline_bottlenecks(service, freshness)
            recommendations, auto_actions = self.get_recommendations(service, freshness, cookie_health, bottlenecks)
            
            # Calculate weighted health score based on service priority
            health_score = self._calculate_weighted_health_score(
                service, freshness, cookie_health, bottlenecks
            )
            
            # Determine service status
            if health_score >= 80:
                status = HealthStatus.HEALTHY
            elif health_score >= 60:
                status = HealthStatus.WARNING
            elif health_score >= 30:
                status = HealthStatus.CRITICAL
            else:
                status = HealthStatus.FAILED
            
            overall_scores.append(health_score)
            all_auto_actions.extend(auto_actions)
            
            report['services'][service] = {
                'health_score': health_score,
                'status': status.value,
                'priority': self.service_priority.get(service, ServicePriority.LOW).name,
                'freshness': freshness,
                'cookie_health': cookie_health,
                'bottlenecks': bottlenecks,
                'recommendations': recommendations,
                'auto_actions': auto_actions
            }
        
        # Determine overall pipeline status
        avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        critical_services = [s for s, d in report['services'].items() 
                           if d['status'] in [HealthStatus.CRITICAL.value, HealthStatus.FAILED.value]]
        
        if avg_score >= 80 and not critical_services:
            report['overall_status'] = HealthStatus.HEALTHY.value
        elif avg_score >= 60 or len(critical_services) <= 1:
            report['overall_status'] = HealthStatus.WARNING.value
        elif avg_score >= 30 or len(critical_services) <= 2:
            report['overall_status'] = HealthStatus.CRITICAL.value
        else:
            report['overall_status'] = HealthStatus.FAILED.value
        
        # Execute auto-remediation if enabled
        if self.enable_auto_remediation and all_auto_actions:
            report['remediation_actions'] = self._execute_auto_remediation(all_auto_actions)
        else:
            report['remediation_actions'] = all_auto_actions
        
        return report
    
    def _calculate_weighted_health_score(self, service: str, freshness: Dict, 
                                       cookie_health: Dict, bottlenecks: List[str]) -> int:
        """Calculate health score with priority weighting."""
        base_score = 100
        priority = self.service_priority.get(service, ServicePriority.LOW)
        
        # Priority multipliers for score deductions
        priority_multiplier = {
            ServicePriority.CRITICAL: 1.5,
            ServicePriority.HIGH: 1.2,
            ServicePriority.MEDIUM: 1.0,
            ServicePriority.LOW: 0.8
        }
        
        multiplier = priority_multiplier[priority]
        
        # Data freshness deductions
        if freshness['landing']['days_old'] is not None:
            days_old = freshness['landing']['days_old']
            if days_old > 14:
                base_score -= int(40 * multiplier)
            elif days_old > 7:
                base_score -= int(30 * multiplier)
            elif days_old > 3:
                base_score -= int(15 * multiplier)
            elif days_old > 1:
                base_score -= int(5 * multiplier)
        
        # Cookie health deductions
        if cookie_health['status'] == 'expired':
            base_score -= int(30 * multiplier)
        elif cookie_health['status'] == 'missing':
            base_score -= int(50 * multiplier)
        elif cookie_health['status'] == 'valid' and cookie_health.get('expires_in', 30) <= 3:
            base_score -= int(10 * multiplier)
        
        # Bottleneck deductions
        base_score -= int(len(bottlenecks) * 10 * multiplier)
        
        # Special case for TooLost - extra penalty for being out of date
        if service == 'toolost' and freshness['landing']['days_old'] is not None:
            if freshness['landing']['days_old'] > 7:
                base_score -= 20  # Extra penalty for critical service
        
        return max(0, min(100, base_score))
    
    def _execute_auto_remediation(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute automatic remediation actions."""
        executed_actions = []
        
        # Sort actions by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_actions = sorted(actions, key=lambda x: priority_order.get(x['priority'], 999))
        
        for action in sorted_actions:
            result = {
                'action': action,
                'executed': False,
                'success': False,
                'message': '',
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                if action['type'] == 'cookie_refresh' and self.cookie_manager:
                    # Attempt automatic cookie refresh
                    logger.info(f"Attempting auto cookie refresh for {action['service']}")
                    refresh_result = self.cookie_manager.refresh_service(action['service'])
                    
                    if refresh_result['success']:
                        result['executed'] = True
                        result['success'] = True
                        result['message'] = f"Successfully refreshed cookies for {action['service']}"
                        
                        if self.notifier:
                            self.notifier.notify_refresh_success(
                                action['service'],
                                details={'auto_remediation': True, 'reason': action['reason']}
                            )
                    else:
                        result['executed'] = True
                        result['success'] = False
                        result['message'] = refresh_result.get('error', 'Unknown error')
                        
                        if self.notifier:
                            self.notifier.notify_refresh_failed(
                                action['service'],
                                refresh_result.get('error', 'Unknown error'),
                                details={'auto_remediation': True}
                            )
                            
                elif action['type'] == 'run_cleaners':
                    # Run cleaner scripts
                    logger.info(f"Running cleaners for {action['service']}")
                    success = self._run_cleaners(action['service'])
                    
                    result['executed'] = True
                    result['success'] = success
                    result['message'] = f"{'Successfully ran' if success else 'Failed to run'} cleaners for {action['service']}"
                    
                elif action['type'] == 'fix_directory_mismatch' and action['service'] == 'toolost':
                    # Special handling for TooLost directory issue
                    logger.info("Attempting to fix TooLost directory mismatch")
                    success = self._fix_toolost_directory()
                    
                    result['executed'] = True
                    result['success'] = success
                    result['message'] = "Fixed TooLost directory structure" if success else "Failed to fix directory structure"
                    
                else:
                    result['message'] = f"No handler for action type: {action['type']}"
                    
            except Exception as e:
                logger.error(f"Error executing remediation action: {e}")
                result['executed'] = True
                result['success'] = False
                result['message'] = str(e)
            
            executed_actions.append(result)
            self.remediation_log.append(result)
        
        return executed_actions
    
    def _run_cleaners(self, service: str) -> bool:
        """Run cleaner scripts for a service."""
        cleaners_dir = self.project_root / 'src' / service / 'cleaners'
        if not cleaners_dir.exists():
            return False
        
        cleaner_order = [
            f'{service}_landing2raw.py',
            f'{service}_raw2staging.py',
            f'{service}_staging2curated.py'
        ]
        
        success = True
        for cleaner in cleaner_order:
            cleaner_path = cleaners_dir / cleaner
            if cleaner_path.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, str(cleaner_path)],
                        capture_output=True,
                        text=True,
                        cwd=str(self.project_root)
                    )
                    if result.returncode != 0:
                        logger.error(f"Cleaner {cleaner} failed: {result.stderr}")
                        success = False
                        break
                except Exception as e:
                    logger.error(f"Error running cleaner {cleaner}: {e}")
                    success = False
                    break
        
        return success
    
    def _fix_toolost_directory(self) -> bool:
        """Fix TooLost directory structure issue."""
        try:
            raw_dir = self.project_root / 'raw' / 'toolost'
            raw_streams_dir = raw_dir / 'streams'
            
            # Create streams directory if it doesn't exist
            raw_streams_dir.mkdir(parents=True, exist_ok=True)
            
            # Move JSON files from raw/ to raw/streams/
            moved_count = 0
            for json_file in raw_dir.glob('*.json'):
                if json_file.is_file():
                    target = raw_streams_dir / json_file.name
                    json_file.rename(target)
                    moved_count += 1
            
            logger.info(f"Moved {moved_count} files to raw/toolost/streams/")
            return True
            
        except Exception as e:
            logger.error(f"Error fixing TooLost directory: {e}")
            return False
    
    def print_report(self, report: Dict):
        """Print formatted health report with enhanced visual indicators."""
        # Use simple ASCII indicators for better compatibility
        status_indicators = {
            HealthStatus.HEALTHY.value: "[OK]",
            HealthStatus.WARNING.value: "[!!]",
            HealthStatus.CRITICAL.value: "[XX]", 
            HealthStatus.FAILED.value: "[FAIL]"
        }
        
        print("\n" + "="*80)
        print("BEDROT DATA PIPELINE HEALTH REPORT - ACTIVE MANAGEMENT SYSTEM")
        print(f"Generated: {datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Overall Status: {status_indicators.get(report['overall_status'], '[??]')} {report['overall_status']}")
        print(f"Auto-Remediation: {'ENABLED' if report['auto_remediation_enabled'] else 'DISABLED'}")
        print("="*80)
        
        # Priority services first
        print("\nSERVICE HEALTH SUMMARY (Sorted by Priority)")
        print("-"*80)
        print(f"{'Service':12} {'Status':8} {'Score':6} {'Priority':10} {'Issues':30}")
        print("-"*80)
        
        # Sort services by priority and health score
        sorted_services = sorted(
            report['services'].items(),
            key=lambda x: (self.service_priority.get(x[0], ServicePriority.LOW).value, -x[1]['health_score'])
        )
        
        for service, data in sorted_services:
            score = data['health_score']
            status = data['status']
            priority = data['priority']
            
            # Build issues string
            issues = []
            if data['cookie_health']['status'] == 'expired':
                issues.append("COOKIES EXPIRED")
            elif data['cookie_health']['status'] == 'missing':
                issues.append("NO COOKIES")
            
            if data['freshness']['landing']['days_old'] is not None:
                days = data['freshness']['landing']['days_old']
                if days > 7:
                    issues.append(f"{days}d STALE")
                elif days > 3:
                    issues.append(f"{days}d old")
            
            if data['bottlenecks']:
                issues.append(f"{len(data['bottlenecks'])} blocks")
            
            issues_str = ", ".join(issues) if issues else "No issues"
            
            print(f"{service:12} {status_indicators.get(status, '[??]'):8} {score:3}%   {priority:10} {issues_str:30}")
        
        # Remediation actions taken
        if report.get('remediation_actions'):
            print("\nAUTO-REMEDIATION ACTIONS")
            print("-"*80)
            
            for action in report['remediation_actions']:
                if isinstance(action, dict) and action.get('executed'):
                    status = "SUCCESS" if action['success'] else "FAILED"
                    print(f"  [{status}] {action['message']}")
                elif isinstance(action, dict) and 'type' in action:
                    # This is a raw action that wasn't executed
                    print(f"  [PENDING] {action['type']} for {action['service']}")
        
        # Detailed issues for critical/failed services
        critical_services = [(s, d) for s, d in report['services'].items() 
                           if d['status'] in [HealthStatus.CRITICAL.value, HealthStatus.FAILED.value]]
        
        if critical_services:
            print("\nCRITICAL SERVICE DETAILS")
            print("-"*80)
            
            for service, data in critical_services:
                print(f"\n{service.upper()} [{data['priority']} PRIORITY]:")
                
                # Cookie status
                cookie_status = data['cookie_health']['status']
                if cookie_status in ['expired', 'missing']:
                    print(f"  - Cookies: {cookie_status.upper()}")
                    if cookie_status == 'expired':
                        days_expired = data['cookie_health']['days_old'] - data['cookie_health']['max_age']
                        print(f"    Expired: {days_expired} days ago")
                        print(f"    Action: Immediate refresh required")
                    elif data['cookie_health'].get('expires_in', 999) <= 3:
                        print(f"    Warning: Expires in {data['cookie_health']['expires_in']} days")
                
                # Data freshness
                if data['freshness']['landing']['days_old'] is not None:
                    days_old = data['freshness']['landing']['days_old']
                    if days_old > 3:
                        print(f"  - Data Age: {days_old} days old")
                        print(f"    Latest: {data['freshness']['landing']['latest_file']}")
                        print(f"    Action: Run extractor immediately")
                
                # Bottlenecks
                if data['bottlenecks']:
                    print("  - Pipeline Bottlenecks:")
                    for bottleneck in data['bottlenecks']:
                        print(f"    • {bottleneck}")
        
        # Manual action items
        print("\nMANUAL ACTION ITEMS (Sorted by Priority)")
        print("-"*80)
        
        # Group recommendations by urgency
        urgent_recs = []
        normal_recs = []
        
        for service, data in report['services'].items():
            for rec in data['recommendations']:
                full_rec = f"[{service}] {rec}"
                if 'URGENT' in rec or data['status'] in [HealthStatus.CRITICAL.value, HealthStatus.FAILED.value]:
                    urgent_recs.append(full_rec)
                else:
                    normal_recs.append(full_rec)
        
        if urgent_recs:
            print("\nURGENT:")
            for rec in urgent_recs:
                print(f"  !!! {rec}")
        
        if normal_recs:
            print("\nRECOMMENDED:")
            for rec in normal_recs:
                print(f"  • {rec}")
        
        # Save reports in multiple formats
        self._save_reports(report)
        
        # Print summary footer
        print("\n" + "="*80)
        healthy_count = sum(1 for s in report['services'].values() if s['status'] == HealthStatus.HEALTHY.value)
        total_count = len(report['services'])
        print(f"Summary: {healthy_count}/{total_count} services healthy")
        
        if report['overall_status'] in [HealthStatus.CRITICAL.value, HealthStatus.FAILED.value]:
            print("\n!!! IMMEDIATE ACTION REQUIRED !!!")
            print("Run manual authentication for failed services or enable auto-remediation")
    
    def _save_reports(self, report: Dict):
        """Save reports in multiple formats."""
        # JSON report
        json_file = self.project_root / 'pipeline_health_report.json'
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReports saved:")
        print(f"  - JSON: {json_file}")
        
        # HTML report
        html_file = self.project_root / 'pipeline_health_report.html'
        self._generate_html_report(report, html_file)
        print(f"  - HTML: {html_file}")
    
    def _generate_html_report(self, report: Dict, output_path: Path):
        """Generate an HTML report with visual dashboard."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>BEDROT Pipeline Health Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; }}
        .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; color: white; }}
        .status-healthy {{ background: #28a745; }}
        .status-warning {{ background: #ffc107; color: #333; }}
        .status-critical {{ background: #dc3545; }}
        .status-failed {{ background: #6c757d; }}
        .service-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .service-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; }}
        .service-card.critical {{ border-color: #dc3545; background: #f8d7da; }}
        .service-card.warning {{ border-color: #ffc107; background: #fff3cd; }}
        .service-card.healthy {{ border-color: #28a745; background: #d4edda; }}
        .metric {{ margin: 10px 0; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .action-item {{ margin: 5px 0; padding: 8px; background: #e9ecef; border-radius: 4px; }}
        .urgent {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>BEDROT Pipeline Health Report</h1>
        <p class="timestamp">Generated: {datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div style="margin: 20px 0; padding: 15px; background: #{'#d4edda' if report['overall_status'] == 'HEALTHY' else '#f8d7da' if report['overall_status'] in ['CRITICAL', 'FAILED'] else '#fff3cd'}; border-radius: 8px;">
            <h2 style="margin: 0;">Overall Status: <span class="status-badge status-{report['overall_status'].lower()}">{report['overall_status']}</span></h2>
            <p style="margin: 10px 0 0 0;">Auto-Remediation: <strong>{'Enabled' if report['auto_remediation_enabled'] else 'Disabled'}</strong></p>
        </div>
        
        <h2>Service Health Overview</h2>
        <div class="service-grid">
"""
        
        # Add service cards
        for service, data in report['services'].items():
            status_class = data['status'].lower()
            html_content += f"""
            <div class="service-card {status_class}">
                <h3>{service.upper()} <span class="status-badge status-{status_class}">{data['health_score']}%</span></h3>
                <div class="metric">
                    <span class="metric-label">Priority:</span> {data['priority']}
                </div>
                <div class="metric">
                    <span class="metric-label">Cookie Status:</span> {data['cookie_health']['status']}
                    {f" (expires in {data['cookie_health'].get('expires_in', 'N/A')} days)" if data['cookie_health']['status'] == 'valid' else ''}
                </div>
                <div class="metric">
                    <span class="metric-label">Data Age:</span> 
                    {f"{data['freshness']['landing']['days_old']} days" if data['freshness']['landing']['days_old'] is not None else 'No data'}
                </div>
                {f'<div class="metric"><span class="metric-label">Bottlenecks:</span> {len(data["bottlenecks"])}</div>' if data['bottlenecks'] else ''}
            </div>
"""
        
        # Add action items
        urgent_actions = []
        normal_actions = []
        
        for service, data in report['services'].items():
            for rec in data['recommendations']:
                if 'URGENT' in rec or data['status'] in ['CRITICAL', 'FAILED']:
                    urgent_actions.append((service, rec))
                else:
                    normal_actions.append((service, rec))
        
        html_content += """
        </div>
        
        <h2>Action Items</h2>
"""
        
        if urgent_actions:
            html_content += "<h3>Urgent Actions Required</h3>"
            for service, action in urgent_actions:
                html_content += f'<div class="action-item urgent"><strong>[{service}]</strong> {action}</div>'
        
        if normal_actions:
            html_content += "<h3>Recommended Actions</h3>"
            for service, action in normal_actions:
                html_content += f'<div class="action-item"><strong>[{service}]</strong> {action}</div>'
        
        # Add remediation log if present
        if report.get('remediation_actions'):
            html_content += """
        <h2>Auto-Remediation Log</h2>
        <table>
            <tr>
                <th>Service</th>
                <th>Action</th>
                <th>Status</th>
                <th>Message</th>
            </tr>
"""
            for action in report['remediation_actions']:
                if action.get('executed'):
                    status = 'Success' if action['success'] else 'Failed'
                    html_content += f"""
            <tr>
                <td>{action['action']['service']}</td>
                <td>{action['action']['type']}</td>
                <td><span class="status-badge status-{'healthy' if action['success'] else 'critical'}">{status}</span></td>
                <td>{action['message']}</td>
            </tr>
"""
            
            html_content += "</table>"
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BEDROT Pipeline Health Monitor - Active Management System")
    parser.add_argument('--auto-remediate', '-a', action='store_true', 
                       help='Enable automatic remediation of issues')
    parser.add_argument('--no-notifications', '-n', action='store_true',
                       help='Disable notifications')
    parser.add_argument('--json-only', '-j', action='store_true',
                       help='Output JSON report only, no console output')
    parser.add_argument('--service', '-s', help='Check specific service only')
    parser.add_argument('--fix-issues', '-f', action='store_true',
                       help='Automatically fix all detected issues (implies --auto-remediate)')
    
    args = parser.parse_args()
    
    # Create monitor instance
    enable_auto = args.auto_remediate or args.fix_issues
    enable_notif = not args.no_notifications
    
    monitor = PipelineHealthMonitor(
        enable_auto_remediation=enable_auto,
        enable_notifications=enable_notif
    )
    
    # Filter services if specified
    if args.service:
        if args.service not in monitor.services:
            print(f"Error: Unknown service '{args.service}'")
            print(f"Valid services: {', '.join(monitor.services)}")
            return 1
        monitor.services = [args.service]
    
    # Generate report
    report = monitor.generate_report()
    
    # Output based on options
    if args.json_only:
        print(json.dumps(report, indent=2))
    else:
        monitor.print_report(report)
    
    # Determine exit code based on overall status
    exit_codes = {
        HealthStatus.HEALTHY.value: 0,
        HealthStatus.WARNING.value: 0,  # Warnings don't fail the pipeline
        HealthStatus.CRITICAL.value: 1,
        HealthStatus.FAILED.value: 2
    }
    
    return exit_codes.get(report['overall_status'], 1)


if __name__ == "__main__":
    sys.exit(main())