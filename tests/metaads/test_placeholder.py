import os
import sys
import pandas as pd


def get_staging_module(tmp_path):
    os.environ['PROJECT_ROOT'] = str(tmp_path)
    staging = tmp_path / 'staging'
    staging.mkdir()
    (staging / 'tidy_metaads.csv').write_text(
        'date_start,date_stop,campaign_id,adset_id,ad_id\n'
        '2024-01-01,2024-01-01,1,1,1\n'
    )
    from src.metaads.cleaners import metaads_staging2curated as mod
    return mod


def test_df_hash_matches_file_hash(tmp_path):
    mod = get_staging_module(tmp_path)
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    path = tmp_path / 'out.csv'
    df.to_csv(path, index=False)
    assert mod.df_hash(df) == mod.file_hash(path)


def get_raw_module(tmp_path):
    os.environ['PROJECT_ROOT'] = str(tmp_path)
    import types
    ipy = types.ModuleType('IPython')
    display_mod = types.ModuleType('display')
    display_mod.display = lambda *a, **k: None
    ipy.display = display_mod
    sys.modules['IPython'] = ipy
    sys.modules['IPython.display'] = display_mod
    raw_meta = tmp_path / 'raw' / 'metaads' / 'sample'
    raw_meta.mkdir(parents=True)
    import json
    ads_record = {
        'id': 1,
        'campaign_id': 1,
        'adset_id': 1,
        'name': 'ad',
        'status': 'active',
        'effective_status': 'active',
        'created_time': '2024-01-01',
        'updated_time': '2024-01-02',
        'creative': {'id': 'c1'},
        'tracking_specs': {}
    }
    json.dump([ads_record], open(raw_meta / 'ads.json', 'w'))
    adset_record = {'id': 1}
    campaign_record = {'id': 1}
    json.dump([adset_record], open(raw_meta / 'adsets.json', 'w'))
    json.dump([campaign_record], open(raw_meta / 'campaigns.json', 'w'))
    insight_record = {
        'campaign_id': 1,
        'adset_id': 1,
        'ad_id': 1,
        'date_start': '2024-01-01'
    }
    json.dump([insight_record], open(raw_meta / 'insights.json', 'w'))
    from src.metaads.cleaners import metaads_raw2staging as mod
    return mod


def test_stack_deduplicates_on_id(tmp_path):
    mod = get_raw_module(tmp_path)
    d1 = tmp_path / 'd1'
    d2 = tmp_path / 'd2'
    d1.mkdir()
    d2.mkdir()
    data1 = pd.DataFrame([{'id': 1, 'foo': 'a'}, {'id': 2, 'foo': 'b'}])
    data2 = pd.DataFrame([{'id': 2, 'foo': 'b'}, {'id': 3, 'foo': 'c'}])
    data1.to_json(d1 / 'ads.json')
    data2.to_json(d2 / 'ads.json')
    df = mod.stack([d1, d2], 'ads.json')
    assert set(df['id']) == {1, 2, 3}
