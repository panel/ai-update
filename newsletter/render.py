"""Render editions to HTML and maintain the GitHub Pages site."""

from __future__ import annotations

import json
import re
from datetime import date

import markdown as md

from . import config

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
  <p class="colophon">Set twice weekly by machine, read by hand.</p>
</footer>
</body>
</html>
"""

ENTRY_TEMPLATE = """<article class="index-entry">
  <div class="entry-date">{date_long}</div>
  <h2><a href="editions/{slug}.html">{title}</a></h2>
  <p class="standfirst">{standfirst}</p>
</article>"""


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
    _update_index(meta)
    return meta


def _update_index(meta: dict) -> None:
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
