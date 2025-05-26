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

# Keywords that mark extractor sections (case-insensitive)
EXTRACTOR_KEYWORDS = [
    r"Meta Ads Extraction",
    r"DistroKid Auth & Download",
    r"TooLost Scraper"
]

# Keywords that mark the first non-extractor section to resume keeping
RESUME_KEYWORDS = [
    r"DistroKid HTML Validation",
    r"TooLost JSON Validation"
]

def should_skip(line):
    return any(re.search(k, line, re.IGNORECASE) for k in EXTRACTOR_KEYWORDS)

def should_resume(line):
    return any(re.search(k, line, re.IGNORECASE) for k in RESUME_KEYWORDS)

with open(MASTER, encoding="utf-8") as f:
    lines = f.readlines()

result = []
skip = False
for line in lines:
    if should_skip(line):
        skip = True
    if should_resume(line):
        skip = False
    if not skip:
        result.append(line)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.writelines(result)

print(f"Generated {OUTPUT} from {MASTER} (extractor sections removed).")

import subprocess
import sys

print(f"\n[INFO] Running {OUTPUT}...")
PROJECT_ROOT = os.path.dirname(CRONJOB_DIR)
proc = subprocess.run([OUTPUT], shell=True, cwd=PROJECT_ROOT)
print(f"[INFO] {OUTPUT} exited with code {proc.returncode}")
sys.exit(proc.returncode)
