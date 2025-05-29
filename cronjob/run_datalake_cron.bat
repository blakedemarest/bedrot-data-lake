@echo off

REM === Ensure .venv exists and is ready ===
IF NOT EXIST "%~dp0..\.venv\Scripts\activate.bat" (
    echo [INFO] Python virtual environment not found. Creating .venv...
    python -m venv "%~dp0..\.venv"
    echo [INFO] Installing requirements...
    call "%~dp0..\.venv\Scripts\activate.bat"
    pip install --upgrade pip
    pip install -r "%~dp0..\requirements.txt"
    deactivate
)

REM === Activate the venv ===
call "%~dp0..\.venv\Scripts\activate.bat"
REM Master Data Lake Cron Job
REM Uses PROJECT_ROOT from .env for all relative paths

REM Load environment variables
for /f "usebackq tokens=1,2 delims==" %%i in ("%~dp0..\.env") do set %%i=%%j

REM Change to project root directory
cd /d "%PROJECT_ROOT%"

REM 1a. Meta Ads Extraction
REM 1a.1 Runs the Meta Ads pipeline Python script
python src\metaads\extractors\meta_raw_dump.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 2a. DistroKid Auth & Download
REM 2a.1 DistroKid Auth & Download
python src\distrokid\extractors\dk_auth.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 2b. DistroKid HTML Validation
REM 2b.1 DistroKid HTML Validation
python src\distrokid\cleaners\validate_dk_html.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 2c. DistroKid Dataset Cleaner
REM 2c.1 DistroKid Dataset Cleaner
python src\distrokid\cleaners\distrokid_dataset_cleaner.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 2d. Process DistroKid Bank Details (2025-05-27-dk_bank_details_etl)
REM 2d.1 Process DistroKid Bank Details
python src\distrokid\cleaners\process_dk_bank_details.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 3a. TooLost Scraper
REM 3a.1 TooLost Scraper
python src\toolost\extractors\toolost_scraper.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 3b. TooLost JSON Validation
REM 3b.1 Finds the latest TooLost JSON files and validates them
python src\toolost\cleaners\validate_toolost_json.py %LATEST_SPOTIFY% %LATEST_APPLE%
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
python src\toolost\extractors\validate_toolost_json.py %LATEST_SPOTIFY% %LATEST_APPLE%
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 7. TooLost Dataset Cleaner
REM Consolidates and cleans TooLost streaming data, producing a staging CSV for analytics (now outputs to /staging)
python src\toolost\cleaners\toolost_dataset_cleaner.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 6a. TikTok Extractors
REM 6a.1 Extract TikTok analytics for ZONE A0
python src\tiktok\extractors\tiktok_analytics_extractor_zonea0.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
REM 6a.2 Extract TikTok analytics for PIG1987
python src\tiktok\extractors\tiktok_analytics_extractor_pig1987.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 6b. TikTok Cleaners
REM 6b.1 Process TikTok landing zone CSVs into raw zone
python src\tiktok\cleaners\tiktok_landing2raw.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
REM 6b.2 Process TikTok raw zone into staging zone
python src\tiktok\cleaners\tiktok_raw2staging.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 7a. Linktree Extractors
REM 7a.1 Extract Linktree analytics
python src\linktree\extractors\linktree_analytics_extractor.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 8a. Archive/Cleanup
REM 8a.1 Archive Old Data Files
python src\archive_old_data.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM === This step should ALWAYS be the last stage. ===
python cronjob\generate_no_extractors_cron.py

pause
