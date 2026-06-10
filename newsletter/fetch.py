"""Fetch items from all configured sources.

Every fetcher is best-effort: a failing source logs a warning and is skipped,
so one dead feed (or RSSHub rate-limiting) never kills a run.
"""

from __future__ import annotations

import html
import logging
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

from . import config

log = logging.getLogger(__name__)


@dataclass
class Item:
    source: str
    category: str  # writer | publication | lab | trend | social | repo
    title: str
    url: str
    published: str  # ISO date or ""
    summary: str = ""
    signal: str = ""  # e.g. "320 points", "2,400 stars this week"
    tags: list = field(default_factory=list)


def _clean(text: str, limit: int = config.MAX_SUMMARY_CHARS) -> str:
    if not text:
        return ""
    text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit]


def _entry_date(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(time.mktime(parsed), tz=timezone.utc)
    return None


def _matches_keywords(entry, keywords) -> bool:
    haystack = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
    return any(k.lower() in haystack for k in keywords)


# Some hosts (Substack especially) intermittently serve block pages to
# non-browser user agents; a browser-like UA gets far fewer of them.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Literal control characters are the most common cause of feedparser's
# "not well-formed (invalid token)" on otherwise-valid feeds.
_XML_ILLEGAL = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")

RETRIES = 3


def _http_get(url: str, browser_ua: bool = False, **kwargs) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(RETRIES):
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": BROWSER_UA if browser_ua else config.USER_AGENT},
                timeout=config.FETCH_TIMEOUT,
                **kwargs,
            )
            # Retry transient server-side statuses; fail fast on real 4xx.
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{resp.status_code} (transient)", response=resp)
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status is not None and status not in (429, 500, 502, 503, 504):
                raise  # genuine client error — retrying won't help
            last_exc = e
            if attempt < RETRIES - 1:
                time.sleep(2 ** attempt + random.uniform(0, 1))
    raise last_exc  # type: ignore[misc]


def _fetch_and_parse(url: str):
    """Fetch a feed with retries and parse it, tolerating common defects."""
    resp = _http_get(url, browser_ua=True)
    content = resp.content
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        # Last resort: strip illegal control chars and re-parse.
        cleaned = _XML_ILLEGAL.sub(b"", content)
        reparsed = feedparser.parse(cleaned)
        if reparsed.entries:
            return reparsed
        ctype = resp.headers.get("content-type", "?")
        snippet = content[:120].decode("utf-8", "replace")
        raise RuntimeError(
            f"feed unparseable (http {resp.status_code}, {ctype}): "
            f"{parsed.bozo_exception} — starts with: {snippet!r}"
        )
    return parsed


def fetch_feed(feed_cfg: dict, cutoff: datetime) -> list[Item]:
    name = feed_cfg["name"]
    parsed = _fetch_and_parse(feed_cfg["url"])

    keywords = feed_cfg.get("keyword_filter")
    max_items = feed_cfg.get("max_items", config.MAX_ITEMS_PER_SOURCE)
    items = []
    for entry in parsed.entries:
        when = _entry_date(entry)
        if when and when < cutoff:
            continue
        if keywords and not _matches_keywords(entry, keywords):
            continue
        link = entry.get("link", "")
        title = _clean(entry.get("title", ""), 300)
        if not link or not title:
            continue
        items.append(
            Item(
                source=name,
                category=feed_cfg.get("category", "publication"),
                title=title,
                url=link,
                published=when.date().isoformat() if when else "",
                summary=_clean(entry.get("summary", "")),
            )
        )
        if len(items) >= max_items:
            break
    return items


def fetch_hf_papers(papers_cfg: dict, cutoff: datetime) -> list[Item]:
    resp = _http_get("https://huggingface.co/api/daily_papers?limit=50")
    items = []
    for entry in resp.json():
        paper = entry.get("paper", {})
        upvotes = paper.get("upvotes", 0)
        if upvotes < papers_cfg.get("min_upvotes", 10):
            continue
        when = None
        if entry.get("publishedAt"):
            try:
                when = datetime.fromisoformat(
                    entry["publishedAt"].replace("Z", "+00:00")
                )
            except ValueError:
                pass
        if when and when < cutoff:
            continue
        paper_id = paper.get("id", "")
        items.append(
            Item(
                source="Hugging Face Papers",
                category="trend",
                title=_clean(paper.get("title", ""), 300),
                url=f"https://huggingface.co/papers/{paper_id}",
                published=when.date().isoformat() if when else "",
                summary=_clean(paper.get("summary", "")),
                signal=f"{upvotes} upvotes",
            )
        )
        if len(items) >= papers_cfg.get("max_items", 8):
            break
    return items


def _reddit_rss_fallback(sub_cfg: dict, cutoff: datetime) -> list[Item]:
    """Reddit blocks JSON for unauthenticated bots fairly often; the RSS feed
    is more permissive but carries no scores, so take the top few hot posts."""
    sub = sub_cfg["subreddit"]
    parsed = _fetch_and_parse(f"https://www.reddit.com/r/{sub}/hot/.rss")
    items = []
    for entry in parsed.entries:
        when = _entry_date(entry)
        if when and when < cutoff:
            continue
        items.append(
            Item(
                source=f"r/{sub}",
                category="trend",
                title=_clean(entry.get("title", ""), 300),
                url=entry.get("link", ""),
                published=when.date().isoformat() if when else "",
                summary=_clean(entry.get("summary", ""), 600),
            )
        )
        if len(items) >= min(sub_cfg.get("max_items", 10), 8):
            break
    return items


def fetch_reddit(sub_cfg: dict, cutoff: datetime) -> list[Item]:
    sub = sub_cfg["subreddit"]
    try:
        resp = _http_get(f"https://www.reddit.com/r/{sub}/hot.json?limit=50")
        posts = resp.json()["data"]["children"]
    except requests.HTTPError:
        return _reddit_rss_fallback(sub_cfg, cutoff)
    items = []
    for post in posts:
        d = post["data"]
        if d.get("stickied") or d.get("score", 0) < sub_cfg.get("min_score", 100):
            continue
        when = datetime.fromtimestamp(d["created_utc"], tz=timezone.utc)
        if when < cutoff:
            continue
        items.append(
            Item(
                source=f"r/{sub}",
                category="trend",
                title=_clean(d.get("title", ""), 300),
                url=f"https://www.reddit.com{d['permalink']}",
                published=when.date().isoformat(),
                summary=_clean(d.get("selftext", "")),
                signal=f"{d['score']} upvotes, {d.get('num_comments', 0)} comments",
            )
        )
        if len(items) >= sub_cfg.get("max_items", 10):
            break
    return items


def fetch_github_trending(trend_cfg: dict) -> list[Item]:
    resp = _http_get(trend_cfg["url"])
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for row in soup.select("article.Box-row"):
        link_el = row.select_one("h2 a")
        if not link_el:
            continue
        repo = link_el.get("href", "").strip("/")
        desc_el = row.select_one("p")
        stars_el = row.find(string=re.compile(r"stars (this week|today)"))
        stars = ""
        if stars_el:
            stars = _clean(str(stars_el.parent.get_text()), 60)
        items.append(
            Item(
                source=f"GitHub Trending ({trend_cfg['language']})",
                category="repo",
                title=repo,
                url=f"https://github.com/{repo}",
                summary=_clean(desc_el.get_text() if desc_el else "", 400),
                published="",
                signal=stars,
            )
        )
        if len(items) >= 15:
            break
    return items


def fetch_twitter(handle: str, templates: list[str], cutoff: datetime) -> list[Item]:
    parsed = None
    last_exc: Exception | None = None
    for template in templates:
        try:
            parsed = _fetch_and_parse(template.format(handle=handle))
            break
        except Exception as e:  # noqa: BLE001 — try the next mirror
            last_exc = e
    if parsed is None:
        raise last_exc or RuntimeError("no twitter sources configured")
    items = []
    for entry in parsed.entries[:8]:
        when = _entry_date(entry)
        if when and when < cutoff:
            continue
        text = _clean(entry.get("title", "") or entry.get("summary", ""), 500)
        # Skip bare retweets and trivial posts.
        if not text or text.startswith("RT ") or len(text) < 60:
            continue
        items.append(
            Item(
                source=f"@{handle}",
                category="social",
                title=text[:140],
                url=entry.get("link", ""),
                published=when.date().isoformat() if when else "",
                summary=text,
            )
        )
    return items


def fetch_all() -> list[Item]:
    cfg = yaml.safe_load(config.SOURCES_FILE.read_text())
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
    items: list[Item] = []

    for feed_cfg in cfg.get("feeds", []):
        try:
            fetched = fetch_feed(feed_cfg, cutoff)
            items.extend(fetched)
            log.info("feed %-40s %d items", feed_cfg["name"], len(fetched))
        except Exception as e:  # noqa: BLE001 — sources are best-effort
            log.warning("feed %s failed: %s", feed_cfg["name"], e)

    if cfg.get("hf_papers"):
        try:
            fetched = fetch_hf_papers(cfg["hf_papers"], cutoff)
            items.extend(fetched)
            log.info("hf papers %d items", len(fetched))
        except Exception as e:  # noqa: BLE001
            log.warning("hf papers failed: %s", e)

    for sub_cfg in cfg.get("reddit", []):
        try:
            fetched = fetch_reddit(sub_cfg, cutoff)
            items.extend(fetched)
            log.info("reddit r/%-15s %d items", sub_cfg["subreddit"], len(fetched))
        except Exception as e:  # noqa: BLE001
            log.warning("reddit r/%s failed: %s", sub_cfg["subreddit"], e)

    for trend_cfg in cfg.get("github_trending", []):
        try:
            fetched = fetch_github_trending(trend_cfg)
            items.extend(fetched)
            log.info("gh trending %-10s %d items", trend_cfg["language"], len(fetched))
        except Exception as e:  # noqa: BLE001
            log.warning("github trending %s failed: %s", trend_cfg["language"], e)

    tw = cfg.get("twitter", {})
    templates = tw.get("url_templates", [])
    tw_items, tw_ok, tw_failed = 0, 0, []
    for handle in tw.get("handles", []):
        try:
            fetched = fetch_twitter(handle, templates, cutoff)
            items.extend(fetched)
            tw_items += len(fetched)
            tw_ok += 1
            time.sleep(0.5)  # be polite to the nitter instance
        except Exception as e:  # noqa: BLE001
            tw_failed.append(handle)
            log.debug("twitter @%s failed: %s", handle, e)
    if templates:
        log.info(
            "twitter: %d items from %d/%d handles%s",
            tw_items,
            tw_ok,
            tw_ok + len(tw_failed),
            f" (failed: {', '.join('@' + h for h in tw_failed)})" if tw_failed else "",
        )

    return items
