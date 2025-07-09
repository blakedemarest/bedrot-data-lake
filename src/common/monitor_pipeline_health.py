#!/usr/bin/env python3
"""
Monitor data pipeline health, data freshness, and cookie expiration.
Provides comprehensive health checks for the BEDROT data ecosystem.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))
DATA_LAKE_ROOT = PROJECT_ROOT
WAREHOUSE_DB = PROJECT_ROOT.parent / "data-warehouse" / "bedrot_analytics.db"

# Data freshness thresholds (in hours)
FRESHNESS_THRESHOLDS = {
    "critical": 48,    # Data older than 48 hours is critical
    "warning": 24,     # Data older than 24 hours is a warning
    "healthy": 12      # Data updated within 12 hours is healthy
}

# Cookie expiration warning (in days)
COOKIE_WARNING_DAYS = 7


class PipelineMonitor:
    def __init__(self):
        self.zones = ["landing", "raw", "staging", "curated"]
        self.services = ["spotify", "tiktok", "toolost", "distrokid", "metaads", "linktree", "youtube", "mailchimp"]
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "data_freshness": {},
            "cookie_status": {},
            "pipeline_health": {},
            "issues": []
        }
    
    def check_data_freshness(self) -> Dict[str, Dict[str, any]]:
        """Check data freshness for each service across all zones."""
        freshness_report = {}
        
        for service in self.services:
            service_report = {}
            
            for zone in self.zones:
                zone_path = DATA_LAKE_ROOT / zone
                
                # Special handling for TooLost - check both locations
                if service == "toolost" and zone == "raw":
                    files = []
                    # Check raw/toolost/streams/
                    streams_path = zone_path / "toolost" / "streams"
                    if streams_path.exists():
                        files.extend(list(streams_path.glob("toolost_*.json")))
                    # Check raw/toolost/
                    toolost_path = zone_path / "toolost"
                    if toolost_path.exists():
                        files.extend([f for f in toolost_path.glob("toolost_*.json") if f.is_file()])
                else:
                    service_path = zone_path / service
                    if not service_path.exists():
                        continue
                    
                    # Get all files for this service
                    files = list(service_path.rglob("*"))
                    files = [f for f in files if f.is_file() and not f.name.startswith('.')]
                
                if not files:
                    continue
                
                # Find most recent file
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                file_age = datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)
                hours_old = file_age.total_seconds() / 3600
                
                status = "healthy"
                if hours_old > FRESHNESS_THRESHOLDS["critical"]:
                    status = "critical"
                elif hours_old > FRESHNESS_THRESHOLDS["warning"]:
                    status = "warning"
                
                service_report[zone] = {
                    "latest_file": latest_file.name,
                    "last_updated": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                    "hours_old": round(hours_old, 2),
                    "status": status,
                    "path": str(latest_file.relative_to(PROJECT_ROOT))
                }
                
                if status in ["critical", "warning"]:
                    self.report["issues"].append({
                        "type": "data_freshness",
                        "severity": status,
                        "service": service,
                        "zone": zone,
                        "message": f"{service}/{zone} data is {hours_old:.1f} hours old"
                    })
            
            if service_report:
                freshness_report[service] = service_report
        
        self.report["data_freshness"] = freshness_report
        return freshness_report
    
    def check_cookie_status(self) -> Dict[str, any]:
        """Check cookie status and expiration for services that require authentication."""
        cookie_report = {}
        cookie_dir = DATA_LAKE_ROOT / "src" / "common" / "cookies"
        
        authenticated_services = ["spotify", "toolost", "distrokid", "tiktok"]
        
        for service in authenticated_services:
            cookie_file = cookie_dir / f"{service}_cookies.json"
            
            if not cookie_file.exists():
                cookie_report[service] = {
                    "status": "missing",
                    "message": "Cookie file not found",
                    "action_required": True
                }
                self.report["issues"].append({
                    "type": "cookie_missing",
                    "severity": "critical",
                    "service": service,
                    "message": f"Cookie file missing for {service}"
                })
                continue
            
            try:
                with open(cookie_file) as f:
                    cookies = json.load(f)
                
                # Check cookie age
                file_age = datetime.now() - datetime.fromtimestamp(cookie_file.stat().st_mtime)
                days_old = file_age.days
                
                # Check for expiration dates in cookies
                min_expiry = None
                for cookie in cookies:
                    if "expires" in cookie and cookie["expires"] > 0:
                        expiry = datetime.fromtimestamp(cookie["expires"])
                        if min_expiry is None or expiry < min_expiry:
                            min_expiry = expiry
                
                status = "healthy"
                action_required = False
                
                if min_expiry and min_expiry < datetime.now():
                    status = "expired"
                    action_required = True
                elif days_old > COOKIE_WARNING_DAYS:
                    status = "warning"
                    action_required = True
                
                cookie_report[service] = {
                    "status": status,
                    "file_age_days": days_old,
                    "earliest_expiry": min_expiry.isoformat() if min_expiry else None,
                    "action_required": action_required,
                    "last_updated": datetime.fromtimestamp(cookie_file.stat().st_mtime).isoformat()
                }
                
                if action_required:
                    self.report["issues"].append({
                        "type": "cookie_expiration",
                        "severity": "warning" if status == "warning" else "critical",
                        "service": service,
                        "message": f"Cookies for {service} are {days_old} days old or expired"
                    })
                    
            except Exception as e:
                cookie_report[service] = {
                    "status": "error",
                    "message": str(e),
                    "action_required": True
                }
        
        self.report["cookie_status"] = cookie_report
        return cookie_report
    
    def check_pipeline_errors(self) -> Dict[str, any]:
        """Check for recent pipeline errors in logs."""
        error_report = {}
        log_dir = DATA_LAKE_ROOT / "logs"
        
        if log_dir.exists():
            # Get logs from last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_logs = [f for f in log_dir.glob("*.log") 
                          if f.stat().st_mtime > cutoff_time.timestamp()]
            
            for log_file in recent_logs:
                errors = []
                warnings = []
                
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if "ERROR" in line:
                                errors.append(line.strip())
                            elif "WARNING" in line:
                                warnings.append(line.strip())
                
                    if errors or warnings:
                        error_report[log_file.name] = {
                            "error_count": len(errors),
                            "warning_count": len(warnings),
                            "sample_errors": errors[:3],  # First 3 errors
                            "sample_warnings": warnings[:3]  # First 3 warnings
                        }
                        
                except Exception as e:
                    error_report[log_file.name] = {"error": str(e)}
        
        self.report["pipeline_errors"] = error_report
        return error_report
    
    def check_toolost_specific_issues(self) -> Dict[str, any]:
        """Check for TooLost-specific issues like directory mismatches."""
        toolost_report = {
            "directory_mismatch": False,
            "files_in_streams": 0,
            "files_in_root": 0,
            "recommendation": None
        }
        
        # Check both locations
        streams_path = DATA_LAKE_ROOT / "raw" / "toolost" / "streams"
        root_path = DATA_LAKE_ROOT / "raw" / "toolost"
        
        if streams_path.exists():
            stream_files = list(streams_path.glob("toolost_*.json"))
            toolost_report["files_in_streams"] = len(stream_files)
        
        if root_path.exists():
            root_files = [f for f in root_path.glob("toolost_*.json") if f.is_file()]
            toolost_report["files_in_root"] = len(root_files)
        
        if toolost_report["files_in_streams"] > 0 and toolost_report["files_in_root"] > 0:
            toolost_report["directory_mismatch"] = True
            toolost_report["recommendation"] = "Consolidate TooLost files to one location"
            self.report["issues"].append({
                "type": "directory_mismatch",
                "severity": "warning",
                "service": "toolost",
                "message": "TooLost files found in both /raw/toolost/ and /raw/toolost/streams/"
            })
        
        self.report["toolost_specific"] = toolost_report
        return toolost_report
    
    def generate_report(self) -> str:
        """Generate a comprehensive health report."""
        # Run all checks
        self.check_data_freshness()
        self.check_cookie_status()
        self.check_pipeline_errors()
        self.check_toolost_specific_issues()
        
        # Generate report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("BEDROT DATA PIPELINE HEALTH REPORT")
        report_lines.append(f"Generated: {self.report['timestamp']}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary
        critical_count = len([i for i in self.report["issues"] if i["severity"] == "critical"])
        warning_count = len([i for i in self.report["issues"] if i["severity"] == "warning"])
        
        if critical_count == 0 and warning_count == 0:
            report_lines.append("✅ PIPELINE STATUS: HEALTHY")
        elif critical_count > 0:
            report_lines.append("❌ PIPELINE STATUS: CRITICAL ISSUES DETECTED")
        else:
            report_lines.append("⚠️  PIPELINE STATUS: WARNINGS DETECTED")
        
        report_lines.append(f"\nCritical Issues: {critical_count}")
        report_lines.append(f"Warnings: {warning_count}")
        report_lines.append("")
        
        # Data Freshness Table
        report_lines.append("\n📊 DATA FRESHNESS BY SERVICE")
        report_lines.append("-" * 80)
        
        freshness_data = []
        for service, zones in self.report["data_freshness"].items():
            for zone, info in zones.items():
                status_icon = "✅" if info["status"] == "healthy" else "⚠️" if info["status"] == "warning" else "❌"
                freshness_data.append([
                    service,
                    zone,
                    f"{info['hours_old']:.1f}h",
                    f"{status_icon} {info['status']}",
                    info["latest_file"][:40] + "..." if len(info["latest_file"]) > 40 else info["latest_file"]
                ])
        
        if freshness_data:
            report_lines.append(tabulate(freshness_data, 
                                       headers=["Service", "Zone", "Age", "Status", "Latest File"],
                                       tablefmt="grid"))
        
        # Cookie Status
        report_lines.append("\n\n🍪 COOKIE STATUS")
        report_lines.append("-" * 80)
        
        cookie_data = []
        for service, info in self.report["cookie_status"].items():
            status_icon = "✅" if info["status"] == "healthy" else "⚠️" if info["status"] == "warning" else "❌"
            age = f"{info.get('file_age_days', 'N/A')}d" if info.get('file_age_days') is not None else "N/A"
            cookie_data.append([
                service,
                f"{status_icon} {info['status']}",
                age,
                "Yes" if info.get("action_required") else "No"
            ])
        
        if cookie_data:
            report_lines.append(tabulate(cookie_data,
                                       headers=["Service", "Status", "Age", "Action Required"],
                                       tablefmt="grid"))
        
        # TooLost Specific Issues
        if self.report.get("toolost_specific", {}).get("directory_mismatch"):
            report_lines.append("\n\n🔧 TOOLOST SPECIFIC ISSUES")
            report_lines.append("-" * 80)
            report_lines.append(f"Files in /raw/toolost/streams/: {self.report['toolost_specific']['files_in_streams']}")
            report_lines.append(f"Files in /raw/toolost/: {self.report['toolost_specific']['files_in_root']}")
            report_lines.append(f"Recommendation: {self.report['toolost_specific']['recommendation']}")
        
        # Action Items
        if self.report["issues"]:
            report_lines.append("\n\n⚡ REQUIRED ACTIONS")
            report_lines.append("-" * 80)
            
            # Group by severity
            critical_issues = [i for i in self.report["issues"] if i["severity"] == "critical"]
            warning_issues = [i for i in self.report["issues"] if i["severity"] == "warning"]
            
            if critical_issues:
                report_lines.append("\nCRITICAL:")
                for issue in critical_issues:
                    report_lines.append(f"  • [{issue['service']}] {issue['message']}")
            
            if warning_issues:
                report_lines.append("\nWARNINGS:")
                for issue in warning_issues:
                    report_lines.append(f"  • [{issue['service']}] {issue['message']}")
        
        # Recommendations
        report_lines.append("\n\n💡 RECOMMENDATIONS")
        report_lines.append("-" * 80)
        
        # Check for services needing cookie refresh
        services_needing_cookies = [s for s, info in self.report["cookie_status"].items() 
                                   if info.get("action_required")]
        
        if services_needing_cookies:
            report_lines.append("\n1. Refresh cookies for the following services:")
            for service in services_needing_cookies:
                if service == "toolost":
                    report_lines.append(f"   python src/toolost/extractors/toolost_scraper.py")
                else:
                    report_lines.append(f"   python src/{service}/extractors/{service}_login.py")
        
        # Check for stale data
        stale_services = []
        for service, zones in self.report["data_freshness"].items():
            for zone, info in zones.items():
                if info["status"] in ["critical", "warning"]:
                    stale_services.append(service)
                    break
        
        if stale_services:
            report_lines.append("\n2. Run extractors for services with stale data:")
            report_lines.append("   cd data_lake")
            report_lines.append("   cronjob/run_datalake_cron.bat")
        
        if self.report.get("toolost_specific", {}).get("directory_mismatch"):
            report_lines.append("\n3. Fix TooLost directory mismatch:")
            report_lines.append("   - Update toolost_raw2staging.py to check both locations")
            report_lines.append("   - Consolidate future extractions to one directory")
        
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report(self, output_path: Optional[Path] = None):
        """Save the report to a file."""
        if output_path is None:
            output_path = DATA_LAKE_ROOT / "logs" / f"pipeline_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(self.generate_report())
        
        # Also save JSON version
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print(f"Report saved to: {output_path}")
        print(f"JSON report saved to: {json_path}")


def main():
    """Run the pipeline monitor and display results."""
    monitor = PipelineMonitor()
    report = monitor.generate_report()
    
    print(report)
    
    # Save report
    monitor.save_report()
    
    # Exit with appropriate code
    critical_count = len([i for i in monitor.report["issues"] if i["severity"] == "critical"])
    if critical_count > 0:
        sys.exit(1)  # Exit with error if critical issues
    else:
        sys.exit(0)  # Exit successfully


if __name__ == "__main__":
    main()