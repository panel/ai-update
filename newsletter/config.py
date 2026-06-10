"""Central configuration for the newsletter pipeline."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "sources.yaml"
DATA_DIR = REPO_ROOT / "data"
SEEN_FILE = DATA_DIR / "seen.json"
DOCS_DIR = REPO_ROOT / "docs"
EDITIONS_DIR = DOCS_DIR / "editions"
EDITIONS_INDEX = DOCS_DIR / "editions.json"

MODEL = "claude-opus-4-8"
MAX_OUTPUT_TOKENS = 32_000

# Hard ceiling on the estimated cost of a single run, in USD. The pipeline
# aborts before calling the API if the worst-case estimate exceeds this.
MAX_RUN_COST_USD = 7.00
INPUT_PRICE_PER_MTOK = 5.00
OUTPUT_PRICE_PER_MTOK = 25.00

# How far back to look for items, in days. Runs are Sun/Wed, so ~3.5 days
# plus slack for slow feeds.
LOOKBACK_DAYS = 5

# Keep seen-item records this long before pruning.
SEEN_RETENTION_DAYS = 45

# Caps to keep the prompt bounded.
MAX_TOTAL_ITEMS = 220
MAX_ITEMS_PER_SOURCE = 15
MAX_SUMMARY_CHARS = 1_200

FETCH_TIMEOUT = 15
USER_AGENT = "ai-update-newsletter/1.0 (personal newsletter generator)"

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_ADDRESS)

# Base URL of the published site, used for links in the email footer.
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "")
