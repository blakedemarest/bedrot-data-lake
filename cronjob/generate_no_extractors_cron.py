# generate_no_extractors_cron.py
"""
Auto-generates run_datalake_cron_no_extractors.bat from the master cron job file.
Removes all extractor script stages, so only validation/cleaning/reporting remain.
Update ONLY the master file; run this script to sync the secondary file.
"""
import re
import os

CRONJOB_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(CRONJOB_DIR, "run_datalake_cron.bat")
OUTPUT = os.path.join(CRONJOB_DIR, "run_datalake_cron_no_extractors.bat")

# Pattern to match python calls to extractors scripts
EXTRACTOR_PY_PATTERN = re.compile(r"python\s+.*extractors[\\/][^\s]+\.py", re.IGNORECASE)
GENERATOR_PATTERN = re.compile(r"python\s+cronjob[\\/]generate_no_extractors_cron\.py", re.IGNORECASE)

with open(MASTER, encoding="utf-8") as f:
    lines = f.readlines()

output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Remove any call to generate_no_extractors_cron.py (prevents accidental loop)
    if GENERATOR_PATTERN.search(line):
        i += 1
        continue
    # Remove explicit extractor python calls and their adjacent REM/error check
    if EXTRACTOR_PY_PATTERN.search(line):
        # Remove REM comment immediately before
        if output_lines:
            last_line = output_lines[-1].strip()
            if last_line.startswith("REM"):
                output_lines.pop()
        # Optionally skip IF %ERRORLEVEL% after
        if i+1 < len(lines) and lines[i+1].strip().startswith("IF %ERRORLEVEL%"):
            i += 2
        else:
            i += 1
        continue
    # Remove for-loop blocks over extractors/*.py
    for_loop_match = re.match(r'\s*for\s+%%\w+\s+in\s+\(.*extractors[\\/]\*\.py.*\)\s+do\s+\(', line, re.IGNORECASE)
    if for_loop_match:
        # Remove the entire block until the closing paren at the same nesting level
        nesting = 1
        i += 1
        while i < len(lines) and nesting > 0:
            if '(' in lines[i]:
                nesting += lines[i].count('(')
            if ')' in lines[i]:
                nesting -= lines[i].count(')')
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
