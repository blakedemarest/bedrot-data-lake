@echo off
REM Master Data Lake Cron Job
REM Uses PROJECT_ROOT from .env for all relative paths

REM Load environment variables
for /f "usebackq tokens=1,2 delims==" %%i in ("%~dp0..\.env") do set %%i=%%j

REM Change to project root directory
cd /d "%PROJECT_ROOT%"

REM 1. Meta Ads Extraction (Jupyter notebook, recommend convert to .py for automation)
echo Running Meta Ads extraction...
python sandbox\meta_raw_dump.ipynb
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 2. DistroKid Auth & Download
echo Running DistroKid Auth & Download...
python src\distrokid\extractors\dk_auth.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 3. DistroKid HTML Validation
echo Running DistroKid HTML Validation...
python src\distrokid\extractors\validate_dk_html.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 4. DistroKid Dataset Cleaner
echo Running DistroKid Dataset Cleaner...
python src\distrokid\cleaners\distrokid_dataset_cleaner.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 5. TooLost Scraper
echo Running TooLost Scraper...
python src\toolost\extractors\toolost_scraper.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM 6. TooLost JSON Validation
echo Running TooLost JSON Validation...
python src\toolost\validate_toolost_json.py
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
pause
