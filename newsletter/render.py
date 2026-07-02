"""Render editions to HTML and maintain the GitHub Pages site."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape as xml_escape

import markdown as md

from . import config

log = logging.getLogger(__name__)

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — AI Update</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header class="masthead">
  <a class="brand" href="../index.html">AI&nbsp;Update</a>
  <div class="edition-date">{date_long}</div>
</header>
<hr class="rule">
<main class="edition">
{body}
</main>
<hr class="rule">
<footer>
  <p><a href="../index.html">&larr; All editions</a></p>
  <p class="colophon">Set twice weekly by machine, read by hand.</p>
</footer>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Update</title>
<link rel="stylesheet" href="style.css">
<link rel="alternate" type="application/rss+xml" title="AI Update" href="feed.xml">
</head>
<body>
<header class="masthead index-masthead">
  <h1 class="brand-large">AI&nbsp;Update</h1>
  <p class="tagline">Trends, techniques, tools &amp; mental models in AI — Sundays &amp; Wednesdays</p>
</header>
<hr class="rule">
<main class="index">
{entries}
</main>
<hr class="rule">
<footer>
  <p class="colophon">Set twice weekly by machine, read by hand. <a href="feed.xml">RSS</a></p>
</footer>
</body>
</html>
"""

ENTRY_TEMPLATE = """<article class="index-entry">
  <div class="entry-date">{date_long}</div>
  <h2><a href="editions/{slug}.html">{title}</a></h2>
  <p class="standfirst">{standfirst}</p>
</article>"""

FEED_MAX_ITEMS = 20

FEED_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>AI Update</title>
<link>{site_url}/</link>
<atom:link href="{site_url}/feed.xml" rel="self" type="application/rss+xml"/>
<description>Trends, techniques, tools &amp; mental models in AI — Sundays &amp; Wednesdays</description>
<language>en</language>
<lastBuildDate>{last_build_date}</lastBuildDate>
{items}
</channel>
</rss>
"""

FEED_ITEM_TEMPLATE = """<item>
<title>{title}</title>
<link>{link}</link>
<guid isPermaLink="true">{link}</guid>
<pubDate>{pub_date}</pubDate>
<description>{description}</description>
<content:encoded><![CDATA[{content}]]></content:encoded>
</item>"""


def parse_edition(markdown_text: str) -> tuple[str, str]:
    """Return (title, standfirst) from the edition markdown."""
    title_m = re.search(r"^#\s+(.+)$", markdown_text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else "Untitled edition"
    stand_m = re.search(r"^\*(.+?)\*\s*$", markdown_text, re.MULTILINE)
    standfirst = stand_m.group(1).strip() if stand_m else ""
    return title, standfirst


def markdown_to_html(markdown_text: str) -> str:
    return md.markdown(markdown_text, extensions=["extra", "sane_lists", "smarty"])


def write_edition(markdown_text: str, edition_date: date) -> dict:
    """Write the edition HTML + markdown, update the index. Returns metadata."""
    title, standfirst = parse_edition(markdown_text)
    slug = edition_date.isoformat()
    date_long = edition_date.strftime("%A, %B %-d, %Y")
    body = markdown_to_html(markdown_text)

    config.EDITIONS_DIR.mkdir(parents=True, exist_ok=True)
    (config.EDITIONS_DIR / f"{slug}.html").write_text(
        PAGE_TEMPLATE.format(title=title, date_long=date_long, body=body)
    )
    (config.EDITIONS_DIR / f"{slug}.md").write_text(markdown_text)

    meta = {"slug": slug, "title": title, "standfirst": standfirst, "date": slug}
    editions = _update_index(meta)
    _update_feed(editions)
    return meta


def _update_index(meta: dict) -> list[dict]:
    editions = []
    if config.EDITIONS_INDEX.exists():
        editions = json.loads(config.EDITIONS_INDEX.read_text())
    editions = [e for e in editions if e["slug"] != meta["slug"]]
    editions.append(meta)
    editions.sort(key=lambda e: e["slug"], reverse=True)
    config.EDITIONS_INDEX.write_text(json.dumps(editions, indent=2))

    entries = "\n".join(
        ENTRY_TEMPLATE.format(
            slug=e["slug"],
            title=e["title"],
            standfirst=e["standfirst"],
            date_long=date.fromisoformat(e["date"]).strftime("%A, %B %-d, %Y"),
        )
        for e in editions
    )
    (config.DOCS_DIR / "index.html").write_text(INDEX_TEMPLATE.format(entries=entries))
    return editions


def _extract_body(page_path) -> str:
    text = page_path.read_text()
    m = re.search(r'<main class="edition">\n(.*)\n</main>', text, re.DOTALL)
    return m.group(1) if m else ""


def _update_feed(editions: list[dict]) -> None:
    """Write docs/feed.xml with the most recent editions. Requires SITE_BASE_URL."""
    if not config.SITE_BASE_URL:
        log.info("SITE_BASE_URL not set — skipping feed.xml")
        return

    site_url = config.SITE_BASE_URL.rstrip("/")
    items = []
    for e in editions[:FEED_MAX_ITEMS]:
        page_path = config.EDITIONS_DIR / f"{e['slug']}.html"
        body = _extract_body(page_path) if page_path.exists() else ""
        link = f"{site_url}/editions/{e['slug']}.html"
        pub_dt = datetime.combine(
            date.fromisoformat(e["date"]), datetime.min.time(), tzinfo=timezone.utc
        )
        items.append(
            FEED_ITEM_TEMPLATE.format(
                title=xml_escape(e["title"]),
                link=xml_escape(link),
                pub_date=format_datetime(pub_dt),
                description=xml_escape(e["standfirst"]),
                content=body.replace("]]>", "]]]]><![CDATA[>"),
            )
        )

    feed_xml = FEED_TEMPLATE.format(
        site_url=xml_escape(site_url),
        last_build_date=format_datetime(datetime.now(timezone.utc)),
        items="\n".join(items),
    )
    (config.DOCS_DIR / "feed.xml").write_text(feed_xml)
