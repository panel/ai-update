"""Track which items have already appeared in a previous edition."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse

from . import config
from .fetch import Item


def _canonical(url: str) -> str:
    """Normalize a URL so trivial variants dedupe (strip query/fragment, www)."""
    p = urlparse(url)
    netloc = p.netloc.lower().removeprefix("www.")
    return urlunparse((p.scheme, netloc, p.path.rstrip("/"), "", "", ""))


def load_seen() -> dict:
    if config.SEEN_FILE.exists():
        return json.loads(config.SEEN_FILE.read_text())
    return {}


def filter_new(items: list[Item], seen: dict) -> list[Item]:
    fresh, used = [], set()
    for item in items:
        key = _canonical(item.url)
        if key in seen or key in used:
            continue
        used.add(key)
        fresh.append(item)
    return fresh


def mark_seen(items: list[Item], seen: dict) -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    for item in items:
        seen[_canonical(item.url)] = today
    # Prune old entries so the file doesn't grow forever.
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=config.SEEN_RETENTION_DAYS)
    ).date().isoformat()
    return {k: v for k, v in seen.items() if v >= cutoff}


def save_seen(seen: dict) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.SEEN_FILE.write_text(json.dumps(seen, indent=0, sort_keys=True))
