# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Validate DistroKid HTML and TSV files in the landing zone and copy approved
# files to the raw zone. Requires PROJECT_ROOT and optional LANDING_ZONE/RAW_ZONE
# environment variables.
import os, re, json, hashlib, shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
LANDING      = PROJECT_ROOT / os.getenv("LANDING_ZONE", "landing")
RAW          = PROJECT_ROOT / os.getenv("RAW_ZONE",     "raw")


# %%
# ─── Cell 2: Validation Helpers (HTML & TSV) ────────────────────────────────────
streams_re = re.compile(r'"trend365day".*?"dataProvider"\s*:\s*\[(.*?)\]', re.DOTALL)
apple_re   = re.compile(r'var\s+chartData\s*=\s*([\s\S]+?);\s*\n', re.MULTILINE)

def _html_ok(path: Path, pattern: re.Pattern) -> bool:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    return bool(pattern.search(txt))

def validate_streams_html(p: Path):
    if not _html_ok(p, streams_re): return False, "trend365day block missing"
    return True, "OK"

def validate_apple_html(p: Path):
    if not _html_ok(p, apple_re):   return False, "chartData block missing"
    return True, "OK"

def validate_tsv(p: Path):
    return p.stat().st_size > 0, "empty file" if p.stat().st_size == 0 else "OK"


# %%
# ─── Cell 3: Promote Valid Landing Files to RAW ─────────────────────────────────
src_dir  = LANDING / "distrokid" / "streams"
raw_dir  = RAW     / "distrokid" / "streams"
finance_dir = RAW  / "distrokid" / "finance"
raw_dir.mkdir(parents=True, exist_ok=True)
finance_dir.mkdir(parents=True, exist_ok=True)

def _copy_if_new(src: Path, dst_dir: Path):
    dst = dst_dir / src.name
    if dst.exists() and hashlib.md5(dst.read_bytes()).hexdigest() == hashlib.md5(src.read_bytes()).hexdigest():
        return False
    if dst.exists():                                           # version duplicate
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        dst = dst_dir / f"{src.stem}__{ts}{src.suffix}"
    shutil.copy2(src, dst)
    return True

promoted = []
for html in src_dir.glob("streams_stats_*.html"):
    ok, msg = validate_streams_html(html)
    if ok and _copy_if_new(html, raw_dir): promoted.append(html.name)

for html in src_dir.glob("applemusic_stats_*.html"):
    ok, msg = validate_apple_html(html)
    if ok and _copy_if_new(html, raw_dir): promoted.append(html.name)

for tsv in src_dir.glob("dk_bank_details_*.tsv"):
    ok, msg = validate_tsv(tsv)
    if ok:
        csv_tmp = tsv.with_suffix(".csv")
        import pandas as pd
        pd.read_csv(tsv, sep="\t").to_csv(csv_tmp, index=False)
        if _copy_if_new(csv_tmp, finance_dir): promoted.append(csv_tmp.name)
        csv_tmp.unlink()

print(f"✅ Promoted {len(promoted)} new files → RAW")


# %%



