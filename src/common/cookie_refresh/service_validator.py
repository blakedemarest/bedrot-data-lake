"""Service URL validator for cookie refresh strategies.

This module validates that cookie refresh strategies use URLs that are
compatible with their corresponding service extractors, preventing
URL mismatches that could cause authentication failures.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ServiceURLConfig:
    """Configuration for a service's URL requirements."""
    service_name: str
    required_domains: List[str]
    forbidden_domains: List[str]
    extractor_urls: List[str]
    expected_patterns: List[str]

class ServiceURLValidator:
    """Validates that cookie refresh strategies use compatible URLs."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize validator.
        
        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.service_configs = self._load_service_configs()
    
    def _load_service_configs(self) -> Dict[str, ServiceURLConfig]:
        """Load service URL configurations."""
        configs = {}
        
        # Spotify for Artists configuration
        configs['spotify'] = ServiceURLConfig(
            service_name='spotify',
            required_domains=['artists.spotify.com'],
            forbidden_domains=[
                'accounts.spotify.com/login',
                'accounts.spotify.com/en/status',
                'open.spotify.com',
                'spotify.com/login'
            ],
            extractor_urls=[
                'https://artists.spotify.com/c/en/artist/',
                'https://artists.spotify.com/home',
                'https://artists.spotify.com'
            ],
            expected_patterns=[
                r'artists\.spotify\.com',
                r'artists\.spotify\.com/c/en/artist/[a-zA-Z0-9]+',
                r'artists\.spotify\.com/home'
            ]
        )
        
        # TikTok configuration
        configs['tiktok'] = ServiceURLConfig(
            service_name='tiktok',
            required_domains=['tiktok.com'],
            forbidden_domains=['accounts.tiktok.com'],
            extractor_urls=[
                'https://www.tiktok.com/creator-center',
                'https://www.tiktok.com/tiktokstudio'
            ],
            expected_patterns=[
                r'tiktok\.com',
                r'tiktok\.com/creator-center',
                r'tiktok\.com/tiktokstudio'
            ]
        )
        
        # TooLost configuration
        configs['toolost'] = ServiceURLConfig(
            service_name='toolost',
            required_domains=['toolost.com'],
            forbidden_domains=[],
            extractor_urls=[
                'https://toolost.com/login',
                'https://toolost.com/user-portal'
            ],
            expected_patterns=[
                r'toolost\.com',
                r'toolost\.com/user-portal',
                r'toolost\.com/login'
            ]
        )
        
        # Linktree configuration
        configs['linktree'] = ServiceURLConfig(
            service_name='linktree',
            required_domains=['linktr.ee'],
            forbidden_domains=[],
            extractor_urls=[
                'https://linktr.ee/login',
                'https://linktr.ee/admin'
            ],
            expected_patterns=[
                r'linktr\.ee',
                r'linktr\.ee/admin',
                r'linktr\.ee/login'
            ]
        )
        
        # DistroKid configuration
        configs['distrokid'] = ServiceURLConfig(
            service_name='distrokid',
            required_domains=['distrokid.com'],
            forbidden_domains=[],
            extractor_urls=[
                'https://distrokid.com/dashboard',
                'https://distrokid.com/signin'
            ],
            expected_patterns=[
                r'distrokid\.com',
                r'distrokid\.com/dashboard',
                r'distrokid\.com/signin'
            ]
        )
        
        return configs
    
    def validate_strategy_urls(self, service_name: str, strategy_urls: Dict[str, str]) -> bool:
        """Validate that strategy URLs are compatible with service requirements.
        
        Args:
            service_name: Name of the service
            strategy_urls: Dictionary of URL types to URLs (e.g., {'login_url': '...', 'artists_url': '...'})
            
        Returns:
            True if all URLs are valid
            
        Raises:
            ValueError: If URLs are invalid
        """
        if service_name not in self.service_configs:
            logger.warning(f"No URL validation config for service: {service_name}")
            return True
        
        config = self.service_configs[service_name]
        errors = []
        
        for url_type, url in strategy_urls.items():
            # Check required domains
            if not any(domain in url for domain in config.required_domains):
                errors.append(
                    f"{url_type} '{url}' must contain one of: {config.required_domains}"
                )
            
            # Check forbidden domains
            for forbidden_domain in config.forbidden_domains:
                if forbidden_domain in url:
                    errors.append(
                        f"{url_type} '{url}' contains forbidden domain: {forbidden_domain}"
                    )
            
            # Check expected patterns
            pattern_match = False
            for pattern in config.expected_patterns:
                if re.search(pattern, url):
                    pattern_match = True
                    break
            
            if not pattern_match:
                errors.append(
                    f"{url_type} '{url}' doesn't match expected patterns: {config.expected_patterns}"
                )
        
        if errors:
            error_msg = f"URL validation failed for {service_name}:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
        
        logger.info(f"✅ URL validation passed for {service_name}")
        return True
    
    def check_extractor_compatibility(self, service_name: str, strategy_urls: Dict[str, str]) -> bool:
        """Check if strategy URLs are compatible with extractor URLs.
        
        Args:
            service_name: Name of the service
            strategy_urls: Strategy URLs to validate
            
        Returns:
            True if compatible
        """
        if service_name not in self.service_configs:
            return True
        
        config = self.service_configs[service_name]
        extractor_domains = set()
        
        # Extract domains from extractor URLs
        for extractor_url in config.extractor_urls:
            domain_match = re.search(r'https?://([^/]+)', extractor_url)
            if domain_match:
                extractor_domains.add(domain_match.group(1))
        
        # Check if strategy URLs use compatible domains
        strategy_domains = set()
        for url in strategy_urls.values():
            domain_match = re.search(r'https?://([^/]+)', url)
            if domain_match:
                strategy_domains.add(domain_match.group(1))
        
        # Find common domains
        common_domains = extractor_domains.intersection(strategy_domains)
        
        if not common_domains:
            logger.error(
                f"❌ Strategy domains {strategy_domains} don't match extractor domains {extractor_domains} for {service_name}"
            )
            return False
        
        logger.info(f"✅ Strategy URLs compatible with extractors for {service_name} (common domains: {common_domains})")
        return True
    
    def validate_all_strategies(self, strategies: Dict[str, object]) -> Dict[str, bool]:
        """Validate all provided strategies.
        
        Args:
            strategies: Dictionary mapping service names to strategy instances
            
        Returns:
            Dictionary mapping service names to validation results
        """
        results = {}
        
        for service_name, strategy in strategies.items():
            try:
                # Extract URLs from strategy
                strategy_urls = {}
                url_attrs = ['login_url', 'artists_url', 'dashboard_url', 'portal_url', 'auth_url']
                for attr_name in url_attrs:
                    if hasattr(strategy, attr_name):
                        url = getattr(strategy, attr_name)
                        # Only include non-empty URLs
                        if url and url.strip():
                            strategy_urls[attr_name] = url
                
                # Validate URLs
                self.validate_strategy_urls(service_name, strategy_urls)
                self.check_extractor_compatibility(service_name, strategy_urls)
                results[service_name] = True
                
            except Exception as e:
                logger.error(f"❌ Validation failed for {service_name}: {e}")
                results[service_name] = False
        
        return results
    
    def get_service_requirements(self, service_name: str) -> Optional[ServiceURLConfig]:
        """Get URL requirements for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceURLConfig if found, None otherwise
        """
        return self.service_configs.get(service_name)
    
    def list_all_requirements(self) -> Dict[str, ServiceURLConfig]:
        """Get all service URL requirements.
        
        Returns:
            Dictionary mapping service names to their URL configurations
        """
        return self.service_configs.copy()


def validate_service_strategy(service_name: str, strategy_instance: object) -> bool:
    """Convenience function to validate a single strategy.
    
    Args:
        service_name: Name of the service
        strategy_instance: Strategy instance to validate
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If validation fails
    """
    validator = ServiceURLValidator()
    
    # Extract URLs from strategy
    strategy_urls = {}
    for attr_name in ['login_url', 'artists_url', 'dashboard_url', 'portal_url', 'auth_url']:
        if hasattr(strategy_instance, attr_name):
            url = getattr(strategy_instance, attr_name)
            # Only include non-empty URLs
            if url and url.strip():
                strategy_urls[attr_name] = url
    
    return validator.validate_strategy_urls(service_name, strategy_urls) 