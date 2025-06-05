import os


def get_module(tmp_path):
    os.environ['PROJECT_ROOT'] = str(tmp_path)
    from src.distrokid.cleaners import distrokid_landing2raw as dlr
    return dlr


def test_validate_streams_html(tmp_path):
    dlr = get_module(tmp_path)
    f = tmp_path / 'streams_stats_20250101.html'
    f.write_text('"trend365day" "dataProvider": []')
    ok, msg = dlr.validate_streams_html(f)
    assert ok


def test_validate_apple_html(tmp_path):
    dlr = get_module(tmp_path)
    f = tmp_path / 'applemusic_stats_20250101.html'
    f.write_text('var chartData = [];' + '\n')
    ok, msg = dlr.validate_apple_html(f)
    assert ok


def test_validate_tsv(tmp_path):
    dlr = get_module(tmp_path)
    f = tmp_path / 'details.tsv'
    f.write_text('a\tb\n1\t2\n')
    ok, msg = dlr.validate_tsv(f)
    assert ok


def test_copy_if_new(tmp_path):
    dlr = get_module(tmp_path)
    src = tmp_path / 'file.txt'
    dest_dir = tmp_path / 'dest'
    dest_dir.mkdir()
    src.write_text('hello')
    assert dlr._copy_if_new(src, dest_dir) is True
    assert (dest_dir / src.name).exists()
    assert dlr._copy_if_new(src, dest_dir) is False
    src.write_text('new')
    assert dlr._copy_if_new(src, dest_dir) is True
    assert len(list(dest_dir.glob('file*.txt'))) == 2
