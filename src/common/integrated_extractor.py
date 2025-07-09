#!/usr/bin/env python3
"""
Integrated Data Lake Extractor with Seamless Cookie Management

This module provides a unified interface that combines data extraction with 
automatic cookie refresh. When an extractor fails due to authentication issues,
it automatically triggers cookie refresh and retries extraction.

This is the core of our data lake's resilience system.
"""

import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parents[1]))

from common.cookie_refresh.refresher import CookieRefresher
from common.cookie_refresh.storage import AuthStateInfo

logger = logging.getLogger(__name__)


class ExtractionResult:
    """Result of an extraction attempt."""
    
    def __init__(self, service: str, extractor_path: str, success: bool, 
                 message: str, cookie_refresh_attempted: bool = False,
                 retry_after_refresh: bool = False):
        self.service = service
        self.extractor_path = extractor_path
        self.success = success
        self.message = message
        self.cookie_refresh_attempted = cookie_refresh_attempted
        self.retry_after_refresh = retry_after_refresh
        self.timestamp = datetime.now()
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        refresh_info = ""
        if self.cookie_refresh_attempted:
            refresh_info = " (refreshed cookies)" if self.retry_after_refresh else " (refresh failed)"
        return f"{status} {self.service}: {self.message}{refresh_info}"


class IntegratedExtractor:
    """
    Unified extractor that seamlessly handles both data extraction and cookie management.
    
    This class automatically:
    1. Checks cookie status before extraction
    2. Runs extractors with existing cookies
    3. Detects authentication failures
    4. Triggers automatic cookie refresh
    5. Retries extraction after successful refresh
    6. Provides detailed logging and error reporting
    """
    
    def __init__(self, config_path: Optional[str] = None, max_retries: int = 2):
        self.cookie_refresher = CookieRefresher(config_path)
        self.max_retries = max_retries
        self.results: List[ExtractionResult] = []
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _run_extractor_script(self, script_path: str, timeout: int = 300) -> Tuple[bool, str]:
        """
        Run an extractor script and return success status and output.
        
        Args:
            script_path: Path to the extractor script
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, output_message)
        """
        try:
            logger.info(f"Running extractor: {script_path}")
            
            # Run the extractor script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(script_path).parent.parent.parent  # data_lake directory
            )
            
            # Check result
            if result.returncode == 0:
                logger.info(f"Extractor completed successfully: {script_path}")
                return True, "Extraction successful"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.warning(f"Extractor failed: {script_path} - {error_msg}")
                return False, f"Extraction failed: {error_msg[:200]}"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Extractor timed out: {script_path}")
            return False, f"Extraction timed out after {timeout}s"
        except Exception as e:
            logger.error(f"Error running extractor {script_path}: {e}")
            return False, f"Error running extractor: {str(e)}"
    
    def _is_auth_failure(self, error_message: str) -> bool:
        """
        Determine if an error is likely due to authentication/cookie issues.
        
        Args:
            error_message: Error message from extractor
            
        Returns:
            True if likely authentication failure
        """
        auth_indicators = [
            "login", "authentication", "unauthorized", "forbidden",
            "expired", "cookie", "session", "token", "signin", "sign-in",
            "redirect", "permission denied", "access denied", "401", "403",
            "csrf", "captcha"
        ]
        
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in auth_indicators)
    
    def _should_attempt_refresh(self, service: str, error_message: str) -> bool:
        """
        Determine if we should attempt cookie refresh for this service.
        
        Args:
            service: Service name
            error_message: Error message from extraction attempt
            
        Returns:
            True if refresh should be attempted
        """
        # Check if this looks like an auth failure
        if not self._is_auth_failure(error_message):
            return False
        
        # Check if service supports cookie refresh
        if service not in self.cookie_refresher.services:
            logger.warning(f"Service {service} not configured for cookie refresh")
            return False
        
        return True
    
    def extract_with_resilience(self, service: str, extractor_path: str, 
                              account: Optional[str] = None) -> ExtractionResult:
        """
        Run extraction with automatic cookie refresh on auth failure.
        
        Args:
            service: Service name (e.g., 'toolost', 'tiktok')
            extractor_path: Path to the extractor script
            account: Account name for multi-account services
            
        Returns:
            ExtractionResult with detailed information
        """
        logger.info(f"Starting resilient extraction for {service}")
        
        attempt = 1
        cookie_refresh_attempted = False
        retry_after_refresh = False
        
        while attempt <= self.max_retries:
            logger.info(f"Extraction attempt {attempt}/{self.max_retries} for {service}")
            
            # Run the extractor
            success, message = self._run_extractor_script(extractor_path)
            
            if success:
                # Success - we're done
                result = ExtractionResult(
                    service=service,
                    extractor_path=extractor_path,
                    success=True,
                    message=message,
                    cookie_refresh_attempted=cookie_refresh_attempted,
                    retry_after_refresh=retry_after_refresh
                )
                self.results.append(result)
                return result
            
            # Extraction failed - check if we should attempt refresh
            if attempt < self.max_retries and self._should_attempt_refresh(service, message):
                logger.info(f"Auth failure detected for {service}, attempting cookie refresh...")
                
                try:
                    # Attempt cookie refresh
                    refresh_result = self.cookie_refresher.refresh_service(service, account, force=False)
                    cookie_refresh_attempted = True
                    
                    if refresh_result.success:
                        logger.info(f"Cookie refresh successful for {service}, retrying extraction...")
                        retry_after_refresh = True
                        # Wait a moment for cookies to settle
                        time.sleep(2)
                    else:
                        logger.error(f"Cookie refresh failed for {service}: {refresh_result.message}")
                        # Continue to next attempt anyway - maybe it's a different issue
                        
                except Exception as e:
                    logger.error(f"Error during cookie refresh for {service}: {e}")
            
            attempt += 1
            
            # Add delay between attempts
            if attempt <= self.max_retries:
                time.sleep(5)
        
        # All attempts failed
        final_message = f"All {self.max_retries} attempts failed: {message}"
        if cookie_refresh_attempted and not retry_after_refresh:
            final_message += " (cookie refresh also failed)"
        
        result = ExtractionResult(
            service=service,
            extractor_path=extractor_path,
            success=False,
            message=final_message,
            cookie_refresh_attempted=cookie_refresh_attempted,
            retry_after_refresh=retry_after_refresh
        )
        self.results.append(result)
        return result
    
    def run_service_extractors(self, service_config: Dict[str, List[str]]) -> Dict[str, List[ExtractionResult]]:
        """
        Run all extractors for specified services.
        
        Args:
            service_config: Dict mapping service names to list of extractor paths
            
        Returns:
            Dict mapping service names to list of extraction results
        """
        logger.info("Starting integrated extraction pipeline...")
        
        all_results = {}
        
        for service, extractor_paths in service_config.items():
            logger.info(f"Processing service: {service}")
            service_results = []
            
            for extractor_path in extractor_paths:
                # Determine account from path if applicable (e.g., pig1987, zonea0)
                account = None
                if 'pig1987' in extractor_path:
                    account = 'pig1987'
                elif 'zonea0' in extractor_path:
                    account = 'zonea0'
                
                result = self.extract_with_resilience(service, extractor_path, account)
                service_results.append(result)
                
                # Add delay between extractors
                time.sleep(2)
            
            all_results[service] = service_results
            logger.info(f"Completed {service}: {len(service_results)} extractors processed")
        
        return all_results
    
    def get_summary(self) -> Dict[str, any]:
        """Get extraction summary statistics."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        refreshed = sum(1 for r in self.results if r.cookie_refresh_attempted)
        
        return {
            'total_extractors': total,
            'successful': successful,
            'failed': failed,
            'cookie_refreshes_attempted': refreshed,
            'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%"
        }
    
    def print_results(self):
        """Print detailed results to console."""
        print("\n" + "="*80)
        print("INTEGRATED EXTRACTION RESULTS")
        print("="*80)
        
        for result in self.results:
            print(result)
        
        print("\n" + "-"*80)
        summary = self.get_summary()
        print(f"SUMMARY: {summary['successful']}/{summary['total_extractors']} successful "
              f"({summary['success_rate']}) | {summary['cookie_refreshes_attempted']} cookie refreshes")
        print("-"*80)


def create_service_extractor_config() -> Dict[str, List[str]]:
    """
    Create the configuration mapping services to their extractor scripts.
    
    Returns:
        Dict mapping service names to lists of extractor script paths
    """
    base_path = Path(__file__).parents[1]  # src/ directory
    
    config = {
        'toolost': [
            str(base_path / 'toolost' / 'extractors' / 'toolost_scraper_cron.py')
        ],
        'tiktok': [
            str(base_path / 'tiktok' / 'extractors' / 'tiktok_analytics_extractor_pig1987.py'),
            str(base_path / 'tiktok' / 'extractors' / 'tiktok_analytics_extractor_zonea0.py')
        ],
        'linktree': [
            str(base_path / 'linktree' / 'extractors' / 'linktree_analytics_extractor.py')
        ],
        'distrokid': [
            str(base_path / 'distrokid' / 'extractors' / 'dk_auth.py')
        ]
    }
    
    # Filter to only include existing files
    filtered_config = {}
    for service, paths in config.items():
        existing_paths = [p for p in paths if Path(p).exists()]
        if existing_paths:
            filtered_config[service] = existing_paths
        else:
            logger.warning(f"No extractors found for service {service}")
    
    return filtered_config


def main():
    """Main entry point for integrated extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description='BEDROT Integrated Data Lake Extractor')
    parser.add_argument('--service', help='Extract data for specific service only')
    parser.add_argument('--config', help='Path to cookie refresh configuration file')
    parser.add_argument('--max-retries', type=int, default=2, help='Maximum retry attempts per extractor')
    
    args = parser.parse_args()
    
    # Create extractor
    extractor = IntegratedExtractor(args.config, args.max_retries)
    
    # Get service configuration
    service_config = create_service_extractor_config()
    
    if args.service:
        # Run single service
        if args.service not in service_config:
            print(f"Error: Service '{args.service}' not found. Available: {list(service_config.keys())}")
            sys.exit(1)
        
        service_config = {args.service: service_config[args.service]}
    
    # Run extractions
    results = extractor.run_service_extractors(service_config)
    
    # Print results
    extractor.print_results()
    
    # Exit with error if any extractions failed
    summary = extractor.get_summary()
    if summary['failed'] > 0:
        print(f"\nWARNING: {summary['failed']} extractors failed")
        sys.exit(1)
    else:
        print(f"\nSUCCESS: All {summary['successful']} extractors completed successfully")


if __name__ == '__main__':
    main() 