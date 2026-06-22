"""Synthesize fetched items into a newsletter edition with Claude."""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path

import anthropic

from . import config
from .fetch import Item

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the editor of a twice-weekly personal AI newsletter for one reader: a \
software developer who follows AI tooling closely. Your single most important \
job is making sure the reader does not miss big things — new techniques, \
tools, workflows, models, or mental models coming onto the scene.

Editorial principles:
- Organize by TRENDS and THEMES, never by source or article. Synthesize: when \
three sources circle the same idea, name the idea and connect them.
- When a summary of the previous edition is provided, treat those themes as \
already covered. Only return to them if this period contains a genuinely \
significant new development — and if so, frame it as an update, not a \
re-introduction.
- Every theme and every claim must link out so the reader can jump off and go \
deeper. Use inline markdown links on meaningful phrases, not bare URLs.
- Separate signal from noise. Skip press releases, marketing, and incremental \
news with no technical substance. A small sharp edition beats a long dull one.
- Calibrate confidence: distinguish "this is clearly landing" from "early \
signal, watch this."
- Voice: literate, direct, a touch dry. Think a well-read colleague's Sunday \
letter, not a content-marketing digest.

Structure the edition exactly as follows, in markdown:

# <An evocative, specific title for this edition — not "AI Newsletter">

*One- or two-sentence standfirst summarizing the edition.*

## The Big Picture
2-4 paragraphs synthesizing the dominant theme(s) of the period. What shifted? \
What does it mean for how the reader works?

## Themes
3-5 themed sections, each with a `### <Theme title>` heading, 1-3 paragraphs of \
synthesis, and a short "Go deeper:" line of 2-5 links.

## Radar
A bulleted list (6-12 bullets) of concrete new things worth knowing about: \
tools, repos, models, papers, techniques. Each bullet: **[Name](url)** — one \
sentence on what it is and why it matters. Include adoption signals (stars, \
points) when notable.

## Don't Miss
1-3 short items that don't fit a theme but the reader would regret missing — \
a great essay, a mental-model piece, an important policy development.

Rules:
- Output ONLY the markdown edition. No preamble, no meta-commentary.
- Use only links that appear in the source material. Never invent URLs.
- If the period is genuinely quiet, say so honestly and keep it short."""


def _previous_edition_context(docs_dir: Path) -> str | None:
    index_path = docs_dir / "editions.json"
    if not index_path.exists():
        return None
    index = json.loads(index_path.read_text())
    if not index:
        return None
    latest = index[0]  # most recent first
    md_path = docs_dir / "editions" / f"{latest['slug']}.md"
    if not md_path.exists():
        return None
    text = md_path.read_text()

    # Extract title (first # line)
    title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = title_match.group(1) if title_match else latest.get("title", "")

    # Extract standfirst (first *…* block)
    stand_match = re.search(r"^\*(.+?)\*$", text, re.MULTILINE)
    standfirst = stand_match.group(1) if stand_match else ""

    # Extract theme headings under ## Themes
    themes_match = re.search(r"^## Themes\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    themes: list[str] = []
    if themes_match:
        themes = re.findall(r"^### (.+)$", themes_match.group(1), re.MULTILINE)

    lines = [f'Previous edition — "{title}" ({latest["date"]})']
    if standfirst:
        lines.append(f"Standfirst: {standfirst}")
    if themes:
        lines.append("Themes covered: " + " · ".join(themes))
    return "\n".join(lines)


def _format_items(items: list[Item]) -> str:
    by_category: dict[str, list[Item]] = {}
    for item in items:
        by_category.setdefault(item.category, []).append(item)

    order = ["lab", "writer", "publication", "trend", "repo", "social"]
    labels = {
        "lab": "LAB & COMPANY ANNOUNCEMENTS",
        "writer": "INDIVIDUAL WRITERS & THINKERS",
        "publication": "NEWSLETTERS & PUBLICATIONS",
        "trend": "TREND SIGNALS (HN / Reddit / Papers / Product Hunt)",
        "repo": "GITHUB TRENDING",
        "social": "X / TWITTER",
    }
    blocks = []
    for cat in order:
        group = by_category.get(cat)
        if not group:
            continue
        lines = [f"=== {labels[cat]} ==="]
        for it in group:
            lines.append(f"- [{it.source}] {it.title}")
            lines.append(f"  url: {it.url}")
            if it.published:
                lines.append(f"  date: {it.published}")
            if it.signal:
                lines.append(f"  signal: {it.signal}")
            if it.summary and it.summary != it.title:
                lines.append(f"  summary: {it.summary}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _build_messages(
    items: list[Item], edition_date: date, prev_context: str | None = None
) -> list[dict]:
    corpus = _format_items(items)
    prev_block = (
        f"--- PREVIOUS EDITION SUMMARY ---\n{prev_context}\n--- END PREVIOUS EDITION ---\n\n"
        if prev_context
        else ""
    )
    user_msg = (
        f"Edition date: {edition_date.strftime('%A, %B %-d, %Y')}\n"
        f"{prev_block}"
        f"Source material ({len(items)} items collected since the last "
        f"edition):\n\n{corpus}\n\nWrite the edition."
    )
    return [{"role": "user", "content": user_msg}]


def estimate_cost(client: anthropic.Anthropic, messages: list[dict]) -> float:
    """Worst-case run cost in USD (full input + maximum output)."""
    count = client.messages.count_tokens(
        model=config.MODEL, system=SYSTEM_PROMPT, messages=messages
    )
    input_cost = count.input_tokens * config.INPUT_PRICE_PER_MTOK / 1_000_000
    output_cost = config.MAX_OUTPUT_TOKENS * config.OUTPUT_PRICE_PER_MTOK / 1_000_000
    log.info(
        "input tokens: %d — worst-case cost: $%.2f",
        count.input_tokens,
        input_cost + output_cost,
    )
    return input_cost + output_cost


def synthesize(
    items: list[Item], edition_date: date, prev_context: str | None = None
) -> str:
    client = anthropic.Anthropic()
    messages = _build_messages(items, edition_date, prev_context)

    cost = estimate_cost(client, messages)
    if cost > config.MAX_RUN_COST_USD:
        raise RuntimeError(
            f"Estimated worst-case cost ${cost:.2f} exceeds the "
            f"${config.MAX_RUN_COST_USD:.2f} cap — aborting before the API call. "
            f"Reduce MAX_TOTAL_ITEMS or MAX_SUMMARY_CHARS in config.py."
        )

    with client.messages.stream(
        model=config.MODEL,
        max_tokens=config.MAX_OUTPUT_TOKENS,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        message = stream.get_final_message()

    usage = message.usage
    actual = (
        usage.input_tokens * config.INPUT_PRICE_PER_MTOK
        + usage.output_tokens * config.OUTPUT_PRICE_PER_MTOK
    ) / 1_000_000
    log.info(
        "synthesis done — in: %d tok, out: %d tok, cost: $%.2f",
        usage.input_tokens,
        usage.output_tokens,
        actual,
    )

    markdown = "".join(b.text for b in message.content if b.type == "text").strip()
    if not markdown.startswith("#"):
        raise RuntimeError("Model output did not start with a title heading.")
    return markdown
