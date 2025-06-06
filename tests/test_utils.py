from src.utils import sanitize_filename


def test_sanitize_filename_strips_directory():
    malicious = '../evil.csv'
    assert sanitize_filename(malicious, 'safe.csv') == 'evil.csv'


def test_sanitize_filename_falls_back_when_empty():
    assert sanitize_filename('', 'safe.csv') == 'safe.csv'
