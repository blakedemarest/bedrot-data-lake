# generate_no_extractors_cron.py
"""
Auto-generates run_datalake_cron_no_extractors.bat from the master cron job file.
Removes all extractor script stages (STEP 3), so only validation/cleaning/reporting remain.
Update ONLY the master file; run this script to sync the secondary file.
"""
import re
import os

CRONJOB_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(CRONJOB_DIR, "run_datalake_cron.bat")
OUTPUT = os.path.join(CRONJOB_DIR, "run_datalake_cron_no_extractors.bat")

# Pattern to match python calls to extractors scripts
EXTRACTOR_PY_PATTERN = re.compile(r"python\s+.*extractors[\\/][^\s]+\.py", re.IGNORECASE)
GENERATOR_PATTERN = re.compile(r"python\s+6_automated_cronjob[\\/]generate_no_extractors_cron\.py", re.IGNORECASE)

with open(MASTER, encoding="utf-8") as f:
    lines = f.readlines()

output_lines = []
i = 0
skip_step3 = False
extraction_failures_found = False

while i < len(lines):
    line = lines[i]
    
    # Detect start of STEP 3 (Data Extraction)
    if "[STEP 3/6]" in line and "Running Data Extractors" in line:
        skip_step3 = True
        # Keep the header but add a skip message
        output_lines.append(line)
        i += 1
        # Skip lines until we find STEP 4
        while i < len(lines) and "[STEP 4/6]" not in lines[i]:
            i += 1
        # Add a message that we're skipping extractors
        output_lines.append("echo [INFO] Skipping data extraction (no-extractors mode) | tee -a \"%LOG_FILE%\"\n")
        output_lines.append("echo. | tee -a \"%LOG_FILE%\"\n")
        output_lines.append("\n")
        continue
    
    # Track if we've seen EXTRACTION_FAILURES variable
    if "set EXTRACTION_FAILURES=0" in line:
        extraction_failures_found = True
        # Skip this line in no-extractors mode
        i += 1
        continue
    
    # Skip lines that reference EXTRACTION_FAILURES
    if extraction_failures_found and "%EXTRACTION_FAILURES%" in line:
        # Replace with hardcoded 0 for summary
        if "Extraction failures:" in line:
            output_lines.append(line.replace("%EXTRACTION_FAILURES%", "0"))
        elif "set /a TOTAL_FAILURES=" in line:
            # Adjust total failures calculation
            output_lines.append(line.replace("%EXTRACTION_FAILURES%+", ""))
        else:
            # Skip other references
            pass
        i += 1
        continue
    
    # Remove any call to generate_no_extractors_cron.py (prevents accidental loop)
    if GENERATOR_PATTERN.search(line):
        i += 1
        continue
        
    # Otherwise, keep the line
    output_lines.append(line)
    i += 1


with open(OUTPUT, "w", encoding="utf-8") as f:
    f.writelines(output_lines)

print(f"Generated {OUTPUT} from {MASTER} (extractor sections removed).\n")

# Run the generated batch file
import subprocess
import sys
PROJECT_ROOT = os.path.dirname(CRONJOB_DIR)
print(f"[INFO] Running {OUTPUT}...")
proc = subprocess.run([OUTPUT], shell=True, cwd=PROJECT_ROOT)
print(f"[INFO] {OUTPUT} exited with code {proc.returncode}")
sys.exit(proc.returncode)
