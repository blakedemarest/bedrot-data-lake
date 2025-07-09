#!/usr/bin/env python3
"""Test script to verify all cookie refresh strategies are working correctly.

This script tests that all strategies can be imported and instantiated properly.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, PROJECT_ROOT)

from src.common.cookie_refresh.storage import CookieStorageManager
from src.common.cookie_refresh.notifier import CookieRefreshNotifier
from src.common.cookie_refresh.config import CookieRefreshConfig
from src.common.cookie_refresh.strategies import (
    DistroKidRefreshStrategy,
    SpotifyRefreshStrategy,
    TikTokRefreshStrategy,
    TooLostRefreshStrategy,
    LinktreeRefreshStrategy
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_strategy_import():
    """Test that all strategies can be imported."""
    logger.info("Testing strategy imports...")
    
    strategies = [
        ('DistroKid', DistroKidRefreshStrategy),
        ('Spotify', SpotifyRefreshStrategy),
        ('TikTok', TikTokRefreshStrategy),
        ('TooLost', TooLostRefreshStrategy),
        ('Linktree', LinktreeRefreshStrategy)
    ]
    
    for name, strategy_class in strategies:
        logger.info(f"✓ {name} strategy imported successfully")
    
    return True


def test_strategy_instantiation():
    """Test that all strategies can be instantiated."""
    logger.info("\nTesting strategy instantiation...")
    
    # Create mock components
    storage_manager = CookieStorageManager(
        base_path=Path(PROJECT_ROOT) / 'data_lake' / 'src',
        backup_path=Path(PROJECT_ROOT) / 'data_lake' / 'backups' / 'cookies'
    )
    
    notifier = CookieRefreshNotifier({
        'enabled': True,
        'console': {'enabled': True, 'log_level': 'INFO'}
    })
    
    # Test config
    test_config = {
        'browser_headless': False,
        'browser_timeout_seconds': 300,
        'screenshot_on_failure': True,
        'screenshots_dir': str(Path(PROJECT_ROOT) / 'data_lake' / 'logs' / 'screenshots'),
        'max_refresh_attempts': 3
    }
    
    strategies = [
        ('DistroKid', DistroKidRefreshStrategy),
        ('Spotify', SpotifyRefreshStrategy),
        ('TikTok', TikTokRefreshStrategy),
        ('TooLost', TooLostRefreshStrategy),
        ('Linktree', LinktreeRefreshStrategy)
    ]
    
    for name, strategy_class in strategies:
        try:
            strategy = strategy_class(
                storage_manager=storage_manager,
                notifier=notifier,
                config=test_config
            )
            logger.info(f"✓ {name} strategy instantiated successfully")
            
            # Check key attributes
            assert hasattr(strategy, 'service_name')
            assert hasattr(strategy, 'refresh_cookies')
            assert hasattr(strategy, 'validate_cookies')
            
        except Exception as e:
            logger.error(f"✗ {name} strategy failed: {e}")
            return False
    
    return True


def test_service_specific_features():
    """Test service-specific features of each strategy."""
    logger.info("\nTesting service-specific features...")
    
    # Create mock components
    storage_manager = CookieStorageManager(
        base_path=Path(PROJECT_ROOT) / 'data_lake' / 'src',
        backup_path=Path(PROJECT_ROOT) / 'data_lake' / 'backups' / 'cookies'
    )
    
    notifier = CookieRefreshNotifier({
        'enabled': True,
        'console': {'enabled': True, 'log_level': 'INFO'}
    })
    
    # DistroKid specific tests
    dk_strategy = DistroKidRefreshStrategy(storage_manager, notifier)
    assert dk_strategy.login_url == 'https://distrokid.com/signin'
    assert dk_strategy.dashboard_url == 'https://distrokid.com/stats/?data=streams'
    logger.info("✓ DistroKid: URLs configured correctly")
    
    # Spotify specific tests
    spotify_strategy = SpotifyRefreshStrategy(storage_manager, notifier)
    assert spotify_strategy.login_url == 'https://accounts.spotify.com/login'
    assert spotify_strategy.artists_url == 'https://artists.spotify.com'
    logger.info("✓ Spotify: URLs configured correctly")
    
    # TikTok specific tests
    tiktok_strategy = TikTokRefreshStrategy(storage_manager, notifier)
    assert 'pig1987' in tiktok_strategy.supported_accounts
    assert 'zone.a0' in tiktok_strategy.supported_accounts
    assert set(tiktok_strategy.required_cookies) == {'sessionid', 'sid_guard', 'uid_tt'}
    logger.info("✓ TikTok: Multi-account support and required cookies configured")
    
    # TooLost specific tests
    toolost_strategy = TooLostRefreshStrategy(storage_manager, notifier)
    assert toolost_strategy.jwt_expiration_days == 7
    assert toolost_strategy.portal_url == 'https://toolost.com/user-portal/analytics/platform'
    logger.info("✓ TooLost: JWT expiration and URLs configured correctly")
    
    # Linktree specific tests
    linktree_strategy = LinktreeRefreshStrategy(storage_manager, notifier)
    assert linktree_strategy.login_url == 'https://linktr.ee/login'
    assert linktree_strategy.dashboard_url == 'https://linktr.ee/admin'
    logger.info("✓ Linktree: URLs configured correctly")
    
    return True


def test_refresher_integration():
    """Test that strategies work with the main refresher."""
    logger.info("\nTesting refresher integration...")
    
    try:
        from src.common.cookie_refresh.refresher import CookieRefresher
        
        # Create refresher instance
        refresher = CookieRefresher()
        
        # Check that all services are loaded
        expected_services = ['spotify', 'distrokid', 'tiktok', 'toolost', 'linktree']
        loaded_services = list(refresher.services.keys())
        
        for service in expected_services:
            if service in loaded_services:
                logger.info(f"✓ {service} loaded in refresher")
                
                # Check strategy class
                service_info = refresher.services[service]
                if service_info.strategy_class:
                    logger.info(f"  - Strategy class: {service_info.strategy_class.__name__}")
                else:
                    logger.warning(f"  - No strategy class found")
            else:
                logger.warning(f"✗ {service} not loaded in refresher")
        
        return True
        
    except Exception as e:
        logger.error(f"Refresher integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Cookie Refresh Strategy Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Import Test", test_strategy_import),
        ("Instantiation Test", test_strategy_instantiation),
        ("Service Features Test", test_service_specific_features),
        ("Refresher Integration Test", test_refresher_integration)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            if test_func():
                logger.info(f"\n✓ {test_name} PASSED\n")
            else:
                logger.error(f"\n✗ {test_name} FAILED\n")
                all_passed = False
        except Exception as e:
            logger.error(f"\n✗ {test_name} FAILED with exception: {e}\n")
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("All tests PASSED!")
    else:
        logger.error("Some tests FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()