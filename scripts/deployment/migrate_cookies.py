#!/usr/bin/env python3
"""
Cookie migration script for upgrading to new cookie refresh system
Safely migrates existing cookies to new structure
"""

import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Dict, List, Optional, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class CookieMigrator:
    """Migrates cookies from old structure to new cookie refresh system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.backup_dir = self.project_root / 'backups' / 'cookie_migration'
        self.stats = {
            'total_files': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0
        }
        self.migration_log = []
        
    def run_migration(self, verify_only: bool = True) -> bool:
        """Run cookie migration"""
        print("=" * 60)
        print("Cookie Migration Tool")
        print("=" * 60)
        print(f"Mode: {'VERIFY ONLY' if verify_only else 'EXECUTE MIGRATION'}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # Find all cookie files
        cookie_files = self.find_cookie_files()
        
        if not cookie_files:
            print("No cookie files found to migrate.")
            return True
        
        print(f"Found {len(cookie_files)} cookie files to process\n")
        
        # Create backup directory
        if not verify_only:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"Backup directory: {self.backup_dir}\n")
        
        # Process each cookie file
        success = True
        for cookie_file in cookie_files:
            if verify_only:
                success &= self.verify_cookie_file(cookie_file)
            else:
                success &= self.migrate_cookie_file(cookie_file)
        
        # Print summary
        self.print_summary(verify_only)
        
        # Save migration log
        if not verify_only:
            self.save_migration_log()
        
        return success
    
    def find_cookie_files(self) -> List[Path]:
        """Find all existing cookie files"""
        cookie_patterns = [
            "src/*/cookies/*_cookies.json",
            "src/*/cookies/*_cookie.json",
            "src/*/cookies/*.json",
        ]
        
        cookie_files = []
        for pattern in cookie_patterns:
            cookie_files.extend(self.project_root.glob(pattern))
        
        # Filter out non-cookie files
        filtered_files = []
        for file in cookie_files:
            # Skip hash files and other metadata
            if '_hashes.json' in file.name or 'metadata' in file.name:
                continue
            filtered_files.append(file)
        
        return sorted(set(filtered_files))
    
    def verify_cookie_file(self, cookie_file: Path) -> bool:
        """Verify a cookie file can be migrated"""
        self.stats['total_files'] += 1
        
        try:
            # Read and validate JSON
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            # Determine service name
            service = self.get_service_name(cookie_file)
            
            # Validate cookie format
            if not isinstance(cookies, list):
                self.log_error(cookie_file, "Invalid format: not a list")
                return False
            
            # Check cookie structure
            valid_cookies = 0
            for cookie in cookies:
                if self.validate_cookie_structure(cookie):
                    valid_cookies += 1
            
            if valid_cookies == 0:
                self.log_error(cookie_file, "No valid cookies found")
                return False
            
            # Check file age
            age_days = self.get_file_age_days(cookie_file)
            status = "✓ Valid" if age_days < 30 else "⚠ Old"
            
            print(f"{status} {service}: {cookie_file.relative_to(self.project_root)}")
            print(f"  - Cookies: {valid_cookies}/{len(cookies)} valid")
            print(f"  - Age: {age_days:.1f} days")
            print(f"  - Size: {cookie_file.stat().st_size} bytes")
            
            if service in ['toolost', 'distrokid']:
                # Check for JWT expiration
                jwt_info = self.check_jwt_expiration(cookies)
                if jwt_info:
                    print(f"  - JWT: {jwt_info}")
            
            print()
            
            self.stats['migrated'] += 1
            return True
            
        except json.JSONDecodeError as e:
            self.log_error(cookie_file, f"Invalid JSON: {e}")
            return False
        except Exception as e:
            self.log_error(cookie_file, f"Error: {e}")
            return False
    
    def migrate_cookie_file(self, cookie_file: Path) -> bool:
        """Migrate a single cookie file"""
        self.stats['total_files'] += 1
        
        try:
            # Create backup
            backup_path = self.backup_cookie_file(cookie_file)
            
            # Read cookies
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            # Get service name
            service = self.get_service_name(cookie_file)
            
            # Validate and transform cookies
            migrated_cookies = []
            for cookie in cookies:
                if self.validate_cookie_structure(cookie):
                    # Add any missing required fields
                    migrated_cookie = self.transform_cookie(cookie, service)
                    migrated_cookies.append(migrated_cookie)
            
            if not migrated_cookies:
                self.log_error(cookie_file, "No valid cookies to migrate")
                return False
            
            # Write migrated cookies
            with open(cookie_file, 'w') as f:
                json.dump(migrated_cookies, f, indent=2)
            
            # Create metadata file
            metadata_file = cookie_file.parent / f"{service}_metadata.json"
            metadata = {
                'service': service,
                'last_refresh': datetime.now().isoformat(),
                'cookie_count': len(migrated_cookies),
                'migration_date': datetime.now().isoformat(),
                'original_backup': str(backup_path.relative_to(self.project_root))
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Migrated {service}: {len(migrated_cookies)} cookies")
            print(f"  - Backup: {backup_path.relative_to(self.project_root)}")
            print(f"  - Metadata: {metadata_file.relative_to(self.project_root)}")
            print()
            
            self.stats['migrated'] += 1
            self.migration_log.append({
                'service': service,
                'file': str(cookie_file.relative_to(self.project_root)),
                'backup': str(backup_path.relative_to(self.project_root)),
                'cookies_migrated': len(migrated_cookies),
                'timestamp': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.log_error(cookie_file, f"Migration failed: {e}")
            # Restore from backup if available
            if 'backup_path' in locals():
                try:
                    shutil.copy2(backup_path, cookie_file)
                    print(f"  - Restored original file from backup")
                except:
                    pass
            return False
    
    def backup_cookie_file(self, cookie_file: Path) -> Path:
        """Create backup of cookie file"""
        # Generate unique backup name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        service = self.get_service_name(cookie_file)
        backup_name = f"{service}_cookies_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        # Copy file
        shutil.copy2(cookie_file, backup_path)
        
        # Also create a hash for verification
        with open(cookie_file, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        hash_file = backup_path.with_suffix('.hash')
        hash_file.write_text(file_hash)
        
        return backup_path
    
    def get_service_name(self, cookie_file: Path) -> str:
        """Extract service name from file path"""
        # Try to get from parent directory
        service_dir = cookie_file.parent.parent.name
        if service_dir in ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree', 'metaads']:
            return service_dir
        
        # Try to get from filename
        filename = cookie_file.stem.lower()
        for service in ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree', 'metaads']:
            if service in filename:
                return service
        
        # Default to directory name
        return service_dir
    
    def validate_cookie_structure(self, cookie: Dict) -> bool:
        """Validate cookie has required fields"""
        # Minimum required fields
        if not isinstance(cookie, dict):
            return False
        
        # Check for essential fields
        if 'name' not in cookie or 'value' not in cookie:
            return False
        
        # Check field types
        if not isinstance(cookie.get('name'), str) or not isinstance(cookie.get('value'), str):
            return False
        
        return True
    
    def transform_cookie(self, cookie: Dict, service: str) -> Dict:
        """Transform cookie to ensure compatibility"""
        # Start with original cookie
        transformed = cookie.copy()
        
        # Add domain if missing
        if 'domain' not in transformed:
            domain_map = {
                'spotify': '.spotify.com',
                'tiktok': '.tiktok.com',
                'distrokid': '.distrokid.com',
                'toolost': '.toolost.com',
                'linktree': '.linktr.ee',
                'metaads': '.facebook.com'
            }
            transformed['domain'] = domain_map.get(service, f'.{service}.com')
        
        # Add path if missing
        if 'path' not in transformed:
            transformed['path'] = '/'
        
        # Add secure flag if missing
        if 'secure' not in transformed:
            transformed['secure'] = True
        
        # Add httpOnly flag if missing
        if 'httpOnly' not in transformed:
            transformed['httpOnly'] = True
        
        # Add sameSite if missing
        if 'sameSite' not in transformed:
            transformed['sameSite'] = 'Lax'
        
        # Convert expiry formats
        if 'expirationDate' in transformed:
            # Playwright uses 'expires' instead of 'expirationDate'
            transformed['expires'] = transformed.pop('expirationDate')
        
        # Ensure expires is a number (timestamp)
        if 'expires' in transformed and isinstance(transformed['expires'], str):
            try:
                # Try to parse ISO date
                from dateutil import parser
                dt = parser.parse(transformed['expires'])
                transformed['expires'] = dt.timestamp()
            except:
                # Remove invalid expires
                transformed.pop('expires', None)
        
        return transformed
    
    def get_file_age_days(self, file_path: Path) -> float:
        """Get age of file in days"""
        file_time = file_path.stat().st_mtime
        age_seconds = datetime.now().timestamp() - file_time
        return age_seconds / (24 * 3600)
    
    def check_jwt_expiration(self, cookies: List[Dict]) -> Optional[str]:
        """Check JWT token expiration for services that use JWT"""
        for cookie in cookies:
            if cookie.get('name') in ['jwt', 'token', 'access_token']:
                if 'expires' in cookie:
                    expires_timestamp = cookie['expires']
                    if isinstance(expires_timestamp, (int, float)):
                        expires_date = datetime.fromtimestamp(expires_timestamp)
                        days_until_expiry = (expires_date - datetime.now()).days
                        
                        if days_until_expiry < 0:
                            return f"Expired {abs(days_until_expiry)} days ago"
                        elif days_until_expiry < 7:
                            return f"Expires in {days_until_expiry} days"
                        else:
                            return f"Valid for {days_until_expiry} days"
        
        return None
    
    def log_error(self, cookie_file: Path, error: str):
        """Log an error for a cookie file"""
        print(f"✗ Error {self.get_service_name(cookie_file)}: {cookie_file.relative_to(self.project_root)}")
        print(f"  - {error}")
        print()
        
        self.stats['errors'] += 1
        self.migration_log.append({
            'service': self.get_service_name(cookie_file),
            'file': str(cookie_file.relative_to(self.project_root)),
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def print_summary(self, verify_only: bool):
        """Print migration summary"""
        print("=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        
        print(f"Total files processed: {self.stats['total_files']}")
        print(f"Successfully {'verified' if verify_only else 'migrated'}: {self.stats['migrated']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        
        success_rate = (self.stats['migrated'] / self.stats['total_files'] * 100) if self.stats['total_files'] > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        if verify_only and self.stats['errors'] == 0:
            print("\n✅ All cookie files are ready for migration!")
            print("\nTo execute migration, run:")
            print("  python scripts/deployment/migrate_cookies.py --execute")
        elif not verify_only:
            if self.stats['errors'] == 0:
                print("\n✅ Migration completed successfully!")
            else:
                print(f"\n⚠️  Migration completed with {self.stats['errors']} errors")
        
        print("=" * 60)
    
    def save_migration_log(self):
        """Save detailed migration log"""
        log_file = self.backup_dir / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'migrations': self.migration_log
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\nMigration log saved to: {log_file.relative_to(self.project_root)}")


def main():
    """Run cookie migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate cookies to new refresh system')
    parser.add_argument('--execute', action='store_true', help='Execute migration (default is verify only)')
    parser.add_argument('--verify', action='store_true', help='Verify only (default)')
    
    args = parser.parse_args()
    
    # Default to verify mode
    verify_only = not args.execute
    
    migrator = CookieMigrator()
    success = migrator.run_migration(verify_only=verify_only)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()