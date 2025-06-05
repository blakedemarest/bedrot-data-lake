import os
import sys
from pathlib import Path
import pandas as pd
import pytest

# Ensure src/ is on the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})

@pytest.fixture
def project_root(tmp_path, monkeypatch):
    monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
    return tmp_path
