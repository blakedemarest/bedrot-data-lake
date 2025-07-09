@echo off
setlocal EnableDelayedExpansion

REM ================================================================================
REM                       BEDROT DATA LAKE MASTER PIPELINE
REM           Comprehensive ETL with Cookie Management and Health Monitoring
REM ================================================================================
REM This is the main consolidated pipeline that handles:
REM - Cookie status checking and auto-refresh
REM - Pipeline health monitoring with auto-remediation
REM - Individual service extractors (no integrated_extractor.py)
REM - Data cleaning pipeline
REM - Data warehouse ETL
REM - Comprehensive reporting
REM ================================================================================

REM === EARLY ERROR CATCHING ===
if "%~1"=="--help" (
    echo Usage: run_datalake_cron.bat [--skip-extractors]
    echo.
    echo Options:
    echo   --skip-extractors    Skip data extraction, only run cleaners
    echo   --help              Show this help message
    exit /b 0
)

REM === ENVIRONMENT SETUP ===
echo.
echo ================================================================================
echo                         BEDROT DATA LAKE PIPELINE
echo                          Starting at %date% %time%
echo ================================================================================
echo.

REM Ensure we're in the correct directory
echo [DEBUG] Changing to project directory...
cd /d "%~dp0.."
if errorlevel 1 (
    echo [ERROR] Failed to change directory!
    pause
    exit /b 1
)
set "PROJECT_ROOT=%CD%"
echo [DEBUG] PROJECT_ROOT: %PROJECT_ROOT%

REM === Ensure .venv exists and is ready ===
IF NOT EXIST "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    echo [INFO] Python virtual environment not found. Creating .venv...
    python -m venv "%PROJECT_ROOT%\.venv"
    echo [INFO] Installing requirements...
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
    pip install --upgrade pip
    pip install -r "%PROJECT_ROOT%\requirements.txt"
    deactivate
)

REM === Activate the venv ===
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"

REM Load environment variables from .env
if exist "%PROJECT_ROOT%\.env" (
    for /f "usebackq tokens=1,2 delims==" %%i in ("%PROJECT_ROOT%\.env") do set %%i=%%j
)

REM Expose src/ on PYTHONPATH so 'from common...' works in all child scripts
set "PYTHONPATH=%PROJECT_ROOT%\src;%PYTHONPATH%"

REM Create logs directory if it doesn't exist
if not exist "%PROJECT_ROOT%\logs" (
    echo Creating logs directory...
    mkdir "%PROJECT_ROOT%\logs"
)

REM Set log file for this run - use simple timestamp
set HOUR=%time:~0,2%
set HOUR=%HOUR: =0%
set "LOG_FILE=%PROJECT_ROOT%\logs\pipeline_%date:~-4%%date:~4,2%%date:~7,2%_%HOUR%%time:~3,2%%time:~6,2%.log"

REM Test if we can write to the log file
echo [INFO] Pipeline started at %date% %time% > "%LOG_FILE%" 2>nul
if errorlevel 1 (
    echo WARNING: Cannot write to log file. Continuing without logging...
    set "LOG_FILE=nul"
) else (
    echo Log file created: %LOG_FILE%
    echo [INFO] Project Root: %PROJECT_ROOT% >> "%LOG_FILE%"
)
echo.

REM === STEP 1: COOKIE STATUS CHECK AND AUTO-REFRESH ===
echo [STEP 1/6] ============================================
echo [STEP 1/6] ============================================ >> "%LOG_FILE%"
echo [STEP 1/6] Cookie Status Check and Auto-Refresh
echo [STEP 1/6] Cookie Status Check and Auto-Refresh >> "%LOG_FILE%"
echo [STEP 1/6] ============================================
echo [STEP 1/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

echo [INFO] Checking current cookie status...
echo [INFO] Checking current cookie status... >> "%LOG_FILE%"
python cookie_status.py >> "%LOG_FILE%" 2>&1
set COOKIE_STATUS=%ERRORLEVEL%

if %COOKIE_STATUS% NEQ 0 (
    echo [INFO] Some cookies need refresh. Attempting auto-refresh...
    echo [INFO] Some cookies need refresh. Attempting auto-refresh... >> "%LOG_FILE%"
    python cookie_refresh.py --refresh-all >> "%LOG_FILE%" 2>&1
    set REFRESH_RESULT=!ERRORLEVEL!
    if !REFRESH_RESULT! NEQ 0 (
        echo [WARNING] Cookie refresh encountered issues. Some services may fail.
        echo [WARNING] Cookie refresh encountered issues. Some services may fail. >> "%LOG_FILE%"
        echo [WARNING] You may need to manually refresh cookies for some services.
        echo [WARNING] You may need to manually refresh cookies for some services. >> "%LOG_FILE%"
    ) else (
        echo [INFO] Cookie refresh completed successfully.
        echo [INFO] Cookie refresh completed successfully. >> "%LOG_FILE%"
    )
) else (
    echo [INFO] All cookies are healthy.
    echo [INFO] All cookies are healthy. >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM === STEP 2: PIPELINE HEALTH CHECK WITH AUTO-REMEDIATION ===
echo [STEP 2/6] ============================================
echo [STEP 2/6] ============================================ >> "%LOG_FILE%"
echo [STEP 2/6] Pipeline Health Check with Auto-Remediation
echo [STEP 2/6] Pipeline Health Check with Auto-Remediation >> "%LOG_FILE%"
echo [STEP 2/6] ============================================
echo [STEP 2/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

echo [INFO] Running pipeline health monitor...
echo [INFO] Running pipeline health monitor... >> "%LOG_FILE%"
python src\common\pipeline_health_monitor.py >> "%LOG_FILE%" 2>&1
set HEALTH_STATUS=%ERRORLEVEL%

if %HEALTH_STATUS% EQU 2 (
    echo [WARNING] Pipeline is in CRITICAL state. Review the report above.
echo [WARNING] Pipeline is in CRITICAL state. Review the report above. >> "%LOG_FILE%"
) else if %HEALTH_STATUS% EQU 1 (
    echo [WARNING] Some services have issues. Auto-remediation attempted.
echo [WARNING] Some services have issues. Auto-remediation attempted. >> "%LOG_FILE%"
) else (
    echo [INFO] Pipeline health check passed.
echo [INFO] Pipeline health check passed. >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM === STEP 3: DATA EXTRACTION WITH INDIVIDUAL EXTRACTORS ===
echo [STEP 3/6] ============================================
echo [STEP 3/6] ============================================ >> "%LOG_FILE%"
echo [STEP 3/6] Running Data Extractors
echo [STEP 3/6] Running Data Extractors >> "%LOG_FILE%"
echo [STEP 3/6] ============================================
echo [STEP 3/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM Track extraction results
set EXTRACTION_FAILURES=0

REM --- Spotify Extractor ---
echo [INFO] Running Spotify extractor...
echo [INFO] Running Spotify extractor... >> "%LOG_FILE%"
python src\spotify\extractors\spotify_audience_extractor.py >> "%LOG_FILE%" 2>&1
set SPOTIFY_RESULT=%ERRORLEVEL%
if %SPOTIFY_RESULT% NEQ 0 (
    echo [WARNING] Spotify extraction failed (exit code: %SPOTIFY_RESULT%)
echo [WARNING] Spotify extraction failed (exit code: %SPOTIFY_RESULT%) >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] ✓ Spotify extraction completed
echo [INFO] ✓ Spotify extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- DistroKid Extractor ---
echo [INFO] Running DistroKid extractor...
echo [INFO] Running DistroKid extractor... >> "%LOG_FILE%"
python src\distrokid\extractors\dk_auth.py >> "%LOG_FILE%" 2>&1
set DISTROKID_RESULT=%ERRORLEVEL%
if %DISTROKID_RESULT% NEQ 0 (
    echo [WARNING] DistroKid extraction failed (exit code: %DISTROKID_RESULT%)
    echo [WARNING] DistroKid extraction failed (exit code: %DISTROKID_RESULT%) >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] ✓ DistroKid extraction completed
echo [INFO] ✓ DistroKid extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- TikTok Extractors (Multiple Accounts) ---
echo [INFO] Running TikTok extractors...
echo [INFO] Running TikTok extractors... >> "%LOG_FILE%"

echo [INFO] - TikTok Zone A0 account...
echo [INFO] - TikTok Zone A0 account... >> "%LOG_FILE%"
python src\tiktok\extractors\tiktok_analytics_extractor_zonea0.py >> "%LOG_FILE%" 2>&1
set TIKTOK_ZONEA0_RESULT=%ERRORLEVEL%
if %TIKTOK_ZONEA0_RESULT% NEQ 0 (
    echo [WARNING] TikTok Zone A0 extraction failed (exit code: %TIKTOK_ZONEA0_RESULT%)
    echo [WARNING] TikTok Zone A0 extraction failed (exit code: %TIKTOK_ZONEA0_RESULT%) >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] ✓ TikTok Zone A0 extraction completed
echo [INFO] ✓ TikTok Zone A0 extraction completed >> "%LOG_FILE%"
)

echo [INFO] - TikTok PIG1987 account...
echo [INFO] - TikTok PIG1987 account... >> "%LOG_FILE%"
python src\tiktok\extractors\tiktok_analytics_extractor_pig1987.py >> "%LOG_FILE%" 2>&1
set TIKTOK_PIG_RESULT=%ERRORLEVEL%
if %TIKTOK_PIG_RESULT% NEQ 0 (
    echo [WARNING] TikTok PIG1987 extraction failed (exit code: %TIKTOK_PIG_RESULT%)
    echo [WARNING] TikTok PIG1987 extraction failed (exit code: %TIKTOK_PIG_RESULT%) >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] ✓ TikTok PIG1987 extraction completed
echo [INFO] ✓ TikTok PIG1987 extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- TooLost Extractor (with fallback) ---
echo [INFO] Running TooLost extractor...
echo [INFO] Running TooLost extractor... >> "%LOG_FILE%"
python src\toolost\extractors\toolost_scraper_automated.py >> "%LOG_FILE%" 2>&1
set TOOLOST_RESULT=%ERRORLEVEL%
if %TOOLOST_RESULT% NEQ 0 (
    echo [WARNING] TooLost automated extraction failed, trying manual scraper...
    echo [WARNING] TooLost automated extraction failed, trying manual scraper... >> "%LOG_FILE%"
    python src\toolost\extractors\toolost_scraper.py >> "%LOG_FILE%" 2>&1
    set TOOLOST_MANUAL_RESULT=!ERRORLEVEL!
    if !TOOLOST_MANUAL_RESULT! NEQ 0 (
        echo [WARNING] TooLost extraction failed (both methods)
echo [WARNING] TooLost extraction failed (both methods) >> "%LOG_FILE%"
        set /a EXTRACTION_FAILURES+=1
    ) else (
        echo [INFO] ✓ TooLost extraction completed (manual method)
echo [INFO] ✓ TooLost extraction completed (manual method) >> "%LOG_FILE%"
    )
) else (
    echo [INFO] ✓ TooLost extraction completed
echo [INFO] ✓ TooLost extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- Linktree Extractor ---
echo [INFO] Running Linktree extractor...
echo [INFO] Running Linktree extractor... >> "%LOG_FILE%"
python src\linktree\extractors\linktree_analytics_extractor.py >> "%LOG_FILE%" 2>&1
set LINKTREE_RESULT=%ERRORLEVEL%
if %LINKTREE_RESULT% NEQ 0 (
    echo [WARNING] Linktree extraction failed (exit code: %LINKTREE_RESULT%)
    echo [WARNING] Linktree extraction failed (exit code: %LINKTREE_RESULT%) >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] ✓ Linktree extraction completed
echo [INFO] ✓ Linktree extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- MetaAds Extractor ---
echo [INFO] Running MetaAds extractor...
echo [INFO] Running MetaAds extractor... >> "%LOG_FILE%"
python src\metaads\extractors\meta_daily_campaigns_extractor.py >> "%LOG_FILE%" 2>&1
set METAADS_RESULT=%ERRORLEVEL%
if %METAADS_RESULT% NEQ 0 (
    echo [WARNING] MetaAds extraction failed (exit code: %METAADS_RESULT%)
    echo [WARNING] MetaAds extraction failed (exit code: %METAADS_RESULT%) >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] ✓ MetaAds extraction completed
echo [INFO] ✓ MetaAds extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

echo [INFO] Data extraction phase completed. Failures: %EXTRACTION_FAILURES%
echo [INFO] Data extraction phase completed. Failures: %EXTRACTION_FAILURES% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM === STEP 4: DATA CLEANING PIPELINE ===
echo [STEP 4/6] ============================================
echo [STEP 4/6] ============================================ >> "%LOG_FILE%"
echo [STEP 4/6] Running Data Cleaners
echo [STEP 4/6] Running Data Cleaners >> "%LOG_FILE%"
echo [STEP 4/6] ============================================
echo [STEP 4/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

set CLEANER_FAILURES=0

for /d %%P in (src\*) do (
    REM Ignore .playwright, common, and any hidden folders
    if /I not "%%~nxP"==".playwright" if /I not "%%~nxP"=="common" if not "%%~nxP:~0,1"=="." (
        REM Run all cleaners for this platform
        if exist "%%P\cleaners" (
            echo [INFO] Running cleaners for %%~nxP
echo [INFO] Running cleaners for %%~nxP >> "%LOG_FILE%"
            
            REM Run cleaners in order: landing2raw, raw2staging, staging2curated
            for %%S in (landing2raw raw2staging staging2curated) do (
                if exist "%%P\cleaners\%%~nxP_%%S.py" (
                    echo [INFO]   - Running %%~nxP_%%S.py
                    echo [INFO]   - Running %%~nxP_%%S.py >> "%LOG_FILE%"
                    python "%%P\cleaners\%%~nxP_%%S.py" >> "%LOG_FILE%" 2>&1
                    set CLEANER_RESULT=!ERRORLEVEL!
                    if !CLEANER_RESULT! NEQ 0 (
                        echo [WARNING]   - %%~nxP_%%S.py failed
                        echo [WARNING]   - %%~nxP_%%S.py failed >> "%LOG_FILE%"
                        set /a CLEANER_FAILURES+=1
                    ) else (
                        echo [INFO]   ✓ %%~nxP_%%S.py completed
                        echo [INFO]   ✓ %%~nxP_%%S.py completed >> "%LOG_FILE%"
                    )
                )
            )
            echo.
echo. >> "%LOG_FILE%"
        )
    )
)

echo [INFO] Data cleaning phase completed. Failures: %CLEANER_FAILURES%
echo [INFO] Data cleaning phase completed. Failures: %CLEANER_FAILURES% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM === STEP 5: DATA WAREHOUSE ETL PIPELINE ===
echo [STEP 5/6] ============================================
echo [STEP 5/6] ============================================ >> "%LOG_FILE%"
echo [STEP 5/6] Running Data Warehouse ETL Pipeline
echo [STEP 5/6] Running Data Warehouse ETL Pipeline >> "%LOG_FILE%"
echo [STEP 5/6] ============================================
echo [STEP 5/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM Save current directory
set "ORIGINAL_DIR=%CD%"

REM Navigate to data warehouse directory
cd /d "%PROJECT_ROOT%\..\data-warehouse"

REM Check if warehouse virtual environment exists, otherwise use data lake venv
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating data warehouse virtual environment
echo [INFO] Activating data warehouse virtual environment >> "%LOG_FILE%"
    call ".venv\Scripts\activate.bat"
) else (
    echo [INFO] Using data lake virtual environment for warehouse ETL
echo [INFO] Using data lake virtual environment for warehouse ETL >> "%LOG_FILE%"
)

REM Run the warehouse ETL pipeline
echo [INFO] Running warehouse ETL pipeline...
echo [INFO] Running warehouse ETL pipeline... >> "%LOG_FILE%"
if exist "scripts\run_all_etl.py" (
    python scripts\run_all_etl.py >> "%LOG_FILE%" 2>&1
) else if exist "run_all_etl.py" (
    python run_all_etl.py >> "%LOG_FILE%" 2>&1
) else (
    echo [ERROR] Could not find warehouse ETL script
echo [ERROR] Could not find warehouse ETL script >> "%LOG_FILE%"
    set WAREHOUSE_ERRORLEVEL=1
)
set WAREHOUSE_ERRORLEVEL=%ERRORLEVEL%

REM Return to original directory
cd /d "%ORIGINAL_DIR%"

REM Re-activate data lake venv if we switched
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"

REM Check warehouse ETL result
IF %WAREHOUSE_ERRORLEVEL% NEQ 0 (
    echo [ERROR] Data Warehouse ETL failed with code %WAREHOUSE_ERRORLEVEL%
echo [ERROR] Data Warehouse ETL failed with code %WAREHOUSE_ERRORLEVEL% >> "%LOG_FILE%"
) else (
    echo [INFO] ✓ Data Warehouse ETL completed successfully
echo [INFO] ✓ Data Warehouse ETL completed successfully >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM === STEP 6: FINAL REPORTING AND MAINTENANCE ===
echo [STEP 6/6] ============================================
echo [STEP 6/6] ============================================ >> "%LOG_FILE%"
echo [STEP 6/6] Generating Reports and Maintenance
echo [STEP 6/6] Generating Reports and Maintenance >> "%LOG_FILE%"
echo [STEP 6/6] ============================================
echo [STEP 6/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM Run final health check
echo [INFO] Running final health check...
echo [INFO] Running final health check... >> "%LOG_FILE%"
python src\common\pipeline_health_monitor.py >> "%LOG_FILE%" 2>&1

REM Generate visual dashboard if available
if exist "src\common\cookie_refresh\dashboard.py" (
    echo [INFO] Generating visual dashboard...
echo [INFO] Generating visual dashboard... >> "%LOG_FILE%"
    python src\common\cookie_refresh\dashboard.py --output pipeline_status.html >> "%LOG_FILE%" 2>&1
)

REM Skip generating no-extractors version to prevent infinite loop

REM Archive old logs (keep last 30 days)
echo [INFO] Archiving old logs...
echo [INFO] Archiving old logs... >> "%LOG_FILE%"
forfiles /p "%PROJECT_ROOT%\logs" /s /m *.log /d -30 /c "cmd /c del @path" 2>nul

echo.
echo. >> "%LOG_FILE%"
echo ================================================================================
echo ================================================================================ >> "%LOG_FILE%"
echo                           PIPELINE SUMMARY
echo                           PIPELINE SUMMARY >> "%LOG_FILE%"
echo ================================================================================
echo ================================================================================ >> "%LOG_FILE%"
echo [INFO] Pipeline completed at %date% %time%
echo [INFO] Pipeline completed at %date% %time% >> "%LOG_FILE%"
echo [INFO] Extraction failures: %EXTRACTION_FAILURES%
echo [INFO] Extraction failures: %EXTRACTION_FAILURES% >> "%LOG_FILE%"
echo [INFO] Cleaner failures: %CLEANER_FAILURES%
echo [INFO] Cleaner failures: %CLEANER_FAILURES% >> "%LOG_FILE%"
echo [INFO] Log file: %LOG_FILE%
echo [INFO] Log file: %LOG_FILE% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

set /a TOTAL_FAILURES=%EXTRACTION_FAILURES%+%CLEANER_FAILURES%
if %WAREHOUSE_ERRORLEVEL% NEQ 0 set /a TOTAL_FAILURES+=1

if %TOTAL_FAILURES% EQU 0 (
    echo [SUCCESS] ✓ All pipeline components completed successfully!
echo [SUCCESS] ✓ All pipeline components completed successfully! >> "%LOG_FILE%"
) else (
    echo [WARNING] ⚠️  Pipeline completed with %TOTAL_FAILURES% failures.
echo [WARNING] ⚠️  Pipeline completed with %TOTAL_FAILURES% failures. >> "%LOG_FILE%"
    echo [WARNING] Check the log file for details: %LOG_FILE%
echo [WARNING] Check the log file for details: %LOG_FILE% >> "%LOG_FILE%"
)

echo.
echo. >> "%LOG_FILE%"
echo [INFO] Next steps:
echo [INFO] Next steps: >> "%LOG_FILE%"
echo [INFO] 1. Review the pipeline health report above
echo [INFO] 1. Review the pipeline health report above >> "%LOG_FILE%"
echo [INFO] 2. Check failed services and refresh cookies if needed
echo [INFO] 2. Check failed services and refresh cookies if needed >> "%LOG_FILE%"
echo [INFO] 3. View the visual dashboard: pipeline_status.html
echo [INFO] 3. View the visual dashboard: pipeline_status.html >> "%LOG_FILE%"
echo [INFO] 4. Run specific extractors manually if needed
echo [INFO] 4. Run specific extractors manually if needed >> "%LOG_FILE%"
echo ================================================================================
echo ================================================================================ >> "%LOG_FILE%"

endlocal
echo.
echo [INFO] Press any key to exit...
pause >nul