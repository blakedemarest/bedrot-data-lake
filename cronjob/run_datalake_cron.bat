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
REM Expose src/ on PYTHONPATH so 'from common...' works in all child scripts
set "PYTHONPATH=%PROJECT_ROOT%\src;%PYTHONPATH%"

REM === Modular ETL: Loop through platforms and run extractors/cleaners automatically ===
for /d %%P in (src\*) do (
    REM Ignore .playwright and any hidden folders
    if /I not "%%~nxP"==".playwright" if not "%%~nxP"=="." if not "%%~nxP"==".." if not "%%~nxP:~0,1"=="." (
        REM Run all extractors for this platform
        if exist "%%P\extractors" (
            echo [INFO] Running extractors for %%~nxP
            for %%E in ("%%P\extractors\*.py") do (
                if exist "%%E" (
                    echo [INFO] Running extractor: %%E
                    python "%%E"
                    IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
                )
            )
        )
        REM Run all cleaners for this platform
        if exist "%%P\cleaners" (
            echo [INFO] Running cleaners for %%~nxP
            for %%C in ("%%P\cleaners\*.py") do (
                if exist "%%C" (
                    echo [INFO] Running cleaner: %%C
                    python "%%C"
                    IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
                )
            )
        )
    )
)

REM === This step should ALWAYS be the last stage. ===
python cronjob\generate_no_extractors_cron.py

pause
