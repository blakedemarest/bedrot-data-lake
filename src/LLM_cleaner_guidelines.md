# Guidelines for Generating Data‐Cleaning Scripts

> **Scope**  
> These rules apply to *landing→raw*, *raw→staging*, and *staging→curated* cleaner scripts for **every** data platform in the BEDROT Data Lake.  
> Follow them exactly when instructing an LLM to generate new cleaners.

---

## 1. File-Naming & Location
| Stage | Mandatory Filename | Output Zone |
|-------|-------------------|-------------|
| Landing → Raw | `<platform>_landing2raw.py` | `raw/<platform>/…` |
| Raw → Staging | `<platform>_raw2staging.py` | `staging/<platform>/…` |
| Staging → Curated | `<platform>_staging2curated.py` | `curated/<platform>/…` |

* Place scripts in `src/<platform>/cleaners/`.
* Keep names **all-lowercase**, snake_case.

## 2. Code-Cell Structure
* Use **`# %%`** delimiters to mimic Jupyter cells for interactive execution.
* Recommended sections (all scripts):
  1. **Imports & Constants**
  2. Helper / transformation functions
  3. Core processing logic
  4. CLI entry-point (`main()`)
* Keep top-level executable code only inside `if __name__ == "__main__":`.

## 3. Environment & Directory Conventions
* All cleaners must rely on the env var `PROJECT_ROOT` (already exported by runners).

```python
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
LANDING_DIR  = PROJECT_ROOT / "landing" / platform / subdir
RAW_DIR      = PROJECT_ROOT / "raw" / platform / subdir
STAGING_DIR  = PROJECT_ROOT / "staging" / platform / subdir
CURATED_DIR  = PROJECT_ROOT / "curated" / platform / subdir
```
* `DIR.mkdir(parents=True, exist_ok=True)` immediately after definition.

## 4. Logging & CLI
* Use lightweight `print()` logging with stage tags (`[RAW]`, `[STAGING]`, `[CURATED]`, `[ERROR]`, `[INFO]`).
* Provide a minimal `argparse` CLI; typical flags:
  * `--file` (Landing → Raw) – process single file.
  * `--out`  (Raw → Staging) – custom CSV path.
  * `--input` (Staging → Curated) – specific staging file.

## 5. Data Formats & IO
| Stage | Reads | Writes |
|-------|-------|--------|
| Landing → Raw | JSON blobs | **NDJSON** (one JSON per line) |
| Raw → Staging | NDJSON | CSV (single file per run) |
| Staging → Curated | CSV | **CSV** |

* Use **UTF-8** encoding when writing text.
* CSV writing via `DataFrame.to_csv`. (If column types need preservation, use compression options like `.csv.gz`).

## 6. Transformation Logic Templates
### 6.1 Landing → Raw
```python
# pseudo
payload   = json.loads(file.read())
record    = transform_response(payload)
json.dump(record, out_f); out_f.write("\n")
```
* Provide `transform_response(payload)` stub.  
  * Flatten nested GraphQL `data -> edges/nodes`.  
  * Remove irrelevant metadata.

### 6.2 Raw → Staging
* Build list of rows using `record_to_row(record)` helper.
* Return `pd.DataFrame`.
* Enforce basic column presence (`id`, `date`, metric columns).  
  * Use `pd.to_datetime`, `pd.to_numeric` with `errors="coerce"`.

### 6.3 Staging → Curated
* `curate_dataframe(df)` handles business rules:
  * Deduplicate on key fields (e.g., `id`, `date`).
  * Cast types & derive metrics.
* Write CSV with a timestamp stem; keep one file per run in the curated directory.

## 7. Error Handling
* Wrap file-level processing in `try/except` and log `[ERROR] …`.
* Do **not** terminate entire run on single-file failure; continue.
* Raise `RuntimeError` only if zero records processed.

## 8. Timestamp & File-Stem Conventions
* Use `datetime.now().strftime('%Y%m%d_%H%M%S')`.
* Output NDJSON keeps original landing filename stem.  
* Staging/Curated files prefixed with `platform_analytics_<stage>_<timestamp>`.

## 9. Dependencies
* Standard library + `pandas` (no optional dependencies required).  
* Avoid heavy libs; no external HTTP calls.

## 10. Documentation
* Top-of-file docstring briefly explains purpose, zones, and TODOs.
* Reference this ruleset in future scripts: “Guided by `LLM_cleaner_guidelines.md`”.

---
**Change-ID:** 2025-06-12-linktree_cleaner_guidelines
