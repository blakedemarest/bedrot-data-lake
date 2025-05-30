# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
import os, json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from IPython.display import display

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
RAW      = PROJECT_ROOT / os.getenv("RAW_ZONE",     "raw")
STAGING  = PROJECT_ROOT / os.getenv("STAGING_ZONE", "staging")


# %%
# ─── Cell 2: Union ALL raw dumps into consolidated DataFrames ──────────────────
raw_meta = RAW / "metaads"
folders  = [d for d in raw_meta.iterdir() if d.is_dir()]
assert folders, f"No raw dumps found in {raw_meta}"

def stack(folders, fname):
    """Load a JSON file type from every folder, concat, and deduplicate."""
    dfs = [pd.read_json(f / fname, dtype_backend="pyarrow") for f in folders if (f / fname).exists()]
    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    if fname != "insights.json":                       # ads / adsets / campaigns
        return df.drop_duplicates(subset="id")
    # insights → dedupe on minimal primary key
    pk = [c for c in ["date_start","ad_id","adset_id","campaign_id"] if c in df.columns]
    return df.drop_duplicates(subset=pk) if pk else df.drop_duplicates()

ads       = stack(folders, "ads.json")
adsets    = stack(folders, "adsets.json")
campaigns = stack(folders, "campaigns.json")
insights  = stack(folders, "insights.json")

for col in ("spend","impressions","clicks","reach","cpc","ctr","frequency"):
    if col in insights.columns:
        insights[col] = pd.to_numeric(insights[col], errors="coerce")

print(f"Rows → campaigns {len(campaigns)}, adsets {len(adsets)}, ads {len(ads)}, insights {len(insights)}")


# %%
# ─── Cell 3: Flatten ads.json (include campaign_id & adset_id) ─────────────────
import json

ads_flat = ads.copy()
ads_flat["creative_id"]    = ads_flat["creative"].apply(
    lambda c: c.get("id") if isinstance(c, dict) else None)
ads_flat["tracking_specs"] = ads_flat["tracking_specs"].apply(json.dumps)

ads_flat = ads_flat[[
    "id","campaign_id","adset_id","name","status","effective_status",
    "created_time","updated_time","creative_id","tracking_specs"
]].rename(columns={
    "id":   "ad_id",
    "name": "ad_name"
})

print("ads_flat cols:", ads_flat.columns.tolist())


# %%
# ─── Cell 4: Prepare campaigns_ & adsets_ for merge ────────────────────────────
campaigns_ = campaigns.rename(columns={
    "id":        "campaign_id",
    "name":      "campaign_name",
    "status":    "campaign_status",
    "objective": "campaign_objective"
})

adsets_ = (adsets.rename(columns={
    "id":              "adset_id",
    "name":            "adset_name",
    "status":          "adset_status",
    "daily_budget":    "adset_daily_budget",
    "lifetime_budget": "adset_lifetime_budget"
})
.drop(columns=["campaign_id"], errors="ignore"))

print("campaigns_ cols:", campaigns_.columns.tolist())
print("adsets_ cols:",    adsets_.columns.tolist())


# %%
# ─── Cell 5: Merge to AD-level tidy & write to STAGING ─────────────────────────
tidy = (insights
        .merge(adsets_,    on="adset_id",    how="left")
        .merge(campaigns_, on="campaign_id", how="left")
        .merge(ads_flat,   on=["campaign_id","adset_id"], how="left")
        .loc[:, lambda d: ~d.columns.duplicated()])

STAGING.mkdir(parents=True, exist_ok=True)
out_csv = STAGING / "tidy_metaads.csv"
tidy.to_csv(out_csv, index=False)

print(f"✅ tidy_metaads → {out_csv}  (rows: {len(tidy)})")
display(tidy.head(5))


# %%



