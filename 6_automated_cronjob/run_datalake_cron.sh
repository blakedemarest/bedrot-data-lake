#!/usr/bin/env bash

# ================================================================================
#                       BEDROT DATA LAKE MASTER PIPELINE (Linux Version)
#           Comprehensive ETL with Cookie Management and Health Monitoring
# ================================================================================
# This is the main consolidated pipeline that handles:
# - Cookie status checking and auto-refresh
# - Pipeline health monitoring with auto-remediation
# - Individual service extractors (no integrated_extractor.py)
# - Data cleaning pipeline
# - Data warehouse ETL
# - Comprehensive reporting
# ================================================================================

# === EARLY ERROR CATCHING ===
if [ "$1" == "--help" ]; then
    echo "Usage: run_datalake_cron.sh [--skip-extractors]"
    echo ""
    echo "Options:"
    echo "  --skip-extractors    Skip data extraction, only run cleaners"
    echo "  --help              Show this help message"
    exit 0
fi

# === ENVIRONMENT SETUP ===
echo ""
echo "================================================================================"
echo "                         BEDROT DATA LAKE PIPELINE"
echo "                          Starting at $(date)"
echo "================================================================================"
echo ""

# Ensure we're in the correct directory
echo "[DEBUG] Changing to project directory..."
cd "$(dirname "$0")/.." || exit 1
export PROJECT_ROOT="$(pwd)"
echo "[DEBUG] PROJECT_ROOT: $PROJECT_ROOT"

# === Ensure venv exists and is ready ===
if [ -d "venv_linux" ]; then
    VENV_DIR="venv_linux"
elif [ -d ".venv" ]; then
    VENV_DIR=".venv"
else
    echo "[INFO] Python virtual environment not found. Creating venv_linux..."
    python3 -m venv venv_linux
    VENV_DIR="venv_linux"
    echo "[INFO] Installing requirements..."
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
fi

# === Activate the venv ===
source "$VENV_DIR/bin/activate"

# Load environment variables from .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Expose src/ on PYTHONPATH so 'from common...' works in all child scripts
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Create logs directory if it doesn't exist
if [ ! -d "$PROJECT_ROOT/logs" ]; then
    echo "Creating logs directory..."
    mkdir -p "$PROJECT_ROOT/logs"
fi

# Set log file for this run
LOG_FILE="$PROJECT_ROOT/logs/pipeline_$(date +%Y%m%d_%H%M%S).log"

# Test if we can write to the log file
echo "[INFO] Pipeline started at $(date)" > "$LOG_FILE" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: Cannot write to log file. Continuing without logging..."
    LOG_FILE="/dev/null"
else
    echo "Log file created: $LOG_FILE"
    echo "[INFO] Project Root: $PROJECT_ROOT" >> "$LOG_FILE"
fi
echo ""

# === STEP 1: COOKIE STATUS CHECK AND AUTO-REFRESH ===
echo "[STEP 1/6] ============================================"
echo "[STEP 1/6] ============================================" >> "$LOG_FILE"
echo "[STEP 1/6] Cookie Status Check and Auto-Refresh"
echo "[STEP 1/6] Cookie Status Check and Auto-Refresh" >> "$LOG_FILE"
echo "[STEP 1/6] ============================================"
echo "[STEP 1/6] ============================================" >> "$LOG_FILE"
echo ""
echo "" >> "$LOG_FILE"

echo "[INFO] Checking current cookie status..."
echo "[INFO] Checking current cookie status..." >> "$LOG_FILE"
python cookie_status.py >> "$LOG_FILE" 2>&1
COOKIE_STATUS=$?

if [ $COOKIE_STATUS -ne 0 ]; then
    echo "[INFO] Some cookies need refresh. Attempting auto-refresh..."
    echo "[INFO] Some cookies need refresh. Attempting auto-refresh..." >> "$LOG_FILE"
    python cookie_refresh.py --refresh-all >> "$LOG_FILE" 2>&1
    REFRESH_RESULT=$?
    if [ $REFRESH_RESULT -ne 0 ]; then
        echo "[WARNING] Cookie refresh encountered issues. Some services may fail."
        echo "[WARNING] Cookie refresh encountered issues. Some services may fail." >> "$LOG_FILE"
        echo "[WARNING] You may need to manually refresh cookies for some services."
        echo "[WARNING] You may need to manually refresh cookies for some services." >> "$LOG_FILE"
    else
        echo "[INFO] Cookie refresh completed successfully."
        echo "[INFO] Cookie refresh completed successfully." >> "$LOG_FILE"
    fi
else
    echo "[INFO] All cookies are healthy."
    echo "[INFO] All cookies are healthy." >> "$LOG_FILE"
fi
echo ""
echo "" >> "$LOG_FILE"

# === STEP 2: PIPELINE HEALTH CHECK WITH AUTO-REMEDIATION ===
echo "[STEP 2/6] ============================================"
echo "[STEP 2/6] ============================================" >> "$LOG_FILE"
echo "[STEP 2/6] Pipeline Health Check with Auto-Remediation"
echo "[STEP 2/6] Pipeline Health Check with Auto-Remediation" >> "$LOG_FILE"
echo "[STEP 2/6] ============================================"
echo "[STEP 2/6] ============================================" >> "$LOG_FILE"
echo ""
echo "" >> "$LOG_FILE"

echo "[INFO] Running pipeline health monitor..."
echo "[INFO] Running pipeline health monitor..." >> "$LOG_FILE"
python src/common/pipeline_health_monitor.py >> "$LOG_FILE" 2>&1
HEALTH_STATUS=$?

if [ $HEALTH_STATUS -eq 2 ]; then
    echo "[WARNING] Pipeline is in CRITICAL state. Review the report above."
    echo "[WARNING] Pipeline is in CRITICAL state. Review the report above." >> "$LOG_FILE"
elif [ $HEALTH_STATUS -eq 1 ]; then
    echo "[WARNING] Some services have issues. Auto-remediation attempted."
    echo "[WARNING] Some services have issues. Auto-remediation attempted." >> "$LOG_FILE"
else
    echo "[INFO] Pipeline health check passed."
    echo "[INFO] Pipeline health check passed." >> "$LOG_FILE"
fi
echo ""
echo "" >> "$LOG_FILE"

# === STEP 3: DATA EXTRACTION WITH INDIVIDUAL EXTRACTORS ===
if [ "$1" != "--skip-extractors" ]; then
    echo "[STEP 3/6] ============================================"
    echo "[STEP 3/6] ============================================" >> "$LOG_FILE"
    echo "[STEP 3/6] Running Data Extractors"
    echo "[STEP 3/6] Running Data Extractors" >> "$LOG_FILE"
    echo "[STEP 3/6] ============================================"
    echo "[STEP 3/6] ============================================" >> "$LOG_FILE"
    echo ""
    echo "" >> "$LOG_FILE"

    # Track extraction results
    EXTRACTION_FAILURES=0

    # --- Spotify Extractor ---
    echo "[INFO] Running Spotify extractor..."
    echo "[INFO] Running Spotify extractor..." >> "$LOG_FILE"
    python src/spotify/extractors/spotify_audience_extractor.py >> "$LOG_FILE" 2>&1
    SPOTIFY_RESULT=$?
    if [ $SPOTIFY_RESULT -ne 0 ]; then
        echo "[WARNING] Spotify extraction failed (exit code: $SPOTIFY_RESULT)"
        echo "[WARNING] Spotify extraction failed (exit code: $SPOTIFY_RESULT)" >> "$LOG_FILE"
        ((EXTRACTION_FAILURES++))
    else
        echo "[INFO] ✓ Spotify extraction completed"
        echo "[INFO] ✓ Spotify extraction completed" >> "$LOG_FILE"
    fi
    echo ""
    echo "" >> "$LOG_FILE"

    # --- DistroKid Extractor ---
    echo "[INFO] Running DistroKid extractor..."
    echo "[INFO] Running DistroKid extractor..." >> "$LOG_FILE"
    python src/distrokid/extractors/dk_auth.py >> "$LOG_FILE" 2>&1
    DISTROKID_RESULT=$?
    if [ $DISTROKID_RESULT -ne 0 ]; then
        echo "[WARNING] DistroKid extraction failed (exit code: $DISTROKID_RESULT)"
        echo "[WARNING] DistroKid extraction failed (exit code: $DISTROKID_RESULT)" >> "$LOG_FILE"
        ((EXTRACTION_FAILURES++))
    else
        echo "[INFO] ✓ DistroKid extraction completed"
        echo "[INFO] ✓ DistroKid extraction completed" >> "$LOG_FILE"
    fi
    echo ""
    echo "" >> "$LOG_FILE"

    # --- TikTok Extractors (Multiple Accounts) ---
    echo "[INFO] Running TikTok extractors..."
    echo "[INFO] Running TikTok extractors..." >> "$LOG_FILE"

    echo "[INFO] - TikTok Zone A0 account..."
    echo "[INFO] - TikTok Zone A0 account..." >> "$LOG_FILE"
    python src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py >> "$LOG_FILE" 2>&1
    TIKTOK_ZONEA0_RESULT=$?
    if [ $TIKTOK_ZONEA0_RESULT -ne 0 ]; then
        echo "[WARNING] TikTok Zone A0 extraction failed (exit code: $TIKTOK_ZONEA0_RESULT)"
        echo "[WARNING] TikTok Zone A0 extraction failed (exit code: $TIKTOK_ZONEA0_RESULT)" >> "$LOG_FILE"
        ((EXTRACTION_FAILURES++))
    else
        echo "[INFO] ✓ TikTok Zone A0 extraction completed"
        echo "[INFO] ✓ TikTok Zone A0 extraction completed" >> "$LOG_FILE"
    fi

    echo "[INFO] - TikTok PIG1987 account..."
    echo "[INFO] - TikTok PIG1987 account..." >> "$LOG_FILE"
    python src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py >> "$LOG_FILE" 2>&1
    TIKTOK_PIG_RESULT=$?
    if [ $TIKTOK_PIG_RESULT -ne 0 ]; then
        echo "[WARNING] TikTok PIG1987 extraction failed (exit code: $TIKTOK_PIG_RESULT)"
        echo "[WARNING] TikTok PIG1987 extraction failed (exit code: $TIKTOK_PIG_RESULT)" >> "$LOG_FILE"
        ((EXTRACTION_FAILURES++))
    else
        echo "[INFO] ✓ TikTok PIG1987 extraction completed"
        echo "[INFO] ✓ TikTok PIG1987 extraction completed" >> "$LOG_FILE"
    fi
    echo ""
    echo "" >> "$LOG_FILE"

    # --- TooLost Extractor (with fallback) ---
    echo "[INFO] Running TooLost extractor..."
    echo "[INFO] Running TooLost extractor..." >> "$LOG_FILE"
    python src/toolost/extractors/toolost_scraper_automated.py >> "$LOG_FILE" 2>&1
    TOOLOST_RESULT=$?
    if [ $TOOLOST_RESULT -ne 0 ]; then
        echo "[WARNING] TooLost automated extraction failed, trying manual scraper..."
        echo "[WARNING] TooLost automated extraction failed, trying manual scraper..." >> "$LOG_FILE"
        python src/toolost/extractors/toolost_scraper.py >> "$LOG_FILE" 2>&1
        TOOLOST_MANUAL_RESULT=$?
        if [ $TOOLOST_MANUAL_RESULT -ne 0 ]; then
            echo "[WARNING] TooLost extraction failed (both methods)"
            echo "[WARNING] TooLost extraction failed (both methods)" >> "$LOG_FILE"
            ((EXTRACTION_FAILURES++))
        else
            echo "[INFO] ✓ TooLost extraction completed (manual method)"
            echo "[INFO] ✓ TooLost extraction completed (manual method)" >> "$LOG_FILE"
        fi
    else
        echo "[INFO] ✓ TooLost extraction completed"
        echo "[INFO] ✓ TooLost extraction completed" >> "$LOG_FILE"
    fi
    echo ""
    echo "" >> "$LOG_FILE"

    # --- Linktree Extractor ---
    echo "[INFO] Running Linktree extractor..."
    echo "[INFO] Running Linktree extractor..." >> "$LOG_FILE"
    python src/linktree/extractors/linktree_analytics_extractor.py >> "$LOG_FILE" 2>&1
    LINKTREE_RESULT=$?
    if [ $LINKTREE_RESULT -ne 0 ]; then
        echo "[WARNING] Linktree extraction failed (exit code: $LINKTREE_RESULT)"
        echo "[WARNING] Linktree extraction failed (exit code: $LINKTREE_RESULT)" >> "$LOG_FILE"
        ((EXTRACTION_FAILURES++))
    else
        echo "[INFO] ✓ Linktree extraction completed"
        echo "[INFO] ✓ Linktree extraction completed" >> "$LOG_FILE"
    fi
    echo ""
    echo "" >> "$LOG_FILE"

    # --- MetaAds Extractor ---
    echo "[INFO] Running MetaAds extractor..."
    echo "[INFO] Running MetaAds extractor..." >> "$LOG_FILE"
    python src/metaads/extractors/meta_daily_campaigns_extractor.py >> "$LOG_FILE" 2>&1
    METAADS_RESULT=$?
    if [ $METAADS_RESULT -ne 0 ]; then
        echo "[WARNING] MetaAds extraction failed (exit code: $METAADS_RESULT)"
        echo "[WARNING] MetaAds extraction failed (exit code: $METAADS_RESULT)" >> "$LOG_FILE"
        ((EXTRACTION_FAILURES++))
    else
        echo "[INFO] ✓ MetaAds extraction completed"
        echo "[INFO] ✓ MetaAds extraction completed" >> "$LOG_FILE"
    fi
    echo ""
    echo "" >> "$LOG_FILE"

    echo "[INFO] Data extraction phase completed. Failures: $EXTRACTION_FAILURES"
    echo "[INFO] Data extraction phase completed. Failures: $EXTRACTION_FAILURES" >> "$LOG_FILE"
    echo ""
    echo "" >> "$LOG_FILE"
else
    echo "[INFO] Skipping data extraction phase (--skip-extractors flag)"
    echo "[INFO] Skipping data extraction phase (--skip-extractors flag)" >> "$LOG_FILE"
    EXTRACTION_FAILURES=0
fi

# === STEP 4: DATA CLEANING PIPELINE ===
echo "[STEP 4/6] ============================================"
echo "[STEP 4/6] ============================================" >> "$LOG_FILE"
echo "[STEP 4/6] Running Data Cleaners"
echo "[STEP 4/6] Running Data Cleaners" >> "$LOG_FILE"
echo "[STEP 4/6] ============================================"
echo "[STEP 4/6] ============================================" >> "$LOG_FILE"
echo ""
echo "" >> "$LOG_FILE"

CLEANER_FAILURES=0

# Loop through all service directories
for SERVICE_DIR in src/*/; do
    SERVICE=$(basename "$SERVICE_DIR")
    
    # Ignore .playwright, common, and any hidden folders
    if [[ "$SERVICE" == ".playwright" ]] || [[ "$SERVICE" == "common" ]] || [[ "$SERVICE" == .* ]]; then
        continue
    fi
    
    # Run all cleaners for this platform
    if [ -d "$SERVICE_DIR/cleaners" ]; then
        echo "[INFO] Running cleaners for $SERVICE"
        echo "[INFO] Running cleaners for $SERVICE" >> "$LOG_FILE"
        
        # Run cleaners in order: landing2raw, raw2staging, staging2curated
        for STAGE in landing2raw raw2staging staging2curated; do
            CLEANER_FILE="$SERVICE_DIR/cleaners/${SERVICE}_${STAGE}.py"
            if [ -f "$CLEANER_FILE" ]; then
                echo "[INFO]   - Running ${SERVICE}_${STAGE}.py"
                echo "[INFO]   - Running ${SERVICE}_${STAGE}.py" >> "$LOG_FILE"
                python "$CLEANER_FILE" >> "$LOG_FILE" 2>&1
                CLEANER_RESULT=$?
                if [ $CLEANER_RESULT -ne 0 ]; then
                    echo "[WARNING]   - ${SERVICE}_${STAGE}.py failed"
                    echo "[WARNING]   - ${SERVICE}_${STAGE}.py failed" >> "$LOG_FILE"
                    ((CLEANER_FAILURES++))
                else
                    echo "[INFO]   ✓ ${SERVICE}_${STAGE}.py completed"
                    echo "[INFO]   ✓ ${SERVICE}_${STAGE}.py completed" >> "$LOG_FILE"
                fi
            fi
        done
        echo ""
        echo "" >> "$LOG_FILE"
    fi
done

echo "[INFO] Data cleaning phase completed. Failures: $CLEANER_FAILURES"
echo "[INFO] Data cleaning phase completed. Failures: $CLEANER_FAILURES" >> "$LOG_FILE"
echo ""
echo "" >> "$LOG_FILE"

# === STEP 5: DATA WAREHOUSE ETL PIPELINE ===
echo "[STEP 5/6] ============================================"
echo "[STEP 5/6] ============================================" >> "$LOG_FILE"
echo "[STEP 5/6] Running Data Warehouse ETL Pipeline"
echo "[STEP 5/6] Running Data Warehouse ETL Pipeline" >> "$LOG_FILE"
echo "[STEP 5/6] ============================================"
echo "[STEP 5/6] ============================================" >> "$LOG_FILE"
echo ""
echo "" >> "$LOG_FILE"

# Save current directory
ORIGINAL_DIR="$(pwd)"

# Navigate to data warehouse directory
cd "$PROJECT_ROOT/../data-warehouse" 2>/dev/null

if [ $? -eq 0 ]; then
    # Check if warehouse virtual environment exists
    if [ -d ".venv/bin" ]; then
        echo "[INFO] Activating data warehouse virtual environment"
        echo "[INFO] Activating data warehouse virtual environment" >> "$LOG_FILE"
        deactivate  # Deactivate data lake venv
        source ".venv/bin/activate"
    else
        echo "[INFO] Using data lake virtual environment for warehouse ETL"
        echo "[INFO] Using data lake virtual environment for warehouse ETL" >> "$LOG_FILE"
    fi

    # Run the warehouse ETL pipeline
    echo "[INFO] Running warehouse ETL pipeline..."
    echo "[INFO] Running warehouse ETL pipeline..." >> "$LOG_FILE"
    if [ -f "scripts/run_all_etl.py" ]; then
        python scripts/run_all_etl.py >> "$LOG_FILE" 2>&1
    elif [ -f "run_all_etl.py" ]; then
        python run_all_etl.py >> "$LOG_FILE" 2>&1
    else
        echo "[ERROR] Could not find warehouse ETL script"
        echo "[ERROR] Could not find warehouse ETL script" >> "$LOG_FILE"
        WAREHOUSE_ERRORLEVEL=1
    fi
    WAREHOUSE_ERRORLEVEL=$?

    # Return to original directory
    cd "$ORIGINAL_DIR"

    # Re-activate data lake venv if we switched
    if [ -d "$PROJECT_ROOT/../data-warehouse/.venv/bin" ]; then
        deactivate
        source "$PROJECT_ROOT/$VENV_DIR/bin/activate"
    fi
else
    echo "[WARNING] Data warehouse directory not found"
    echo "[WARNING] Data warehouse directory not found" >> "$LOG_FILE"
    WAREHOUSE_ERRORLEVEL=1
fi

# Check warehouse ETL result
if [ $WAREHOUSE_ERRORLEVEL -ne 0 ]; then
    echo "[ERROR] Data Warehouse ETL failed with code $WAREHOUSE_ERRORLEVEL"
    echo "[ERROR] Data Warehouse ETL failed with code $WAREHOUSE_ERRORLEVEL" >> "$LOG_FILE"
else
    echo "[INFO] ✓ Data Warehouse ETL completed successfully"
    echo "[INFO] ✓ Data Warehouse ETL completed successfully" >> "$LOG_FILE"
fi
echo ""
echo "" >> "$LOG_FILE"

# === STEP 6: FINAL REPORTING AND MAINTENANCE ===
echo "[STEP 6/6] ============================================"
echo "[STEP 6/6] ============================================" >> "$LOG_FILE"
echo "[STEP 6/6] Generating Reports and Maintenance"
echo "[STEP 6/6] Generating Reports and Maintenance" >> "$LOG_FILE"
echo "[STEP 6/6] ============================================"
echo "[STEP 6/6] ============================================" >> "$LOG_FILE"
echo ""
echo "" >> "$LOG_FILE"

# Run final health check
echo "[INFO] Running final health check..."
echo "[INFO] Running final health check..." >> "$LOG_FILE"
python src/common/pipeline_health_monitor.py >> "$LOG_FILE" 2>&1

# Generate visual dashboard if available
if [ -f "src/common/cookie_refresh/dashboard.py" ]; then
    echo "[INFO] Generating visual dashboard..."
    echo "[INFO] Generating visual dashboard..." >> "$LOG_FILE"
    python src/common/cookie_refresh/dashboard.py --output pipeline_status.html >> "$LOG_FILE" 2>&1
fi

# Archive old logs (keep last 30 days)
echo "[INFO] Archiving old logs..."
echo "[INFO] Archiving old logs..." >> "$LOG_FILE"
find "$PROJECT_ROOT/logs" -name "*.log" -mtime +30 -delete 2>/dev/null

echo ""
echo "" >> "$LOG_FILE"
echo "================================================================================"
echo "================================================================================" >> "$LOG_FILE"
echo "                           PIPELINE SUMMARY"
echo "                           PIPELINE SUMMARY" >> "$LOG_FILE"
echo "================================================================================"
echo "================================================================================" >> "$LOG_FILE"
echo "[INFO] Pipeline completed at $(date)"
echo "[INFO] Pipeline completed at $(date)" >> "$LOG_FILE"
echo "[INFO] Extraction failures: $EXTRACTION_FAILURES"
echo "[INFO] Extraction failures: $EXTRACTION_FAILURES" >> "$LOG_FILE"
echo "[INFO] Cleaner failures: $CLEANER_FAILURES"
echo "[INFO] Cleaner failures: $CLEANER_FAILURES" >> "$LOG_FILE"
echo "[INFO] Log file: $LOG_FILE"
echo "[INFO] Log file: $LOG_FILE" >> "$LOG_FILE"
echo ""
echo "" >> "$LOG_FILE"

TOTAL_FAILURES=$((EXTRACTION_FAILURES + CLEANER_FAILURES))
if [ $WAREHOUSE_ERRORLEVEL -ne 0 ]; then
    ((TOTAL_FAILURES++))
fi

if [ $TOTAL_FAILURES -eq 0 ]; then
    echo "[SUCCESS] ✓ All pipeline components completed successfully!"
    echo "[SUCCESS] ✓ All pipeline components completed successfully!" >> "$LOG_FILE"
else
    echo "[WARNING] ⚠️  Pipeline completed with $TOTAL_FAILURES failures."
    echo "[WARNING] ⚠️  Pipeline completed with $TOTAL_FAILURES failures." >> "$LOG_FILE"
    echo "[WARNING] Check the log file for details: $LOG_FILE"
    echo "[WARNING] Check the log file for details: $LOG_FILE" >> "$LOG_FILE"
fi

echo ""
echo "" >> "$LOG_FILE"
echo "[INFO] Next steps:"
echo "[INFO] Next steps:" >> "$LOG_FILE"
echo "[INFO] 1. Review the pipeline health report above"
echo "[INFO] 1. Review the pipeline health report above" >> "$LOG_FILE"
echo "[INFO] 2. Check failed services and refresh cookies if needed"
echo "[INFO] 2. Check failed services and refresh cookies if needed" >> "$LOG_FILE"
echo "[INFO] 3. View the visual dashboard: pipeline_status.html"
echo "[INFO] 3. View the visual dashboard: pipeline_status.html" >> "$LOG_FILE"
echo "[INFO] 4. Run specific extractors manually if needed"
echo "[INFO] 4. Run specific extractors manually if needed" >> "$LOG_FILE"
echo "================================================================================"
echo "================================================================================" >> "$LOG_FILE"

echo ""
echo "[INFO] Press any key to exit..."
read -n 1 -s -r

# Deactivate virtual environment
deactivate

exit $TOTAL_FAILURES