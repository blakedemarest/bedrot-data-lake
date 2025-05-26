@echo off
REM Master Data Lake Cron Job
REM Uses PROJECT_ROOT from .env for all relative paths

REM Load environment variables
for /f "usebackq tokens=1,2 delims==" %%i in ("%~dp0..\.env") do set %%i=%%j

REM Change to project root directory
cd /d "%PROJECT_ROOT%"

REM 3. DistroKid HTML Validation
echo Running DistroKid HTML Validation...
python src\distrokid\extractors\validate_dk_html.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 4. DistroKid Dataset Cleaner
echo Running DistroKid Dataset Cleaner...
python src\distrokid\cleaners\distrokid_dataset_cleaner.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 6. TooLost JSON Validation
REM Finds the latest TooLost JSON files and validates them
for /f "delims=" %%a in ('dir /b /o-d "landing\toolost\toolost_spotify_*.json"') do set LATEST_SPOTIFY=landing\toolost\%%a & goto :found_spotify
:found_spotify
for /f "delims=" %%a in ('dir /b /o-d "landing\toolost\toolost_apple_*.json"') do set LATEST_APPLE=landing\toolost\%%a & goto :found_apple
:found_apple
python src\toolost\extractors\validate_toolost_json.py %LATEST_SPOTIFY% %LATEST_APPLE%
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 7. TooLost Dataset Cleaner
REM Consolidates and cleans TooLost streaming data, producing a curated CSV for analytics
python src\toolost\cleaners\toolost_dataset_cleaner.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 8. Analytics & Reporting (replace with your script/notebook)
echo Running Analytics & Reporting...
python curated\analytics_notebook_or_script.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo All steps completed successfully.

REM === This step should ALWAYS be the last stage. ===
python cronjob\generate_no_extractors_cron.py

pause
