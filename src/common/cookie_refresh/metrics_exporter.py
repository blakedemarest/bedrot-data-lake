"""
Grafana-compatible metrics exporter for cookie refresh system
Exports metrics in Prometheus format for monitoring dashboards
"""

import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from flask import Flask, Response
import logging

logger = logging.getLogger('cookie_refresh.metrics')


class MetricsExporter:
    """Exports cookie refresh metrics in Prometheus format"""
    
    def __init__(self, db_path: str = "data/metrics.db", port: int = 9090):
        self.db_path = db_path
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()
        self.init_database()
        
    def init_database(self):
        """Initialize metrics database if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refresh_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                service TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                duration_seconds REAL,
                error_message TEXT,
                cookie_age_days REAL,
                strategy TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_status (
                service TEXT PRIMARY KEY,
                last_refresh DATETIME,
                last_success DATETIME,
                consecutive_failures INTEGER DEFAULT 0,
                total_refreshes INTEGER DEFAULT 0,
                total_failures INTEGER DEFAULT 0,
                avg_duration_seconds REAL,
                cookie_expiry DATETIME
            )
        """)
        
        conn.commit()
        conn.close()
        
    def setup_routes(self):
        """Set up Flask routes for metrics endpoints"""
        
        @self.app.route('/metrics')
        def metrics():
            """Prometheus metrics endpoint"""
            metrics_text = self.generate_prometheus_metrics()
            return Response(metrics_text, mimetype='text/plain')
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
        
        @self.app.route('/api/metrics/<service>')
        def service_metrics(service):
            """Service-specific metrics in JSON"""
            metrics = self.get_service_metrics(service)
            return metrics
        
    def generate_prometheus_metrics(self) -> str:
        """Generate metrics in Prometheus format"""
        lines = []
        
        # Add header
        lines.append("# HELP cookie_refresh_total Total cookie refresh attempts")
        lines.append("# TYPE cookie_refresh_total counter")
        
        # Get metrics from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total refreshes per service
        cursor.execute("""
            SELECT service, COUNT(*) as total, 
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM refresh_metrics
            GROUP BY service
        """)
        
        for service, total, successful in cursor.fetchall():
            lines.append(f'cookie_refresh_total{{service="{service}",status="all"}} {total}')
            lines.append(f'cookie_refresh_total{{service="{service}",status="success"}} {successful}')
            lines.append(f'cookie_refresh_total{{service="{service}",status="failure"}} {total - successful}')
        
        # Success rate
        lines.append("\n# HELP cookie_refresh_success_rate Success rate of cookie refreshes")
        lines.append("# TYPE cookie_refresh_success_rate gauge")
        
        cursor.execute("""
            SELECT service, 
                   CAST(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as rate
            FROM refresh_metrics
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY service
        """)
        
        for service, rate in cursor.fetchall():
            lines.append(f'cookie_refresh_success_rate{{service="{service}"}} {rate:.3f}')
        
        # Average duration
        lines.append("\n# HELP cookie_refresh_duration_seconds Average refresh duration")
        lines.append("# TYPE cookie_refresh_duration_seconds gauge")
        
        cursor.execute("""
            SELECT service, AVG(duration_seconds) as avg_duration
            FROM refresh_metrics
            WHERE success = 1 AND timestamp > datetime('now', '-7 days')
            GROUP BY service
        """)
        
        for service, avg_duration in cursor.fetchall():
            if avg_duration:
                lines.append(f'cookie_refresh_duration_seconds{{service="{service}"}} {avg_duration:.3f}')
        
        # Cookie age
        lines.append("\n# HELP cookie_age_days Current age of cookies in days")
        lines.append("# TYPE cookie_age_days gauge")
        
        cursor.execute("""
            SELECT service, cookie_age_days
            FROM (
                SELECT service, cookie_age_days,
                       ROW_NUMBER() OVER (PARTITION BY service ORDER BY timestamp DESC) as rn
                FROM refresh_metrics
                WHERE cookie_age_days IS NOT NULL
            )
            WHERE rn = 1
        """)
        
        for service, age_days in cursor.fetchall():
            lines.append(f'cookie_age_days{{service="{service}"}} {age_days:.1f}')
        
        # Consecutive failures
        lines.append("\n# HELP cookie_refresh_consecutive_failures Consecutive failure count")
        lines.append("# TYPE cookie_refresh_consecutive_failures gauge")
        
        cursor.execute("SELECT service, consecutive_failures FROM service_status")
        
        for service, failures in cursor.fetchall():
            lines.append(f'cookie_refresh_consecutive_failures{{service="{service}"}} {failures}')
        
        # Time since last success
        lines.append("\n# HELP cookie_refresh_last_success_hours Hours since last successful refresh")
        lines.append("# TYPE cookie_refresh_last_success_hours gauge")
        
        cursor.execute("""
            SELECT service, 
                   (julianday('now') - julianday(last_success)) * 24 as hours_ago
            FROM service_status
            WHERE last_success IS NOT NULL
        """)
        
        for service, hours_ago in cursor.fetchall():
            lines.append(f'cookie_refresh_last_success_hours{{service="{service}"}} {hours_ago:.1f}')
        
        conn.close()
        
        return '\n'.join(lines) + '\n'
    
    def get_service_metrics(self, service: str) -> Dict:
        """Get detailed metrics for a specific service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get service status
        cursor.execute("""
            SELECT * FROM service_status WHERE service = ?
        """, (service,))
        
        status_row = cursor.fetchone()
        if not status_row:
            return {'error': 'Service not found'}
        
        # Convert to dict
        columns = [desc[0] for desc in cursor.description]
        status = dict(zip(columns, status_row))
        
        # Get recent refresh history
        cursor.execute("""
            SELECT timestamp, success, duration_seconds, error_message, cookie_age_days
            FROM refresh_metrics
            WHERE service = ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (service,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'timestamp': row[0],
                'success': bool(row[1]),
                'duration_seconds': row[2],
                'error_message': row[3],
                'cookie_age_days': row[4]
            })
        
        # Get success rate over time
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM refresh_metrics
            WHERE service = ? AND timestamp > datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (service,))
        
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row[0],
                'total': row[1],
                'successful': row[2],
                'success_rate': row[2] / row[1] if row[1] > 0 else 0
            })
        
        conn.close()
        
        return {
            'service': service,
            'status': status,
            'recent_history': history,
            'daily_stats': daily_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def record_refresh(self, service: str, success: bool, duration: float = None,
                      error: str = None, cookie_age_days: float = None, strategy: str = None):
        """Record a refresh attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert metric
        cursor.execute("""
            INSERT INTO refresh_metrics 
            (service, success, duration_seconds, error_message, cookie_age_days, strategy)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (service, success, duration, error, cookie_age_days, strategy))
        
        # Update service status
        if success:
            cursor.execute("""
                INSERT INTO service_status (service, last_refresh, last_success, consecutive_failures,
                                          total_refreshes, total_failures, avg_duration_seconds)
                VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 1, 0, ?)
                ON CONFLICT(service) DO UPDATE SET
                    last_refresh = CURRENT_TIMESTAMP,
                    last_success = CURRENT_TIMESTAMP,
                    consecutive_failures = 0,
                    total_refreshes = total_refreshes + 1,
                    avg_duration_seconds = 
                        CASE 
                            WHEN avg_duration_seconds IS NULL THEN ?
                            ELSE (avg_duration_seconds * total_refreshes + ?) / (total_refreshes + 1)
                        END
            """, (service, duration, duration, duration))
        else:
            cursor.execute("""
                INSERT INTO service_status (service, last_refresh, consecutive_failures,
                                          total_refreshes, total_failures)
                VALUES (?, CURRENT_TIMESTAMP, 1, 1, 1)
                ON CONFLICT(service) DO UPDATE SET
                    last_refresh = CURRENT_TIMESTAMP,
                    consecutive_failures = consecutive_failures + 1,
                    total_refreshes = total_refreshes + 1,
                    total_failures = total_failures + 1
            """, (service,))
        
        conn.commit()
        conn.close()
    
    def cleanup_old_metrics(self, days: int = 90):
        """Clean up metrics older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM refresh_metrics
            WHERE timestamp < datetime('now', '-{} days')
        """.format(days))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted} old metric records")
        return deleted
    
    def start(self):
        """Start the metrics server"""
        logger.info(f"Starting metrics exporter on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)


def create_grafana_dashboard() -> Dict:
    """Create a Grafana dashboard configuration"""
    dashboard = {
        "dashboard": {
            "title": "BEDROT Cookie Refresh Monitoring",
            "panels": [
                {
                    "title": "Success Rate by Service",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "cookie_refresh_success_rate",
                            "legendFormat": "{{service}}"
                        }
                    ]
                },
                {
                    "title": "Cookie Age (Days)",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "cookie_age_days",
                            "legendFormat": "{{service}}"
                        }
                    ]
                },
                {
                    "title": "Refresh Duration (Seconds)",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "cookie_refresh_duration_seconds",
                            "legendFormat": "{{service}}"
                        }
                    ]
                },
                {
                    "title": "Consecutive Failures",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "cookie_refresh_consecutive_failures",
                            "legendFormat": "{{service}}"
                        }
                    ]
                },
                {
                    "title": "Total Refreshes (24h)",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "increase(cookie_refresh_total[24h])",
                            "legendFormat": "{{service}} - {{status}}"
                        }
                    ]
                },
                {
                    "title": "Hours Since Last Success",
                    "type": "table",
                    "targets": [
                        {
                            "expr": "cookie_refresh_last_success_hours",
                            "format": "table"
                        }
                    ]
                }
            ],
            "refresh": "30s",
            "time": {
                "from": "now-24h",
                "to": "now"
            }
        }
    }
    
    return dashboard


def export_dashboard(output_path: str):
    """Export Grafana dashboard configuration"""
    dashboard = create_grafana_dashboard()
    
    with open(output_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    logger.info(f"Exported Grafana dashboard to {output_path}")


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Cookie Refresh Metrics Exporter')
    parser.add_argument('--port', type=int, default=9090, help='Port to run metrics server')
    parser.add_argument('--export-dashboard', help='Export Grafana dashboard to file')
    parser.add_argument('--record-test', action='store_true', help='Record test metrics')
    
    args = parser.parse_args()
    
    if args.export_dashboard:
        export_dashboard(args.export_dashboard)
    elif args.record_test:
        # Record some test metrics
        exporter = MetricsExporter()
        
        test_data = [
            ('spotify', True, 5.2, None, 15.3),
            ('tiktok', True, 12.5, None, 8.7),
            ('distrokid', False, 8.1, 'Authentication failed', 25.1),
            ('toolost', True, 3.8, None, 2.5),
            ('linktree', True, 6.9, None, 18.9),
        ]
        
        for service, success, duration, error, age in test_data:
            exporter.record_refresh(service, success, duration, error, age)
            print(f"Recorded test metric for {service}")
        
        print("Test metrics recorded successfully")
    else:
        # Start metrics server
        exporter = MetricsExporter(port=args.port)
        print(f"Starting metrics exporter on http://localhost:{args.port}/metrics")
        print(f"Grafana dashboard export: python {__file__} --export-dashboard dashboard.json")
        exporter.start()