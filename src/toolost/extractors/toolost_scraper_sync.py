#!/usr/bin/env python3
"""
Synchronous wrapper for the async TooLost scraper.
This allows it to be called from the batch file cron job.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the async TooLost scraper using subprocess."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    async_script = script_dir / "toolost_scraper.py"
    
    if not async_script.exists():
        print(f"ERROR: Async script not found at {async_script}")
        sys.exit(1)
    
    # Run the async script as a subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(async_script)],
            capture_output=True,
            text=True,
            cwd=os.environ.get('PROJECT_ROOT', Path(__file__).parents[3])
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Exit with same code as subprocess
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"ERROR: Failed to run TooLost scraper: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()