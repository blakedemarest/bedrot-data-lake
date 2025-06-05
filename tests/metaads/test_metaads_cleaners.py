import os
import pandas as pd


def get_module(tmp_path):
    os.environ['PROJECT_ROOT'] = str(tmp_path)
    staging = tmp_path / 'staging'
    staging.mkdir()
    (staging / 'tidy_metaads.csv').write_text(
        'date_start,date_stop,campaign_id,adset_id,ad_id\n'
        '2024-01-01,2024-01-01,1,1,1\n'
    )
    # create minimal module
    from src.metaads.cleaners import metaads_staging2curated as mod
    return mod


def test_df_hash_matches_file_hash(tmp_path):
    mod = get_module(tmp_path)
    df = pd.DataFrame({'a':[1,2],'b':[3,4]})
    path = tmp_path / 'out.csv'
    df.to_csv(path, index=False)
    assert mod.df_hash(df) == mod.file_hash(path)
