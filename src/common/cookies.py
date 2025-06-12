"""Shared utilities for Playwright cookie/session handling.

This module provides two helpers – ``load_cookies`` and ``load_cookies_async`` – 
which load one or more cookie JSON files from ``src/<service>/cookies`` into 
the provided Playwright *persistent* ``browser_context``.  It ensures:

1. **One-time import** per ``user_data_dir`` to avoid duplicate cookies.
2. **sameSite sanitisation** – invalid values coerced to "Lax" so Playwright
   will accept the cookie.
3. **Graceful no-op** when no cookie files are present.

Example
-------
```python
from playwright.sync_api import sync_playwright
from common.cookies import load_cookies

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(user_data_dir, headless=False)
    load_cookies(context, service_name="distrokid")
    page = context.new_page()
    ...
```

Example (async)
-------
```python
from playwright.async_api import async_playwright
from common.cookies import load_cookies_async

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(user_data_dir, headless=False)
        await load_cookies_async(context, service_name="distrokid")
        page = await context.new_page()
        ...

asyncio.run(main())
```
"""
from __future__ import annotations

import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

__all__ = ["load_cookies", "load_cookies_async"]

_VALID_SAMESITE: set[str] = {"Strict", "Lax", "None"}


def _resolve_cookie_dir(service: str) -> Path:
    """Return path to ``src/<service>/cookies`` (create if missing)."""
    root = Path(__file__).resolve().parents[1]
    cookie_dir = root / service / "cookies"
    cookie_dir.mkdir(parents=True, exist_ok=True)
    return cookie_dir


def _get_marker_path(context, service: str) -> Path:
    """Return a marker-file path scoped to *context*'s user_data_dir."""
    # The attr name differs between sync / async contexts; fall back to cwd.
    user_data_dir = getattr(context, "_user_data_dir", None)
    if not user_data_dir:
        # Fallback for non-persistent contexts – use current working dir.
        user_data_dir = os.getcwd()
    return Path(user_data_dir) / f".{service}_cookies_imported"


def _load_cookie_file(path: Path) -> List[Dict[str, Any]]:
    """Return cookies from ``path`` normalizing invalid values."""
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            data = data.get("cookies", [])
        if not isinstance(data, list):
            return []
        cookies = []
        for c in data:
            if "sameSite" in c and c["sameSite"] not in _VALID_SAMESITE:
                c["sameSite"] = "Lax"
            cookies.append(c)
        return cookies
    except Exception as exc:  # pragma: no cover – log but continue
        print(f"[WARN] Skipping cookie file {path}: {exc}")
        return []


def _collect_cookie_dicts(cookie_dir: Path) -> List[Dict[str, Any]]:
    cookies: List[Dict[str, Any]] = []
    for file in cookie_dir.glob("*.json"):
        cookies.extend(_load_cookie_file(file))
    return cookies


def load_cookies(context, service_name: str) -> None:
    """Inject cookies into *context* **once** per user_data_dir.

    Parameters
    ----------
    context
        A Playwright ``BrowserContext`` (usually persistent).
    service_name
        Name of the ETL service – must match sub-directory under ``src``.
    """
    cookie_dir = _resolve_cookie_dir(service_name)
    marker_path = _get_marker_path(context, service_name)

    if marker_path.exists():
        print(f"[cookies] {service_name}: already imported – skipping.")
        return

    cookie_dicts = _collect_cookie_dicts(cookie_dir)
    if not cookie_dicts:
        print(f"[cookies] {service_name}: no cookie files found – nothing to import.")
        return

    try:
        context.add_cookies(cookie_dicts)
        marker_path.write_text("imported")
        print(f"[cookies] {service_name}: imported {len(cookie_dicts)} cookies → marker created.")
    except Exception as exc:  # pragma: no cover – log but continue
        print(f"[ERROR] Failed to import cookies for {service_name}: {exc}")


async def load_cookies_async(context, service_name: str) -> None:
    """Asynchronous variant of ``load_cookies`` for Playwright ``async_api`` contexts."""
    cookie_dir = _resolve_cookie_dir(service_name)
    marker_path = _get_marker_path(context, service_name)

    if marker_path.exists():
        print(f"[cookies] {service_name}: already imported – skipping.")
        return

    cookie_dicts = _collect_cookie_dicts(cookie_dir)
    if not cookie_dicts:
        print(f"[cookies] {service_name}: no cookie files found – nothing to import.")
        return

    try:
        await context.add_cookies(cookie_dicts)  # type: ignore[arg-type]
        marker_path.write_text("imported")
        print(f"[cookies] {service_name}: imported {len(cookie_dicts)} cookies → marker created.")
    except Exception as exc:
        print(f"[ERROR] Failed to import cookies for {service_name}: {exc}")
