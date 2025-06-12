import hashlib
from pathlib import Path
import pandas as pd


def df_hash(df: pd.DataFrame) -> str:
    """Return MD5 hash of DataFrame contents."""
    return hashlib.md5(df.to_csv(index=False).encode()).hexdigest()


def file_hash(path: Path) -> str:
    """Return MD5 hash of file bytes."""
    return hashlib.md5(path.read_bytes()).hexdigest()
