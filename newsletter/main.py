"""Orchestrate a full newsletter run: fetch → dedupe → synthesize → publish → email."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from . import config, dedupe
from .emailer import send_edition
from .fetch import fetch_all
from .render import markdown_to_html, write_edition
from .synthesize import _previous_edition_context, synthesize

log = logging.getLogger(__name__)

MIN_ITEMS = 10


def run(send_email: bool = True, dry_run: bool = False) -> None:
    edition_date = date.today()

    items = fetch_all()
    log.info("fetched %d items total", len(items))

    seen = dedupe.load_seen()
    items = dedupe.filter_new(items, seen)
    log.info("%d items after dedupe", len(items))

    if len(items) < MIN_ITEMS:
        log.warning("only %d new items — skipping this edition", len(items))
        return

    # Bound the prompt: keep editorial sources intact, trim trend noise last.
    if len(items) > config.MAX_TOTAL_ITEMS:
        priority = {"lab": 0, "writer": 1, "publication": 2, "repo": 3, "trend": 4, "social": 5}
        items.sort(key=lambda i: priority.get(i.category, 9))
        items = items[: config.MAX_TOTAL_ITEMS]
        log.info("trimmed to %d items", len(items))

    if dry_run:
        log.info("dry run — stopping before synthesis")
        return

    docs_dir = Path(__file__).parent.parent / "docs"
    prev_context = _previous_edition_context(docs_dir)
    if prev_context:
        log.info("including previous edition context for deduplication")

    markdown_text = synthesize(items, edition_date, prev_context=prev_context)

    meta = write_edition(markdown_text, edition_date)
    log.info("published edition: %s — %s", meta["slug"], meta["title"])

    dedupe.save_seen(dedupe.mark_seen(items, seen))

    if send_email:
        date_long = edition_date.strftime("%A, %B %-d, %Y")
        send_edition(
            body_html=markdown_to_html(markdown_text),
            title=meta["title"],
            date_long=date_long,
            slug=meta["slug"],
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description="Generate an AI Update edition.")
    parser.add_argument("--no-email", action="store_true", help="publish only, skip email")
    parser.add_argument("--dry-run", action="store_true", help="fetch + dedupe only, no API call")
    args = parser.parse_args()

    try:
        run(send_email=not args.no_email, dry_run=args.dry_run)
    except Exception:
        log.exception("run failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
