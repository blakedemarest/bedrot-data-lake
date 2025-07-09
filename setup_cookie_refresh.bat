@echo off
REM =========================================================
REM BEDROT Cookie Refresh System - Setup & Integration
REM =========================================================
REM This script sets up and integrates the cookie refresh
REM system into your existing pipeline
REM =========================================================

echo.
echo =========================================================
echo BEDROT Cookie Refresh System Setup
echo =========================================================
echo.

REM Get the directory where this script is located
set PROJECT_ROOT=%~dp0

REM Change to project directory
cd /d "%PROJECT_ROOT%"

echo [1/5] Creating required directories...
if not exist "logs\cookie_refresh" mkdir "logs\cookie_refresh"
if not exist "config" mkdir "config"
if not exist "dashboards" mkdir "dashboards"
echo Done.

echo.
echo [2/5] Checking Python environment...
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python --version

echo.
echo [3/5] Installing required packages...
pip install playwright apscheduler pyyaml email-validator structlog colorama requests --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/5] Installing Playwright browser...
playwright install chromium --with-deps
if errorlevel 1 (
    echo WARNING: Playwright browser installation failed
    echo You may need to run this manually later
)

echo.
echo [5/5] Running validation...
python cookie_refresh.py --check
if errorlevel 1 (
    echo.
    echo WARNING: Some cookies need attention
    echo This is normal for first run
)

echo.
echo =========================================================
echo Setup Complete!
echo =========================================================
echo.
echo Next Steps:
echo.
echo 1. Check cookie status:
echo    cronjob\cookie_check.bat
echo.
echo 2. Refresh specific service (e.g., TooLost):
echo    python cookie_refresh.py --refresh toolost
echo.
echo 3. Set up automated refresh:
echo    - Add to Windows Task Scheduler: cronjob\cookie_refresh_auto.bat
echo    - Or add to your pipeline: call cronjob\cookie_check.bat
echo.
echo 4. Integration with run_bedrot_pipeline.bat:
echo    Add this line after health check:
echo    call cronjob\cookie_check.bat
echo.

REM Create integration snippet
echo Creating integration snippet...
echo. > integration_snippet.txt
echo REM Add this to run_bedrot_pipeline.bat after health check: >> integration_snippet.txt
echo. >> integration_snippet.txt
echo echo. >> integration_snippet.txt
echo echo ======================================================================== >> integration_snippet.txt
echo echo STEP 1.5: COOKIE REFRESH CHECK >> integration_snippet.txt
echo echo ======================================================================== >> integration_snippet.txt
echo call cronjob\cookie_check.bat >> integration_snippet.txt
echo if errorlevel 1 ( >> integration_snippet.txt
echo     echo WARNING: Some cookies may need refresh >> integration_snippet.txt
echo     echo Run: python cookie_refresh.py --refresh SERVICE_NAME >> integration_snippet.txt
echo ) >> integration_snippet.txt
echo. >> integration_snippet.txt

echo.
echo Integration snippet saved to: integration_snippet.txt
echo.

pause