#!/usr/bin/env python3
"""
Cookie Refresh Dashboard Generator

Creates HTML dashboards with:
- Service status visualization
- Expiration countdowns
- Success/failure metrics
- Quick action buttons
- Auto-refresh functionality
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import webbrowser
from collections import defaultdict

from .storage import CookieStorage
from .config_loader import load_config


class CookieRefreshDashboard:
    """Generate visual dashboards for cookie refresh status."""
    
    def __init__(self, storage: Optional[CookieStorage] = None):
        """Initialize dashboard generator.
        
        Args:
            storage: Cookie storage instance (creates default if not provided)
        """
        self.config = load_config()
        self.storage = storage or CookieStorage(self.config)
        self.project_root = Path(os.environ.get('PROJECT_ROOT', Path(__file__).resolve().parents[3]))
        self.dashboard_dir = self.project_root / 'dashboards'
        self.dashboard_dir.mkdir(exist_ok=True)
    
    def generate_dashboard(self, output_file: Optional[str] = None, 
                         auto_open: bool = False) -> Path:
        """Generate HTML dashboard.
        
        Args:
            output_file: Output filename (defaults to cookie_dashboard.html)
            auto_open: Open dashboard in browser after generation
            
        Returns:
            Path to generated dashboard file
        """
        # Gather data
        services_data = self._gather_services_data()
        metrics = self._calculate_metrics(services_data)
        history = self._get_refresh_history()
        
        # Generate HTML
        html_content = self._generate_html(services_data, metrics, history)
        
        # Save to file
        output_file = output_file or 'cookie_dashboard.html'
        output_path = self.dashboard_dir / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Dashboard generated: {output_path}")
        
        # Open in browser if requested
        if auto_open:
            webbrowser.open(f'file:///{output_path.absolute()}')
        
        return output_path
    
    def _gather_services_data(self) -> List[Dict[str, Any]]:
        """Gather data for all services."""
        services_data = []
        
        for service in self.config['services']:
            service_name = service['name']
            
            # Get cookie status
            status = self.storage.get_status(service_name)
            
            # Calculate expiration info
            if status['exists'] and status['last_refreshed']:
                last_refreshed = datetime.fromisoformat(status['last_refreshed'])
                max_age_days = service.get('cookie_max_age_days', 30)
                expires_at = last_refreshed + timedelta(days=max_age_days)
                days_until_expiry = (expires_at - datetime.now()).days
                
                if days_until_expiry < 0:
                    status_class = 'expired'
                    status_text = 'EXPIRED'
                elif days_until_expiry <= 3:
                    status_class = 'critical'
                    status_text = 'EXPIRING SOON'
                elif days_until_expiry <= 7:
                    status_class = 'warning'
                    status_text = 'WARNING'
                else:
                    status_class = 'healthy'
                    status_text = 'OK'
            else:
                last_refreshed = None
                expires_at = None
                days_until_expiry = None
                status_class = 'missing'
                status_text = 'MISSING'
            
            # Get accounts if multi-account
            accounts = []
            if service.get('multi_account', False):
                for account in service.get('accounts', []):
                    account_status = self.storage.get_status(service_name, account['name'])
                    accounts.append({
                        'name': account['name'],
                        'exists': account_status['exists'],
                        'last_refreshed': account_status.get('last_refreshed'),
                        'status': self._get_account_status_class(account_status, service)
                    })
            
            services_data.append({
                'name': service_name,
                'status_class': status_class,
                'status_text': status_text,
                'exists': status['exists'],
                'last_refreshed': last_refreshed,
                'expires_at': expires_at,
                'days_until_expiry': days_until_expiry,
                'max_age_days': service.get('cookie_max_age_days', 30),
                'priority': service.get('priority', 'medium'),
                'multi_account': service.get('multi_account', False),
                'accounts': accounts,
                'auto_refresh': service.get('auto_refresh', False),
                'manual_url': service.get('manual_login_url', '#')
            })
        
        # Sort by priority and status
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        status_order = {'expired': 0, 'missing': 1, 'critical': 2, 'warning': 3, 'healthy': 4}
        
        services_data.sort(key=lambda x: (
            priority_order.get(x['priority'], 999),
            status_order.get(x['status_class'], 999)
        ))
        
        return services_data
    
    def _get_account_status_class(self, account_status: Dict[str, Any], 
                                 service: Dict[str, Any]) -> str:
        """Determine status class for an account."""
        if not account_status['exists']:
            return 'missing'
        
        if account_status.get('last_refreshed'):
            last_refreshed = datetime.fromisoformat(account_status['last_refreshed'])
            max_age_days = service.get('cookie_max_age_days', 30)
            days_old = (datetime.now() - last_refreshed).days
            
            if days_old > max_age_days:
                return 'expired'
            elif days_old > max_age_days - 3:
                return 'critical'
            elif days_old > max_age_days - 7:
                return 'warning'
            else:
                return 'healthy'
        
        return 'unknown'
    
    def _calculate_metrics(self, services_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate dashboard metrics."""
        metrics = {
            'total_services': len(services_data),
            'healthy': sum(1 for s in services_data if s['status_class'] == 'healthy'),
            'warning': sum(1 for s in services_data if s['status_class'] == 'warning'),
            'critical': sum(1 for s in services_data if s['status_class'] == 'critical'),
            'expired': sum(1 for s in services_data if s['status_class'] == 'expired'),
            'missing': sum(1 for s in services_data if s['status_class'] == 'missing'),
            'auto_refresh_enabled': sum(1 for s in services_data if s['auto_refresh']),
            'next_expiry': None,
            'critical_services': []
        }
        
        # Find next expiry
        valid_services = [s for s in services_data if s['expires_at']]
        if valid_services:
            next_expiry_service = min(valid_services, key=lambda x: x['expires_at'])
            metrics['next_expiry'] = {
                'service': next_expiry_service['name'],
                'date': next_expiry_service['expires_at'],
                'days': next_expiry_service['days_until_expiry']
            }
        
        # List critical services
        metrics['critical_services'] = [
            s['name'] for s in services_data 
            if s['status_class'] in ['expired', 'critical', 'missing']
        ]
        
        return metrics
    
    def _get_refresh_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent refresh history."""
        history = []
        
        # Read refresh log if exists
        log_file = self.project_root / 'logs' / 'cookie_refresh.log'
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-limit:]  # Get last N lines
                    
                for line in lines:
                    try:
                        # Parse log entry (simple format for now)
                        if 'Cookie refresh' in line:
                            parts = line.strip().split(' - ')
                            if len(parts) >= 3:
                                timestamp = parts[0]
                                message = ' - '.join(parts[2:])
                                
                                # Determine status from message
                                if 'success' in message.lower():
                                    status = 'success'
                                elif 'failed' in message.lower():
                                    status = 'failed'
                                else:
                                    status = 'info'
                                
                                history.append({
                                    'timestamp': timestamp,
                                    'message': message,
                                    'status': status
                                })
                    except:
                        continue
                        
            except Exception as e:
                print(f"Error reading refresh log: {e}")
        
        return history
    
    def _generate_html(self, services_data: List[Dict[str, Any]], 
                      metrics: Dict[str, Any], 
                      history: List[Dict[str, Any]]) -> str:
        """Generate HTML content for dashboard."""
        
        # Generate service cards
        service_cards_html = ""
        for service in services_data:
            # Format last refreshed time
            if service['last_refreshed']:
                last_refreshed_str = service['last_refreshed'].strftime('%Y-%m-%d %H:%M')
                days_ago = (datetime.now() - service['last_refreshed']).days
                time_info = f"{last_refreshed_str} ({days_ago}d ago)"
            else:
                time_info = "Never"
            
            # Format expiration info
            if service['days_until_expiry'] is not None:
                if service['days_until_expiry'] < 0:
                    expiry_info = f"Expired {abs(service['days_until_expiry'])} days ago"
                else:
                    expiry_info = f"Expires in {service['days_until_expiry']} days"
            else:
                expiry_info = "No expiration data"
            
            # Account info for multi-account services
            accounts_html = ""
            if service['multi_account'] and service['accounts']:
                accounts_html = '<div class="accounts">'
                for account in service['accounts']:
                    account_class = account['status']
                    accounts_html += f'<span class="account-badge {account_class}">{account["name"]}</span>'
                accounts_html += '</div>'
            
            # Action buttons
            actions_html = f'''
                <button onclick="refreshService('{service['name']}')" class="action-btn refresh">
                    Refresh Now
                </button>
                <a href="{service['manual_url']}" target="_blank" class="action-btn manual">
                    Manual Login
                </a>
            '''
            
            service_cards_html += f'''
            <div class="service-card {service['status_class']}">
                <div class="service-header">
                    <h3>{service['name'].upper()}</h3>
                    <span class="status-badge {service['status_class']}">{service['status_text']}</span>
                </div>
                <div class="service-details">
                    <div class="detail-row">
                        <span class="label">Priority:</span>
                        <span class="value priority-{service['priority']}">{service['priority'].upper()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Last Refresh:</span>
                        <span class="value">{time_info}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Status:</span>
                        <span class="value">{expiry_info}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Auto-Refresh:</span>
                        <span class="value">{'Enabled' if service['auto_refresh'] else 'Disabled'}</span>
                    </div>
                    {accounts_html}
                </div>
                <div class="service-actions">
                    {actions_html}
                </div>
            </div>
            '''
        
        # Generate history entries
        history_html = ""
        for entry in history[-10:]:  # Show last 10 entries
            status_class = entry['status']
            history_html += f'''
            <div class="history-entry {status_class}">
                <span class="timestamp">{entry['timestamp']}</span>
                <span class="message">{entry['message']}</span>
            </div>
            '''
        
        # Generate full HTML
        html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BEDROT Cookie Refresh Dashboard</title>
    <meta http-equiv="refresh" content="300"> <!-- Auto-refresh every 5 minutes -->
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .last-updated {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #7f8c8d;
            font-size: 14px;
            text-transform: uppercase;
        }}
        
        .metric-healthy {{ color: #27ae60; }}
        .metric-warning {{ color: #f39c12; }}
        .metric-critical {{ color: #e74c3c; }}
        .metric-expired {{ color: #c0392b; }}
        .metric-missing {{ color: #95a5a6; }}
        
        .services-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .service-card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .service-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .service-card.healthy {{ border-left: 5px solid #27ae60; }}
        .service-card.warning {{ border-left: 5px solid #f39c12; }}
        .service-card.critical {{ border-left: 5px solid #e74c3c; }}
        .service-card.expired {{ border-left: 5px solid #c0392b; }}
        .service-card.missing {{ border-left: 5px solid #95a5a6; }}
        
        .service-header {{
            padding: 15px 20px;
            background: #f8f9fa;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .service-header h3 {{
            margin: 0;
            color: #2c3e50;
        }}
        
        .status-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            color: white;
        }}
        
        .status-badge.healthy {{ background: #27ae60; }}
        .status-badge.warning {{ background: #f39c12; }}
        .status-badge.critical {{ background: #e74c3c; }}
        .status-badge.expired {{ background: #c0392b; }}
        .status-badge.missing {{ background: #95a5a6; }}
        
        .service-details {{
            padding: 20px;
        }}
        
        .detail-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        
        .detail-row .label {{
            color: #7f8c8d;
        }}
        
        .detail-row .value {{
            font-weight: 500;
        }}
        
        .priority-critical {{ color: #e74c3c; }}
        .priority-high {{ color: #e67e22; }}
        .priority-medium {{ color: #f39c12; }}
        .priority-low {{ color: #95a5a6; }}
        
        .accounts {{
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        
        .account-badge {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            background: #ecf0f1;
        }}
        
        .account-badge.healthy {{ background: #d5f4e6; color: #27ae60; }}
        .account-badge.warning {{ background: #ffedc9; color: #f39c12; }}
        .account-badge.critical {{ background: #fadbd8; color: #e74c3c; }}
        .account-badge.expired {{ background: #f5b7b1; color: #c0392b; }}
        .account-badge.missing {{ background: #d5dbdb; color: #7f8c8d; }}
        
        .service-actions {{
            padding: 15px 20px;
            background: #f8f9fa;
            display: flex;
            gap: 10px;
        }}
        
        .action-btn {{
            flex: 1;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            transition: background 0.2s;
        }}
        
        .action-btn.refresh {{
            background: #3498db;
            color: white;
        }}
        
        .action-btn.refresh:hover {{
            background: #2980b9;
        }}
        
        .action-btn.manual {{
            background: #ecf0f1;
            color: #2c3e50;
        }}
        
        .action-btn.manual:hover {{
            background: #d5dbdb;
        }}
        
        .history-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .history-section h2 {{
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        
        .history-entry {{
            padding: 10px;
            margin-bottom: 5px;
            border-radius: 4px;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .history-entry.success {{
            background: #d5f4e6;
            color: #27ae60;
        }}
        
        .history-entry.failed {{
            background: #fadbd8;
            color: #e74c3c;
        }}
        
        .history-entry.info {{
            background: #d6eaf8;
            color: #3498db;
        }}
        
        .history-entry .timestamp {{
            font-weight: 500;
        }}
        
        .alert {{
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .alert.warning {{
            background: #fcf8e3;
            color: #8a6d3b;
            border: 1px solid #faebcc;
        }}
        
        .alert.critical {{
            background: #f2dede;
            color: #a94442;
            border: 1px solid #ebccd1;
        }}
        
        .export-buttons {{
            float: right;
            display: flex;
            gap: 10px;
        }}
        
        .export-btn {{
            padding: 8px 16px;
            background: #95a5a6;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
        }}
        
        .export-btn:hover {{
            background: #7f8c8d;
        }}
        
        @media (max-width: 768px) {{
            .services-grid {{
                grid-template-columns: 1fr;
            }}
            
            .metrics {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="export-buttons">
                <button onclick="exportToJSON()" class="export-btn">Export JSON</button>
                <button onclick="exportToCSV()" class="export-btn">Export CSV</button>
                <button onclick="window.print()" class="export-btn">Print/PDF</button>
            </div>
            <h1>BEDROT Cookie Refresh Dashboard</h1>
            <div class="last-updated">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </header>
        
        {self._generate_alerts(metrics)}
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value metric-healthy">{metrics['healthy']}</div>
                <div class="metric-label">Healthy</div>
            </div>
            <div class="metric-card">
                <div class="metric-value metric-warning">{metrics['warning']}</div>
                <div class="metric-label">Warning</div>
            </div>
            <div class="metric-card">
                <div class="metric-value metric-critical">{metrics['critical']}</div>
                <div class="metric-label">Critical</div>
            </div>
            <div class="metric-card">
                <div class="metric-value metric-expired">{metrics['expired']}</div>
                <div class="metric-label">Expired</div>
            </div>
            <div class="metric-card">
                <div class="metric-value metric-missing">{metrics['missing']}</div>
                <div class="metric-label">Missing</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['auto_refresh_enabled']}/{metrics['total_services']}</div>
                <div class="metric-label">Auto-Refresh</div>
            </div>
        </div>
        
        <h2>Services Status</h2>
        <div class="services-grid">
            {service_cards_html}
        </div>
        
        <div class="history-section">
            <h2>Recent Activity</h2>
            <div class="history-container">
                {history_html or '<div class="history-entry info"><span class="message">No recent activity recorded</span></div>'}
            </div>
        </div>
    </div>
    
    <script>
        // Dashboard data for export
        const dashboardData = {json.dumps({
            'generated_at': datetime.now().isoformat(),
            'metrics': metrics,
            'services': services_data
        }, indent=2, default=str)};
        
        function refreshService(serviceName) {{
            if (confirm(`Refresh cookies for ${{serviceName}}?`)) {{
                // In a real implementation, this would call the refresh API
                alert(`Refreshing ${{serviceName}}... This feature requires API integration.`);
                // window.location.href = `/api/refresh/${{serviceName}}`;
            }}
        }}
        
        function exportToJSON() {{
            const dataStr = JSON.stringify(dashboardData, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportLink = document.createElement('a');
            exportLink.setAttribute('href', dataUri);
            exportLink.setAttribute('download', 'cookie_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json');
            document.body.appendChild(exportLink);
            exportLink.click();
            document.body.removeChild(exportLink);
        }}
        
        function exportToCSV() {{
            const services = dashboardData.services;
            const headers = ['Service', 'Status', 'Priority', 'Last Refreshed', 'Days Until Expiry', 'Auto Refresh'];
            
            let csv = headers.join(',') + '\\n';
            
            services.forEach(service => {{
                const row = [
                    service.name,
                    service.status_text,
                    service.priority,
                    service.last_refreshed || 'Never',
                    service.days_until_expiry !== null ? service.days_until_expiry : 'N/A',
                    service.auto_refresh ? 'Yes' : 'No'
                ];
                csv += row.map(v => `"${{v}}"`).join(',') + '\\n';
            }});
            
            const dataUri = 'data:text/csv;charset=utf-8,'+ encodeURIComponent(csv);
            
            const exportLink = document.createElement('a');
            exportLink.setAttribute('href', dataUri);
            exportLink.setAttribute('download', 'cookie_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv');
            document.body.appendChild(exportLink);
            exportLink.click();
            document.body.removeChild(exportLink);
        }}
        
        // Auto-refresh countdown
        let secondsUntilRefresh = 300; // 5 minutes
        
        setInterval(() => {{
            secondsUntilRefresh--;
            if (secondsUntilRefresh <= 0) {{
                location.reload();
            }}
        }}, 1000);
    </script>
</body>
</html>
'''
        
        return html_content
    
    def _generate_alerts(self, metrics: Dict[str, Any]) -> str:
        """Generate alert HTML based on metrics."""
        alerts_html = ""
        
        # Critical services alert
        if metrics['critical_services']:
            services_list = ', '.join(metrics['critical_services'])
            alerts_html += f'''
            <div class="alert critical">
                <strong>⚠️ Critical Alert:</strong> The following services need immediate attention: {services_list}
            </div>
            '''
        
        # Next expiry warning
        if metrics['next_expiry'] and metrics['next_expiry']['days'] <= 3:
            alerts_html += f'''
            <div class="alert warning">
                <strong>⏰ Expiry Warning:</strong> {metrics['next_expiry']['service']} cookies will expire in {metrics['next_expiry']['days']} days
            </div>
            '''
        
        return alerts_html
    
    def generate_summary_report(self, output_format: str = 'text') -> str:
        """Generate a summary report in text or markdown format.
        
        Args:
            output_format: 'text' or 'markdown'
            
        Returns:
            Formatted report string
        """
        services_data = self._gather_services_data()
        metrics = self._calculate_metrics(services_data)
        
        if output_format == 'markdown':
            return self._generate_markdown_report(services_data, metrics)
        else:
            return self._generate_text_report(services_data, metrics)
    
    def _generate_text_report(self, services_data: List[Dict[str, Any]], 
                            metrics: Dict[str, Any]) -> str:
        """Generate plain text report."""
        report = []
        report.append("="*60)
        report.append("BEDROT COOKIE REFRESH STATUS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*60)
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-"*60)
        report.append(f"Total Services: {metrics['total_services']}")
        report.append(f"Healthy: {metrics['healthy']}")
        report.append(f"Warning: {metrics['warning']}")
        report.append(f"Critical: {metrics['critical']}")
        report.append(f"Expired: {metrics['expired']}")
        report.append(f"Missing: {metrics['missing']}")
        report.append("")
        
        # Critical services
        if metrics['critical_services']:
            report.append("CRITICAL SERVICES")
            report.append("-"*60)
            for service in metrics['critical_services']:
                report.append(f"  - {service}")
            report.append("")
        
        # Service details
        report.append("SERVICE DETAILS")
        report.append("-"*60)
        
        for service in services_data:
            report.append(f"\n{service['name'].upper()}")
            report.append(f"  Status: {service['status_text']}")
            report.append(f"  Priority: {service['priority']}")
            
            if service['last_refreshed']:
                days_ago = (datetime.now() - service['last_refreshed']).days
                report.append(f"  Last Refreshed: {service['last_refreshed'].strftime('%Y-%m-%d')} ({days_ago}d ago)")
            else:
                report.append("  Last Refreshed: Never")
            
            if service['days_until_expiry'] is not None:
                if service['days_until_expiry'] < 0:
                    report.append(f"  Expiration: Expired {abs(service['days_until_expiry'])} days ago")
                else:
                    report.append(f"  Expiration: {service['days_until_expiry']} days remaining")
            
            report.append(f"  Auto-Refresh: {'Enabled' if service['auto_refresh'] else 'Disabled'}")
        
        return "\n".join(report)
    
    def _generate_markdown_report(self, services_data: List[Dict[str, Any]], 
                                metrics: Dict[str, Any]) -> str:
        """Generate markdown report."""
        report = []
        report.append("# BEDROT Cookie Refresh Status Report")
        report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        report.append("")
        
        # Summary table
        report.append("## Summary")
        report.append("")
        report.append("| Metric | Count |")
        report.append("|--------|--------|")
        report.append(f"| Total Services | {metrics['total_services']} |")
        report.append(f"| 🟢 Healthy | {metrics['healthy']} |")
        report.append(f"| 🟡 Warning | {metrics['warning']} |")
        report.append(f"| 🔴 Critical | {metrics['critical']} |")
        report.append(f"| ⚫ Expired | {metrics['expired']} |")
        report.append(f"| ⚪ Missing | {metrics['missing']} |")
        report.append("")
        
        # Critical alerts
        if metrics['critical_services']:
            report.append("## ⚠️ Critical Alerts")
            report.append("")
            for service in metrics['critical_services']:
                report.append(f"- **{service}** requires immediate attention")
            report.append("")
        
        # Service status table
        report.append("## Service Status")
        report.append("")
        report.append("| Service | Status | Priority | Last Refreshed | Expiration | Auto-Refresh |")
        report.append("|---------|--------|----------|----------------|------------|--------------|")
        
        for service in services_data:
            status_emoji = {
                'healthy': '🟢',
                'warning': '🟡',
                'critical': '🔴',
                'expired': '⚫',
                'missing': '⚪'
            }.get(service['status_class'], '❓')
            
            if service['last_refreshed']:
                days_ago = (datetime.now() - service['last_refreshed']).days
                last_refreshed = f"{days_ago}d ago"
            else:
                last_refreshed = "Never"
            
            if service['days_until_expiry'] is not None:
                if service['days_until_expiry'] < 0:
                    expiration = f"Expired {abs(service['days_until_expiry'])}d ago"
                else:
                    expiration = f"{service['days_until_expiry']}d remaining"
            else:
                expiration = "N/A"
            
            auto_refresh = "✅" if service['auto_refresh'] else "❌"
            
            report.append(
                f"| {service['name']} | {status_emoji} {service['status_text']} | "
                f"{service['priority']} | {last_refreshed} | {expiration} | {auto_refresh} |"
            )
        
        return "\n".join(report)


def main():
    """Main entry point for dashboard generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate BEDROT Cookie Refresh Dashboard")
    parser.add_argument('--output', '-o', help='Output filename')
    parser.add_argument('--open', '-p', action='store_true', 
                       help='Open dashboard in browser')
    parser.add_argument('--format', '-f', choices=['html', 'text', 'markdown'],
                       default='html', help='Output format')
    
    args = parser.parse_args()
    
    dashboard = CookieRefreshDashboard()
    
    if args.format == 'html':
        dashboard.generate_dashboard(
            output_file=args.output,
            auto_open=args.open
        )
    else:
        report = dashboard.generate_summary_report(args.format)
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_path}")
        else:
            print(report)


if __name__ == "__main__":
    main()