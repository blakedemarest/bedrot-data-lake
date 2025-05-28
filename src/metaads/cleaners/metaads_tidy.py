# %%
# Cell 1: Setup & auto-detect latest landing folder
from pathlib import Path
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
project_root = Path(os.getenv("PROJECT_ROOT"))
landing_dir  = project_root / "landing" / "metaads"
subdirs      = [d for d in landing_dir.iterdir() if d.is_dir()]
if not subdirs:
    raise FileNotFoundError(f"No landing/metaads sub-folders under {landing_dir}")
data_dir     = max(subdirs, key=lambda d: d.stat().st_mtime)

print("⤷ Loading data from:", data_dir)


# %%
# Cell 2: Load raw JSON dumps
ads       = pd.read_json(data_dir / "ads.json")
adsets    = pd.read_json(data_dir / "adsets.json")
campaigns = pd.read_json(data_dir / "campaigns.json")
insights  = pd.read_json(data_dir / "insights.json")

# Convert key metrics to numeric
for col in ("spend","impressions","clicks","reach","cpc","ctr","frequency"):
    if col in insights.columns:
        insights[col] = pd.to_numeric(insights[col], errors="coerce")

print("Loaded shapes → ads:", ads.shape,
      "adsets:", adsets.shape,
      "campaigns:", campaigns.shape,
      "insights:", insights.shape)

# --- Promote staged CSV to curated (as metaads_campaigns_daily.csv) ---
import shutil
staging_csv = project_root / "staging" / "tidy_metaads.csv"
curated_csv = project_root / "curated" / "metaads_campaigns_daily.csv"
shutil.copy2(staging_csv, curated_csv)
print(f"✅ Promoted {staging_csv.name} to curated as {curated_csv.name}")


# %%
# Cell 3: Flatten ads.json (including campaign_id & adset_id)
import json

ads_flat = ads.copy()
ads_flat["creative_id"] = ads_flat["creative"].apply(lambda c: c.get("id") if isinstance(c, dict) else None)
ads_flat["tracking_specs"] = ads_flat["tracking_specs"].apply(json.dumps)

ads_flat = ads_flat[[
    "id","campaign_id","adset_id","name","status","effective_status",
    "created_time","updated_time","creative_id","tracking_specs"
]].rename(columns={
    "id":"ad_id",
    "name":"ad_name"
})

print("ads_flat cols:", ads_flat.columns.tolist())


# %%
# Cell 4: Prepare campaigns_ & adsets_ for merge (drop campaign_id from adsets_)
campaigns_ = campaigns.rename(columns={
    "id":           "campaign_id",
    "name":         "campaign_name",
    "status":       "campaign_status",
    "objective":    "campaign_objective"
})

adsets_ = adsets.rename(columns={
    "id":              "adset_id",
    "name":            "adset_name",
    "status":          "adset_status",
    "daily_budget":    "adset_daily_budget",
    "lifetime_budget": "adset_lifetime_budget"
}).drop(columns=["campaign_id"])

print("campaigns_ cols:", campaigns_.columns.tolist())
print("adsets_ cols:",    adsets_.columns.tolist())


# %%
# Cell 5: Build the tidy DataFrame
tidy = (
    insights
      .merge(campaigns_, on="campaign_id", how="left")
      .merge(adsets_,    on="adset_id",    how="left")
      .merge(ads_flat,   on=["campaign_id","adset_id"], how="left")
)

# Drop any duplicated columns and inspect
tidy = tidy.loc[:, ~tidy.columns.duplicated()]
print("Tidy shape:", tidy.shape)
tidy.head(3)


# %%
# Cell 6: Export tidy DataFrame to CSV (to staging folder)
staging_dir = project_root / "staging"
staging_dir.mkdir(parents=True, exist_ok=True)

out_path = staging_dir / "tidy_metaads.csv"
tidy.to_csv(out_path, index=False)

print("✔ Wrote tidy CSV to:", out_path)


# %%



