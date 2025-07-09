import os
from pathlib import Path


def get_module(tmp_path):
    os.environ['PROJECT_ROOT'] = str(tmp_path)
    from src import archive_old_data as mod
    return mod


def test_group_files(tmp_path):
    mod = get_module(tmp_path)
    files = [
        tmp_path / 'foo_20250526.json',
        tmp_path / 'foo_20250527.json',
        tmp_path / 'bar.txt'
    ]
    for f in files:
        f.write_text('x')
    groups = mod.group_files(files)
    assert set(groups.keys()) == {'foo', 'bar'}
    assert set(groups['foo']) == set(files[:2])
    assert groups['bar'] == [files[2]]
