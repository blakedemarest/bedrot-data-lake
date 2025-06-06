from pathlib import Path


def sanitize_filename(suggested: str | None, default: str) -> str:
    """Return a safe filename derived from a suggested filename.

    Any directory components are stripped and an empty result falls back to
    ``default``.
    """
    if suggested is None:
        return default
    name = Path(suggested).name
    if not name or not name.strip():
        return default
    return name
