# (Removed Jupyter/IPython magic - use requirements.txt for dependencies)
# If you need to install dependencies, run:
# pip install facebook-business==19.0.0 python-dotenv pandas tqdm

# Dump campaigns, ad sets, ads, and insights from the Meta Ads API.
# Creates a timestamped folder in landing/metaads using PROJECT_ROOT variables.

# %%
# ╔════════════════════════════════════════════════════════════════╗
# ║ 📚  Cell 2 – Imports & .env loading                            ║
# ╚════════════════════════════════════════════════════════════════╝
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights

# ── Credentials ────────────────────────────────────────────────
load_dotenv()
ACCESS_TOKEN  = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")      # format: act_123…
PROJECT_ROOT  = os.getenv("PROJECT_ROOT")
assert ACCESS_TOKEN and AD_ACCOUNT_ID and PROJECT_ROOT, ".env vars missing"

FacebookAdsApi.init(access_token=ACCESS_TOKEN, api_version="v19.0")

# Set landing_root using PROJECT_ROOT from .env
landing_root = Path(PROJECT_ROOT) / "landing" / "metaads"
timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
folder_name = f"meta_ads_dump_{timestamp}"
root_dir = landing_root / folder_name
root_dir.mkdir(parents=True, exist_ok=True)

print(f"🔖 Dump directory → {root_dir}")


# %%
# ╔════════════════════════════════════════════════════════════════╗
# ║ 📝  Cell 4 – Field definitions                                 ║
# ╚════════════════════════════════════════════════════════════════╝
CAMPAIGN_FIELDS = [
    Campaign.Field.id, Campaign.Field.name, Campaign.Field.status,
    Campaign.Field.objective, Campaign.Field.spend_cap,
    Campaign.Field.start_time, Campaign.Field.stop_time,
    Campaign.Field.created_time, Campaign.Field.updated_time,
]

ADSET_FIELDS = [
    AdSet.Field.id, AdSet.Field.name, AdSet.Field.status, AdSet.Field.campaign_id,
    AdSet.Field.daily_budget, AdSet.Field.lifetime_budget, AdSet.Field.bid_strategy,
    AdSet.Field.targeting, AdSet.Field.optimization_goal,
    AdSet.Field.start_time, AdSet.Field.end_time, AdSet.Field.pacing_type,
    AdSet.Field.created_time, AdSet.Field.updated_time,
]

AD_FIELDS = [
    Ad.Field.id, Ad.Field.name, Ad.Field.status, Ad.Field.adset_id,
    Ad.Field.campaign_id, Ad.Field.effective_status, Ad.Field.creative,
    Ad.Field.tracking_specs, Ad.Field.created_time, Ad.Field.updated_time,
]

INSIGHT_FIELDS = [
    AdsInsights.Field.campaign_id, AdsInsights.Field.campaign_name,
    AdsInsights.Field.adset_id, AdsInsights.Field.adset_name,
    AdsInsights.Field.ad_id, AdsInsights.Field.ad_name,
    AdsInsights.Field.spend,  # Ensure spend is included
    AdsInsights.Field.impressions, AdsInsights.Field.clicks,
    AdsInsights.Field.cpc, AdsInsights.Field.ctr,
    AdsInsights.Field.reach, AdsInsights.Field.frequency,
    AdsInsights.Field.date_start, AdsInsights.Field.date_stop,
]


# %%
# ╔════════════════════════════════════════════════════════════════╗
# ║ 🚀  Cell 5 – Generic paginator (bug-fixed)                     ║
# ╚════════════════════════════════════════════════════════════════╝
def fetch_all(edge_method, fields, params=None):
    """
    /// Call edge_method (e.g. account.get_campaigns) then auto-page through
    /// results. Returns a list of fully-expanded dicts ready for JSON dump.
    """
    params   = params or {}
    cursor   = edge_method(fields=fields, params=params)
    results  = []

    while True:
        results.extend(cursor)
        if cursor and cursor.load_next_page():
            cursor = cursor.next()
        else:
            break

    return [obj.export_all_data() for obj in results]


# %%
# ╔════════════════════════════════════════════════════════════════╗
# ║ 📦  Cell 6 – Download campaigns, adsets, ads                   ║
# ╚════════════════════════════════════════════════════════════════╝
account = AdAccount(AD_ACCOUNT_ID)

print("Fetching campaigns …")
campaign_data = fetch_all(account.get_campaigns, CAMPAIGN_FIELDS)
Path(root_dir, "campaigns.json").write_text(json.dumps(campaign_data, indent=2))
print(f"🚚 {len(campaign_data)} campaigns saved")

print("Fetching ad sets …")
adset_data = fetch_all(account.get_ad_sets, ADSET_FIELDS, params={"limit": 200})
Path(root_dir, "adsets.json").write_text(json.dumps(adset_data, indent=2))
print(f"🚚 {len(adset_data)} ad sets saved")

print("Fetching ads …")
ad_data = fetch_all(account.get_ads, AD_FIELDS, params={"limit": 200})
Path(root_dir, "ads.json").write_text(json.dumps(ad_data, indent=2))
print(f"🚚 {len(ad_data)} ads saved")


# %%
# ╔════════════════════════════════════════════════════════════════╗
# ║ 📈  Cell 7 – Insights dump (level toggle)                      ║
# ╚════════════════════════════════════════════════════════════════╝
INSIGHT_LEVEL = "adset"            # adset-level insights (for spend, etc). Change to 'campaign' or 'ad' as needed.

insight_records = []
print("Fetching insights …")

for camp in tqdm(campaign_data, desc="Campaign insights"):
    camp_id = camp["id"]
    edge    = Campaign(camp_id).get_insights
    camp_insights = fetch_all(
        edge, INSIGHT_FIELDS,
        params={"date_preset": "maximum", "level": INSIGHT_LEVEL, "limit": 500},
    )
    insight_records.extend(camp_insights)

Path(root_dir, "insights.json").write_text(json.dumps(insight_records, indent=2))
print(f"🚚 {len(insight_records)} insight rows saved")


# %%
# ╔════════════════════════════════════════════════════════════════╗
# ║ 🔍  Cell 8 – Quick sanity checks                               ║
# ╚════════════════════════════════════════════════════════════════╝
df_camps   = pd.DataFrame(campaign_data)
df_adsets  = pd.DataFrame(adset_data)
df_ads     = pd.DataFrame(ad_data)
df_ins     = pd.DataFrame(insight_records)

print("Rows → campaigns:", len(df_camps),
      "| adsets:", len(df_adsets),
      "| ads:", len(df_ads),
      "| insights:", len(df_ins))

if not df_ins.empty:
    total_spend = df_ins["spend"].astype(float).sum()
    print(f"💰 Lifetime spend snapshot: ${total_spend:,.2f}")


# %%
# ╔════════════════════════════════════════════════════════════════╗
# ║ ✅  Cell 9 – Completion banner                                 ║
# ╚════════════════════════════════════════════════════════════════╝
print(f"\n✅ Raw Meta snapshot complete → {root_dir}")



