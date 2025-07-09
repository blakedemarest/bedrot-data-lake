"""Enhanced storage management for cookies and browser state.

This module provides hybrid storage supporting both legacy cookies.json format
and Playwright's storageState format for complete session persistence.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CookieInfo:
    """Cookie information container."""
    name: str
    value: str
    domain: str
    path: str
    expires: Optional[float] = None
    httpOnly: bool = False
    secure: bool = False
    sameSite: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if cookie is expired."""
        if self.expires is None:
            return False
        return datetime.now().timestamp() > self.expires
    
    @property
    def expiration_date(self) -> Optional[datetime]:
        """Get expiration date as datetime object."""
        if self.expires is None:
            return None
        return datetime.fromtimestamp(self.expires)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        # Remove None values for cleaner JSON
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class AuthStateInfo:
    """Authentication state information."""
    service: str
    last_refresh: datetime
    next_expiration: Optional[datetime]
    cookie_count: int
    has_storage_state: bool
    is_expired: bool
    days_until_expiration: Optional[int]
    
    @property
    def status(self) -> str:
        """Get human-readable status."""
        if self.is_expired:
            return "EXPIRED"
        elif self.days_until_expiration is not None:
            if self.days_until_expiration <= 3:
                return "CRITICAL"
            elif self.days_until_expiration <= 7:
                return "WARNING"
            else:
                return "VALID"
        else:
            return "UNKNOWN"


class CookieStorageManager:
    """Manages cookie and browser state storage with backup capabilities."""
    
    def __init__(self, base_path: Union[str, Path], backup_path: Optional[Union[str, Path]] = None):
        """Initialize storage manager.
        
        Args:
            base_path: Base path for cookie storage (typically src/)
            backup_path: Path for backups (optional)
        """
        self.base_path = Path(base_path)
        self.backup_path = Path(backup_path) if backup_path else self.base_path.parent / 'backups' / 'cookies'
        
        # Ensure backup directory exists
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
    def get_cookie_path(self, service: str, account: Optional[str] = None) -> Path:
        """Get path to cookie file for a service.
        
        Args:
            service: Service name (e.g., 'spotify', 'tiktok')
            account: Optional account identifier for multi-account services
            
        Returns:
            Path to cookies.json file
        """
        if account:
            # For services with multiple accounts (e.g., TikTok)
            return self.base_path / service / 'cookies' / f'{account}_cookies.json'
        else:
            return self.base_path / service / 'cookies' / 'cookies.json'
    
    def get_storage_state_path(self, service: str, account: Optional[str] = None) -> Path:
        """Get path to Playwright storage state file.
        
        Args:
            service: Service name
            account: Optional account identifier
            
        Returns:
            Path to storageState.json file
        """
        if account:
            return self.base_path / service / 'cookies' / f'{account}_storageState.json'
        else:
            return self.base_path / service / 'cookies' / 'storageState.json'
    
    def save_cookies(self, service: str, cookies: List[Dict[str, Any]], 
                    account: Optional[str] = None) -> Path:
        """Save cookies in legacy format.
        
        Args:
            service: Service name
            cookies: List of cookie dictionaries
            account: Optional account identifier
            
        Returns:
            Path to saved cookie file
        """
        cookie_path = self.get_cookie_path(service, account)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing cookies if they exist
        if cookie_path.exists():
            self.backup_auth_state(service, account)
        
        # Convert to CookieInfo objects for validation
        cookie_objects = []
        for cookie in cookies:
            if not isinstance(cookie, dict):
                continue
                
            try:
                # Handle field name compatibility
                cookie_data = cookie.copy()
                
                # Convert expirationDate to expires for internal use
                if 'expirationDate' in cookie_data and 'expires' not in cookie_data:
                    cookie_data['expires'] = cookie_data.pop('expirationDate')
                
                # Filter out fields that don't exist in CookieInfo
                allowed_fields = {'name', 'value', 'domain', 'path', 'expires', 'httpOnly', 'secure', 'sameSite'}
                filtered_data = {k: v for k, v in cookie_data.items() if k in allowed_fields}
                
                cookie_info = CookieInfo(**filtered_data)
                
                # Convert back to original format with expirationDate
                cookie_dict = cookie_info.to_dict()
                if 'expires' in cookie_dict:
                    cookie_dict['expirationDate'] = cookie_dict.pop('expires')
                
                cookie_objects.append(cookie_dict)
            except Exception as e:
                logger.warning(f"Invalid cookie format: {e}")
                cookie_objects.append(cookie)  # Keep original if conversion fails
        
        # Save cookies
        with open(cookie_path, 'w') as f:
            json.dump(cookie_objects, f, indent=2)
        
        logger.info(f"Saved {len(cookie_objects)} cookies to {cookie_path}")
        return cookie_path
    
    def save_storage_state(self, service: str, storage_state: Dict[str, Any],
                          account: Optional[str] = None) -> Path:
        """Save Playwright storage state.
        
        Args:
            service: Service name
            storage_state: Playwright storage state dictionary
            account: Optional account identifier
            
        Returns:
            Path to saved storage state file
        """
        state_path = self.get_storage_state_path(service, account)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing state if it exists
        if state_path.exists():
            self.backup_auth_state(service, account)
        
        # Add metadata
        storage_state['_metadata'] = {
            'service': service,
            'account': account,
            'saved_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Save storage state
        with open(state_path, 'w') as f:
            json.dump(storage_state, f, indent=2)
        
        # Also extract and save cookies in legacy format for compatibility
        if 'cookies' in storage_state:
            self.save_cookies(service, storage_state['cookies'], account)
        
        logger.info(f"Saved storage state to {state_path}")
        return state_path
    
    def load_auth_state(self, service: str, account: Optional[str] = None,
                       prefer_storage_state: bool = True) -> Optional[Dict[str, Any]]:
        """Load authentication state (cookies or storage state).
        
        Args:
            service: Service name
            account: Optional account identifier
            prefer_storage_state: If True, prefer storageState over cookies
            
        Returns:
            Dictionary containing auth state or None if not found
        """
        storage_state_path = self.get_storage_state_path(service, account)
        cookie_path = self.get_cookie_path(service, account)
        
        # Try storage state first if preferred
        if prefer_storage_state and storage_state_path.exists():
            try:
                with open(storage_state_path, 'r') as f:
                    state = json.load(f)
                logger.info(f"Loaded storage state from {storage_state_path}")
                return state
            except Exception as e:
                logger.error(f"Failed to load storage state: {e}")
        
        # Fall back to cookies
        if cookie_path.exists():
            try:
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                logger.info(f"Loaded {len(cookies)} cookies from {cookie_path}")
                # Return in storage state format
                return {'cookies': cookies}
            except Exception as e:
                logger.error(f"Failed to load cookies: {e}")
        
        logger.warning(f"No auth state found for {service}" + (f" ({account})" if account else ""))
        return None
    
    def backup_auth_state(self, service: str, account: Optional[str] = None) -> Tuple[Optional[Path], Optional[Path]]:
        """Backup current authentication state.
        
        Args:
            service: Service name
            account: Optional account identifier
            
        Returns:
            Tuple of (cookie_backup_path, state_backup_path)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.backup_path / service
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        cookie_backup = None
        state_backup = None
        
        # Backup cookies
        cookie_path = self.get_cookie_path(service, account)
        if cookie_path.exists():
            backup_name = f"{account}_cookies_{timestamp}.json" if account else f"cookies_{timestamp}.json"
            cookie_backup = backup_dir / backup_name
            shutil.copy2(cookie_path, cookie_backup)
            logger.info(f"Backed up cookies to {cookie_backup}")
        
        # Backup storage state
        state_path = self.get_storage_state_path(service, account)
        if state_path.exists():
            backup_name = f"{account}_storageState_{timestamp}.json" if account else f"storageState_{timestamp}.json"
            state_backup = backup_dir / backup_name
            shutil.copy2(state_path, state_backup)
            logger.info(f"Backed up storage state to {state_backup}")
        
        # Clean old backups
        self._clean_old_backups(backup_dir)
        
        return cookie_backup, state_backup
    
    def restore_from_backup(self, service: str, backup_timestamp: str,
                           account: Optional[str] = None) -> bool:
        """Restore authentication state from a specific backup.
        
        Args:
            service: Service name
            backup_timestamp: Timestamp string (YYYYMMDD_HHMMSS)
            account: Optional account identifier
            
        Returns:
            True if restoration successful
        """
        backup_dir = self.backup_path / service
        
        # Find matching backup files
        cookie_pattern = f"{account}_cookies_{backup_timestamp}.json" if account else f"cookies_{backup_timestamp}.json"
        state_pattern = f"{account}_storageState_{backup_timestamp}.json" if account else f"storageState_{backup_timestamp}.json"
        
        cookie_backup = backup_dir / cookie_pattern
        state_backup = backup_dir / state_pattern
        
        restored = False
        
        # Restore cookies
        if cookie_backup.exists():
            cookie_path = self.get_cookie_path(service, account)
            shutil.copy2(cookie_backup, cookie_path)
            logger.info(f"Restored cookies from {cookie_backup}")
            restored = True
        
        # Restore storage state
        if state_backup.exists():
            state_path = self.get_storage_state_path(service, account)
            shutil.copy2(state_backup, state_path)
            logger.info(f"Restored storage state from {state_backup}")
            restored = True
        
        if not restored:
            logger.error(f"No backup found for {service} with timestamp {backup_timestamp}")
        
        return restored
    
    def get_expiration_info(self, service: str, account: Optional[str] = None) -> AuthStateInfo:
        """Get detailed expiration information for a service.
        
        Args:
            service: Service name
            account: Optional account identifier
            
        Returns:
            AuthStateInfo object with expiration details
        """
        auth_state = self.load_auth_state(service, account)
        
        if not auth_state:
            return AuthStateInfo(
                service=f"{service}" + (f"/{account}" if account else ""),
                last_refresh=datetime.min,
                next_expiration=None,
                cookie_count=0,
                has_storage_state=False,
                is_expired=True,
                days_until_expiration=None
            )
        
        # Extract cookies
        cookies = auth_state.get('cookies', [])
        cookie_objects = []
        
        # Convert cookies with field name compatibility
        for cookie in cookies:
            if not isinstance(cookie, dict):
                continue
            
            # Handle field name compatibility
            cookie_data = cookie.copy()
            
            # Convert expirationDate to expires
            if 'expirationDate' in cookie_data and 'expires' not in cookie_data:
                cookie_data['expires'] = cookie_data.pop('expirationDate')
            
            # Filter out fields that don't exist in CookieInfo
            allowed_fields = {'name', 'value', 'domain', 'path', 'expires', 'httpOnly', 'secure', 'sameSite'}
            filtered_data = {k: v for k, v in cookie_data.items() if k in allowed_fields}
            
            try:
                cookie_obj = CookieInfo(**filtered_data)
                cookie_objects.append(cookie_obj)
            except Exception as e:
                logger.warning(f"Failed to create CookieInfo: {e}, cookie: {filtered_data}")
        
        # Find earliest expiration
        expirations = [c.expiration_date for c in cookie_objects if c.expiration_date]
        next_expiration = min(expirations) if expirations else None
        
        # Check if any critical cookies are expired
        is_expired = any(c.is_expired for c in cookie_objects)
        
        # Calculate days until expiration
        days_until_expiration = None
        if next_expiration:
            delta = next_expiration - datetime.now()
            days_until_expiration = delta.days
        
        # Get last modification time of auth files
        cookie_path = self.get_cookie_path(service, account)
        state_path = self.get_storage_state_path(service, account)
        
        last_refresh = datetime.min
        if cookie_path.exists():
            last_refresh = datetime.fromtimestamp(cookie_path.stat().st_mtime)
        if state_path.exists():
            state_mtime = datetime.fromtimestamp(state_path.stat().st_mtime)
            last_refresh = max(last_refresh, state_mtime)
        
        return AuthStateInfo(
            service=f"{service}" + (f"/{account}" if account else ""),
            last_refresh=last_refresh,
            next_expiration=next_expiration,
            cookie_count=len(cookies),
            has_storage_state=state_path.exists(),
            is_expired=is_expired,
            days_until_expiration=days_until_expiration
        )
    
    def get_all_services_status(self) -> List[AuthStateInfo]:
        """Get expiration status for all services with stored auth.
        
        Returns:
            List of AuthStateInfo objects
        """
        status_list = []
        
        # Scan for all service directories
        for service_dir in self.base_path.iterdir():
            if not service_dir.is_dir():
                continue
            
            cookies_dir = service_dir / 'cookies'
            if not cookies_dir.exists():
                continue
            
            service = service_dir.name
            
            # Check for multi-account services (files like account_cookies.json)
            account_files = list(cookies_dir.glob('*_cookies.json'))
            if account_files:
                # Multi-account service
                for account_file in account_files:
                    account = account_file.stem.replace('_cookies', '')
                    if account != 'cookies':  # Skip the default cookies.json
                        status_list.append(self.get_expiration_info(service, account))
            else:
                # Single account service
                if (cookies_dir / 'cookies.json').exists():
                    status_list.append(self.get_expiration_info(service))
        
        return status_list
    
    def _clean_old_backups(self, backup_dir: Path, retention_days: int = 30):
        """Clean backups older than retention period.
        
        Args:
            backup_dir: Directory containing backups
            retention_days: Number of days to retain backups
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for backup_file in backup_dir.glob('*_cookies_*.json'):
            try:
                # Extract timestamp from filename
                parts = backup_file.stem.split('_')
                if len(parts) >= 3:
                    timestamp_str = f"{parts[-2]}_{parts[-1]}"
                    file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        logger.info(f"Deleted old backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Error processing backup file {backup_file}: {e}")