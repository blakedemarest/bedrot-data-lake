import os
import sys
from pathlib import Path
import pytest

# Ensure src/ is on the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

@pytest.fixture
def project_root(tmp_path, monkeypatch):
    monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
    return tmp_path
