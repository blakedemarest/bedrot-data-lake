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

REM === ENVIRONMENT SETUP ===
echo.
echo ================================================================================
echo                         BEDROT DATA LAKE PIPELINE
echo                          Starting at %date% %time%
echo ================================================================================
echo.

REM Ensure we're in the correct directory
cd /d "%~dp0.."
set "PROJECT_ROOT=%CD%"

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
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM Set log file for this run
set "LOG_FILE=%PROJECT_ROOT%\logs\pipeline_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LOG_FILE=%LOG_FILE: =0%"

echo [INFO] Project Root: %PROJECT_ROOT% >> "%LOG_FILE%"
echo [INFO] Pipeline started at %date% %time% >> "%LOG_FILE%"
echo.

REM === STEP 1: COOKIE STATUS CHECK AND AUTO-REFRESH ===
echo [STEP 1/6] ============================================ | tee -a "%LOG_FILE%"
echo [STEP 1/6] Cookie Status Check and Auto-Refresh | tee -a "%LOG_FILE%"
echo [STEP 1/6] ============================================ | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

echo [INFO] Checking current cookie status... | tee -a "%LOG_FILE%"
python cookie_status.py >> "%LOG_FILE%" 2>&1
set COOKIE_STATUS=%ERRORLEVEL%

if %COOKIE_STATUS% NEQ 0 (
    echo [INFO] Some cookies need refresh. Running auto-refresh... | tee -a "%LOG_FILE%"
    python cookie_refresh.py --refresh-all >> "%LOG_FILE%" 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Cookie refresh encountered issues. Some services may fail. | tee -a "%LOG_FILE%"
    ) else (
        echo [INFO] Cookie refresh completed successfully. | tee -a "%LOG_FILE%"
    )
) else (
    echo [INFO] All cookies are healthy. | tee -a "%LOG_FILE%"
)
echo. | tee -a "%LOG_FILE%"

REM === STEP 2: PIPELINE HEALTH CHECK WITH AUTO-REMEDIATION ===
echo [STEP 2/6] ============================================ | tee -a "%LOG_FILE%"
echo [STEP 2/6] Pipeline Health Check with Auto-Remediation | tee -a "%LOG_FILE%"
echo [STEP 2/6] ============================================ | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

echo [INFO] Running pipeline health monitor... | tee -a "%LOG_FILE%"
python src\common\pipeline_health_monitor.py --auto-remediate >> "%LOG_FILE%" 2>&1
set HEALTH_STATUS=%ERRORLEVEL%

if %HEALTH_STATUS% EQU 2 (
    echo [WARNING] Pipeline is in CRITICAL state. Review the report above. | tee -a "%LOG_FILE%"
) else if %HEALTH_STATUS% EQU 1 (
    echo [WARNING] Some services have issues. Auto-remediation attempted. | tee -a "%LOG_FILE%"
) else (
    echo [INFO] Pipeline health check passed. | tee -a "%LOG_FILE%"
)
echo. | tee -a "%LOG_FILE%"

REM === STEP 3: DATA EXTRACTION WITH INDIVIDUAL EXTRACTORS ===
echo [STEP 3/6] ============================================ | tee -a "%LOG_FILE%"
echo [STEP 3/6] Running Data Extractors | tee -a "%LOG_FILE%"
echo [INFO] Skipping data extraction (no-extractors mode) | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

echo [STEP 4/6] ============================================ | tee -a "%LOG_FILE%"
echo [STEP 4/6] Running Data Cleaners | tee -a "%LOG_FILE%"
echo [STEP 4/6] ============================================ | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

set CLEANER_FAILURES=0

for /d %%P in (src\*) do (
    REM Ignore .playwright, common, and any hidden folders
    if /I not "%%~nxP"==".playwright" if /I not "%%~nxP"=="common" if not "%%~nxP:~0,1"=="." (
        REM Run all cleaners for this platform
        if exist "%%P\cleaners" (
            echo [INFO] Running cleaners for %%~nxP | tee -a "%LOG_FILE%"
            
            REM Run cleaners in order: landing2raw, raw2staging, staging2curated
            for %%S in (landing2raw raw2staging staging2curated) do (
                if exist "%%P\cleaners\%%~nxP_%%S.py" (
                    echo [INFO]   - Running %%~nxP_%%S.py | tee -a "%LOG_FILE%"
                    python "%%P\cleaners\%%~nxP_%%S.py" >> "%LOG_FILE%" 2>&1
                    if %ERRORLEVEL% NEQ 0 (
                        echo [WARNING]   - %%~nxP_%%S.py failed | tee -a "%LOG_FILE%"
                        set /a CLEANER_FAILURES+=1
                    ) else (
                        echo [INFO]   ✓ %%~nxP_%%S.py completed | tee -a "%LOG_FILE%"
                    )
                )
            )
            echo. | tee -a "%LOG_FILE%"
        )
    )
)

echo [INFO] Data cleaning phase completed. Failures: %CLEANER_FAILURES% | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

REM === STEP 5: DATA WAREHOUSE ETL PIPELINE ===
echo [STEP 5/6] ============================================ | tee -a "%LOG_FILE%"
echo [STEP 5/6] Running Data Warehouse ETL Pipeline | tee -a "%LOG_FILE%"
echo [STEP 5/6] ============================================ | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

REM Save current directory
set "ORIGINAL_DIR=%CD%"

REM Navigate to data warehouse directory
cd /d "%PROJECT_ROOT%\..\data-warehouse"

REM Check if warehouse virtual environment exists, otherwise use data lake venv
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating data warehouse virtual environment | tee -a "%LOG_FILE%"
    call ".venv\Scripts\activate.bat"
) else (
    echo [INFO] Using data lake virtual environment for warehouse ETL | tee -a "%LOG_FILE%"
)

REM Run the warehouse ETL pipeline
echo [INFO] Running warehouse ETL pipeline... | tee -a "%LOG_FILE%"
if exist "scripts\run_all_etl.py" (
    python scripts\run_all_etl.py >> "%LOG_FILE%" 2>&1
) else if exist "run_all_etl.py" (
    python run_all_etl.py >> "%LOG_FILE%" 2>&1
) else (
    echo [ERROR] Could not find warehouse ETL script | tee -a "%LOG_FILE%"
    set WAREHOUSE_ERRORLEVEL=1
)
set WAREHOUSE_ERRORLEVEL=%ERRORLEVEL%

REM Return to original directory
cd /d "%ORIGINAL_DIR%"

REM Re-activate data lake venv if we switched
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"

REM Check warehouse ETL result
IF %WAREHOUSE_ERRORLEVEL% NEQ 0 (
    echo [ERROR] Data Warehouse ETL failed with code %WAREHOUSE_ERRORLEVEL% | tee -a "%LOG_FILE%"
) else (
    echo [INFO] ✓ Data Warehouse ETL completed successfully | tee -a "%LOG_FILE%"
)
echo. | tee -a "%LOG_FILE%"

REM === STEP 6: FINAL REPORTING AND MAINTENANCE ===
echo [STEP 6/6] ============================================ | tee -a "%LOG_FILE%"
echo [STEP 6/6] Generating Reports and Maintenance | tee -a "%LOG_FILE%"
echo [STEP 6/6] ============================================ | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

REM Run final health check
echo [INFO] Running final health check... | tee -a "%LOG_FILE%"
python src\common\pipeline_health_monitor.py >> "%LOG_FILE%" 2>&1

REM Generate visual dashboard if available
if exist "src\common\cookie_refresh\dashboard.py" (
    echo [INFO] Generating visual dashboard... | tee -a "%LOG_FILE%"
    python src\common\cookie_refresh\dashboard.py --output pipeline_status.html >> "%LOG_FILE%" 2>&1
)

REM Generate the no-extractors version
echo [INFO] Updating no-extractors cron script... | tee -a "%LOG_FILE%"

REM Archive old logs (keep last 30 days)
echo [INFO] Archiving old logs... | tee -a "%LOG_FILE%"
forfiles /p "%PROJECT_ROOT%\logs" /s /m *.log /d -30 /c "cmd /c del @path" 2>nul

echo. | tee -a "%LOG_FILE%"
echo ================================================================================ | tee -a "%LOG_FILE%"
echo                           PIPELINE SUMMARY | tee -a "%LOG_FILE%"
echo ================================================================================ | tee -a "%LOG_FILE%"
echo [INFO] Pipeline completed at %date% %time% | tee -a "%LOG_FILE%"
echo [INFO] Extraction failures: 0 (skipped) | tee -a "%LOG_FILE%"
echo [INFO] Cleaner failures: %CLEANER_FAILURES% | tee -a "%LOG_FILE%"
echo [INFO] Log file: %LOG_FILE% | tee -a "%LOG_FILE%"
echo. | tee -a "%LOG_FILE%"

set /a TOTAL_FAILURES=%CLEANER_FAILURES%
if %WAREHOUSE_ERRORLEVEL% NEQ 0 set /a TOTAL_FAILURES+=1

if %TOTAL_FAILURES% EQU 0 (
    echo [SUCCESS] ✓ All pipeline components completed successfully! | tee -a "%LOG_FILE%"
) else (
    echo [WARNING] ⚠️  Pipeline completed with %TOTAL_FAILURES% failures. | tee -a "%LOG_FILE%"
    echo [WARNING] Check the log file for details: %LOG_FILE% | tee -a "%LOG_FILE%"
)

echo. | tee -a "%LOG_FILE%"
echo [INFO] Next steps: | tee -a "%LOG_FILE%"
echo [INFO] 1. Review the pipeline health report above | tee -a "%LOG_FILE%"
echo [INFO] 2. Check failed services and refresh cookies if needed | tee -a "%LOG_FILE%"
echo [INFO] 3. View the visual dashboard: pipeline_status.html | tee -a "%LOG_FILE%"
echo [INFO] 4. Run specific extractors manually if needed | tee -a "%LOG_FILE%"
echo ================================================================================ | tee -a "%LOG_FILE%"

endlocal
echo.
echo [INFO] Press any key to exit...
pause >nul